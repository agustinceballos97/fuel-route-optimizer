from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class FuelStation(models.Model):
    
    # Original data from CSV
    opis_id = models.CharField(
        max_length=50,
        verbose_name='OPIS Truckstop ID',
        help_text='Original ID from OPIS dataset'
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name='Station Name',
        db_index=True
    )
    
    address = models.TextField(
        verbose_name='Address',
        help_text='Full address including highway references'
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name='City',
        db_index=True
    )
    
    state = models.CharField(
        max_length=2,
        verbose_name='State Code',
        db_index=True,
        help_text='Two-letter US state code (e.g., CA, NY)'
    )
    
    rack_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Rack ID'
    )
    
    retail_price = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        verbose_name='Retail Price (per gallon)',
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(99.999)
        ],
        db_index=True,
        help_text='Price per gallon in USD'
    )
    
    # Geocoded coordinates
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Latitude',
        validators=[
            MinValueValidator(-90.0),
            MaxValueValidator(90.0)
        ],
        db_index=True,
        help_text='Latitude in decimal degrees'
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Longitude',
        validators=[
            MinValueValidator(-180.0),
            MaxValueValidator(180.0)
        ],
        db_index=True,
        help_text='Longitude in decimal degrees'
    )
    
    geocoded = models.BooleanField(
        default=False,
        verbose_name='Geocoded',
        db_index=True,
        help_text='Whether this station has been geocoded'
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    class Meta:
        verbose_name = 'Fuel Station'
        verbose_name_plural = 'Fuel Stations'
        ordering = ['retail_price', 'name']
        indexes = [
            models.Index(fields=['geocoded', 'retail_price']),
            models.Index(fields=['state', 'city']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        """String representation of the fuel station."""
        return f"{self.name} - {self.city}, {self.state} (${self.retail_price}/gal)"
    
    def get_coordinates(self):

        if self.geocoded and self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None
    
    def get_location_string(self):

        return f"{self.city}, {self.state}, USA"
    
    @property
    def is_geocoded(self):

        return self.geocoded and self.latitude is not None and self.longitude is not None
    
    @property
    def price_float(self):

        return float(self.retail_price)