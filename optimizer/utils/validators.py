#Input validation functions for coordinates, addresses, and other data.

from typing import Tuple
from .constants import US_STATES


def validate_coordinates(lat: float, lng: float) -> bool:
    
    #Validate latitude and longitude values.
    # Latitude must be between -90 and 90
    if lat < -90 or lat > 90:
        return False
    
    # Longitude must be between -180 and 180
    if lng < -180 or lng > 180:
        return False
    
    return True


def validate_us_state(state_code: str) -> bool:

    #Validate US state code.

    if not state_code:
        return False
    
    return state_code.upper() in US_STATES


def validate_address_format(address: str) -> bool:
    
    #Validate basic address format.
  
    if not address or not isinstance(address, str):
        return False
    
    # Must have at least some content
    if len(address.strip()) < 3:
        return False
    
    # Common patterns: "City, State" or full address
    # Basic check: at least has some text
    return True


def validate_price(price: float) -> bool:

    # Price should be positive and reasonable (between $0.50 and $20.00 per gallon)
    return 0.5 <= price <= 20.0


def validate_distance(distance_miles: float) -> bool:

    # Distance must be non-negative and reasonable (< 10,000 miles for single trip)
    return 0 <= distance_miles <= 10000