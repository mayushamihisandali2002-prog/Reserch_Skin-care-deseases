"""
SkinAI Inference Pipeline
==========================
Orchestrates the two fine-tuned models:

  ① image_best_finetuned.pt   →  ResNet-18  → image probabilities
  ② best_model/best_model/    →  DistilBERT → text  probabilities

When both modalities are available the probabilities are fused:
    P_final = α · P_image + (1-α) · P_text        (α = FUSION_ALPHA = 0.6)

When only one modality is available, that single model is used directly.
When neither is loaded, the pipeline falls back to a lightweight sklearn model
(if present) and then to heuristic keyword matching.
"""

from __future__ import annotations

import os
import pickle
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from .config import (
    # Real model paths
    DISTILBERT_MODEL_DIR,
    IMAGE_MODEL_PATH,
    # Legacy sklearn paths
    TEXT_MODEL_PATH,
    VECTORIZER_PATH,
    # CSV knowledge-base
    DISEASE_SYMPTOM_CSV,
    TREATMENT_RECORDS_CSV,
    # Built-in treatment KB
    DISEASE_TREATMENTS,
    DISEASE_LABELS,
    # Inference params
    CONFIDENCE_THRESHOLD,
    FUSION_ALPHA,
    TOP_K_TREATMENTS,
    DEBUG,
    get_model_status,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()


# ── Main Pipeline ──────────────────────────────────────────────────────────────

class InferencePipeline:
    """
    Central inference hub for SkinAI.

    Call predict_from_text(message)  → text-only inference (chat endpoint)
    Call predict_from_image(bytes)   → image-only inference
    Call predict_fused(text, bytes)  → full multimodal inference
    Call predict_disease(message)    → public alias (used by app.py chat route)
    """

    def __init__(self) -> None:
        # DistilBERT text model (primary)
        self.distilbert: Any = None
        self.distilbert_loaded = False

        # ResNet-18 image model
        self.image_model: Any = None
        self.image_model_loaded = False

        # Legacy sklearn fallback
        self.sklearn_model: Any = None
        self.sklearn_vectorizer: Any = None
        self.sklearn_loaded = False

        # CSV knowledge-base (optional enrichment)
        self.disease_symptom_df: Optional[pd.DataFrame] = None
        self.treatment_df: Optional[pd.DataFrame] = None
        self.data_loaded = False

        self._load_models()
        self._load_data()

    # ── Loading ────────────────────────────────────────────────────────────────

    def _load_models(self) -> None:
        """Load all three model tiers (DistilBERT → ResNet → sklearn fallback)."""

        # 1) DistilBERT fine-tuned text model
        try:
            from .distilbert_model import get_distilbert_model
            self.distilbert = get_distilbert_model(DISTILBERT_MODEL_DIR)
            self.distilbert_loaded = self.distilbert.loaded
            if self.distilbert_loaded:
                print("[Pipeline] ✅ DistilBERT text model loaded")
            else:
                print("[Pipeline] ⚠️  DistilBERT not loaded — will try legacy")
        except Exception as exc:
            print(f"[Pipeline] DistilBERT import error: {exc}")

        # 2) ResNet-18 image model
        try:
            from .image_model import get_image_model
            self.image_model = get_image_model(IMAGE_MODEL_PATH)
            self.image_model_loaded = self.image_model.loaded
            if self.image_model_loaded:
                print("[Pipeline] ✅ ResNet-18 image model loaded")
            else:
                print("[Pipeline] ⚠️  Image model not loaded")
        except Exception as exc:
            print(f"[Pipeline] Image model import error: {exc}")

        # 3) Legacy sklearn model (fallback if DistilBERT unavailable)
        if not self.distilbert_loaded:
            try:
                if TEXT_MODEL_PATH.exists() and VECTORIZER_PATH.exists():
                    with open(TEXT_MODEL_PATH, "rb") as f:
                        self.sklearn_model = pickle.load(f)
                    with open(VECTORIZER_PATH, "rb") as f:
                        self.sklearn_vectorizer = pickle.load(f)
                    self.sklearn_loaded = True
                    print("[Pipeline] ✅ Legacy sklearn model loaded (fallback)")
            except Exception as exc:
                print(f"[Pipeline] sklearn load error: {exc}")

    def _load_data(self) -> None:
        """Load CSV knowledge-base for treatment enrichment."""
        try:
            if DISEASE_SYMPTOM_CSV.exists():
                self.disease_symptom_df = pd.read_csv(DISEASE_SYMPTOM_CSV)
                if DEBUG:
                    print(f"[Pipeline] Disease-symptom CSV → {len(self.disease_symptom_df)} rows")

            if TREATMENT_RECORDS_CSV.exists():
                self.treatment_df = pd.read_csv(TREATMENT_RECORDS_CSV)
                if DEBUG:
                    print(f"[Pipeline] Treatment CSV → {len(self.treatment_df)} rows")

            if self.disease_symptom_df is not None or self.treatment_df is not None:
                self.data_loaded = True
        except Exception as exc:
            if DEBUG:
                print(f"[Pipeline] CSV load error: {exc}")

    # ── Core Prediction ────────────────────────────────────────────────────────

    def _text_probs(self, text: str) -> Tuple[Optional[str], float, np.ndarray]:
        """
        Run text through DistilBERT (or sklearn fallback).
        Returns (disease_name, confidence, probabilities_array)
        """
        num_cls = len(DISEASE_LABELS)

        # ── DistilBERT (preferred) ──────────────────────────────
        if self.distilbert_loaded and self.distilbert:
            return self.distilbert.predict(text)

        # ── sklearn fallback ────────────────────────────────────
        if self.sklearn_loaded and self.sklearn_model and self.sklearn_vectorizer:
            try:
                X = self.sklearn_vectorizer.transform([text])
                cls = int(self.sklearn_model.predict(X)[0])
                probs_raw = self.sklearn_model.predict_proba(X)[0]
                disease = DISEASE_LABELS.get(cls, f"Disease_{cls}")
                confidence = float(np.max(probs_raw))
                # Pad/trim to num_cls
                probs = np.zeros(num_cls)
                probs[: len(probs_raw)] = probs_raw[: num_cls]
                return disease, confidence, probs
            except Exception as exc:
                if DEBUG:
                    print(f"[Pipeline] sklearn predict error: {exc}")

        return None, 0.0, np.zeros(num_cls)

    def _image_probs(self, image_bytes: bytes) -> Tuple[Optional[str], float, np.ndarray]:
        """
        Run image through ResNet-18.
        Returns (disease_name, confidence, probabilities_array)
        """
        if self.image_model_loaded and self.image_model:
            return self.image_model.predict_from_bytes(image_bytes)
        return None, 0.0, np.zeros(len(DISEASE_LABELS))

    def _fuse(
        self,
        img_probs: np.ndarray,
        txt_probs: np.ndarray,
        img_loaded: bool,
        txt_loaded: bool,
    ) -> np.ndarray:
        """
        Weighted linear fusion of image and text probability vectors.

          P_final = α · P_image + (1-α) · P_text   where α = FUSION_ALPHA

        Falls back to single modality if only one is available.
        """
        if img_loaded and txt_loaded:
            return FUSION_ALPHA * img_probs + (1 - FUSION_ALPHA) * txt_probs
        elif img_loaded:
            return img_probs
        else:
            return txt_probs

    def _get_treatments(self, disease: str) -> List[Dict[str, str]]:
        """
        Retrieve treatment recommendations for a disease.
        Priority: CSV KB → built-in DISEASE_TREATMENTS dict
        """
        # Try CSV first
        if self.treatment_df is not None:
            try:
                mask = (
                    self.treatment_df["primary_disease"]
                    .str.lower()
                    .str.contains(disease.lower(), na=False)
                ) | (
                    self.treatment_df["disease_category"]
                    .str.lower()
                    .str.contains(disease.lower(), na=False)
                )
                matching = self.treatment_df[mask].head(TOP_K_TREATMENTS)
                if len(matching) > 0:
                    treatments = []
                    seen: set = set()
                    for _, row in matching.iterrows():
                        med = str(row.get("recommended_medicine", ""))
                        if med and med not in seen:
                            treatments.append({
                                "medicine": med,
                                "advice": (
                                    f"Severity: {row.get('severity', 'N/A')}. "
                                    f"Follow-up required: {row.get('follow_up_required', 'N/A')}"
                                ),
                            })
                            seen.add(med)
                    if treatments:
                        return treatments
            except Exception as exc:
                if DEBUG:
                    print(f"[Pipeline] CSV treatment lookup error: {exc}")

        # Built-in knowledge base
        return DISEASE_TREATMENTS.get(disease, [])

    # ── Public API ─────────────────────────────────────────────────────────────

    def predict_from_text(self, text: str) -> Dict[str, Any]:
        """
        Text-only disease prediction (used by /api/chat).

        Returns
        -------
        {
            "disease"            : str,
            "confidence"         : float,
            "treatments"         : list[{medicine, advice}],
            "followup_questions" : list[str],
            "model_used"         : "distilbert" | "sklearn" | "unavailable",
        }
        """
        disease, confidence, _ = self._text_probs(text)

        model_used = (
            "distilbert" if self.distilbert_loaded
            else "sklearn" if self.sklearn_loaded
            else "unavailable"
        )

        treatments = self._get_treatments(disease) if disease else []

        followup: List[str] = []
        if len(text.split()) < 5 or confidence < 0.50:
            followup = [
                "Where on your body is the skin condition?",
                "How long have you had these symptoms?",
                "Is it itchy, painful, or burning?",
            ]

        return {
            "disease":            disease or "Unable to determine",
            "confidence":         float(confidence),
            "treatments":         treatments,
            "followup_questions": followup,
            "model_used":         model_used,
        }

    # Alias kept for compatibility with existing app.py routes
    def predict_disease(self, text: str) -> Dict[str, Any]:
        return self.predict_from_text(text)

    def predict_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Image-only disease prediction (used by /api/analyze endpoint).

        Returns
        -------
        {
            "disease"    : str,
            "confidence" : float,
            "treatments" : list[{medicine, advice}],
            "model_used" : "resnet" | "unavailable",
        }
        """
        disease, confidence, _ = self._image_probs(image_bytes)

        return {
            "disease":    disease or "Unable to determine",
            "confidence": float(confidence),
            "treatments": self._get_treatments(disease) if disease else [],
            "model_used": "resnet" if self.image_model_loaded else "unavailable",
        }

    def predict_fused(self, text: str, image_bytes: bytes) -> Dict[str, Any]:
        """
        Full multimodal prediction: ResNet-18 image + DistilBERT text → fusion.

        Fusion formula:
            P_final = 0.6 · P_image + 0.4 · P_text

        Returns
        -------
        {
            "disease"            : str,
            "confidence"         : float,
            "image_disease"      : str,
            "image_confidence"   : float,
            "text_disease"       : str,
            "text_confidence"    : float,
            "treatments"         : list,
            "model_used"         : "fusion" | "image_only" | "text_only",
        }
        """
        img_name, img_conf, img_probs = self._image_probs(image_bytes)
        txt_name, txt_conf, txt_probs = self._text_probs(text)

        have_img = self.image_model_loaded and img_conf > 0
        have_txt = (self.distilbert_loaded or self.sklearn_loaded) and txt_conf > 0

        fused = self._fuse(img_probs, txt_probs, have_img, have_txt)
        final_class = int(np.argmax(fused))
        final_conf = float(fused[final_class])
        final_disease = DISEASE_LABELS.get(final_class, "Unknown")

        model_used = (
            "fusion"     if (have_img and have_txt) else
            "image_only" if have_img else
            "text_only"
        )

        return {
            "disease":          final_disease,
            "confidence":       final_conf,
            "image_disease":    img_name,
            "image_confidence": img_conf,
            "text_disease":     txt_name,
            "text_confidence":  txt_conf,
            "treatments":       self._get_treatments(final_disease),
            "model_used":       model_used,
        }

    def get_treatments_for_disease(self, disease: str) -> List[str]:
        """
        Return a flat list of medicine names for a given disease.
        Used by the ask_treatment intent in app.py.
        """
        raw = self._get_treatments(disease)
        return [t.get("medicine", "Unknown") for t in raw]


# ── Singleton ─────────────────────────────────────────────────────────────────

def get_inference_pipeline() -> InferencePipeline:
    """Return the global singleton InferencePipeline (lazy-loaded)."""
    if not hasattr(get_inference_pipeline, "_instance"):
        get_inference_pipeline._instance = InferencePipeline()
    return get_inference_pipeline._instance
