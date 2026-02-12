"""
Repository pattern for FuelStation data access.
Abstracts database queries from business logic.
"""

from typing import List, Optional, Tuple
from optimizer.models import FuelStation
from django.db.models import QuerySet


class FuelStationRepository:
    """
    Repository for FuelStation entity.
    Provides clean interface for data access without exposing ORM details.
    """
    
    def get_all_geocoded(self) -> QuerySet:
        """
        Get all geocoded fuel stations.
        
        Returns:
            QuerySet of geocoded FuelStation objects
        """
        return FuelStation.objects.filter(geocoded=True)
    
    def get_stations_in_bounding_box(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        order_by_price: bool = True
    ) -> QuerySet:
        """
        Get stations within a geographic bounding box.
        
        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lon: Minimum longitude
            max_lon: Maximum longitude
            order_by_price: If True, order by retail_price ascending
        
        Returns:
            QuerySet of FuelStation objects in the bounding box
        
        Example:
            >>> repo = FuelStationRepository()
            >>> stations = repo.get_stations_in_bounding_box(
            ...     min_lat=40.0, max_lat=41.0,
            ...     min_lon=-75.0, max_lon=-74.0
            ... )
        """
        queryset = FuelStation.objects.filter(
            geocoded=True,
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_lon,
            longitude__lte=max_lon
        )
        
        if order_by_price:
            queryset = queryset.order_by('retail_price')
        
        return queryset
    
    def get_cheapest_stations(self, limit: int = 100) -> QuerySet:
        """
        Get the cheapest fuel stations.
        
        Args:
            limit: Maximum number of stations to return
        
        Returns:
            QuerySet of cheapest FuelStation objects
        """
        return FuelStation.objects.filter(
            geocoded=True
        ).order_by('retail_price')[:limit]
    
    def get_stations_by_state(self, state_code: str) -> QuerySet:
        """
        Get all geocoded stations in a specific state.
        
        Args:
            state_code: Two-letter state code (e.g., 'CA', 'NY')
        
        Returns:
            QuerySet of FuelStation objects in the state
        """
        return FuelStation.objects.filter(
            geocoded=True,
            state__iexact=state_code
        ).order_by('retail_price')
    
    def get_stations_near_point(
        self,
        latitude: float,
        longitude: float,
        radius_degrees: float = 0.145  # ~10 miles
    ) -> QuerySet:
        """
        Get stations near a specific point (simple bounding box).
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_degrees: Search radius in degrees (~0.145 = 10 miles)
        
        Returns:
            QuerySet of FuelStation objects near the point
        
        Note:
            This uses a simple bounding box, not precise circle distance.
            For precise distance filtering, use with geopy.distance.geodesic
        """
        return FuelStation.objects.filter(
            geocoded=True,
            latitude__gte=latitude - radius_degrees,
            latitude__lte=latitude + radius_degrees,
            longitude__gte=longitude - radius_degrees,
            longitude__lte=longitude + radius_degrees
        )
    
    def count_geocoded_stations(self) -> int:
        """
        Count total number of geocoded stations.
        
        Returns:
            Integer count of geocoded stations
        """
        return FuelStation.objects.filter(geocoded=True).count()
    
    def count_total_stations(self) -> int:
        """
        Count total number of stations (geocoded + not geocoded).
        
        Returns:
            Integer count of all stations
        """
        return FuelStation.objects.count()
    
    def get_station_by_id(self, station_id: int) -> Optional[FuelStation]:
        """
        Get a specific station by ID.
        
        Args:
            station_id: Primary key of the station
        
        Returns:
            FuelStation object or None if not found
        """
        try:
            return FuelStation.objects.get(id=station_id)
        except FuelStation.DoesNotExist:
            return None
    
    def get_price_range(self) -> Tuple[float, float]:
        """
        Get the minimum and maximum fuel prices.
        
        Returns:
            Tuple of (min_price, max_price)
        """
        from django.db.models import Min, Max
        
        result = FuelStation.objects.filter(
            geocoded=True
        ).aggregate(
            min_price=Min('retail_price'),
            max_price=Max('retail_price')
        )
        
        return (
            float(result['min_price']) if result['min_price'] else 0.0,
            float(result['max_price']) if result['max_price'] else 0.0
        )
    
    def get_average_price_by_state(self, state_code: str) -> float:
        """
        Get average fuel price in a specific state.
        
        Args:
            state_code: Two-letter state code
        
        Returns:
            Average price as float
        """
        from django.db.models import Avg
        
        result = FuelStation.objects.filter(
            geocoded=True,
            state__iexact=state_code
        ).aggregate(avg_price=Avg('retail_price'))
        
        return float(result['avg_price']) if result['avg_price'] else 0.0
    
    def get_stations_by_price_range(
        self,
        min_price: float,
        max_price: float
    ) -> QuerySet:
        """
        Get stations within a specific price range.
        
        Args:
            min_price: Minimum price per gallon
            max_price: Maximum price per gallon
        
        Returns:
            QuerySet of FuelStation objects in price range
        """
        return FuelStation.objects.filter(
            geocoded=True,
            retail_price__gte=min_price,
            retail_price__lte=max_price
        ).order_by('retail_price')