from django.urls import path
from . import views
from . import image_views

urlpatterns = [
    path('detect_disease/', views.DetectDiseaseView.as_view(), name='detect_disease'),
    path('transcribe_audio/', views.TranscribeAudioView.as_view(), name='transcribe_audio'),
    path('translate/', views.TranslateTextView.as_view(), name='translate_text'),
    
    # Image-based diagnosis
    path('diagnose_image/', image_views.diagnose_image, name='diagnose_image'),
    
    # Chat session management
    path('chat-sessions/', views.chat_sessions, name='chat_sessions'),
    path('chat-sessions/<int:session_id>/', views.chat_session_detail, name='chat_session_detail'),
    path('chat-sessions/<int:session_id>/messages/', views.add_message_to_session, name='add_message'),
]
