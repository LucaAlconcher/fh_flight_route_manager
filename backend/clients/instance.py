import os
from dotenv import load_dotenv
from clients.fh_openapi_client import FlightHubClient

load_dotenv()

# One single instance shared across the whole app
fh_client = FlightHubClient(
  base_url=os.getenv("FH_BASE_URL"),
  x_user_token=os.getenv("FH_X_USER_TOKEN"),
  x_project_uuid=os.getenv("FH_PROJECT_UUID")
)