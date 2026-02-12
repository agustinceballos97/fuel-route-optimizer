
from optimizer.services.map_service import MapService
from optimizer.services.optimization_service import OptimizationService

class RoutingService:
    
    #Service to orchestrate route planning and optimization.
    
    
    def __init__(self):
        self.map_service = MapService()
        self.optimization_service = OptimizationService()
        
    def calculate_optimal_route(self, start_location, end_location):
   
        # 1. Get coordinates
        start_coords = self.map_service.get_coordinates(start_location)
        end_coords = self.map_service.get_coordinates(end_location)
         
        if not start_coords or not end_coords:
            return {'error': 'Could not geocode locations'}
            
        # 2. Get route from OSRM
        route_data = self.map_service.get_route(start_coords, end_coords)
        
        if not route_data or 'routes' not in route_data:
            return {'error': 'Could not find route'}
            
        route = route_data['routes'][0]
        distance_meters = route['distance']
        duration_seconds = route['duration']
        geometry = route['geometry'] # GeoJSON
        
        # 3. Optimize fuel stops
        optimization_result = self.optimization_service.find_optimal_stops(
            geometry, 
            distance_meters
        )
        
        if 'error' in optimization_result:
            return {'error': optimization_result['error']}
            
        return {
            'route': {
                'start': start_location,
                'end': end_location,
                'distance_miles': round(distance_meters * 0.000621371, 1),
                'duration_hours': round(duration_seconds / 3600, 1),
                'geometry': geometry
            },
            'stops': optimization_result['stops'],
            'total_cost': optimization_result['total_cost'],
            'fuel_consumed_gallons': optimization_result['fuel_consumed_gallons']
        }
