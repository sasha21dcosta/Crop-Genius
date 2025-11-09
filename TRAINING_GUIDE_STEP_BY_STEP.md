# 🎓 Training Your Disease Detection Model - Complete Guide

## 📦 What You Need Before Starting

### Required Files in Google Drive:
```
MyDrive/
└── plantdataset-1.zip    ← Your plant disease dataset (MUST HAVE)
```

### What Will Be Created:
```
MyDrive/
├── plantdataset-1.zip                        ← Your original dataset
├── plantdataset_extracted/                   ← Extracted dataset
│   └── plantdataset/                         ← Actual data folders
│       ├── rice_blast/
│       ├── tomato_blight/
│       └── [other diseases]/
├── clip_features.pt                          ← CLIP features (cache)
├── clip_labels.pt                            ← Labels (cache)
└── mvpdr_highacc_model.pth                   ← 🎯 YOUR TRAINED MODEL
```

---

## 🚀 Training Steps (Run in Google Colab)

### **Step 0: Open Google Colab**
1. Go to https://colab.research.google.com
2. Click "New Notebook"
3. Enable GPU: Runtime → Change runtime type → GPU → Save

---

### **CELL 1: Extract Dataset**

```python
# Mount Drive and Extract Dataset
from google.colab import drive
import zipfile, os

# Mount Drive
drive.mount('/content/drive', force_remount=True)

# Define paths
zip_path = "/content/drive/MyDrive/plantdataset-1.zip"
extract_path = "/content/drive/MyDrive/plantdataset_extracted"

# Check if ZIP exists
if not os.path.exists(zip_path):
    raise FileNotFoundError(f"❌ ZIP not found at {zip_path}. Please upload it to Drive first.")
else:
    print("✅ Found dataset zip:", zip_path)

# Extract
print("📂 Extracting dataset ...")
os.makedirs(extract_path, exist_ok=True)
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

print("✅ Extraction complete!")
print("📁 Contents:", os.listdir(extract_path)[:10])

DATA_ROOT = extract_path + "/plantdataset"  # Adjust if needed
print(f"\n✅ Dataset ready at: {DATA_ROOT}")
```

**Expected Output:**
```
✅ Found dataset zip: /content/drive/MyDrive/plantdataset-1.zip
📂 Extracting dataset ...
✅ Extraction complete!
📁 Contents: ['plantdataset']
✅ Dataset ready at: /content/drive/MyDrive/plantdataset_extracted/plantdataset
```

---

### **CELL 2: Install Dependencies & Setup**

```python
# Install dependencies
!pip install git+https://github.com/openai/CLIP.git -q
!pip install torch torchvision scikit-learn matplotlib -q

print("✅ Dependencies installed!")

# Imports and config
import os, torch, numpy as np
from torch import nn
from torch.utils.data import DataLoader, Dataset
from PIL import Image
from tqdm import tqdm
import clip
from sklearn.model_selection import train_test_split

# Configuration
DATA_ROOT = '/content/drive/MyDrive/plantdataset_extracted/plantdataset'
FEATURES_PATH = '/content/drive/MyDrive/clip_features.pt'
LABELS_PATH = '/content/drive/MyDrive/clip_labels.pt'
MODEL_SAVE_PATH = '/content/drive/MyDrive/mvpdr_highacc_model.pth'

BATCH_SIZE = 16
EPOCHS = 40
LR = 1e-3

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Using device: {device}")
print(f"📂 Dataset: {DATA_ROOT}")
```

---

### **CELL 3: Load CLIP & Prepare Dataset**

```python
# Load CLIP model
model, preprocess = clip.load("ViT-L/14", device=device, jit=False)
print("✅ CLIP ViT-L/14 loaded!")

# Dataset class
class PlantDataset(Dataset):
    def __init__(self, root, transform=None):
        self.samples = []
        root = os.path.expanduser(root)
        self.classes = sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))])
        
        for i, cls in enumerate(self.classes):
            folder = os.path.join(root, cls)
            for f in os.listdir(folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    self.samples.append((os.path.join(folder, f), i))
        
        self.transform = transform
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label

# Load dataset
ds = PlantDataset(DATA_ROOT, transform=preprocess)
print(f"✅ Found {len(ds)} images across {len(ds.classes)} classes")
print(f"📋 Classes: {ds.classes}")
```

