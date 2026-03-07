"""
Feature-engineered face skin severity inference.

Pipeline:
  1) Read image (RGB)
  2) Resize + center crop
  3) Contrast normalization (CLAHE when OpenCV is available)
  4) Extract engineered features
  5) Min-max normalize using metadata.json
  6) Predict severity class with RandomForest model
  7) Compute weighted severity score (0-100)
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
from PIL import Image, ImageFilter, ImageOps

try:  # pragma: no cover - optional dependency
    import cv2

    CV2_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    cv2 = None
    CV2_AVAILABLE = False


TARGET_SIZE = 224
RESIZE_SHORT_SIDE = 256


def _clamp01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


class SeverityModel:
    """
    RandomForest-based severity classifier backed by engineered image features.
    """

    def __init__(self, model_path: Path, metadata_path: Path) -> None:
        self.model_path = model_path
        self.metadata_path = metadata_path

        self.model = None
        self.loaded = False
        self.load_error: Optional[str] = None

        self.feature_cols: list[str] = []
        self.mins: dict[str, float] = {}
        self.maxs: dict[str, float] = {}
        self.weights: dict[str, float] = {}
        self.threshold_q1: float = 40.0
        self.threshold_q2: float = 60.0
        self.severity_levels: list[str] = ["mild", "moderate", "severe"]

        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            self.load_error = f"Severity model file not found: {self.model_path}"
            return
        if not self.metadata_path.exists():
            self.load_error = f"Severity metadata file not found: {self.metadata_path}"
            return

        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception as exc:
            self.load_error = f"Failed to parse severity metadata JSON: {exc}"
            return

        try:
            self.feature_cols = [str(col) for col in meta.get("feature_cols", [])]
            self.mins = {str(k): float(v) for k, v in (meta.get("mins", {}) or {}).items()}
            self.maxs = {str(k): float(v) for k, v in (meta.get("maxs", {}) or {}).items()}
            self.weights = {
                str(k): float(v) for k, v in (meta.get("weights", {}) or {}).items()
            }

            thresholds = meta.get("severity_thresholds", {}) or {}
            self.threshold_q1 = float(thresholds.get("q1", self.threshold_q1))
            self.threshold_q2 = float(thresholds.get("q2", self.threshold_q2))
            levels = meta.get("severity_levels", []) or self.severity_levels
            self.severity_levels = [str(level).strip().lower() for level in levels]
            self.disease_weights = meta.get("disease_weights", {})

            if not self.feature_cols:
                raise ValueError("feature_cols is missing or empty in metadata.json")
        except Exception as exc:
            self.load_error = f"Invalid severity metadata format: {exc}"
            return

        try:
            self.model = joblib.load(self.model_path)
        except Exception as exc:
            self.load_error = f"Failed to load severity model: {exc}"
            return

        self.loaded = True

    def _resize_keep_aspect(self, image: Image.Image, short_side: int) -> Image.Image:
        width, height = image.size
        if width <= 0 or height <= 0:
            raise ValueError("Invalid image dimensions")

        if width <= height:
            new_width = short_side
            new_height = int(round(height * (short_side / width)))
        else:
            new_height = short_side
            new_width = int(round(width * (short_side / height)))

        return image.resize((new_width, new_height), Image.Resampling.BILINEAR)

    @staticmethod
    def _center_crop(image: Image.Image, target_size: int) -> Image.Image:
        width, height = image.size
        left = max(0, (width - target_size) // 2)
        top = max(0, (height - target_size) // 2)
        right = left + target_size
        bottom = top + target_size
        return image.crop((left, top, right, bottom))

    def _apply_clahe_or_fallback(self, image_rgb: np.ndarray) -> tuple[np.ndarray, str]:
        if CV2_AVAILABLE:
            try:
                image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab)

                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l_channel = clahe.apply(l_channel)

                lab_clahe = cv2.merge((l_channel, a_channel, b_channel))
                bgr_clahe = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
                rgb_clahe = cv2.cvtColor(bgr_clahe, cv2.COLOR_BGR2RGB)
                return rgb_clahe, "opencv_clahe"
            except Exception:
                pass

        # Fallback when OpenCV is unavailable.
        equalized = ImageOps.equalize(Image.fromarray(image_rgb))
        return np.array(equalized), "equalize_fallback"

    def _detect_face_count(self, image_rgb: np.ndarray) -> Optional[int]:
        if not CV2_AVAILABLE:
            return None

        try:
            cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
            if not cascade_path.exists():
                return None

            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            detector = cv2.CascadeClassifier(str(cascade_path))
            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(45, 45),
            )
            return int(len(faces))
        except Exception:
            return None

    @staticmethod
    def _hist_entropy(gray_u8: np.ndarray, bins: int = 64) -> float:
        hist, _ = np.histogram(gray_u8, bins=bins, range=(0, 256), density=True)
        hist = hist[hist > 0]
        if hist.size == 0:
            return 0.0
        entropy = float(-np.sum(hist * np.log2(hist)))
        return max(0.0, entropy)

    def _extract_features(self, image_rgb: np.ndarray) -> dict[str, float]:
        rgb_float = image_rgb.astype(np.float32) / 255.0
        red = rgb_float[:, :, 0]
        green = rgb_float[:, :, 1]
        blue = rgb_float[:, :, 2]

        # Redness proxy: ratio of red channel to total RGB intensity.
        redness_index = float(np.mean(red / (red + green + blue + 1e-6)))

        # Saturation mean in HSV color space.
        if CV2_AVAILABLE:
            hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
            saturation_mean = float(np.mean(hsv[:, :, 1]) / 255.0)
        else:
            hsv = np.array(Image.fromarray(image_rgb).convert("HSV"))
            saturation_mean = float(np.mean(hsv[:, :, 1]) / 255.0)

        # Grayscale map for texture and edge features.
        gray_float = 0.299 * red + 0.587 * green + 0.114 * blue
        gray_u8 = np.clip(gray_float * 255.0, 0, 255).astype(np.uint8)

        # Edge density from Canny (or gradient fallback).
        if CV2_AVAILABLE:
            edges = cv2.Canny(gray_u8, threshold1=80, threshold2=160)
            edge_density = float(np.mean(edges > 0))
        else:
            gx, gy = np.gradient(gray_float)
            grad_mag = np.sqrt(gx * gx + gy * gy)
            threshold = float(np.percentile(grad_mag, 75))
            edge_density = float(np.mean(grad_mag > threshold))

        texture_entropy = self._hist_entropy(gray_u8, bins=64)

        # Spotness proxy: local dark spot contrast vs blurred background.
        if CV2_AVAILABLE:
            blurred = cv2.GaussianBlur(gray_u8, (0, 0), sigmaX=2.0, sigmaY=2.0)
            local_contrast = np.clip(blurred.astype(np.float32) - gray_u8.astype(np.float32), 0, None)
        else:
            blurred_img = Image.fromarray(gray_u8).filter(ImageFilter.GaussianBlur(radius=2.0))
            blurred = np.array(blurred_img, dtype=np.float32)
            local_contrast = np.clip(blurred - gray_u8.astype(np.float32), 0, None)

        if local_contrast.size == 0:
            spotness = 0.0
        else:
            high_contrast = np.percentile(local_contrast, 95)
            spotness = float(high_contrast)

        return {
            "redness_index": redness_index,
            "saturation_mean": saturation_mean,
            "edge_density": edge_density,
            "texture_entropy": texture_entropy,
            "spotness": spotness,
        }

    def _normalize_features(self, raw_features: dict[str, float]) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for col in self.feature_cols:
            value = float(raw_features.get(col, 0.0))
            min_val = float(self.mins.get(col, 0.0))
            max_val = float(self.maxs.get(col, 1.0))
            denom = max_val - min_val
            if denom <= 1e-12:
                normalized[col] = 0.0
            else:
                normalized[col] = _clamp01((value - min_val) / denom)
        return normalized

    def _compute_weighted_score(self, normalized_features: dict[str, float], disease_name: Optional[str] = None) -> tuple[float, str]:
        weight_sum = 0.0
        weighted_value = 0.0

        # Use disease-specific weights if available
        current_weights = self.weights
        if disease_name and disease_name in self.disease_weights:
            current_weights = self.disease_weights[disease_name]
            # print(f"[Severity] Using specialized weights for {disease_name}")

        for col in self.feature_cols:
            w = float(current_weights.get(col, 0.0))
            v = float(normalized_features.get(col, 0.0))
            weighted_value += w * v
            # If disease weights are relative (don't sum to 1), weight_sum handles it
            weight_sum += abs(w)

        if weight_sum <= 1e-12:
            if not self.feature_cols:
                score = 0.0
            else:
                score = float(np.mean([normalized_features.get(c, 0.0) for c in self.feature_cols])) * 100.0
        else:
            score = float((weighted_value / weight_sum) * 100.0)

        if score < self.threshold_q1:
            level = "mild"
        elif score < self.threshold_q2:
            level = "moderate"
        else:
            level = "severe"
        return score, level

    def _normalize_level(self, value: Any) -> str:
        if value is None:
            return "moderate"

        raw = str(value).strip().lower()
        if raw in self.severity_levels:
            return raw

        if raw.isdigit():
            idx = int(raw)
            if 0 <= idx < len(self.severity_levels):
                return self.severity_levels[idx]

        alias = {
            "low": "mild",
            "mid": "moderate",
            "medium": "moderate",
            "high": "severe",
        }
        return alias.get(raw, "moderate")

    @staticmethod
    def _display_level(level: str) -> str:
        return str(level).strip().replace("_", " ").title()

    def predict_from_pil(self, image: Image.Image, use_tta: bool = True, disease_name: Optional[str] = None) -> dict[str, Any]:
        if not self.loaded or self.model is None:
            raise RuntimeError(self.load_error or "Severity model not loaded")

        if image.mode != "RGB":
            image = image.convert("RGB")

        original_w, original_h = image.size
        
        # Prepare views for TTA (4 views: Original, H-Flip, V-Flip, HV-Flip)
        views = [image]
        if use_tta:
            views.append(image.transpose(Image.FLIP_LEFT_RIGHT))
            views.append(image.transpose(Image.FLIP_TOP_BOTTOM))
            views.append(image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM))

        all_raw_features = []
        all_normalized_features = []
        
        # Meta for last view (just for reporting)
        normalization_method = "unknown"
        face_count = None

        for view in views:
            resized = self._resize_keep_aspect(view, RESIZE_SHORT_SIDE)
            cropped = self._center_crop(resized, TARGET_SIZE)
            view_rgb = np.array(cropped, dtype=np.uint8)
            view_rgb, normalization_method = self._apply_clahe_or_fallback(view_rgb)
            
            # Extract features for this view
            view_face_count = self._detect_face_count(view_rgb)
            if face_count is None: face_count = view_face_count # Capture first view's face count
            
            view_raw = self._extract_features(view_rgb)
            view_norm = self._normalize_features(view_raw)
            
            all_raw_features.append(view_raw)
            all_normalized_features.append(view_norm)

        # Average features across views
        avg_raw = {}
        avg_norm = {}
        for col in self.feature_cols:
            avg_raw[col] = float(np.mean([f.get(col, 0.0) for f in all_raw_features]))
            avg_norm[col] = float(np.mean([f.get(col, 0.0) for f in all_normalized_features]))

        vector = np.array(
            [[avg_norm[col] for col in self.feature_cols]],
            dtype=np.float32,
        )

        model_pred_raw = self.model.predict(vector)[0]
        model_level = self._normalize_level(model_pred_raw)

        confidence = 0.0
        probabilities: dict[str, float] = {}
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(vector)[0]
            classes = getattr(self.model, "classes_", [])
            for idx, cls in enumerate(classes):
                cls_level = self._normalize_level(cls)
                probabilities[self._display_level(cls_level)] = float(probs[idx])
            confidence = float(np.max(probs))

        score, score_level = self._compute_weighted_score(avg_norm, disease_name=disease_name)

        return {
            "severity_level": self._display_level(model_level),
            "severity_score": round(float(score), 2),
            "confidence": confidence,
            "probabilities": probabilities,
            "model_prediction": self._display_level(model_level),
            "score_based_level": self._display_level(score_level),
            "feature_vector": avg_raw,
            "normalized_features": avg_norm,
            "thresholds": {
                "q1": float(self.threshold_q1),
                "q2": float(self.threshold_q2),
            },
            "preprocessing": {
                "input_size": {"width": int(original_w), "height": int(original_h)},
                "target_size": {"width": TARGET_SIZE, "height": TARGET_SIZE},
                "normalization": normalization_method,
                "face_count": face_count,
                "face_visible": None if face_count is None else (face_count > 0),
                "tta_views": len(views)
            },
        }

    def predict_from_bytes(self, image_bytes: bytes, disease_name: Optional[str] = None) -> dict[str, Any]:
        with Image.open(BytesIO(image_bytes)) as image:
            return self.predict_from_pil(image, disease_name=disease_name)


_instance: Optional[SeverityModel] = None


def get_severity_model(
    model_path: Path,
    metadata_path: Path,
    force_reload: bool = False,
) -> SeverityModel:
    """
    Return singleton severity model instance.
    """
    global _instance
    if force_reload or _instance is None:
        _instance = SeverityModel(model_path=model_path, metadata_path=metadata_path)
    return _instance
