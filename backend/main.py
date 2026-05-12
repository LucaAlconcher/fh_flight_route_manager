from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.flight_routes import router as flight_routes_router
from api.annotations import router as annotations_router

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:5173"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Include the sync routes
app.include_router(flight_routes_router)
app.include_router(annotations_router)


@app.get("/")
def root():
  return {"message": "FlightHub Proxy API Running"}

if __name__ == "__main__":
  import uvicorn
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)