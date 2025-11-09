"""
URL patterns for crop recommendation app
"""

from django.urls import path
from . import views

urlpatterns = [
    path('recommend/', views.recommend_crop, name='recommend_crop'),
    path('history/', views.get_recommendation_history, name='recommendation_history'),
    path('model-info/', views.get_model_info, name='model_info'),
    path('train/', views.train_model, name='train_model'),
    path('weather/', views.get_weather_data, name='weather_data'),
    path('crop-info/', views.get_crop_info, name='crop_info'),
]