**Expected Output:**
```
✅ CLIP ViT-L/14 loaded!
✅ Found 54303 images across 38 classes
📋 Classes: ['apple_scab', 'rice_blast', 'tomato_blight', ...]
```

---

### **CELL 4: Extract CLIP Features** (Takes ~10-20 min)

```python
# Extract features (or load cached)
if not os.path.exists(FEATURES_PATH):
    print("📥 Extracting CLIP features... (this will take 10-20 minutes)")
    feats, labels = [], []
    dl = DataLoader(ds, batch_size=16, shuffle=False)
    
    with torch.no_grad():
        for imgs, lbls in tqdm(dl, desc="Extracting features"):
            imgs = imgs.to(device)
            f = model.encode_image(imgs)
            f = f / f.norm(dim=-1, keepdim=True)
            feats.append(f.cpu())
            labels.append(lbls)
    
    feats = torch.cat(feats)
    labels = torch.cat(labels)
    
    torch.save(feats, FEATURES_PATH)
    torch.save(labels, LABELS_PATH)
    print(f"✅ Features saved to: {FEATURES_PATH}")
else:
    feats = torch.load(FEATURES_PATH)
    labels = torch.load(LABELS_PATH)
    print("✅ Loaded cached features")

print(f"✅ Features shape: {feats.shape}, Labels: {labels.shape}")
```

**Expected Output:**
```
📥 Extracting CLIP features... (this will take 10-20 minutes)
Extracting features: 100%|██████████| 3394/3394 [15:23<00:00, 3.67it/s]
✅ Features saved to: /content/drive/MyDrive/clip_features.pt
✅ Features shape: torch.Size([54303, 768]), Labels: torch.Size([54303])
```

---

### **CELL 5: Train Classifier** (Takes ~30-60 min)

```python
# Train-test split
X_train, X_val, y_train, y_val = train_test_split(
    feats, labels, test_size=0.2, stratify=labels, random_state=42
)
print(f"Train: {X_train.shape}, Val: {X_val.shape}")

feat_dim = X_train.shape[1]
num_classes = len(ds.classes)

# Define classifier
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

model_clf = Classifier(feat_dim, num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model_clf.parameters(), lr=LR, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3)

# DataLoaders
train_dl = DataLoader(list(zip(X_train, y_train)), batch_size=BATCH_SIZE, shuffle=True)
val_dl = DataLoader(list(zip(X_val, y_val)), batch_size=BATCH_SIZE, shuffle=False)

# Training loop
best_val = 0.0
best_epoch = 0
patience = 8

print("🚀 Starting training...")
for epoch in range(1, EPOCHS+1):
    # Train
    model_clf.train()
    total, correct, running_loss = 0, 0, 0.0
    
    for feats_batch, labs in train_dl:
        feats_batch, labs = feats_batch.to(device).float(), labs.to(device)
        logits = model_clf(feats_batch)
        loss = criterion(logits, labs)
        
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model_clf.parameters(), 2.0)
        optimizer.step()
        
        running_loss += loss.item() * feats_batch.size(0)
        preds = logits.argmax(dim=1)
        correct += (preds == labs).sum().item()
        total += feats_batch.size(0)
    
    train_acc = correct / total
    train_loss = running_loss / total
    
    # Validate
    model_clf.eval()
    v_total, v_correct = 0, 0
    with torch.no_grad():
        for feats_batch, labs in val_dl:
            feats_batch, labs = feats_batch.to(device).float(), labs.to(device)
            logits = model_clf(feats_batch)
            preds = logits.argmax(dim=1)
            v_correct += (preds == labs).sum().item()
            v_total += feats_batch.size(0)
    
    val_acc = v_correct / v_total
    scheduler.step(val_acc)
    
    print(f"Epoch {epoch}/{EPOCHS} - Train: {train_acc:.4f} | Val: {val_acc:.4f} | Loss: {train_loss:.4f} | LR: {optimizer.param_groups[0]['lr']:.2e}")
    
    # Save best model
    if val_acc > best_val:
        best_val = val_acc
        best_epoch = epoch
        torch.save({
            'model_state': model_clf.state_dict(),
            'classes': ds.classes
        }, MODEL_SAVE_PATH)
        print(f"  ✅ Saved best model (val_acc={best_val:.4f})")
    
    # Early stopping
    if epoch - best_epoch >= patience:
        print("⏹️ Early stopping triggered.")
        break

print(f"\n🎯 Training complete!")
print(f"🏆 Best validation accuracy: {best_val:.4f}")
print(f"💾 Model saved to: {MODEL_SAVE_PATH}")
```

