import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from optimizer.models import FuelStation


class Command(BaseCommand):
    help = 'Load fuel stations from CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/fuel-prices-for-be-assessment.csv',
            help='Path to CSV file (default: data/fuel-prices-for-be-assessment.csv)'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing fuel stations before loading'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']
        
        # Validate file exists
        csv_file = Path(file_path)
        if not csv_file.exists():
            raise CommandError(f'File not found: {file_path}')
        
        self.stdout.write(self.style.MIGRATE_HEADING('Loading Fuel Stations'))
        self.stdout.write(f'Reading from: {file_path}')
        
        # Clear existing data if requested
        if clear_existing:
            count = FuelStation.objects.count()
            if count > 0:
                self.stdout.write(self.style.WARNING(f'Deleting {count} existing stations...'))
                FuelStation.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('✓ Existing data cleared'))
        
        # Load CSV data
        stations_to_create = []
        errors = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Read CSV
                reader = csv.DictReader(f)
                
                self.stdout.write('Processing CSV rows...')
                
                for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                    try:
                        # Parse and validate data
                        station = self._create_station_from_row(row)
                        stations_to_create.append(station)
                        
                        # Progress indicator every 1000 rows
                        if len(stations_to_create) % 1000 == 0:
                            self.stdout.write(f'  Processed {len(stations_to_create)} stations...')
                        
                    except Exception as e:
                        errors.append(f'Row {row_num}: {str(e)}')
                        # Continue processing other rows
                        continue
            
            # Bulk create stations
            if stations_to_create:
                self.stdout.write(f'\nInserting {len(stations_to_create)} stations into database...')
                
                with transaction.atomic():
                    FuelStation.objects.bulk_create(
                        stations_to_create,
                        batch_size=500,
                        ignore_conflicts=True
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successfully loaded {len(stations_to_create)} fuel stations')
                )
            else:
                self.stdout.write(self.style.WARNING('No stations to load'))
            
            # Report errors if any
            if errors:
                self.stdout.write(
                    self.style.WARNING(f'\n⚠ Encountered {len(errors)} errors:')
                )
                for error in errors[:10]:  # Show first 10 errors
                    self.stdout.write(f'  - {error}')
                if len(errors) > 10:
                    self.stdout.write(f'  ... and {len(errors) - 10} more')
            
            # Summary
            total_count = FuelStation.objects.count()
            self.stdout.write(f'\nTotal stations in database: {total_count}')
            
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
    
    def _create_station_from_row(self, row):
        
        # Parse retail price
        try:
            retail_price = float(row['Retail Price'])
        except (ValueError, KeyError):
            raise ValueError(f"Invalid retail price: {row.get('Retail Price', 'N/A')}")
        
        # Parse rack_id (optional)
        rack_id = None
        if row.get('Rack ID') and row['Rack ID'].strip():
            try:
                rack_id = int(row['Rack ID'])
            except ValueError:
                # If conversion fails, leave as None
                pass
        
        # Validate required fields
        required_fields = ['OPIS Truckstop ID', 'Truckstop Name', 'Address', 'City', 'State']
        for field in required_fields:
            if not row.get(field) or not row[field].strip():
                raise ValueError(f"Missing required field: {field}")
        
        # Create station object
        station = FuelStation(
            opis_id=row['OPIS Truckstop ID'].strip(),
            name=row['Truckstop Name'].strip(),
            address=row['Address'].strip(),
            city=row['City'].strip(),
            state=row['State'].strip().upper()[:2],  # Ensure 2-letter state code
            rack_id=rack_id,
            retail_price=retail_price,
            geocoded=False  # Will be geocoded later
        )
        
        return station