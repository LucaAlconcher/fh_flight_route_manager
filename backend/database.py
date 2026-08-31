from sqlalchemy import create_engine, Column, String, Integer, BigInteger, Float, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./flighthub.db"
RESET_DATABASE = False

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FlightRoute(Base):
  __tablename__ = "flight_routes"

  # Core Data (Common to both)
  id = Column(String, primary_key=True, index=True)
  project_uuid = Column(String, index=True)
  name = Column(String)
  device_model_key = Column(String)
  update_time = Column(BigInteger) # API timestamp
  size = Column(BigInteger)        # Size reported by the list endpoint
  
  template_types = Column(JSON, nullable=True) 
  payload_information = Column(JSON, nullable=True)
  
  # Detail specific (Flattened)
  download_url = Column(String, nullable=True)
  distance = Column(Float, nullable=True)
  wayline_point_nums = Column(Integer, nullable=True)
  
  # Verification & Sync
  local_file_path = Column(String, nullable=True)
  actual_size = Column(BigInteger, nullable=True) # For your file check logic
  sync_status = Column(String, default="PENDING")

  is_execution_route = Column(Boolean, default=False)

class Annotation(Base):
  __tablename__ = "annotations"

  # We use the 'id' from the JSON as the primary key
  id = Column(String, primary_key=True, index=True)
  project_uuid = Column(String, index=True)
  name = Column(String)
  
  # Geographic data
  latitude = Column(Float)
  longitude = Column(Float)
  
  # Visuals
  color = Column(String, nullable=True)
  
class AnnotationState(Base):
  __tablename__ = "annotation_states"
  # This ID maps 1:1 to the Annotation ID from the JSON
  annotation_id = Column(String, primary_key=True, index=True)
  compromised = Column(Boolean, default=False)


class Waypoint(Base):
  __tablename__ = "waypoints"
  
  id = Column(Integer, primary_key=True, index=True)
  route_id = Column(String, ForeignKey("flight_routes.id"), index=True)
  
  # The DJI WPML index (e.g., 0, 1, 2...) 
  # This is our link back to the XML file
  index = Column(Integer)
  
  # Minimum spatial info
  latitude = Column(Float)
  longitude = Column(Float)
  height = Column(Float)

class Model3D(Base):
  __tablename__ = "models_3d"

  id = Column(String, primary_key=True, index=True)
  project_uuid = Column(String, index=True)
  name = Column(String)
  file_type = Column(String)
  size = Column(BigInteger)
  update_time = Column(BigInteger)
  create_time = Column(BigInteger)

  # Set once the model has been downloaded and extracted locally
  local_tileset_path = Column(String, nullable=True)
  sync_status = Column(String, default="PENDING")

if RESET_DATABASE:
  print("⚠️  RESET_DATABASE is True. Dropping all tables...")
  Base.metadata.drop_all(bind=engine)
  print("✅ Tables dropped.")


# Create the tables
Base.metadata.create_all(bind=engine)