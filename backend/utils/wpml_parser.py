import os
import xml.etree.ElementTree as ET

def parse_dji_waypoints(file_to_parse: str):
    if not os.path.exists(file_to_parse):
        raise FileNotFoundError(f"Could not find {file_to_parse}")

    # Parse the XML
    tree = ET.parse(file_to_parse)
    root = tree.getroot()

    # --- STRIP ALL NAMESPACES ---
    # This makes the code immune to DJI changing from 1.0.6 to 1.0.7 tomorrow
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]

    waypoints = []

    # Now we just look for the raw tag names!
    for placemark in root.findall('.//Placemark'):
        # 1. Get the Index
        index_node = placemark.find('.//index')
        if index_node is None:
            continue
            
        wp_index = int(index_node.text)

        # 2. Get the Coordinates (Nested inside Point)
        coords_node = placemark.find('.//coordinates')
        if coords_node is None:
            continue
            
        # Coordinates are usually "longitude,latitude" or "longitude,latitude,altitude"
        coords_text = coords_node.text.strip()
        parts = coords_text.split(',')
        
        lon = float(parts[0])
        lat = float(parts[1])

        # 3. Get the Execute Height (crucial for drones)
        height_node = placemark.find('.//executeHeight')
        height = float(height_node.text) if height_node is not None else 0.0

        waypoints.append({
            "index": wp_index,
            "latitude": lat,
            "longitude": lon,
            "height": height
        })

    # Sort by index just to be safe
    waypoints.sort(key=lambda x: x["index"])
    return waypoints