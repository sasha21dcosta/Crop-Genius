# 🚀 Quick Start: Image Diagnosis Feature

## ✅ What Was Done

### Backend Changes
1. ✅ Created `backend/disease_detection/image_views.py` - Forwards images to Colab
2. ✅ Updated `backend/disease_detection/urls.py` - Added `/api/disease/diagnose_image/` endpoint
3. ✅ Created `backend/disease_detection/COLAB_IMAGE_SERVER.py` - Complete Colab server code
4. ✅ Created setup guide: `IMAGE_DIAGNOSIS_SETUP.md`

### Frontend Changes
1. ✅ Added image picker import to `diagnosis_chat.dart`
2. ✅ Added `_pickAndDiagnoseImage()` function - Handles image upload & display
3. ✅ Added image icon button (🖼️) next to mic button
4. ✅ Added loading states for image upload
5. ✅ Integrated with existing chat system

### Dependencies
- ✅ `image_picker` - Already in pubspec.yaml (no changes needed)

---

## 🎯 How to Use (3 Steps)

### **1. Start Colab Server**
```python
# In Google Colab, run these cells:

# Cell 1: Mount & Install
from google.colab import drive
drive.mount('/content/drive')
!pip install flask flask-cors pyngrok torch torchvision
!pip install git+https://github.com/openai/CLIP.git

# Cell 2-4: Copy from COLAB_IMAGE_SERVER.py

# Cell 5: Start server
from pyngrok import ngrok
ngrok.set_auth_token("YOUR_NGROK_TOKEN")
public_url = ngrok.connect(5000)
print(f"URL: {public_url}")
app.run(port=5000)
```

### **2. Update Backend URL**

Edit `backend/disease_detection/image_views.py`:
```python
COLAB_IMAGE_API_URL = "https://your-ngrok-url.ngrok-free.app/diagnose"
```

### **3. Test in App**
1. Select a crop
2. Tap the 🖼️ image icon
3. Choose a plant image
4. See results!

---

## 📱 User Experience

### Before Image Upload:
```
[Crop Dropdown: Select Rice]
[🖼️] [🎤] [_____________] [📤]
  ↑
New button!
```

### After Upload:
```
User: [📷 Uploaded image for diagnosis]

AI: 🔍 Image Analysis Result:

    🌿 Disease Detected: Rice Blast
    📊 Confidence: 85.3%
    
    Top Predictions:
      • Rice Blast: 85.3%
      • Brown Spot: 8.2%
      • Healthy: 4.1%
    
    What would you like to know about this disease?

[💊 Treatment] [🛡️ Prevention] [📋 More Info]
```

---

## 🔧 Architecture

```
Flutter App
    ↓ (multipart/form-data)
Django Backend (image_views.py)
    ↓ (forwards image)
Colab Server (Flask + ngrok)
    ↓ (CLIP + Classifier)
Disease Prediction
    ↓ (JSON response)
Back to App
```

---

## 📂 Files Modified/Created

```
CropGenius/
├── backend/
│   └── disease_detection/
│       ├── image_views.py              ← NEW (image forwarding)
│       ├── urls.py                     ← UPDATED (added endpoint)
│       ├── COLAB_IMAGE_SERVER.py       ← NEW (Colab server code)
│       └── IMAGE_DIAGNOSIS_SETUP.md    ← NEW (detailed guide)
│
├── frontend/
│   └── lib/
│       └── diagnosis_chat.dart         ← UPDATED (image upload UI)
│
└── QUICK_START_IMAGE_DIAGNOSIS.md      ← THIS FILE
```

---

## 🧪 Testing Checklist

- [ ] Colab server running (check URL in browser)
- [ ] Backend URL updated in `image_views.py`
- [ ] Django backend running (`python manage.py runserver`)
- [ ] Flutter app running
- [ ] Crop selected in app
- [ ] Image upload works (🖼️ button)
- [ ] Results displayed correctly
- [ ] Action buttons work (Treatment, Prevention)
- [ ] Chat history saves image diagnoses

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Cannot connect to model server" | Check Colab is running, verify ngrok URL |
| "Model server timeout" | Restart Colab Cell 5 |
| "No image file provided" | Check Flutter permissions |
| Image upload stuck | Check Django console for errors |
| Low confidence | Try clearer images, better lighting |

---

## 📊 API Endpoint Details

### Request
```http
POST /api/disease/diagnose_image/
Content-Type: multipart/form-data

image: [binary image data]
crop: "rice"
```

### Response (Success)
```json
{
  "success": true,
  "disease": "rice_blast",
  "class_name": "Rice Blast",
  "confidence": 0.853,
  "message": "Detected Rice Blast with 85.3% confidence",
  "crop": "rice",
  "top_predictions": [
    {"class_name": "Rice Blast", "confidence": 0.853},
    {"class_name": "Brown Spot", "confidence": 0.082},
    {"class_name": "Healthy", "confidence": 0.041}
  ]
}
```

### Response (Error - Server Not Running)
```json
{
  "error": "Cannot connect to model server. Please ensure Colab is running with ngrok."
}
```

---

## 💡 Pro Tips

1. **Keep Colab Alive**: Add code to prevent disconnection:
   ```javascript
   function KeepAlive() {
     console.log("Keeping alive...");
   }
   setInterval(KeepAlive, 60000); // Every minute
   ```

2. **Environment Variable**: Instead of hardcoding URL:
   ```bash
   export COLAB_IMAGE_API_URL="https://abc123.ngrok-free.app/diagnose"
   python manage.py runserver
   ```

3. **Test from Terminal**:
   ```bash
   curl -X POST \
     -F "image=@test_image.jpg" \
     -F "crop=rice" \
     http://localhost:8000/api/disease/diagnose_image/
   ```

4. **Monitor Requests**: Watch Colab output for live logs

5. **Image Quality**: 
   - Max resolution: 1024x1024 (automatically resized)
   - Quality: 85% (adjustable in code)
   - Format: JPEG recommended

---

## 🎓 How It Works

### Image Processing Pipeline:
1. User selects image → Flutter `ImagePicker`
2. Resize to 1024x1024, 85% quality
3. Upload to Django → `diagnose_image()`
4. Django forwards to Colab → `requests.post()`
5. Colab preprocesses → CLIP `preprocess()`
6. Extract features → CLIP `encode_image()`
7. Classify → MLP `forward()`
8. Softmax probabilities → Top 3 predictions
9. Return JSON → Back through chain
10. Display in chat → With action buttons

---

## 🚀 Future Enhancements

- [ ] Camera support (in addition to gallery)
- [ ] Multiple image upload
- [ ] Image preview before sending
- [ ] Save diagnosed images
- [ ] Disease comparison (upload 2 images)
- [ ] Offline model (TFLite/CoreML)

---

## 📞 Need Help?

1. **Check Full Guide**: `backend/disease_detection/IMAGE_DIAGNOSIS_SETUP.md`
2. **Colab Logs**: Cell 5 output shows all requests
3. **Django Logs**: Terminal running `manage.py runserver`
4. **Flutter Logs**: Check console for error messages
5. **Test Endpoint**: `curl` test first before app testing

---

**🎉 You're all set! The image diagnosis feature is ready to use!**

*Remember: Keep your Colab notebook running while using the feature.*

