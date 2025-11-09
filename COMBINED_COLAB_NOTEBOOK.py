# ===================================================================
# 🚀 COMBINED COLAB NOTEBOOK: Transcribe + Translate + Image Diagnosis
# ===================================================================
# This notebook provides:
# - Audio transcription (Whisper)
# - Translation (Ollama + Mistral)
# - Image disease diagnosis (CLIP + Custom Model)
# All accessible through ONE ngrok URL!
# ===================================================================

# ===================================================================
# 📦 CELL 1: Install All Dependencies
# ===================================================================
print("📦 Installing dependencies...")

!pip install -q pyngrok
!pip install -q openai-whisper==20231117 flask flask-cors
!pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
!pip install -q git+https://github.com/openai/CLIP.git

print("✅ All dependencies installed!")

# ===================================================================
# 🔑 CELL 2: Setup ngrok Authentication
# ===================================================================
from pyngrok import ngrok

# Paste your ngrok authtoken here
NGROK_TOKEN = "2zMkz0ctKnVIRi6gRwXzyokbJn4_5Q7kerzj3Ch2vZ6cbr6Lj"

ngrok.set_auth_token(NGROK_TOKEN)
print("✅ ngrok authenticated!")

# ===================================================================
# 🤖 CELL 3: Install and Start Ollama
# ===================================================================
print("🤖 Installing Ollama...")
!curl -fsSL https://ollama.com/install.sh | sh

import subprocess
import time
import os

