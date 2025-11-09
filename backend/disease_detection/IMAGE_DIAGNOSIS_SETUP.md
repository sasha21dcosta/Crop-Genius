# 📷 Image-Based Disease Diagnosis Setup Guide

This guide will help you set up the image-based disease diagnosis feature using your trained CLIP model running on Google Colab.

---

## 🎯 Overview

The system works as follows:
1. **User uploads image** in Flutter app
2. **Django backend** receives image and forwards it to Colab
3. **Colab server** runs CLIP model and returns disease prediction
4. **App displays** results with treatment options

---

## 📋 Prerequisites

✅ Trained model file: `/content/drive/MyDrive/mvpdr_highacc_model.pth`  
✅ Test image for verification  
✅ Google Colab account  
✅ ngrok account (free tier is fine)  

---

## 🚀 Step-by-Step Setup

### **STEP 1: Get ngrok Auth Token**

1. Go to: https://dashboard.ngrok.com/signup
2. Sign up (free account works)
3. Navigate to: https://dashboard.ngrok.com/get-started/your-authtoken
4. Copy your authtoken (looks like: `2abc123def456...`)

---

### **STEP 2: Prepare Your Colab Notebook**

1. Open Google Colab: https://colab.research.google.com
2. Create a new notebook or open an existing one
3. Copy the code from `COLAB_IMAGE_SERVER.py` into separate cells

**Important:** Make sure your trained model is at:
```
/content/drive/MyDrive/mvpdr_highacc_model.pth
```

---

### **STEP 3: Run the Colab Server**

#### **Cell 1: Mount Drive & Install**
```python
from google.colab import drive
import os

drive.mount('/content/drive', force_remount=True)

print("📦 Installing dependencies...")
!pip install flask flask-cors pyngrok pillow torch torchvision > /dev/null
!pip install git+https://github.com/openai/CLIP.git > /dev/null

print("✅ Dependencies installed!")
```

#### **Cell 2: Load Model**
```python
import torch
import clip
from torch import nn
from PIL import Image
import io

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Using device: {device}")

# Load CLIP
print("📥 Loading CLIP ViT-L/14...")
model_clip, preprocess = clip.load("ViT-L/14", device=device, jit=False)
model_clip.eval()

# Define Classifier
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
checkpoint = torch.load(MODEL_PATH, map_location=device)
classes = checkpoint['classes']
model_clf = Classifier(768, len(classes)).to(device)
model_clf.load_state_dict(checkpoint['model_state'])
model_clf.eval()

print(f"✅ Model loaded! {len(classes)} classes")
```

#### **Cell 3: Define Prediction Function**
```python
import torch.nn.functional as F

def predict_disease(image_bytes):
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

print("✅ Prediction function ready!")
```

#### **Cell 4: Create Flask API**
```python
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'running',
        'model': 'CLIP ViT-L/14 + MLP',
        'classes': len(classes),
        'device': device
    })

@app.route('/diagnose', methods=['POST'])
def diagnose():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
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

print("✅ Flask app ready!")
```

#### **Cell 5: Start Server with ngrok**
```python
from pyngrok import ngrok

# IMPORTANT: Replace with YOUR ngrok token
NGROK_AUTH_TOKEN = "YOUR_TOKEN_HERE"  # 👈 PASTE YOUR TOKEN HERE

ngrok.set_auth_token(NGROK_AUTH_TOKEN)
ngrok.kill()  # Kill any existing tunnels

# Create tunnel
public_url = ngrok.connect(5000)

print(f"\n{'='*60}")
print(f"🌐 PUBLIC URL: {public_url}")
print(f"{'='*60}")
print(f"\n📋 COPY THIS URL:")
print(f"   {public_url}/diagnose")
print(f"\n🧪 Test in browser: {public_url}/")
print(f"{'='*60}\n")

# Start server
app.run(port=5000)
```

---

### **STEP 4: Update Django Backend**

Once your Colab server is running, you'll see a URL like:
```
https://abc123def456.ngrok-free.app
```

**Update your backend:**

1. Open `backend/disease_detection/image_views.py`
2. Find line with `COLAB_IMAGE_API_URL`
3. Replace with your ngrok URL:

```python
COLAB_IMAGE_API_URL = "https://your-actual-ngrok-url.ngrok-free.app/diagnose"
```

**OR** use environment variable (recommended):

```bash
# In your terminal or .env file
export COLAB_IMAGE_API_URL="https://your-ngrok-url.ngrok-free.app/diagnose"
```

---

### **STEP 5: Test the System**

