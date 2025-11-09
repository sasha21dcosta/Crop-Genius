"""
URL configuration for crop_prices app
"""
from django.urls import path
from .views import (
    get_crop_price,
    get_available_crops_view,
    get_available_states_view,
    get_multiple_crop_prices
)

urlpatterns = [
    path('', get_crop_price, name='get_crop_price'),  # GET /api/crop-prices/?crop_name=...&state=...&district=...
    path('crops/', get_available_crops_view, name='available_crops'),  # GET /api/crop-prices/crops/
    path('states/', get_available_states_view, name='available_states'),  # GET /api/crop-prices/states/
    path('bulk/', get_multiple_crop_prices, name='bulk_prices'),  # POST /api/crop-prices/bulk/
]

