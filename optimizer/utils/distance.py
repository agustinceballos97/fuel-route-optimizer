#Uses haversine formula for accurate distance calculations on Earth's surface.

import math
from typing import Tuple, Dict, List
from .constants import EARTH_RADIUS_MILES


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:

    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    # Distance in miles
    distance = EARTH_RADIUS_MILES * c
    
    return distance


def calculate_bounding_box(lat: float, lng: float, radius_miles: float) -> Dict[str, float]:

    # Approximate degrees per mile (works well for USA latitudes)
    # 1 degree latitude ≈ 69 miles everywhere
    # 1 degree longitude varies by latitude
    lat_degrees_per_mile = 1 / 69.0
    lng_degrees_per_mile = 1 / (69.0 * math.cos(math.radians(lat)))
    
    lat_delta = radius_miles * lat_degrees_per_mile
    lng_delta = radius_miles * lng_degrees_per_mile
    
    return {
        'min_lat': lat - lat_delta,
        'max_lat': lat + lat_delta,
        'min_lng': lng - lng_delta,
        'max_lng': lng + lng_delta
    }


def point_to_line_distance(point: Tuple[float, float], line_points: List[Tuple[float, float]]) -> float:
 
    if not line_points:
        return float('inf')
    
    if len(line_points) == 1:
        return haversine(point[0], point[1], line_points[0][0], line_points[0][1])
    
    min_distance = float('inf')
    
    # Check distance to each segment of the polyline
    for i in range(len(line_points) - 1):
        # For simplicity, we calculate distance to each point
        # A more sophisticated approach would calculate distance to the line segment itself
        dist = haversine(point[0], point[1], line_points[i][0], line_points[i][1])
        min_distance = min(min_distance, dist)
    
    # Check distance to last point
    dist = haversine(point[0], point[1], line_points[-1][0], line_points[-1][1])
    min_distance = min(min_distance, dist)
    
    return min_distance


def distance_along_route(route_points: List[Tuple[float, float]]) -> List[float]:

    if not route_points:
        return []
    
    cumulative_distances = [0.0]
    total_distance = 0.0
    
    for i in range(1, len(route_points)):
        segment_distance = haversine(
            route_points[i-1][0], route_points[i-1][1],
            route_points[i][0], route_points[i][1]
        )
        total_distance += segment_distance
        cumulative_distances.append(total_distance)
    
    return cumulative_distances