from django.contrib import admin
from .models import FuelStation


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    """
    Admin interface for FuelStation model.
    """
    
    list_display = [
        'name',
        'city',
        'state',
        'retail_price',
        'geocoded',
        'created_at'
    ]
    
    list_filter = [
        'geocoded',
        'state',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'city',
        'state',
        'address'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'opis_id'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('opis_id', 'name', 'address', 'city', 'state')
        }),
        ('Pricing', {
            'fields': ('retail_price', 'rack_id')
        }),
        ('Geocoding', {
            'fields': ('latitude', 'longitude', 'geocoded'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        queryset = super().get_queryset(request)
        return queryset.select_related()