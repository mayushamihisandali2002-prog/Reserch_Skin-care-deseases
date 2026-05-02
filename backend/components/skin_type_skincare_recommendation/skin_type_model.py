"""
ConvNeXt skin-type inference model.

Loads:
  - skin_type_convnext_cleaned_best.pt
  - label_map_skin_type.json

The checkpoint format is expected to contain:
  {
    "model_name": "convnext_tiny",
    "model_state": <state_dict>,
    "label_map": {...}
  }
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import numpy as np


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
IMAGE_SIZE = 224


class SkinTypeModel:
    """
    Wrapper for ConvNeXt skin-type classification.
    """

    def __init__(self, model_path: Path, label_map_path: Path) -> None:
        self.model_path = model_path
        self.label_map_path = label_map_path
        self.model = None
        self.transform = None
        self.model_name = "convnext_tiny"
        self.label_map: dict[str, int] = {}
        self.id_to_label: dict[int, str] = {}
        self.loaded = False
        self.load_error: Optional[str] = None
        self._load()

    def _load(self) -> None:
        # 1. Try loading Random Forest first (it's much lighter and we just trained it)
        rf_path = self.model_path.parent / "skin_type_rf.joblib"
        if rf_path.exists():
            try:
                import joblib
                from components.severity_assessment_tracking.severity_model import SeverityModel
                self.rf_model = joblib.load(rf_path)
                # Use SeverityModel's logic for extraction
                sev_meta = self.model_path.parents[2] / "severity_assessment_tracking" / "severity" / "metadata.json"
                sev_model_dummy = self.model_path.parents[2] / "severity_assessment_tracking" / "severity" / "severity_model.joblib"
                self.rf_extractor = SeverityModel(sev_model_dummy, sev_meta)
                self.model_name = "random_forest_feature_based"
                self.loaded = True
                print(f"[SkinTypeModel] Loaded RF model from {rf_path}")
                return
            except Exception as exc:
                print(f"[SkinTypeModel] RF Load failed: {exc}")

        # 2. Fallback to ConvNext (Original Logic)
        try:
            import torch
            import torchvision.transforms as T
        except Exception as exc:
            self.load_error = f"torch/torchvision not available: {exc}"
            return

        timm_module = self._import_or_install_timm()
        if timm_module is None:
            return

        if not self.model_path.exists():
            self.load_error = f"Model file not found: {self.model_path}"
            return

        if not self.label_map_path.exists():
            self.load_error = f"Label map file not found: {self.label_map_path}"
            return

        try:
            with open(self.label_map_path, "r", encoding="utf-8") as f:
                label_map_raw = json.load(f)
            self.label_map = self._normalize_label_map(label_map_raw)
            self.id_to_label = {idx: label for label, idx in self.label_map.items()}
            
            checkpoint = torch.load(
                str(self.model_path),
                map_location=torch.device("cpu"),
                weights_only=False,
            )

            state_dict = self._extract_state_dict(checkpoint)
            self.model_name = str(checkpoint.get("model_name", self.model_name))
            num_classes = len(self.id_to_label)

            model = timm_module.create_model(
                self.model_name,
                pretrained=False,
                num_classes=num_classes,
            )
            model.load_state_dict(state_dict, strict=True)
            model.eval()

            self.model = model
            self.transform = T.Compose(
                [
                    T.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                    T.ToTensor(),
                    T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
                ]
            )
            self.loaded = True
        except Exception as exc:
            self.load_error = f"Failed to load skin-type checkpoint: {exc}"
            self.loaded = False

    def _import_or_install_timm(self):
        """
        Import timm, or attempt runtime installation in the current interpreter.
        """
        try:
            return importlib.import_module("timm")
        except Exception as first_exc:
            install_cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "timm",
            ]
            try:
                proc = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    timeout=240,
                    check=False,
                )
            except Exception as install_exc:
                self.load_error = (
                    "timm not available and auto-install failed "
                    f"(interpreter={sys.executable}): {install_exc}"
                )
                return None

            if proc.returncode != 0:
                stderr = (proc.stderr or "").strip().splitlines()
                stderr_tail = stderr[-1] if stderr else "unknown pip error"
                self.load_error = (
                    "timm not available and pip install failed "
                    f"(interpreter={sys.executable}): {stderr_tail}"
                )
                return None

            try:
                return importlib.import_module("timm")
            except Exception as second_exc:
                self.load_error = (
                    "timm install completed but import still failed "
                    f"(interpreter={sys.executable}): {second_exc}; "
                    f"initial error: {first_exc}"
                )
                return None

    @staticmethod
    def _normalize_label_map(raw_map: dict[Any, Any]) -> dict[str, int]:
        """
        Accept either:
          - {"oily": 0, "dry": 1, ...}
          - {"0": "oily", "1": "dry", ...}
        and normalize to label->id.
        """
        if not isinstance(raw_map, dict):
            raise ValueError("label map must be a JSON object")

        normalized: dict[str, int] = {}
        for key, value in raw_map.items():
            if isinstance(value, int):
                normalized[str(key).strip().lower()] = int(value)
                continue

            key_int = int(key) if str(key).strip().isdigit() else None
            if key_int is not None and isinstance(value, str):
                normalized[str(value).strip().lower()] = key_int
                continue

            raise ValueError(f"Unsupported label map entry: {key} -> {value}")

        if not normalized:
            raise ValueError("label map is empty")

        return normalized

    @staticmethod
    def _extract_state_dict(checkpoint: Any) -> dict[str, Any]:
        """
        Extract a torch state_dict from common checkpoint formats.
        """
        if isinstance(checkpoint, dict):
            if "model_state" in checkpoint and isinstance(checkpoint["model_state"], dict):
                state_dict = checkpoint["model_state"]
            elif "state_dict" in checkpoint and isinstance(checkpoint["state_dict"], dict):
                state_dict = checkpoint["state_dict"]
            elif all(isinstance(k, str) for k in checkpoint.keys()):
                state_dict = checkpoint
            else:
                raise ValueError("Unsupported checkpoint dictionary format")
        else:
            raise ValueError("Unsupported checkpoint format (expected dict)")

        if any(k.startswith("module.") for k in state_dict.keys()):
            state_dict = {k.replace("module.", "", 1): v for k, v in state_dict.items()}
        return state_dict

    def _predict_proba(self, pil_image, use_tta: bool = True) -> np.ndarray:
        if not self.loaded or self.model is None or self.transform is None:
            raise RuntimeError(self.load_error or "Skin-type model not loaded")

        import torch
        from PIL import Image

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Prepare images for TTA (6 views)
        images = [pil_image]
        if use_tta:
            images.append(pil_image.transpose(Image.FLIP_LEFT_RIGHT))
            images.append(pil_image.transpose(Image.FLIP_TOP_BOTTOM))
            images.append(pil_image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM))
            images.append(pil_image.transpose(Image.ROTATE_90))
            images.append(pil_image.transpose(Image.ROTATE_270))

        all_logits = []
        for img in images:
            tensor = self.transform(img).unsqueeze(0)
            with torch.no_grad():
                logits = self.model(tensor)
                all_logits.append(logits)

        # Average logits across augmentations (TTA)
        avg_logits = torch.mean(torch.stack(all_logits), dim=0)
        probs = torch.softmax(avg_logits, dim=-1)[0].cpu().numpy()
        return probs

    def predict_from_pil(self, pil_image) -> dict[str, Any]:
        if hasattr(self, "rf_model") and self.rf_model:
            import numpy as np
            # RF prediction
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            
            # Extract features using the cached extractor
            resized = self.rf_extractor._resize_keep_aspect(pil_image, 256)
            cropped = self.rf_extractor._center_crop(resized, 224)
            rgb_na = np.array(cropped, dtype=np.uint8)
            rgb_na, _ = self.rf_extractor._apply_clahe_or_fallback(rgb_na)
            
            raw_features = self.rf_extractor._extract_features(rgb_na)
            norm_features = self.rf_extractor._normalize_features(raw_features)
            
            vector = np.array(
                [[norm_features[col] for col in self.rf_extractor.feature_cols]],
                dtype=np.float32,
            )
            
            pred_label = self.rf_model.predict(vector)[0]
            probs_array = self.rf_model.predict_proba(vector)[0]
            classes = self.rf_model.classes_
            probabilities = {
                self._display_label(str(cls)): float(probs_array[i])
                for i, cls in enumerate(classes)
            }
            
            conf = float(np.max(probs_array))
            
            return {
                "skin_type_raw": pred_label,
                "skin_type": self._display_label(pred_label),
                "class_id": 0, # Not strictly mapped for RF
                "confidence": conf,
                "probabilities": probabilities,
                "model_name": "random_forest_feature_based",
            }

        # Fallback to deep model
        probs = self._predict_proba(pil_image)
        pred_id = int(np.argmax(probs))
        pred_label = self.id_to_label.get(pred_id, f"class_{pred_id}")

        probabilities = {
            self._display_label(self.id_to_label.get(i, f"class_{i}")): float(probs[i])
            for i in range(len(probs))
        }

        return {
            "skin_type_raw": pred_label,
            "skin_type": self._display_label(pred_label),
            "class_id": pred_id,
            "confidence": float(probs[pred_id]),
            "probabilities": probabilities,
            "model_name": self.model_name,
        }

    def predict_from_bytes(self, image_bytes: bytes) -> dict[str, Any]:
        from PIL import Image

        with Image.open(BytesIO(image_bytes)) as img:
            return self.predict_from_pil(img)

    @staticmethod
    def _display_label(raw_label: str) -> str:
        return raw_label.strip().replace("_", " ").title()


_instance: Optional[SkinTypeModel] = None


def get_skin_type_model(
    model_path: Path,
    label_map_path: Path,
    force_reload: bool = False,
) -> SkinTypeModel:
    """
    Return singleton skin-type model instance.
    """
    global _instance
    if force_reload or _instance is None:
        _instance = SkinTypeModel(model_path=model_path, label_map_path=label_map_path)
    return _instance
