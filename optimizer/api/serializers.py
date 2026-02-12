from rest_framework import serializers


class RouteOptimizationRequestSerializer(serializers.Serializer):

    #Validates request data for route optimization endpoint.
    
    #POST /api/v1/route/optimize

    start_location = serializers.CharField(
        max_length=200,
        required=True,
        trim_whitespace=True,
        help_text="Starting location (e.g., 'Los Angeles, CA')"
    )
    
    end_location = serializers.CharField(
        max_length=200,
        required=True,
        trim_whitespace=True,
        help_text="Destination location (e.g., 'New York, NY')"
    )
    
    def validate_start_location(self, value):
        #Validate start location is not empty.
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Start location must be at least 3 characters long."
            )
        return value.strip()
    
    def validate_end_location(self, value):
        #Validate end location is not empty.
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "End location must be at least 3 characters long."
            )
        return value.strip()
    
    def validate(self, data):
        #Cross-field validation.
        if data['start_location'].lower() == data['end_location'].lower():
            raise serializers.ValidationError(
                "Start and end locations must be different."
            )
        return data


class FuelStopSerializer(serializers.Serializer):
    
    #Serializes a single fuel stop in the route.
    
    station = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    price = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    refill_gallons = serializers.FloatField()
    cost = serializers.FloatField()


class RouteInfoSerializer(serializers.Serializer):
    
    #Serializes route information.
    
    start = serializers.CharField()
    end = serializers.CharField()
    distance_miles = serializers.FloatField()
    duration_hours = serializers.FloatField()
    geometry = serializers.DictField()


class RouteOptimizationResponseSerializer(serializers.Serializer):
    
    #Serializes response data for route optimization endpoint.

    route = RouteInfoSerializer()
    stops = FuelStopSerializer(many=True)
    total_cost = serializers.FloatField()
    fuel_consumed_gallons = serializers.FloatField()


class StationsNearRequestSerializer(serializers.Serializer):
    
    #Validates query parameters for nearby stations endpoint.

    lat = serializers.FloatField(
        required=True,
        min_value=-90.0,
        max_value=90.0,
        help_text="Latitude coordinate (-90 to 90)"
    )
    
    lon = serializers.FloatField(
        required=True,
        min_value=-180.0,
        max_value=180.0,
        help_text="Longitude coordinate (-180 to 180)"
    )
    
    radius = serializers.FloatField(
        required=False,
        default=10.0,
        min_value=1.0,
        max_value=50.0,
        help_text="Search radius in miles (1-50, default: 10)"
    )


class FuelStationSerializer(serializers.Serializer):

    #Serializes a fuel station for nearby stations response.

    id = serializers.IntegerField()
    station = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    price = serializers.FloatField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    address = serializers.CharField()


class StationsNearResponseSerializer(serializers.Serializer):

    stations = FuelStationSerializer(many=True)