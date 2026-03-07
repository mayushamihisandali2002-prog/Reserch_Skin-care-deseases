"""
ResNet-18 Image Classification Model
======================================
Fine-tuned ResNet-18 CNN for skin disease prediction from images.

Model path : image_best_finetuned.pt   (full model saved via torch.save)

Input  : PIL Image  OR  raw image bytes
Output : (disease_name, confidence, probabilities_array[5])
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

# ── Disease label mapping ─────────────────────────────────────────────────────
# The image model is trained on 30 classes
TRAINED_CLASSES = 30

DISEASE_LABELS: dict[int, str] = {
    0: "Eczema",
    1: "Dermatitis",
    2: "Psoriasis",
    3: "Acne",
    4: "Urticaria",
    5: "Pigmentation / Dark Spots",
    6: "Ringworm",
    7: "Rosacea",
    8: "Shingles",
    9: "Vitiligo",
    10: "Impetigo",
    11: "Molluscum Contagiosum",
    12: "Folliculitis",
    13: "Scabies",
    14: "Warts",
    15: "Seborrheic Dermatitis",
    16: "Lichen Planus",
    17: "Cellulitis",
    18: "Herpes Simplex",
    19: "Pityriasis Versicolor",
    20: "Melanoma",
    21: "Basal Cell Carcinoma",
    22: "Actinic Keratosis",
    23: "Seborrheic Keratosis",
    24: "Dermatofibroma",
    25: "Cherry Angioma",
    26: "Melanocytic Nevi",
    27: "Hidradenitis Suppurativa",
    28: "Alopecia Areata",
    29: "Melasma",
}
NUM_CLASSES = len(DISEASE_LABELS)

# ImageNet normalization (standard for ResNet fine-tuning)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]
IMAGE_SIZE    = 224


class ResNetImageModel:
    """
    Wraps a fine-tuned ResNet-18 model for skin disease image classification.

    Usage
    -----
    model = ResNetImageModel(Path("image_best_finetuned.pt"))
    disease, conf, probs = model.predict_from_bytes(image_bytes)
    """

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.model = None
        self.transform = None
        self.loaded = False
        self._load()

    # ── Loading ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load the ResNet-18 .pt file (supports full model or state_dict)."""
        try:
            import torch
            import torchvision.transforms as T
            import torchvision.models as models
            from collections import OrderedDict

            if not self.model_path.exists():
                print(f"[ResNet] ❌ File not found: {self.model_path}")
                return

            print(f"[ResNet] Loading {self.model_path.name} …")

            # Load the checkpoint
            checkpoint = torch.load(
                str(self.model_path),
                map_location=torch.device("cpu"),
                weights_only=False,
            )

            # Check if it's a state_dict or a full model
            if isinstance(checkpoint, OrderedDict) or isinstance(checkpoint, dict):
                # It's a state_dict — create ResNet-18 architecture and load weights
                print("[ResNet] Detected state_dict format — building ResNet-18 architecture")
                self.model = models.resnet18(weights=None)
                # Modify final layer for 30 classes (skin diseases) which it was trained on
                self.model.fc = torch.nn.Linear(self.model.fc.in_features, TRAINED_CLASSES)
                
                # Handle potential key prefix issues (e.g., 'module.' from DataParallel)
                state_dict = checkpoint
                if any(k.startswith('module.') for k in state_dict.keys()):
                    state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
                
                self.model.load_state_dict(state_dict)
                print(f"[ResNet] Loaded state_dict with {len(state_dict)} parameters")
            else:
                # It's a full model object
                self.model = checkpoint
                print("[ResNet] Loaded full model object")

            self.model.eval()

            # Standard ResNet preprocessing pipeline
            self.transform = T.Compose([
                T.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                T.ToTensor(),
                T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ])

            self.loaded = True
            print("[ResNet] ✅ Image model ready")

        except ImportError as exc:
            print(f"[ResNet] ❌ torch/torchvision not installed: {exc}")
        except Exception as exc:
            import traceback
            print(f"[ResNet] ❌ Load error: {exc}")
            traceback.print_exc()

    # ── Inference ──────────────────────────────────────────────────────────────

    def predict_from_pil(
        self, pil_image, use_tta: bool = True
    ) -> Tuple[str, float, np.ndarray]:
        """
        Predict skin disease from a PIL Image.
        Includes Test-Time Augmentation (TTA) for increased robustness.
        """
        fallback = ("Unknown", 0.0, np.zeros(NUM_CLASSES))
        if not self.loaded:
            return fallback

        try:
            import torch
            import torch.nn.functional as F
            from PIL import Image

            # Ensure RGB
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Prepare images for TTA (6 views: Original, H-Flip, V-Flip, HV-Flip, Rot90, Rot270)
            images = [pil_image]
            if use_tta:
                images.append(pil_image.transpose(Image.FLIP_LEFT_RIGHT))
                images.append(pil_image.transpose(Image.FLIP_TOP_BOTTOM))
                images.append(pil_image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM))
                images.append(pil_image.transpose(Image.ROTATE_90))
                images.append(pil_image.transpose(Image.ROTATE_270))

            all_logits = []
            for img in images:
                # Preprocess to tensor + add batch dimension
                tensor = self.transform(img).unsqueeze(0)
                with torch.no_grad():
                    raw_output = self.model(tensor)
                
                # Handle different output formats (some models return objects, some tensors)
                if hasattr(raw_output, "logits"):
                    logits = raw_output.logits
                elif isinstance(raw_output, torch.Tensor):
                    logits = raw_output
                else:
                    try:
                        logits = raw_output[0] if hasattr(raw_output, "__getitem__") else raw_output
                    except:
                        logits = raw_output
                
                all_logits.append(logits)

            # Average logits across augmentations (TTA)
            avg_logits = torch.mean(torch.stack(all_logits), dim=0)
            probs: np.ndarray = F.softmax(avg_logits, dim=-1)[0].cpu().numpy()
            
            # Pad the probabilities array so it has NUM_CLASSES elements (i.e., add 0 for Pigmentation)
            if len(probs) == TRAINED_CLASSES and NUM_CLASSES > TRAINED_CLASSES:
                padded_probs = np.zeros(NUM_CLASSES)
                padded_probs[:TRAINED_CLASSES] = probs
                probs = padded_probs

            predicted_class = int(np.argmax(probs))
            confidence = float(probs[predicted_class])
            disease_name = DISEASE_LABELS.get(predicted_class, f"Disease_{predicted_class}")

            return disease_name, confidence, probs

        except Exception as exc:
            print(f"[ResNet] ⚠️ Prediction error: {exc}")
            return ("Unknown", 0.0, np.zeros(NUM_CLASSES))

    def predict_from_bytes(self, image_bytes: bytes) -> Tuple[str, float, np.ndarray]:
        """Predict from raw image bytes (JPEG/PNG)."""
        try:
            from PIL import Image
            pil_image = Image.open(BytesIO(image_bytes))
            return self.predict_from_pil(pil_image)
        except Exception as exc:
            print(f"[ResNet] bytes → PIL error: {exc}")
            return ("Unknown", 0.0, np.zeros(NUM_CLASSES))


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[ResNetImageModel] = None


def get_image_model(model_path: Path) -> ResNetImageModel:
    """Return the singleton ResNet image model (lazy-loaded on first call)."""
    global _instance
    if _instance is None:
        _instance = ResNetImageModel(model_path)
    return _instance
