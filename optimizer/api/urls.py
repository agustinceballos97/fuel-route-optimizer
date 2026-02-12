from django.urls import path
from .views import RouteOptimizationView, StationsNearView

app_name = 'optimizer_api'

urlpatterns = [
    path('route/optimize', RouteOptimizationView.as_view(), name='route-optimize'),
    path('stations/near', StationsNearView.as_view(), name='stations-near'),
]