from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from optimizer.services.routing_service import RoutingService
from optimizer.models import FuelStation


class RouteOptimizationView(APIView):

    #Endpoint for route optimization.
    
    authentication_classes = [] # Public endpoint, no auth/CSRF required
    permission_classes = []

    
    def post(self, request):

        start_location = request.data.get('start_location')
        end_location = request.data.get('end_location')
        
        if not start_location or not end_location:
            return Response(
                {'error': 'Both start_location and end_location are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        service = RoutingService()
        result = service.calculate_optimal_route(start_location, end_location)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(result, status=status.HTTP_200_OK)

class StationsNearView(APIView):

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lon = float(request.query_params.get('lon'))
            radius = float(request.query_params.get('radius', 10.0)) # Default 10 miles
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid lat, lon, or radius parameters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Bounding box filter for speed
        # 1 deg ~ 69 miles. 
        # radius / 69 = degrees
        deg_radius = radius / 69.0
        min_lat, max_lat = lat - deg_radius, lat + deg_radius
        min_lon, max_lon = lon - deg_radius, lon + deg_radius
        
        candidates = FuelStation.objects.filter(
            geocoded=True,
            latitude__gte=min_lat, latitude__lte=max_lat,
            longitude__gte=min_lon, longitude__lte=max_lon
        )
        
        stations = []
        for station in candidates:
            # We could do precise distance check here if strict radius is needed
            # For UI "nearby" display, box is often fine or we can add precise dist
            stations.append({
                'id': station.id,
                'station': station.name,
                'city': station.city,
                'state': station.state,
                'price': float(station.retail_price),
                'lat': float(station.latitude),
                'lon': float(station.longitude),
                'address': station.address
            })
            
        return Response({'stations': stations}, status=status.HTTP_200_OK)
