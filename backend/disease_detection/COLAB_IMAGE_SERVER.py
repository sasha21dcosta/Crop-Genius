"""
🌿 COLAB IMAGE DIAGNOSIS SERVER
================================
Run this code in Google Colab to create an API server for image-based disease diagnosis.

SETUP INSTRUCTIONS:
1. Upload this file to your Google Drive
2. Open it in Google Colab
3. Run all cells sequentially
4. Copy the ngrok URL and update COLAB_IMAGE_API_URL in image_views.py

MODEL REQUIREMENTS:
- Trained model saved at: /content/drive/MyDrive/mvpdr_highacc_model.pth
- Model should contain 'model_state' and 'classes' keys
"""

# ================================================================
# CELL 1: Mount Drive and Install Dependencies
# ================================================================
from google.colab import drive
import os

# Mount Google Drive
drive.mount('/content/drive', force_remount=True)

# Install dependencies
print("📦 Installing dependencies...")
!pip install flask flask-cors pyngrok pillow torch torchvision > /dev/null
!pip install git+https://github.com/openai/CLIP.git > /dev/null

print("✅ Dependencies installed!")

# ================================================================
# CELL 2: Load CLIP and Model
# ================================================================
import torch
import clip
from torch import nn
from PIL import Image
import io

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Using device: {device}")

# Load CLIP model
print("📥 Loading CLIP ViT-L/14...")
model_clip, preprocess = clip.load("ViT-L/14", device=device, jit=False)
model_clip.eval()
print("✅ CLIP loaded!")

# Define Classifier architecture (same as training)
class Classifier(nn.Module):
    def __init__(self, in_dim, num_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        return self.net(x)

# Load trained model
MODEL_PATH = '/content/drive/MyDrive/mvpdr_highacc_model.pth'

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"❌ Model not found at {MODEL_PATH}. Please train the model first!")

print("📥 Loading trained classifier...")
checkpoint = torch.load(MODEL_PATH, map_location=device)
classes = checkpoint['classes']
model_clf = Classifier(768, len(classes)).to(device)  # ViT-L/14 has 768 features
model_clf.load_state_dict(checkpoint['model_state'])
model_clf.eval()

print(f"✅ Model loaded! {len(classes)} classes:")
print(classes)

# ================================================================
# CELL 3: Define Prediction Function
# ================================================================
import torch.nn.functional as F

def predict_disease(image_bytes):
    """
    Predicts disease from image bytes
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        dict with keys: disease, confidence, class_name, top_predictions
    """
    try:
        # Load and preprocess image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_tensor = preprocess(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            # Extract CLIP features
            feat = model_clip.encode_image(img_tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
            
            # Classify
            logits = model_clf(feat.float())
            probs = F.softmax(logits, dim=-1)[0]
            
            # Get top 3 predictions
            top_probs, top_indices = torch.topk(probs, min(3, len(classes)))
            
            top_predictions = [
                {
                    'class_name': classes[idx.item()],
                    'confidence': prob.item()
                }
                for prob, idx in zip(top_probs, top_indices)
            ]
            
            # Best prediction
            pred_idx = probs.argmax().item()
            disease_name = classes[pred_idx]
            confidence = probs[pred_idx].item()
            
            return {
                'success': True,
                'disease': disease_name,
                'class_name': disease_name,
                'confidence': confidence,
                'top_predictions': top_predictions
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Test the function
print("🧪 Testing prediction function...")
test_result = predict_disease(open('/content/drive/MyDrive/rice_blast_2.jpg', 'rb').read())
print(f"Test prediction: {test_result}")

# ================================================================
# CELL 4: Create Flask API Server
# ================================================================
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'model': 'CLIP ViT-L/14 + MLP Classifier',
        'classes': len(classes),
        'device': device
    })

@app.route('/diagnose', methods=['POST'])
def diagnose():
    """
    Main diagnosis endpoint
    Expects: multipart/form-data with 'image' file
    Optional: 'crop' field
    """
    try:
        # Check if image is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        crop = request.form.get('crop', 'unknown')
        
        if image_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Read image bytes
        image_bytes = image_file.read()
        
        print(f"📸 Processing image: {image_file.filename} for crop: {crop}")
        
        # Predict
        result = predict_disease(image_bytes)
        
        if result['success']:
            print(f"✅ Prediction: {result['disease']} ({result['confidence']*100:.1f}%)")
            return jsonify(result), 200
        else:
            print(f"❌ Prediction failed: {result['error']}")
            return jsonify(result), 500
    
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({
            'error': error_msg,
            'success': False
        }), 500

print("✅ Flask app created!")

# ================================================================
# CELL 5: Start Server with ngrok
# ================================================================
from pyngrok import ngrok
import sys

# Kill any existing ngrok tunnels
ngrok.kill()

# Start Flask in background
print("🚀 Starting Flask server on port 5000...")

# Set ngrok auth token (REQUIRED - get from https://dashboard.ngrok.com/get-started/your-authtoken)
# Run this command with YOUR token:
NGROK_AUTH_TOKEN = "YOUR_NGROK_TOKEN_HERE"  # 👈 REPLACE THIS!

if NGROK_AUTH_TOKEN == "YOUR_NGROK_TOKEN_HERE":
    print("⚠️  WARNING: Please set your ngrok auth token!")
    print("Get it from: https://dashboard.ngrok.com/get-started/your-authtoken")
    print("Then run: ngrok.set_auth_token('your_token_here')")
else:
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# Create tunnel
public_url = ngrok.connect(5000)
print(f"\n{'='*60}")
print(f"🌐 PUBLIC URL: {public_url}")
print(f"{'='*60}")
print(f"\n📋 Copy this URL and update COLAB_IMAGE_API_URL in image_views.py:")
print(f"   COLAB_IMAGE_API_URL = '{public_url}/diagnose'")
print(f"\n🧪 Test endpoint: {public_url}/")
print(f"{'='*60}\n")

# Run Flask app
app.run(port=5000)

# ================================================================
# NOTES:
# ================================================================
# 1. Keep this Colab notebook running while using the app
# 2. If disconnected, rerun Cell 5 to get a new ngrok URL
# 3. Update the URL in image_views.py after each restart
# 4. For production, consider using Google Cloud Run or AWS Lambda
# ================================================================

