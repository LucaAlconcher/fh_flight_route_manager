import requests
from tqdm import tqdm

class FlightHubClient:
  def __init__(self, base_url: str, x_user_token: str, x_project_uuid: str):
    self.project_uuid = x_project_uuid
    self.headers = {
      "X-User-Token": x_user_token,
      "X-Project-Uuid": self.project_uuid,
      "Content-Type": "application/json"
    }
    self.base_url = base_url.rstrip('/')
    print(f'FlightHubClient initialized at {self.base_url}')

  def _request(self, method, endpoint, params=None, json_data=None):
    url = f"{self.base_url}/{endpoint.lstrip('/')}"
    
    kwargs = {"headers": self.headers}
    
    if params:
        kwargs['params'] = params
        
    if method in ['POST', 'PUT', 'PATCH']:
      kwargs['json'] = json_data if json_data is not None else {}
    
    tqdm.write(f"🚀 {method} -> {url}")
    
    response = requests.request(method, url, **kwargs)
    response.raise_for_status()
    return response.json()

  # Specific resource methods
  def get_project_flight_routes(self, filters=None):
    return self._request("GET", "/openapi/v0.1/wayline", params=filters)

  def get_project_flight_route_details(self, route_id):
    return self._request("GET", f"/openapi/v0.1/wayline/{route_id}")