from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, Model3D
from dotenv import load_dotenv
import os
import time
import zipfile
import requests

load_dotenv()

from clients.instance import fh_client

router = APIRouter(prefix="/api/models", tags=["models"])

# Siblings under D:\Desktop\Luca\git\ by default: fh_flight_route_manager/backend -> mission_automator/cesium-cctv/public/models
MODELS_DIR = os.path.abspath(os.getenv("FH_MODELS_DIR", "../../mission_automator/cesium-cctv/public/models"))

DOWNLOAD_URL_RETRIES = 3
DOWNLOAD_URL_RETRY_DELAY_SECONDS = 2


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


def _to_dict(m: Model3D):
  return {
    "id": m.id,
    "name": m.name,
    "file_type": m.file_type,
    "size": m.size,
    "update_time": m.update_time,
    "create_time": m.create_time,
    "sync_status": m.sync_status,
    "tileset_url": f"/models/{m.local_tileset_path}" if m.local_tileset_path else None,
  }


@router.get("")
def get_models(db: Session = Depends(get_db)):
  models = db.query(Model3D).filter(Model3D.file_type == "model_3d").all()
  return [_to_dict(m) for m in models]


@router.post("/sync")
def sync_models(db: Session = Depends(get_db)):
  try:
    list_resp = fh_client.get_project_models()
    raw_models = list_resp.get("data", {}).get("list", [])

    for item in raw_models:
      mid = str(item["id"])
      existing = db.query(Model3D).filter(Model3D.id == mid).first()

      if existing:
        existing.name = item.get("name")
        existing.file_type = item.get("file_type")
        existing.size = item.get("size")
        existing.update_time = item.get("update_at")
        existing.create_time = item.get("create_at")
      else:
        db.add(Model3D(
          id=mid,
          project_uuid=fh_client.project_uuid,
          name=item.get("name"),
          file_type=item.get("file_type"),
          size=item.get("size"),
          update_time=item.get("update_at"),
          create_time=item.get("create_at"),
          sync_status="PENDING"
        ))

    db.commit()

    models = db.query(Model3D).filter(Model3D.file_type == "model_3d").all()
    return [_to_dict(m) for m in models]

  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/download")
def download_model(model_id: str, db: Session = Depends(get_db)):
  model = db.query(Model3D).filter(Model3D.id == model_id).first()
  if not model:
    raise HTTPException(status_code=404, detail="Model not found")

  try:
    # FlightHub compresses large models on demand; the url comes back empty
    # while that's in progress, so we poll it a few times before giving up
    # and letting the frontend retry later.
    download_url = None
    for _attempt in range(DOWNLOAD_URL_RETRIES):
      url_resp = fh_client.get_model_download_url(model_id)
      download_url = url_resp.get("data", {}).get("url")
      if download_url:
        break
      time.sleep(DOWNLOAD_URL_RETRY_DELAY_SECONDS)

    if not download_url:
      model.sync_status = "COMPRESSING"
      db.commit()
      return _to_dict(model)

    os.makedirs(MODELS_DIR, exist_ok=True)
    zip_path = os.path.join(MODELS_DIR, f"{model.name}.zip")
    extract_path = os.path.join(MODELS_DIR, model.name)

    resp = requests.get(download_url, timeout=120, stream=True)
    resp.raise_for_status()
    with open(zip_path, "wb") as f:
      for chunk in resp.iter_content(chunk_size=8192):
        f.write(chunk)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
      zip_ref.extractall(extract_path)
    os.remove(zip_path)

    tileset_path = None
    for root, _dirs, files in os.walk(extract_path):
      if "tileset.json" in files:
        tileset_path = os.path.join(root, "tileset.json")
        break

    if not tileset_path:
      model.sync_status = "ERROR"
      db.commit()
      raise HTTPException(status_code=500, detail="tileset.json not found inside the downloaded model")

    model.local_tileset_path = os.path.relpath(tileset_path, MODELS_DIR).replace(os.sep, "/")
    model.sync_status = "DOWNLOADED"
    db.commit()

    return _to_dict(model)

  except HTTPException:
    raise
  except Exception as e:
    model.sync_status = "ERROR"
    db.commit()
    raise HTTPException(status_code=500, detail=str(e))
