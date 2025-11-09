from django.db import models
from django.contrib.auth.models import User


class CropRecommendation(models.Model):
    """Store crop recommendation requests and results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    n_content = models.FloatField(help_text="Nitrogen content in soil")
    p_content = models.FloatField(help_text="Phosphorus content in soil")
    k_content = models.FloatField(help_text="Potassium content in soil")
    ph = models.FloatField(help_text="Soil pH level")
    temperature = models.FloatField(help_text="Temperature in Celsius")
    humidity = models.FloatField(help_text="Humidity percentage")
    rainfall = models.FloatField(help_text="Rainfall in mm")
    latitude = models.FloatField(null=True, blank=True, help_text="Location latitude")
    longitude = models.FloatField(null=True, blank=True, help_text="Location longitude")
    
    # Results
    predicted_crop = models.CharField(max_length=100, help_text="Recommended crop")
    confidence_score = models.FloatField(help_text="Model confidence score")
    alternative_crops = models.JSONField(default=list, help_text="Alternative crop suggestions")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    model_version = models.CharField(max_length=50, default="1.0")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Crop recommendation for {self.predicted_crop} (confidence: {self.confidence_score:.2f})"


class ModelPerformance(models.Model):
    """Track model performance metrics"""
    model_name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    training_date = models.DateTimeField(auto_now_add=True)
    test_samples = models.IntegerField()
    
    class Meta:
        ordering = ['-training_date']
    
    def __str__(self):
        return f"{self.model_name} v{self.version} - Accuracy: {self.accuracy:.3f}"