# Start Ollama server in background
print("Starting Ollama server...")
ollama_process = subprocess.Popen(
    ['ollama', 'serve'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
time.sleep(10)  # Wait for Ollama to start

# Pull Mistral model
print("📥 Downloading Mistral model... (this may take 5-10 minutes)")
!ollama pull mistral
print("✅ Mistral model ready!")

# ===================================================================
# 🎤 CELL 4: Load Whisper Model
# ===================================================================
import whisper

print("🎤 Loading Whisper model...")
whisper_model = whisper.load_model("large-v3")  # Or "medium" for faster processing
print("✅ Whisper model loaded!")

# ===================================================================
# 🖼️ CELL 5: Mount Drive & Load Image Models
# ===================================================================
from google.colab import drive
drive.mount('/content/drive')

import torch
import clip
from torch import nn
from PIL import Image
import io
import torch.nn.functional as F

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Device: {device}")

# Load CLIP
print("🖼️ Loading CLIP model...")
model_clip, preprocess = clip.load("ViT-L/14", device=device, jit=False)
model_clip.eval()
print("✅ CLIP loaded")

# Define Classifier
class Classifier(nn.Module):
    def __init__(self, in_dim, num_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 512), nn.BatchNorm1d(512), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )
    def forward(self, x): 
        return self.net(x)

# Load your trained disease detection model
MODEL_PATH = '/content/drive/MyDrive/mvpdr_highacc_model.pth'
checkpoint = torch.load(MODEL_PATH, map_location=device)
classes = checkpoint['classes']
model_clf = Classifier(768, len(classes)).to(device)
model_clf.load_state_dict(checkpoint['model_state'])
model_clf.eval()
print(f"✅ Disease detection model loaded! {len(classes)} classes")

# ===================================================================
# 🧠 CELL 6: Define Helper Functions
# ===================================================================

# Translation function using Ollama
def translate_with_ollama(text: str) -> str:
    """
    Translate mixed-language text to English using Mistral via Ollama
    with agricultural context
    """
    if not text or not text.strip():
        return text
    
    # Agricultural context prompt
    prompt = f"""
You are a professional translator. Translate the following text into clear and accurate English.

If the sentence contains agricultural content (e.g., crops, plants, diseases, pests, leaves, farming terms, etc.),
use the appropriate agricultural meaning for terms like:
- "patte" = leaves
- "daag" = spots
- "keeda" = insect/pest
- "bimari" = disease
- "paudha"/"paudhe" = plant/plants
- "fal" = fruit

If the sentence is NOT related to agriculture, DO NOT apply agricultural meaning — translate it normally without adding or modifying context.

Text: {text}

Return ONLY the English translation. No explanations or added details.
"""
    
    try:
        # Call Ollama using subprocess
        result = subprocess.run(
            ['ollama', 'run', 'mistral', prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            translated = result.stdout.strip()
            # Clean up any extra formatting
            translated = translated.replace('"', '').replace("'", "").strip()
            print(f"[OLLAMA] Original: {text}")
            print(f"[OLLAMA] Translated: {translated}")
            return translated
        else:
            print(f"[OLLAMA ERROR] {result.stderr}")
            return text  # Fallback to original
    
    except Exception as e:
        print(f"[OLLAMA ERROR] {e}")
        return text  # Fallback to original

# Image prediction function
def predict_disease(image_bytes):
    """
    Predict disease from image bytes using CLIP + Custom Classifier
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_tensor = preprocess(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            feat = model_clip.encode_image(img_tensor)
            feat = feat / feat.norm(dim=-1, keepdim=True)
            logits = model_clf(feat.float())
            probs = F.softmax(logits, dim=-1)[0]
            
            top_probs, top_indices = torch.topk(probs, min(3, len(classes)))
            top_predictions = [
                {'class_name': classes[idx.item()], 'confidence': prob.item()}
                for prob, idx in zip(top_probs, top_indices)
            ]
            
            pred_idx = probs.argmax().item()
            return {
                'success': True,
                'disease': classes[pred_idx],
                'class_name': classes[pred_idx],
                'confidence': probs[pred_idx].item(),
                'top_predictions': top_predictions
            }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

print("✅ All helper functions ready!")

# ===================================================================
# 🌐 CELL 7: Create Unified Flask API
# ===================================================================
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile

app = Flask(__name__)
CORS(app)

# Health check endpoint
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "services": ["whisper", "ollama", "clip", "disease_detection"],
        "device": device,
        "num_classes": len(classes)
    })

# Homepage
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'running',
        'services': {
            'transcription': '/api/transcribe',
            'translation': '/api/translate',
            'image_diagnosis': '/diagnose',
            'health_check': '/health'
        },
        'models': {
            'whisper': 'large-v3',
            'translation': 'mistral',
            'image': 'CLIP ViT-L/14',
            'classes': len(classes)
        },
        'device': device
    })

# Transcribe and translate endpoint
@app.route("/api/transcribe", methods=["POST"])
def transcribe_and_translate():
    """
    Combined endpoint: Transcribe audio with Whisper, then translate with Ollama
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files["audio"]
    
    # Step 1: Transcribe with Whisper
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        audio_file.save(tmp.name)
        try:
            print(f"\n[WHISPER] Transcribing audio...")
            result = whisper_model.transcribe(
                tmp.name,
                language=None,  # Auto-detect language
                task="transcribe"
            )
            os.unlink(tmp.name)
            
            transcript = result["text"].strip()
            detected_language = result.get("language", "unknown")
            
            print(f"[WHISPER] Transcript: {transcript}")
            print(f"[WHISPER] Detected language: {detected_language}")
            
            # Step 2: Translate with Ollama (if not pure English)
            translated_text = transcript
            translation_applied = False
            
            # Only translate if it contains non-English content
            if detected_language in ['hi', 'mr'] or detected_language != 'en':
                print(f"[OLLAMA] Translating to English...")
                translated_text = translate_with_ollama(transcript)
                translation_applied = True
            
            return jsonify({
                "transcript": transcript,
                "translated": translated_text,
                "detected_language": detected_language,
                "translation_applied": translation_applied,
                "engine": "whisper+ollama"
            })
        
        except Exception as e:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            print(f"[ERROR] {e}")
            return jsonify({"error": str(e)}), 500

# Text-only translation endpoint
@app.route("/api/translate", methods=["POST"])
def translate_only():
    """
    Standalone translation endpoint (for text-only translation)
    """
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
    
    text = data["text"]
    translated = translate_with_ollama(text)
    
    return jsonify({
        "original": text,
        "translated": translated
    })

# Image diagnosis endpoint
@app.route('/diagnose', methods=['POST'])
def diagnose():
    """
    Image disease diagnosis endpoint
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image'}), 400
        
        image_file = request.files['image']
        crop = request.form.get('crop', 'unknown')
        
        image_bytes = image_file.read()
        result = predict_disease(image_bytes)
        
        if result['success']:
            print(f"✅ {result['disease']} ({result['confidence']*100:.1f}%)")
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

print("✅ Flask API with all endpoints ready!")

# ===================================================================
# 🚀 CELL 8: Start Server with ngrok
# ===================================================================
from threading import Thread

# Kill any existing ngrok tunnels
ngrok.kill()

# Create ngrok tunnel
public_url = ngrok.connect(5000)

print("\n" + "="*70)
print("🚀 UNIFIED API IS LIVE!")
print("="*70)
print(f"\n📡 PUBLIC URL: {public_url}")
print("\n" + "="*70)
print("🔧 AVAILABLE ENDPOINTS:")
print("="*70)
print(f"  1. Health Check:      {public_url}/health")
print(f"  2. Transcribe Audio:  {public_url}/api/transcribe (POST with 'audio' file)")
print(f"  3. Translate Text:    {public_url}/api/translate (POST with JSON)")
print(f"  4. Diagnose Image:    {public_url}/diagnose (POST with 'image' file)")
print("="*70)
print("\n📋 DJANGO CONFIGURATION:")
print("="*70)
print("Copy these URLs to your Django backend:\n")
print(f'# In backend/disease_detection/views.py:')
print(f'COLAB_STT_URL = "{public_url}/api/transcribe"')
print(f'COLAB_TRANSLATE_URL = "{public_url}/api/translate"')
print(f'\n# In backend/disease_detection/image_views.py:')
print(f'COLAB_IMAGE_API_URL = "{public_url}/diagnose"')
print("="*70 + "\n")

# Start Flask server
print("🎤 Starting Flask server on port 5000...")
Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000}).start()

print("\n✅ SERVER IS RUNNING! Keep this cell active.")
print("⚠️  Do NOT stop this cell or the API will go offline.\n")

