"""
Django REST API views for real-time crop prices
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from .utils import fetch_crop_price, get_available_crops, get_available_states
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated access for price checking
def get_crop_price(request):
    """
    GET /api/crop-prices/?crop_name=Tomato&state=Maharashtra&district=Nashik
    
    Fetch real-time crop price from AGMARKNET API.
    Returns the most recent price data available (today or previous dates).
    """
    # Get query parameters
    crop_name = request.GET.get('crop_name', '').strip()
    state = request.GET.get('state', '').strip()
    district = request.GET.get('district', '').strip()
    
    # Validate required parameters
    if not crop_name:
        return Response(
            {"error": "crop_name parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not state:
        return Response(
            {"error": "state parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not district:
        return Response(
            {"error": "district parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create cache key
    cache_key = f"crop_price_{crop_name}_{state}_{district}".lower().replace(" ", "_")
    
    # Try to get cached data (cache for 1 hour)
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Returning cached price data for {crop_name}")
        cached_data['cached'] = True
        return Response(cached_data, status=status.HTTP_200_OK)
    
    # Fetch fresh data from API
    logger.info(f"Fetching fresh price data for {crop_name} in {district}, {state}")
    result = fetch_crop_price(crop_name, state, district)
    
    # Check if fetch was successful
    if not result.get('success', False):
        return Response(result, status=status.HTTP_404_NOT_FOUND)
    
    # Cache the result for 1 hour (3600 seconds)
    cache.set(cache_key, result, 3600)
    result['cached'] = False
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_crops_view(request):
    """
    GET /api/crop-prices/crops/
    
    Get list of available crops/commodities.
    """
    cache_key = "available_crops"
    
    # Try to get cached data (cache for 24 hours)
    cached_crops = cache.get(cache_key)
    if cached_crops:
        return Response({"crops": cached_crops, "cached": True}, status=status.HTTP_200_OK)
    
    # Fetch fresh data
    crops = get_available_crops()
    
    # Cache for 24 hours (86400 seconds)
    cache.set(cache_key, crops, 86400)
    
    return Response({"crops": crops, "cached": False}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_states_view(request):
    """
    GET /api/crop-prices/states/
    
    Get list of available states.
    """
    states = get_available_states()
    return Response({"states": states}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_multiple_crop_prices(request):
    """
    POST /api/crop-prices/bulk/
    
    Fetch prices for multiple crops at once.
    
    Request body:
    {
        "queries": [
            {"crop_name": "Tomato", "state": "Maharashtra", "district": "Nashik"},
            {"crop_name": "Onion", "state": "Maharashtra", "district": "Pune"}
        ]
    }
    """
    queries = request.data.get('queries', [])
    
    if not queries or not isinstance(queries, list):
        return Response(
            {"error": "queries list is required in request body"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    results = []
    
    for query in queries[:10]:  # Limit to 10 queries per request
        crop_name = query.get('crop_name', '').strip()
        state = query.get('state', '').strip()
        district = query.get('district', '').strip()
        
        if not crop_name or not state or not district:
            results.append({
                "query": query,
                "error": "Missing required fields",
                "success": False
            })
            continue
        
        # Check cache first
        cache_key = f"crop_price_{crop_name}_{state}_{district}".lower().replace(" ", "_")
        cached_data = cache.get(cache_key)
        
        if cached_data:
            results.append({**cached_data, "cached": True})
        else:
            result = fetch_crop_price(crop_name, state, district)
            if result.get('success', False):
                cache.set(cache_key, result, 3600)
                results.append({**result, "cached": False})
            else:
                results.append(result)
    
    return Response({"results": results}, status=status.HTTP_200_OK)

