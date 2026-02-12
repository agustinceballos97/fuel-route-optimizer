#Centralized location for all magic numbers and configuration values.

# Vehicle specifications
VEHICLE_MPG = 10  # Miles per gallon
TANK_RANGE_MILES = 500  # Maximum distance on full tank

# Earth measurements
EARTH_RADIUS_MILES = 3959  # Earth's radius in miles (for haversine calculations)

# Route optimization parameters
SEARCH_BUFFER_MILES = 20  # How far from route to search for stations
STOP_TOLERANCE_MILES = 100  # Tolerance window for ideal stop location

# Geocoding settings
MAX_STATIONS_TO_GEOCODE = 1000  # Maximum stations to geocode by default
GEOCODING_RATE_LIMIT_SECONDS = 1.0  # Delay between geocoding requests (Nominatim limit)

# OpenRouteService settings
OPENROUTE_BASE_URL = 'https://api.openrouteservice.org'
OPENROUTE_TIMEOUT_SECONDS = 30

# Distance conversion
KM_TO_MILES = 0.621371
MILES_TO_KM = 1.60934

# US State codes (for validation)
US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
]