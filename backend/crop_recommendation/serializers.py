"""
Serializers for crop recommendation models
"""

from rest_framework import serializers
from .models import CropRecommendation, ModelPerformance


class CropRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for crop recommendation model"""
    
    class Meta:
        model = CropRecommendation
        fields = [
            'id', 'n_content', 'p_content', 'k_content', 'ph',
            'temperature', 'humidity', 'rainfall', 'latitude', 'longitude',
            'predicted_crop', 'confidence_score', 'alternative_crops',
            'created_at', 'model_version'
        ]
        read_only_fields = ['id', 'created_at']


class ModelPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for model performance metrics"""
    
    class Meta:
        model = ModelPerformance
        fields = [
            'id', 'model_name', 'version', 'accuracy', 'precision',
            'recall', 'f1_score', 'training_date', 'test_samples'
        ]
        read_only_fields = ['id', 'training_date']


class CropRecommendationRequestSerializer(serializers.Serializer):
    """Serializer for crop recommendation request"""
    n_content = serializers.FloatField(min_value=0, max_value=200)
    p_content = serializers.FloatField(min_value=0, max_value=200)
    k_content = serializers.FloatField(min_value=0, max_value=200)
    ph = serializers.FloatField(min_value=0, max_value=14)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
