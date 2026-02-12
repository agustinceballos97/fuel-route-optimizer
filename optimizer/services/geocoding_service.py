
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from django.conf import settings

class GeocodingService:
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="fuel-route-optimizer-demo")
        self.last_request_time = 0
        self.rate_limit_seconds = getattr(settings, 'GEOCODING_RATE_LIMIT_SECONDS', 1.0)

    def geocode_station(self, city, state):

        query = f"{city}, {state}, USA"
        
        # Enforce rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - time_since_last)
            
        try:
            self.last_request_time = time.time()
            location = self.geolocator.geocode(query, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error for {query}: {e}")
            return None