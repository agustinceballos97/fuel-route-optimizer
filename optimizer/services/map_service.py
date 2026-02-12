
import requests
import json
from decimal import Decimal

class MapService:

    OSRM_BASE_URL = "http://router.project-osrm.org"
    
    def get_coordinates(self, location_query):

        # Using Nominatim directly here for simplicity in this service, 
        # but in a real app better to reuse GeocodingService
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_query,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us'
        }
        headers = {'User-Agent': 'fuel-route-optimizer-demo'}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return (float(data[0]['lat']), float(data[0]['lon']))
            return None
        except Exception as e:
            print(f"Error geocoding {location_query}: {e}")
            return None

    def get_route(self, start_coords, end_coords):

        # OSRM expects "lon,lat"
        start_str = f"{start_coords[1]},{start_coords[0]}"
        end_str = f"{end_coords[1]},{end_coords[0]}"
        
        url = f"{self.OSRM_BASE_URL}/route/v1/driving/{start_str};{end_str}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'true'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                json_response = response.json()
                return json_response
            return None
        except Exception as e:
            print(f"Error getting route: {e}")
            return None
