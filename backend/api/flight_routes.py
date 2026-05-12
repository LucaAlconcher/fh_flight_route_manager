from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.wpml_parser import parse_dji_waypoints
from utils.collision_math import calculate_route_collisions
from database import SessionLocal, FlightRoute, Waypoint, Annotation, AnnotationState
from dotenv import load_dotenv
from datetime import datetime
import requests
import zipfile
import json
import os

load_dotenv()

from clients.instance import fh_client

router = APIRouter(prefix="/api/flight_routes", tags=["flight_routes"])

ROUTES_DIR = "./storage/flight_routes"

x_project_uuid=os.getenv("FH_PROJECT_UUID")

# Dependency to get DB session
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

@router.get("")
def get_flights(db: Session = Depends(get_db)):
  try:
    # 1. Fetch all routes from the database
    routes = db.query(FlightRoute).all()
    
    # 2. Build response and selectively attach waypoints
    response_data = []
    for r in routes:
      # Convert SQLAlchemy model to a standard dictionary
      route_dict = {col.name: getattr(r, col.name) for col in r.__table__.columns}
      
      # Only fetch and attach waypoints if digested and marked for execution
      if r.sync_status == "PROCESSED" and r.is_execution_route:
        wps = db.query(Waypoint).filter(
          Waypoint.route_id == r.id
        ).order_by(Waypoint.index).all()
        
        route_dict["waypoints"] = [
          {
            "id": wp.id,
            "index": wp.index,
            "latitude": wp.latitude,
            "longitude": wp.longitude,
            "height": wp.height
          }
          for wp in wps
        ]
      else:
        route_dict["waypoints"] = []
        
      response_data.append(route_dict)

    return response_data

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
def validate(db: Session = Depends(get_db)):

  target_routes = db.query(FlightRoute).filter(
    FlightRoute.sync_status == "PROCESSED",
    FlightRoute.is_execution_route == True
  ).all()

  route_ids = [r.id for r in target_routes]

  if route_ids:
    waypoints = db.query(Waypoint).filter(
      Waypoint.route_id.in_(route_ids)
    ).all()
  else:
    waypoints = []

  compromised_annos = db.query(Annotation).join(
    AnnotationState, Annotation.id == AnnotationState.annotation_id
  ).filter(
    AnnotationState.compromised == True 
  ).all()

  route_collisions = calculate_route_collisions(target_routes, waypoints, compromised_annos)

  return {"status": "success", "message": "Validation complete", "route_collisions": route_collisions}

@router.post("/sync")
def sync_flights(db: Session = Depends(get_db)):
  try:
    # Pass 1: Get List
    list_resp = fh_client.get_project_flight_routes()
    raw_routes_from_api = list_resp.get("data", {}).get("list", [])

    unique_routes = {}
    for item in raw_routes_from_api:
      rid = item["id"]
      # If we haven't seen it, OR if this duplicate has a newer update_time, keep it
      if rid not in unique_routes or unique_routes[rid]["update_time"] < item["update_time"]:
        unique_routes[rid] = item

    for route_id, item in unique_routes.items():

      safe_id = str(route_id).strip()
      existing = db.query(FlightRoute).filter(FlightRoute.id == safe_id).first()

      t_types = item.get("template_types")
      p_info = item.get("payload_information")

      # If new or update_time changed, wipe dependent data and update
      if not existing or existing.update_time < item["update_time"]:
        route_data = {
          "id": route_id,
          "project_uuid": fh_client.project_uuid,
          "name": item.get("name"),
          "size": item.get("size"),
          "device_model_key": item.get("device_model_key"),
          "update_time": item.get("update_time"),
          "template_types": json.dumps(t_types) if isinstance(t_types, (list, dict)) else str(t_types),
          "payload_information": json.dumps(p_info) if isinstance(p_info, (list, dict)) else str(p_info),
          "sync_status": "PENDING"
        }

        if existing:
          db.query(Waypoint).filter(Waypoint.route_id == existing.id).delete()
          existing.waypoints = []
          existing.download_url = None
          existing.distance = None
          existing.wayline_point_nums = None
          existing.actual_size = None
          
          for key, value in route_data.items():
            setattr(existing, key, value)
        else:
          db.add(FlightRoute(**route_data))

        db.flush()
    
    db.commit()

    updated_routes = db.query(FlightRoute).filter(
      FlightRoute.project_uuid == fh_client.project_uuid
    ).all()
    
    # Pass 3: Build response and selectively attach waypoints
    response_data = []
    for r in updated_routes:
      # Convert SQLAlchemy model to a standard dictionary
      route_dict = {col.name: getattr(r, col.name) for col in r.__table__.columns}
      
      # Only fetch and attach waypoints if it meets your exact criteria
      if r.sync_status == "PROCESSED" and r.is_execution_route:
        wps = db.query(Waypoint).filter(
          Waypoint.route_id == r.id
        ).order_by(Waypoint.index).all()
        
        route_dict["waypoints"] = [
          {
            "id": wp.id,
            "index": wp.index,
            "latitude": wp.latitude,
            "longitude": wp.longitude,
            "height": wp.height
          }
          for wp in wps
        ]
      else:
        route_dict["waypoints"] = []
        
      response_data.append(route_dict)

    return response_data

  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(e))

