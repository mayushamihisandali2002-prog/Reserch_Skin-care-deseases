import torch
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(BACKEND_DIR))

from components.multimodal_image_audio_diagnosis.image_model import get_image_model
from PIL import Image
import numpy as np

def test_prediction(
    image_path: Path | None = None,
):
    """Load the fine‑tuned ResNet‑18 model and run a single prediction.
    The default image path points to a sample image from the newly‑downloaded
    research dataset (you can replace it with any local image)."""
    model_path = (
        BACKEND_DIR
        / "assets"
        / "models"
        / "multimodal_image_audio_diagnosis"
        / "image_best_finetuned.pt"
    )
    if image_path is None:
        image_path = (
            BACKEND_DIR
            / "assets"
            / "data"
            / "multimodal_image_audio_diagnosis"
            / "research_dataset"
            / "Eczema"
            / "Eczema_0.jpg"
        )
    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        return
    if not image_path.exists():
        print(f"❌ Image not found at {image_path}")
        return

    # Load singleton model (lazy‑loaded on first call)
    model = get_image_model(model_path)
    # Read image bytes
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    disease, confidence, probs = model.predict_from_bytes(img_bytes)
    print("🔎 Prediction result:")
    print(f"   Disease   : {disease}")
    print(f"   Confidence: {confidence:.4f}")
    # Show top‑3 probabilities
    top3_idx = np.argsort(probs)[-3:][::-1]
    print("   Top‑3 classes:")
    for idx in top3_idx:
        print(f"     {idx}: {probs[idx]:.4f}")

if __name__ == "__main__":
    test_prediction()
