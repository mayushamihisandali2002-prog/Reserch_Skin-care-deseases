from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from components.multimodal_image_audio_diagnosis.image_model import get_image_model  # noqa: E402


def run_prediction_smoke(image_path: Path | None = None) -> None:
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
        print(f"Model not found at {model_path}")
        return
    if not image_path.exists():
        print(f"Image not found at {image_path}")
        return

    model = get_image_model(model_path)
    with open(image_path, "rb") as handle:
        img_bytes = handle.read()

    disease, confidence, probs = model.predict_from_bytes(img_bytes)
    print("Prediction result:")
    print(f"   Disease   : {disease}")
    print(f"   Confidence: {confidence:.4f}")
    print("   Top-3 classes:")
    for idx in np.argsort(probs)[-3:][::-1]:
        print(f"     {idx}: {probs[idx]:.4f}")


if __name__ == "__main__":
    run_prediction_smoke()