@router.post("/details")
def sync_details(db: Session = Depends(get_db)):
  try:
    # 1. Find all records marked as PENDING from the previous list sync
    targets = db.query(FlightRoute).filter(
      FlightRoute.sync_status == "PENDING",
      FlightRoute.is_execution_route == True
    ).all()
    
    synced_count = 0
    errors = []

    for route in targets:
      try:
        # 2. Call the Detail API for this specific route
        detail_resp = fh_client.get_project_flight_route_details(route.id)
        details = detail_resp.get("data", {})
        
        # 3. Flatten the response into our existing record
        route.download_url = details.get("download_url")
        route.distance = details.get("distance")
        route.wayline_point_nums = details.get("wayline_point_nums")
        
        # If detail API has fresher payload info, update it
        if "payload_information" in details:
          route.payload_information = details.get("payload_information")
        
        # 4. Mark as SYNCED so we don't process it again next time
        route.sync_status = "SYNCED"
        
        synced_count += 1
        
      except Exception as e:
        print(f"Error fetching details for {route.id}: {e}")
        route.sync_status = "ERROR"
        errors.append({"id": route.id, "error": str(e)})

    db.commit()
    return {
      "status": "details_synced",
      "total_processed": synced_count,
      "failed": len(errors),
      "errors": errors
    }

  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(e))
  
@router.post("/download_files")
def download_flight_route_files(db: Session = Depends(get_db)):
    # 1. Find targets: SYNCED + Execution
    targets = db.query(FlightRoute).filter(
        FlightRoute.sync_status == "SYNCED",
        FlightRoute.is_execution_route == True,
        FlightRoute.download_url != None
    ).all()

    processed_count = 0
    results = []

    for route in targets:
        try:
            # 2. Setup paths
            project_path = os.path.join(ROUTES_DIR, route.project_uuid)
            os.makedirs(project_path, exist_ok=True)
            
            kmz_path = os.path.join(project_path, f"{route.id}.kmz")
            extract_path = os.path.join(project_path, route.id)

            # 3. Download the KMZ
            resp = requests.get(route.download_url, timeout=30)
            resp.raise_for_status()
            
            with open(kmz_path, "wb") as f:
                f.write(resp.content)

            # 4. Extract KMZ (it's a zip)
            with zipfile.ZipFile(kmz_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # 5. Update DB Status
            route.local_file_path = os.path.abspath(extract_path)
            route.actual_size = os.path.getsize(kmz_path)
            route.sync_status = "DOWNLOADED"
            processed_count += 1
            results.append({"id": route.id, "status": "success"})

        except Exception as e:
            print(f"❌ Error processing {route.id}: {e}")
            results.append({"id": route.id, "status": "error", "message": str(e)})

    db.commit()
    return {
        "processed": processed_count,
        "details": results
    }

@router.post("/process_files")
def process_flight_route_files(db: Session = Depends(get_db)):
  # 1. Find targets: SYNCED + Execution
  targets = db.query(FlightRoute).filter(
    FlightRoute.sync_status == "DOWNLOADED",
    FlightRoute.is_execution_route == True,
    FlightRoute.local_file_path != None
  ).all()

  processed_count = 0
  results = []

  print(len(targets))


  for route in targets:
    print(route.name)
    try:
      # 2. Setup paths
      project_path = os.path.join(ROUTES_DIR, route.project_uuid)
      extract_path = os.path.join(project_path, route.id)

      wpml_path = os.path.join(extract_path, "wpmz", "waylines.wpml")

      waypoints = parse_dji_waypoints(wpml_path)

      db.query(Waypoint).filter(Waypoint.route_id == route.id).delete()

      db_waypoints = [
          Waypoint(
              route_id=route.id,
              index=wp["index"],
              latitude=wp["latitude"],
              longitude=wp["longitude"],
              height=wp["height"]
          ) 
          for wp in waypoints
      ]

      db.add_all(db_waypoints)
      route.sync_status = "PROCESSED"
      processed_count += 1
      results.append({"id": route.id, "status": "success"})

    except Exception as e:
      print(f"❌ Error processing {route.id}: {e}")
      results.append({"id": route.id, "status": "error", "message": str(e)})

  db.commit()
  return {
      "processed": processed_count,
      "details": results
  }


@router.post("/toggle_execution/{route_id}")
def toggle_execution(route_id: str, db: Session = Depends(get_db)):
  route = db.query(FlightRoute).filter(FlightRoute.id == route_id).first()
  if not route:
    raise HTTPException(status_code=404, detail="Route not found")
  
  # Flip the boolean
  route.is_execution_route = not route.is_execution_route
  db.commit()
  
  return {"id": route.id, "is_execution_route": route.is_execution_route}