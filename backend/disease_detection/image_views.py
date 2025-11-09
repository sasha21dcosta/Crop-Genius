"""
Image-based Disease Detection Views
Forwards images to Colab server for diagnosis using CLIP-based model
"""

import requests
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

# ========================================
# CONFIGURATION
# ========================================
# Replace with your Colab ngrok URL when running
COLAB_IMAGE_API_URL = "https://89cf407227c9.ngrok-free.app/diagnose"

# You can also use environment variable:
import os
COLAB_IMAGE_API_URL = os.environ.get('COLAB_IMAGE_API_URL', COLAB_IMAGE_API_URL)


@csrf_exempt
def diagnose_image(request):
    """
    Receives an image from Flutter app and forwards it to Colab server
    for disease diagnosis using CLIP-based model.
    
    Expected: POST with 'image' file and optional 'crop' field
    Returns: {
        "disease": "rice_blast",
        "confidence": 0.85,
        "class_name": "Rice Blast",
        "message": "Detected Rice Blast with 85% confidence"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    # Get the uploaded image
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image file provided'}, status=400)
    
    image_file = request.FILES['image']
    crop = request.POST.get('crop', 'unknown')
    
    logger.info(f"Received image diagnosis request for crop: {crop}")
    
    try:
        # Forward image to Colab server
        files = {'image': (image_file.name, image_file.read(), image_file.content_type)}
        data = {'crop': crop}
        
        logger.info(f"Forwarding to Colab: {COLAB_IMAGE_API_URL}")
        response = requests.post(
            COLAB_IMAGE_API_URL,
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Colab response: {result}")
            
            # Format response for Flutter app
            disease_name = result.get('disease', 'unknown')
            confidence = result.get('confidence', 0.0)
            class_name = result.get('class_name', disease_name)
            
            return JsonResponse({
                'success': True,
                'disease': disease_name,
                'confidence': confidence,
                'class_name': class_name,
                'message': f"Detected {class_name} with {confidence*100:.1f}% confidence",
                'crop': crop
            })
        else:
            logger.error(f"Colab returned error: {response.status_code} {response.text}")
            return JsonResponse({
                'error': f'Model server error: {response.status_code}',
                'details': response.text
            }, status=500)
            
    except requests.exceptions.Timeout:
        logger.error("Colab server timeout")
        return JsonResponse({
            'error': 'Model server timeout. Please try again.'
        }, status=504)
    
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Colab server")
        return JsonResponse({
            'error': 'Cannot connect to model server. Please ensure Colab is running with ngrok.'
        }, status=503)
    
    except Exception as e:
        logger.exception(f"Error processing image: {e}")
        return JsonResponse({
            'error': f'Internal error: {str(e)}'
        }, status=500)

