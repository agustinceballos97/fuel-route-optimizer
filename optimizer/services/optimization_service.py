from optimizer.models import FuelStation
from geopy.distance import geodesic
import numpy as np
import math

class OptimizationService:

    
    def __init__(self, tank_range=500, mpg=10):
        self.tank_range = tank_range
        self.mpg = mpg
        self._distance_cache = {}
        
    def find_optimal_stops(self, route_geometry, total_distance_meters):

        self._distance_cache.clear()
        
        total_distance_miles = total_distance_meters * 0.000621371
        route_coords = route_geometry['coordinates']
        route_points = [(c[1], c[0]) for c in route_coords]
        
        # Convert to numpy array for vectorized operations
        route_array = np.array(route_points, dtype=np.float32)
        
        # Pre-compute cumulative distances along route
        cum_dist = self._precompute_cumulative_distances_fast(route_array)
        
        # Find fuel stations near the route
        stations = self._get_stations_near_route(route_array, cum_dist)
        
        if not stations and total_distance_miles > self.tank_range:
            return {'error': 'No fuel stations found along route, cannot complete trip'}
            
        # Map stations to their position along the route path
        stations_on_path = self._order_stations_by_path(stations, route_array, cum_dist)
        
        # Calculate optimal stops and total cost
        result = self._calculate_greedy_stops(stations_on_path, total_distance_miles)
        
        self._distance_cache.clear()
        return result

    def _precompute_cumulative_distances_fast(self, route_array):

        lat1, lon1 = route_array[:-1, 0], route_array[:-1, 1]
        lat2, lon2 = route_array[1:, 0], route_array[1:, 1]
        
        R = 3959  # Earth radius in miles
        lat1_rad, lat2_rad = np.radians(lat1), np.radians(lat2)
        delta_lat, delta_lon = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
        
        a = (np.sin(delta_lat/2)**2 + 
             np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2)
        c = 2 * np.arcsin(np.sqrt(a))
        distances = R * c
        
        return np.concatenate(([0], np.cumsum(distances)))

    def _haversine_vectorized(self, lat1, lon1, lat2_array, lon2_array):
        """Calculate distances from a point to multiple points using Haversine formula."""
        R = 3959
        lat1_rad, lat2_rad = np.radians(lat1), np.radians(lat2_array)
        delta_lat, delta_lon = np.radians(lat2_array - lat1), np.radians(lon2_array - lon1)
        
        a = (np.sin(delta_lat/2)**2 + 
             np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2)
        return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

    def _get_stations_near_route(self, route_array, cum_dist):

        lats, lons = route_array[:, 0], route_array[:, 1]
        
        # Phase 1: Bounding box filter (database-level)
        candidates = FuelStation.objects.filter(
            geocoded=True,
            latitude__gte=float(lats.min()) - 0.3, 
            latitude__lte=float(lats.max()) + 0.3,
            longitude__gte=float(lons.min()) - 0.3, 
            longitude__lte=float(lons.max()) + 0.3
        )
        
        # Simplify route for proximity checks (performance optimization)
        step = max(1, len(route_array) // 150)
        simplified_lats = route_array[::step, 0].astype(np.float32)
        simplified_lons = route_array[::step, 1].astype(np.float32)
        
        valid_stations = []
        for station in candidates:
            s_lat, s_lon = np.float32(station.latitude), np.float32(station.longitude)
            
            # Phase 2: Fast Euclidean approximation
            d_lat = np.abs(simplified_lats - s_lat)
            d_lon = np.abs(simplified_lons - s_lon)
            if not ((d_lat <= 0.15) & (d_lon <= 0.15)).any():
                continue
                
            # Phase 3: Precise Haversine calculation
            distances = self._haversine_vectorized(s_lat, s_lon, simplified_lats, simplified_lons)
            if distances.min() < 10:  # 10 miles corridor
                valid_stations.append(station)
        
        return valid_stations

    def _order_stations_by_path(self, stations, route_array, cum_dist):

        station_data = []
        step = max(1, len(route_array) // 300)
        simplified_lats = route_array[::step, 0].astype(np.float32)
        simplified_lons = route_array[::step, 1].astype(np.float32)
        simplified_indices = np.arange(len(route_array))[::step]
        
        for station in stations:
            s_lat, s_lon = np.float32(station.latitude), np.float32(station.longitude)
            distances = self._haversine_vectorized(s_lat, s_lon, simplified_lats, simplified_lons)
            best_idx = int(simplified_indices[distances.argmin()])
            
            station_data.append({
                'station': station,
                'dist_from_start': float(cum_dist[best_idx]),
                'price': float(station.retail_price)
            })
        
        return sorted(station_data, key=lambda x: x['dist_from_start'])

    def _calculate_greedy_stops(self, stations, total_distance):
        """
        Greedy algorithm: Select cheapest reachable fuel station at each stop.
        
        Cost calculation approach:
        Vehicle starts with a full tank (500 miles range)
        At each refuel stop, we pay for the gallons consumed since last fill
        Final leg cost is calculated using the last refuel price
        For short trips (<500 miles) with no stops, we estimate cost using 
          average fuel price along the route

        """
        stops = []
        current_pos = 0
        current_fuel_range = self.tank_range  # Miles we can travel from current position
        total_cost = 0
        last_refill_price = None
        
        # Find optimal fuel stops along the route
        while current_pos + current_fuel_range < total_distance:
            max_reach = current_pos + current_fuel_range
            
            # Find all stations reachable from current position
            reachable = [s for s in stations 
                        if current_pos < s['dist_from_start'] <= max_reach]
            
            if not reachable:
                return {'error': f'Stranded at mile {current_pos:.1f}. No stations in range.'}
            
            # Greedy strategy: Choose cheapest station (tie-break by going further)
            best_stop = min(reachable, key=lambda x: (x['price'], -x['dist_from_start']))
            
            # Calculate fuel consumed to reach this station
            miles_traveled = best_stop['dist_from_start'] - current_pos
            gallons_consumed = miles_traveled / self.mpg
            cost_at_stop = gallons_consumed * best_stop['price']
            
            stops.append({
                'station': best_stop['station'].name,
                'city': best_stop['station'].city,
                'state': best_stop['station'].state,
                'price': f"${best_stop['price']:.3f}/gal",
                'lat': float(best_stop['station'].latitude),
                'lon': float(best_stop['station'].longitude),
                'refill_gallons': round(gallons_consumed, 2),
                'cost': round(cost_at_stop, 2)
            })
            
            total_cost += cost_at_stop
            current_pos = best_stop['dist_from_start']
            current_fuel_range = self.tank_range  # Refilled to full tank
            last_refill_price = best_stop['price']
        
        # Calculate cost for remaining distance to destination
        distance_remaining = total_distance - current_pos
        
        if distance_remaining > 0:
            gallons_needed = distance_remaining / self.mpg
            
            if last_refill_price is not None:
                # Use price from last refuel stop
                final_leg_cost = gallons_needed * last_refill_price
            else:
                # Short trip with no refuel stops needed
                # Estimate cost using average price from nearby stations
                if stations:
                    avg_price = sum(s['price'] for s in stations) / len(stations)
                else:
                    # Fallback to US national average if no stations found
                    avg_price = 3.50
                final_leg_cost = gallons_needed * avg_price
            
            total_cost += final_leg_cost

        return {
            'stops': stops,
            'total_cost': round(total_cost, 2),
            'fuel_consumed_gallons': round(total_distance / self.mpg, 2)
        }