**Expected Output:**
```
Train: torch.Size([43442, 768]), Val: torch.Size([10861, 768])
🚀 Starting training...
Epoch 1/40 - Train: 0.6234 | Val: 0.6512 | Loss: 1.2345 | LR: 1.00e-03
  ✅ Saved best model (val_acc=0.6512)
Epoch 2/40 - Train: 0.7123 | Val: 0.7234 | Loss: 0.9876 | LR: 1.00e-03
  ✅ Saved best model (val_acc=0.7234)
...
🎯 Training complete!
🏆 Best validation accuracy: 0.7856
💾 Model saved to: /content/drive/MyDrive/mvpdr_highacc_model.pth
```

---

### **CELL 6: Test the Model** (Optional but recommended)

```python
# Test prediction on a single image
import torch.nn.functional as F

# Verify model was saved
checkpoint = torch.load(MODEL_SAVE_PATH, map_location=device)
print(f"✅ Model loaded! Classes: {len(checkpoint['classes'])}")
print(f"📋 Classes: {checkpoint['classes']}")

# Test with a random image from dataset
test_idx = 0
test_img, test_label = ds[test_idx]
test_img_tensor = test_img.unsqueeze(0).to(device)

# Load model for inference
model_clf_test = Classifier(768, len(checkpoint['classes'])).to(device)
model_clf_test.load_state_dict(checkpoint['model_state'])
model_clf_test.eval()

with torch.no_grad():
    feat = model.encode_image(test_img_tensor)
    feat = feat / feat.norm(dim=-1, keepdim=True)
    logits = model_clf_test(feat.float())
    probs = F.softmax(logits, dim=-1)[0]
    pred_idx = probs.argmax().item()

print(f"\n🧪 Test Prediction:")
print(f"  Predicted: {checkpoint['classes'][pred_idx]} ({probs[pred_idx]*100:.2f}%)")
print(f"  Actual: {ds.classes[test_label]}")
print(f"  Match: {'✅' if pred_idx == test_label else '❌'}")
```

---

## ✅ Training Complete Checklist

After running all cells, verify these files exist in Drive:

```bash
✅ /MyDrive/plantdataset-1.zip               (original dataset)
✅ /MyDrive/plantdataset_extracted/          (extracted)
✅ /MyDrive/clip_features.pt                 (cached features)
✅ /MyDrive/clip_labels.pt                   (cached labels)
✅ /MyDrive/mvpdr_highacc_model.pth          (🎯 YOUR MODEL!)
```

**The most important file:** `mvpdr_highacc_model.pth` - This is what you need for image diagnosis!

---

## 🎯 What's Next?

Now that you have the trained model, proceed to **PHASE 3** (see main guide):
- Set up the Colab server to serve predictions
- Get ngrok token
- Run the server code
- Connect your Flutter app

---

## 💡 Tips

- **Save notebook**: File → Save a copy in Drive
- **GPU quota**: Free tier has ~12 hours/day GPU quota
- **Resume training**: If disconnected, just rerun Cell 5 (features are cached!)
- **Improve accuracy**: Try more epochs, data augmentation, or different learning rates

---

## 🐛 Common Training Errors

| Error | Fix |
|-------|-----|
| "ZIP not found" | Upload `plantdataset-1.zip` to Google Drive root |
| "No such file or directory" | Check `DATA_ROOT` path in Cell 1 |
| "CUDA out of memory" | Reduce `BATCH_SIZE` from 16 to 8 |
| "Classes list is empty" | Dataset structure incorrect - check folder organization |
| Low accuracy (<50%) | Need more epochs, better data, or check dataset quality |

---

**Good luck with training! 🚀**

