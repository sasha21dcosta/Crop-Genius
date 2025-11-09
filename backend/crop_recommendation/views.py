"""
Django views for crop recommendation API endpoints
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import CropRecommendation, ModelPerformance
from .ml_pipeline import crop_recommender
from .serializers import CropRecommendationSerializer

# Initialize the model when the module loads
try:
    crop_recommender.load_models()
    print("✅ Crop recommendation model loaded successfully!")
except Exception as e:
    print(f"⚠️ Warning: Could not load crop recommendation model: {e}")
    print("Make sure to train the model first: python crop_recommendation/train_with_your_data.py Crop_recommendation.csv")

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_crop(request):
    """
    Get crop recommendation based on soil and weather conditions
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['n_content', 'p_content', 'k_content', 'ph']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {missing_fields}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract parameters
        n_content = float(data['n_content'])
        p_content = float(data['p_content'])
        k_content = float(data['k_content'])
        ph = float(data['ph'])
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Validate parameter ranges
        if not (0 <= n_content <= 200):
            return Response({'error': 'N content must be between 0 and 200'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        if not (0 <= p_content <= 200):
            return Response({'error': 'P content must be between 0 and 200'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        if not (0 <= k_content <= 200):
            return Response({'error': 'K content must be between 0 and 200'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        if not (0 <= ph <= 14):
            return Response({'error': 'pH must be between 0 and 14'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure model is loaded
        if crop_recommender.best_model is None:
            try:
                crop_recommender.load_models()
            except Exception as e:
                return Response({
                    'error': 'Model not loaded. Please train the model first.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Get prediction
        result = crop_recommender.predict_crop(
            n=n_content,
            p=p_content,
            k=k_content,
            ph=ph,
            lat=latitude,
            lon=longitude
        )
        
        # Save recommendation to database
        recommendation = CropRecommendation.objects.create(
            user=request.user,
            n_content=n_content,
            p_content=p_content,
            k_content=k_content,
            ph=ph,
            temperature=result['used_features']['temperature'],
            humidity=result['used_features']['humidity'],
            rainfall=result['used_features']['rainfall'],
            latitude=latitude,
            longitude=longitude,
            predicted_crop=result['predicted_crop'],
            confidence_score=result['confidence_score'],
            alternative_crops=result['alternative_crops']
        )
        
        # Return response
        return Response({
            'success': True,
            'recommendation': {
                'predicted_crop': result['predicted_crop'],
                'confidence_score': result['confidence_score'],
                'alternative_crops': result['alternative_crops'],
                'probabilities': result['probabilities'],
                'model_info': result['model_info']
            },
            'input_features': result['used_features'],
            'recommendation_id': recommendation.id
        })
        
    except Exception as e:
        logger.error(f"Error in crop recommendation: {e}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendation_history(request):
    """
    Get user's crop recommendation history
    """
    try:
        recommendations = CropRecommendation.objects.filter(user=request.user)
        serializer = CropRecommendationSerializer(recommendations, many=True)
        
        return Response({
            'success': True,
            'recommendations': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error fetching recommendation history: {e}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_model_info(request):
    """
    Get information about the current model
    """
    try:
        # Load model metadata
        import os
        import json
        
        model_dir = "./crop_models/"
        metadata_path = os.path.join(model_dir, "model_metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            return Response({
                'success': True,
                'model_info': metadata
            })
        else:
            return Response({
                'error': 'Model not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Error fetching model info: {e}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def train_model(request):
    """
    Train/retrain the crop recommendation model
    Note: This should be restricted to admin users in production
    """
    try:
        # Check if user is staff/admin (in production, use proper permissions)
        if not request.user.is_staff:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        csv_path = request.data.get('csv_path', 'Crop_recommendation.csv')
        optimize = request.data.get('optimize', True)
        
        # Train models
        scores = crop_recommender.train_models(csv_path, optimize=optimize)
        
        # Save performance metrics
        for model_name, accuracy in scores.items():
            ModelPerformance.objects.create(
                model_name=model_name,
                version="2.0",
                accuracy=accuracy,
                precision=accuracy,  # Simplified for now
                recall=accuracy,
                f1_score=accuracy,
                test_samples=1000  # Placeholder
            )
        
        return Response({
            'success': True,
            'message': 'Model training completed',
            'model_scores': scores
        })
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_weather_data(request):
    """
    Get current weather data for a location
    """
    try:
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        
        if not lat or not lon:
            return Response({
                'error': 'Latitude and longitude are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        weather = crop_recommender.fetch_weather_data(float(lat), float(lon))
        
        return Response({
            'success': True,
            'weather': weather
        })
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return Response({
            'error': 'Internal server error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)