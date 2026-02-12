from django.core.management.base import BaseCommand
from django.db.models import Q
from optimizer.models import FuelStation
from optimizer.services.geocoding_service import GeocodingService


class Command(BaseCommand):
    help = 'Geocode fuel stations to get latitude/longitude coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='Maximum number of stations to geocode (default: 1000)'
        )
        
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['cheapest', 'all', 'missing'],
            default='cheapest',
            help='Geocoding strategy: cheapest (default), all, or missing only'
        )
        
        parser.add_argument(
            '--state',
            type=str,
            help='Filter by state code (e.g., CA, TX, NY)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-geocode stations that already have coordinates'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        strategy = options['strategy']
        state_filter = options['state']
        force = options['force']
        
        self.stdout.write(self.style.MIGRATE_HEADING('Geocoding Fuel Stations'))
        
        # Get stations to geocode based on strategy
        stations = self._get_stations_to_geocode(strategy, state_filter, force, limit)
        
        if not stations:
            self.stdout.write(self.style.WARNING('No stations to geocode'))
            return
        
        total = len(stations)
        self.stdout.write(f'Found {total} stations to geocode')
        self.stdout.write(f'Strategy: {strategy}')
        if state_filter:
            self.stdout.write(f'State filter: {state_filter}')
        self.stdout.write('')
        
        # OPTIMIZATION: Group stations by city to avoid redundant geocoding
        cities_map = {}
        for station in stations:
            city_key = f"{station.city}, {station.state}"
            if city_key not in cities_map:
                cities_map[city_key] = []
            cities_map[city_key].append(station)
        
        unique_cities = len(cities_map)
        self.stdout.write(f'Unique cities to geocode: {unique_cities}')
        self.stdout.write(f'Optimization: ~{total - unique_cities} API calls saved!')
        self.stdout.write('')
        
        # Initialize geocoding service
        service = GeocodingService()
        
        # Geocode by city (not by station)
        successful = 0
        failed = 0
        
        for i, (city_key, city_stations) in enumerate(cities_map.items(), 1):
            # Progress indicator
            if i % 10 == 0 or i == 1:
                self.stdout.write(
                    f'Progress: {i}/{unique_cities} cities ({(i/unique_cities)*100:.1f}%) - '
                    f'Stations: {successful + failed}/{total}'
                )
            
            # Geocode city once
            city = city_stations[0].city
            state = city_stations[0].state
            coords = service.geocode_station(city, state)
            
            if coords:
                lat, lng = coords
                
                # Apply coordinates to ALL stations in this city
                for station in city_stations:
                    station.latitude = lat
                    station.longitude = lng
                    station.geocoded = True
                    station.save()
                    successful += 1
                
                # Show some successful geocodings
                if i <= 5:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {city}, {state}: ({lat:.4f}, {lng:.4f}) [{len(city_stations)} stations]'
                        )
                    )
            else:
                # All stations in this city failed
                failed += len(city_stations)
                
                # Show some failures
                if failed <= 20:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ✗ Failed: {city}, {state} [{len(city_stations)} stations]'
                        )
                    )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Summary'))
        self.stdout.write(f'Total processed: {total}')
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successful: {successful} ({(successful/total)*100:.1f}%)')
        )
        
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(f'✗ Failed: {failed} ({(failed/total)*100:.1f}%)')
            )
        
        # Overall database stats
        total_stations = FuelStation.objects.count()
        geocoded_stations = FuelStation.objects.filter(geocoded=True).count()
        self.stdout.write('')
        self.stdout.write(
            f'Total geocoded stations in database: {geocoded_stations}/{total_stations} '
            f'({(geocoded_stations/total_stations)*100:.1f}%)'
        )
    
    def _get_stations_to_geocode(self, strategy, state_filter, force, limit):

        # Base queryset
        queryset = FuelStation.objects.all()
        
        # Apply state filter if provided
        if state_filter:
            queryset = queryset.filter(state__iexact=state_filter.upper())
        
        # Apply force filter (skip already geocoded unless force=True)
        if not force:
            queryset = queryset.filter(geocoded=False)
        
        # Apply strategy
        if strategy == 'cheapest':
            # Get cheapest stations first
            queryset = queryset.order_by('retail_price')
        elif strategy == 'all':
            # Get all stations (already ordered by price in model Meta)
            pass
        elif strategy == 'missing':
            # Only stations without coordinates
            queryset = queryset.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True)
            )
        
        # Apply limit
        queryset = queryset[:limit]
        
        # Convert to list to avoid database queries during geocoding
        return list(queryset)