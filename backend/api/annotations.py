from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, Annotation, AnnotationState
from dotenv import load_dotenv
import os
import json
import glob

load_dotenv()

router = APIRouter(prefix="/api/annotations", tags=["annotations"])

ANNOTATIONS_DIR = "./storage/annotations"

x_project_uuid=os.getenv("FH_PROJECT_UUID")

# Dependency to get DB session
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()




@router.get("")
def get_annotations(db: Session = Depends(get_db)):
    # Join Annotations with their persistent States
    results = db.query(
        Annotation, 
        AnnotationState.compromised
    ).outerjoin(
        AnnotationState, Annotation.id == AnnotationState.annotation_id
    ).all()

    # Format into a clean list for React
    output = []
    for anno, compromised in results:
        data = {
            "id": anno.id,
            "name": anno.name,
            "latitude": anno.latitude,
            "longitude": anno.longitude,
            "color": anno.color,
            "compromised": compromised if compromised is not None else False
        }
        output.append(data)
    
    return output

@router.post("/toggle_compromised/{anno_id}")
def toggle_compromised(anno_id: str, db: Session = Depends(get_db)):
    state = db.query(AnnotationState).filter(AnnotationState.annotation_id == anno_id).first()
    
    if not state:
        # If it's the first time we're touching this annotation, create the state
        state = AnnotationState(annotation_id=anno_id, compromised=True)
        db.add(state)
    else:
        state.compromised = not state.compromised
    
    db.commit()
    return {"id": anno_id, "compromised": state.compromised}

@router.post("/sync")
def sync_annotations(db: Session = Depends(get_db)):
  try:
    if not os.path.exists(ANNOTATIONS_DIR):
      raise HTTPException(status_code=404, detail=f"Folder {ANNOTATIONS_DIR} not found")

    files = glob.glob(os.path.join(ANNOTATIONS_DIR, f"{x_project_uuid}_*.json"))
    
    if not files:
      return {"message": "No annotation files found"}
    
    files.sort(reverse=True)
    latest_file = files[0]

    print(f"🚀 Processing latest file: {latest_file}")



    # 4. Read the JSON content
    with open(latest_file, 'r', encoding='utf-8') as f:
      json_data = json.load(f)

    data = json_data.get('data')

    filename = os.path.basename(latest_file)
    _ = filename.split('_')
    if len(_) >= 2:
      project_uuid = _[0]
      date = _[1]

    db.query(Annotation).filter(Annotation.project_uuid == project_uuid).delete()

    if isinstance(data, list):
      for item in data:
        if item.get('type') == 0:
          elements = item.get('elements')
          if isinstance(elements, list):
            # point_list = []
            for element in elements:

              display = element.get('display')
              if not display: continue

              resource = element.get('resource')
              content = resource.get('content')
              geometry = content.get('geometry')
              type = geometry.get('type')
              if type != "Point": continue

              id = element.get('id')
              name = element.get('name')

              properties = content.get('properties')

              color = properties.get('color')

              coordinates = geometry.get('coordinates', [])
              if len(coordinates) >= 2:
                longitude = coordinates[0]
                latitude = coordinates[1]

              annotation = Annotation(
                id= id,
                project_uuid=project_uuid,
                name= name,
                latitude=latitude,
                longitude=longitude,
                color= color,
              )
              
              db.add(annotation)

    db.commit()

    return {
      "status": "success", 
      "file_processed": os.path.basename(latest_file),
    }

  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(e))
  