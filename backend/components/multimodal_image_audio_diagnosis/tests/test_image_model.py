"""Test image model prediction"""
import torch
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image
import numpy as np
from pathlib import Path

# Load
model = models.resnet18(weights=None)
model.fc = torch.nn.Linear(model.fc.in_features, 5)
model_path = (
    Path(__file__).resolve().parents[3]
    / "assets"
    / "models"
    / "multimodal_image_audio_diagnosis"
    / "image_best_finetuned.pt"
)
state_dict = torch.load(str(model_path), map_location='cpu', weights_only=False)
model.load_state_dict(state_dict)
model.eval()

transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Test
img = Image.new('RGB', (224, 224), color=(200, 100, 100))
tensor = transform(img).unsqueeze(0)

DISEASE_LABELS = {0: "Eczema", 1: "Dermatitis", 2: "Psoriasis", 3: "Acne", 4: "Urticaria"}

with torch.no_grad():
    raw_output = model(tensor)

logits = raw_output
print(f"Logits shape: {logits.shape}")

probs = F.softmax(logits, dim=-1)[0].numpy()
print(f"Probs shape: {probs.shape}")
print(f"Probs: {probs}")

pred_class = int(np.argmax(probs))
conf = float(probs[pred_class])
disease = DISEASE_LABELS[pred_class]
print(f"Prediction: {disease} ({conf:.1%})")
