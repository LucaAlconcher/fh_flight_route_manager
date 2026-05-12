import math

def _get_segment_dist(lat1, lon1, lat2, lon2, c_lat, c_lon):
  """Calculates the closest distance from a circle center to a line segment."""
  k_lat = 111320.0
  k_lon = 40075000.0 * math.cos(math.radians(c_lat)) / 360.0

  x1, y1 = (lon1 - c_lon) * k_lon, (lat1 - c_lat) * k_lat
  x2, y2 = (lon2 - c_lon) * k_lon, (lat2 - c_lat) * k_lat

  dx, dy = x2 - x1, y2 - y1
  len_sq = dx*dx + dy*dy
  if len_sq == 0: return math.hypot(x1, y1)

  # Project origin onto line segment
  t = max(0, min(1, -(x1*dx + y1*dy) / len_sq))
  return math.hypot(x1 + t*dx, y1 + t*dy)

def _calculate_tangent_bypass(lat_a, lon_a, lat_b, lon_b, c_lat, c_lon, radius_m=115.0):
  """(Existing 3-point wrap logic)"""
  k_lat = 111320.0
  k_lon = 40075000.0 * math.cos(math.radians(c_lat)) / 360.0
  ax, ay = (lon_a - c_lon) * k_lon, (lat_a - c_lat) * k_lat
  bx, by = (lon_b - c_lon) * k_lon, (lat_b - c_lat) * k_lat
  dist_a, dist_b = math.hypot(ax, ay), math.hypot(bx, by)

  if dist_a <= radius_m or dist_b <= radius_m: return []

  angle_a, angle_b = math.atan2(ay, ax), math.atan2(by, bx)
  theta_a, theta_b = math.acos(radius_m / dist_a), math.acos(radius_m / dist_b)
  t1_opts, t2_opts = [angle_a + theta_a, angle_a - theta_a], [angle_b + theta_b, angle_b - theta_b]

  best_pair, min_diff = None, float('inf')
  for a1 in t1_opts:
    for a2 in t2_opts:
      diff = abs((a1 - a2 + math.pi) % (2 * math.pi) - math.pi)
      if diff < min_diff: min_diff, best_pair = diff, (a1, a2)

  ang1, ang2 = best_pair
  mid_angle = ang1 + (math.atan2(math.sin(ang2-ang1), math.cos(ang2-ang1)) / 2)
  pts = [(radius_m * math.cos(ang1), radius_m * math.sin(ang1)),
         ((radius_m + 2) * math.cos(mid_angle), (radius_m + 2) * math.sin(mid_angle)),
         (radius_m * math.cos(ang2), radius_m * math.sin(ang2))]

  return [{"latitude": c_lat + (p[1] / k_lat), "longitude": c_lon + (p[0] / k_lon)} for p in pts]

def calculate_route_collisions(routes, waypoints, annotations):
  wps_by_route = {}
  for wp in waypoints:
    if wp.route_id not in wps_by_route: wps_by_route[wp.route_id] = []
    wps_by_route[wp.route_id].append(wp)

  results = []
  for route in routes:
    r_id = route.id
    route_wps = sorted(wps_by_route.get(r_id, []), key=lambda x: x.index)
    safe_waypoints, is_compromised, last_safe_wp, active_danger_zone = [], False, None, None

    for wp in route_wps:
      hit_zone = next((a for a in annotations if math.hypot((wp.longitude - a.longitude) * (40075000 * math.cos(math.radians(a.latitude)) / 360), (wp.latitude - a.latitude) * 111320) <= 100.0), None)

      if not hit_zone:
        if active_danger_zone and last_safe_wp:
          # --- THE NEW CHECK ---
          # Check if the straight line between A and B actually hits the circle
          dist_to_circle = _get_segment_dist(last_safe_wp.latitude, last_safe_wp.longitude, wp.latitude, wp.longitude, active_danger_zone.latitude, active_danger_zone.longitude)
          
          if dist_to_circle < 105.0: # If the straight line is dangerous (within 105m)
            bypass = _calculate_tangent_bypass(last_safe_wp.latitude, last_safe_wp.longitude, wp.latitude, wp.longitude, active_danger_zone.latitude, active_danger_zone.longitude)
            for b_wp in bypass:
              safe_waypoints.append({**b_wp, "index": 999, "height": last_safe_wp.height})
          
          active_danger_zone = None
        
        safe_waypoints.append({"index": wp.index, "latitude": wp.latitude, "longitude": wp.longitude, "height": wp.height})
        last_safe_wp = wp
      else:
        is_compromised, active_danger_zone = True, hit_zone

    results.append({"flight_route_id": r_id, "compromised": is_compromised, "safe_waypoints": safe_waypoints})
  return results