#### **Test 1: Check Colab Server**
Open in browser: `https://your-ngrok-url.ngrok-free.app/`

You should see:
```json
{
  "status": "running",
  "model": "CLIP ViT-L/14 + MLP",
  "classes": 38,
  "device": "cuda"
}
```

#### **Test 2: Test from Terminal**
```bash
curl -X POST \
  -F "image=@/path/to/test/image.jpg" \
  -F "crop=rice" \
  https://your-ngrok-url.ngrok-free.app/diagnose
```

#### **Test 3: Test from App**
1. Run your Django backend
2. Run your Flutter app
3. Select a crop
4. Tap the 🖼️ image icon
5. Upload a plant disease image
6. Check results!

---

## 🎨 What's in the App?

### **New Features Added:**

1. **Image Icon Button** 🖼️
   - Located next to the microphone icon
   - Opens image picker to select photos
   - Disabled until crop is selected

2. **Image Upload & Analysis**
   - Uploads image to backend
   - Shows "📷 Uploaded image for diagnosis" message
   - Displays loading indicator: "Analyzing image..."

3. **Results Display**
   - Shows disease name with confidence
   - Displays top 3 predictions
   - Provides action buttons: Treatment, Prevention, More Info

4. **Session Integration**
   - Image diagnoses are saved in chat history
   - Can continue conversation after image diagnosis
   - Works with existing chat session management

---

## 🐛 Troubleshooting

### **Error: "Cannot connect to model server"**
- ✅ Check if Colab is running (Cell 5)
- ✅ Verify ngrok URL is correct in `image_views.py`
- ✅ Make sure ngrok tunnel is active

### **Error: "Model server timeout"**
- ✅ Colab might be sleeping - run Cell 5 again
- ✅ Check GPU quota (Colab free tier limits)
- ✅ Verify model is loaded (check Cell 2 output)

### **Error: "Model not found"**
- ✅ Verify model path: `/content/drive/MyDrive/mvpdr_highacc_model.pth`
- ✅ Check if Drive is properly mounted
- ✅ Ensure model was trained and saved correctly

### **ngrok Error: "Invalid authtoken"**
- ✅ Get new token from https://dashboard.ngrok.com/get-started/your-authtoken
- ✅ Replace in Cell 5, line: `NGROK_AUTH_TOKEN = "..."`

### **Low Confidence Predictions**
- ✅ Ensure image is clear and well-lit
- ✅ Check if disease is in training classes
- ✅ Try different angles or closer shots
- ✅ Consider retraining model with more data

---

## 📊 Model Performance

Your model should have:
- **Validation Accuracy**: >60% (ideally 70-80%)
- **Classes**: 38+ plant diseases
- **Architecture**: CLIP ViT-L/14 (768 features) + MLP Classifier

If accuracy is low, consider:
1. More training data
2. Data augmentation
3. Longer training (more epochs)
4. Different learning rates

---

## 🔄 Workflow Summary

```
┌─────────────┐
│ Flutter App │
│  (Upload)   │
└──────┬──────┘
       │ Image
       ▼
┌─────────────┐
│   Django    │
│  (Forward)  │
└──────┬──────┘
       │ HTTP POST
       ▼
┌─────────────┐
│   Colab     │
│ (Analyze)   │
└──────┬──────┘
       │ JSON Result
       ▼
┌─────────────┐
│   Django    │
│  (Return)   │
└──────┬──────┘
       │ Response
       ▼
┌─────────────┐
│ Flutter App │
│  (Display)  │
└─────────────┘
```

---

## 🎯 Next Steps

1. ✅ Start Colab server (run all 5 cells)
2. ✅ Copy ngrok URL
3. ✅ Update `image_views.py` with URL
4. ✅ Restart Django backend
5. ✅ Test with app
6. ✅ Monitor Colab for usage logs

---

## 💡 Tips

- **Keep Colab Running**: Colab will disconnect after ~90 min of inactivity
- **Production**: For 24/7 usage, deploy to Google Cloud Run or AWS Lambda
- **Free Tier**: ngrok free tier limits connections - upgrade if needed
- **GPU Quota**: Colab free tier has GPU limits - monitor usage
- **Logs**: Check Colab output for request logs and debugging

---

## 📞 Support

If you encounter issues:
1. Check Colab Cell 5 output for errors
2. Verify ngrok URL in browser
3. Check Django logs: `python manage.py runserver`
4. Check Flutter logs in console
5. Test with curl command first

---

**Happy Diagnosing! 🌿🔬**

