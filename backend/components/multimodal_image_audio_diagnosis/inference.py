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

from inference.config import (
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
    DISEASE_EXPLANATIONS,
    EXPECTED_SYMPTOMS,
    # Inference params
    CONFIDENCE_THRESHOLD,
    FUSION_ALPHA,
    TOP_K_TREATMENTS,
    DEBUG,
    get_model_status,
    # Specialized models
    SEVERITY_MODEL_PATH,
    SEVERITY_METADATA_PATH,
    SKIN_TYPE_MODEL_PATH,
    SKIN_TYPE_LABEL_MAP_PATH,
    RESEARCH_DATASET_DIR,
)
from components.conversational_diagnosis_assistant.knowledge_base import (
    SYMPTOM_KEYWORDS,
    SYMPTOM_MAP,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()


# ── Main Pipeline ──────────────────────────────────────────────────────────────

class InferencePipeline:
    def _get_disease_explanation(self, disease: str) -> str:
        """Retrieve disease explanation from config."""
        return DISEASE_EXPLANATIONS.get(disease, "No explanation available for this disease.")
    """
    Central inference hub for SkinAI.

    Call predict_from_text(message)  → text-only inference (chat endpoint)
    Call predict_from_image(bytes)   → image-only inference
    Call predict_fused(text, bytes)  → full multimodal inference
    Call predict_disease(message)    → public alias (used by app.py chat route)
    """

    def __init__(self):
        # DistilBERT text model (primary)
        self.distilbert = None
        self.distilbert_loaded = False

        # ResNet-18 image model
        self.image_model = None
        self.image_model_loaded = False

        # Legacy sklearn fallback
        self.sklearn_model = None
        self.sklearn_vectorizer = None
        self.sklearn_loaded = False

        # CSV knowledge-base (optional enrichment)
        self.disease_symptom_df = None
        self.treatment_df = None
        self.data_loaded = False

        # Specialized models (Lazy loaded)
        self.severity_model = None
        self.skin_type_model = None

        self._load_models()
        self._load_data()
        self._load_specialized_models()

    # ── Loading ────────────────────────────────────────────────────────────────

    def _load_models(self) -> None:
        """Load all three model tiers (DistilBERT -> ResNet -> sklearn fallback)."""

        # 1) DistilBERT fine-tuned text model
        try:
            from components.conversational_diagnosis_assistant.distilbert_model import (
                get_distilbert_model,
            )
            self.distilbert = get_distilbert_model(DISTILBERT_MODEL_DIR)
            self.distilbert_loaded = self.distilbert.loaded
            if self.distilbert_loaded:
                print("[Pipeline] DistilBERT text model loaded")
            else:
                print("[Pipeline] DistilBERT not loaded - will try legacy")
        except Exception as exc:
            print(f"[Pipeline] DistilBERT import error: {exc}")

        # 2) ResNet-18 image model
        try:
            from components.multimodal_image_audio_diagnosis.image_model import (
                get_image_model,
            )
            self.image_model = get_image_model(
                IMAGE_MODEL_PATH,
                dataset_dir=RESEARCH_DATASET_DIR,
            )
            self.image_model_loaded = self.image_model.loaded
            if self.image_model_loaded:
                print("[Pipeline] ResNet-18 image model loaded")
            else:
                print("[Pipeline] Image model not loaded")
        except Exception as exc:
            print(f"[Pipeline] Image model import error: {exc}")

        # 3) Legacy sklearn model
        self._load_legacy_text_model()

    def _load_legacy_text_model(self) -> None:
        """
        Load the legacy 30-class sklearn text model. This remains useful because
        the current DistilBERT artifact only exposes 20 disease labels.
        """
        try:
            if not (TEXT_MODEL_PATH.exists() and VECTORIZER_PATH.exists()):
                return

            with open(TEXT_MODEL_PATH, "rb") as f:
                self.sklearn_model = pickle.load(f)
            with open(VECTORIZER_PATH, "rb") as f:
                self.sklearn_vectorizer = pickle.load(f)

            self._repair_sklearn_compatibility()
            self.sklearn_loaded = True

            mode = "supporting ensemble" if self.distilbert_loaded else "fallback"
            print(f"[Pipeline] Legacy sklearn text model loaded ({mode})")
        except Exception as exc:
            print(f"[Pipeline] sklearn load error: {exc}")

    def _repair_sklearn_compatibility(self) -> None:
        """Repair compatibility fields expected by the installed sklearn runtime."""
        if not self.sklearn_model or not self.sklearn_vectorizer:
            return

        classes = list(getattr(self.sklearn_model, "classes_", []))
        if not hasattr(self.sklearn_model, "multi_class"):
            self.sklearn_model.multi_class = "multinomial" if len(classes) > 2 else "ovr"

        if not hasattr(self.sklearn_model, "n_features_in_"):
            vocabulary = getattr(self.sklearn_vectorizer, "vocabulary_", {})
            if vocabulary:
                self.sklearn_model.n_features_in_ = len(vocabulary)

    def _sklearn_text_probs(self, text: str) -> Tuple[Optional[str], float, np.ndarray]:
        num_cls = len(DISEASE_LABELS)
        fallback = (None, 0.0, np.zeros(num_cls, dtype=np.float32))
        if not self.sklearn_loaded or not self.sklearn_model or not self.sklearn_vectorizer:
            return fallback

        try:
            self._repair_sklearn_compatibility()
            X = self.sklearn_vectorizer.transform([text])
            probs_raw = self.sklearn_model.predict_proba(X)[0]

            probs = np.zeros(num_cls, dtype=np.float32)
            for idx, cls in enumerate(getattr(self.sklearn_model, "classes_", [])):
                class_index = int(cls)
                if 0 <= class_index < num_cls:
                    probs[class_index] = float(probs_raw[idx])

            if not np.any(probs):
                probs[: len(probs_raw)] = probs_raw[:num_cls]

            predicted_class = int(np.argmax(probs))
            return (
                DISEASE_LABELS.get(predicted_class, f"Disease_{predicted_class}"),
                float(probs[predicted_class]),
                probs,
            )
        except Exception as exc:
            if DEBUG:
                print(f"[Pipeline] sklearn predict error: {exc}")
            return fallback

    def _blend_text_probabilities(
        self,
        distil_name: Optional[str],
        distil_conf: float,
        distil_probs: np.ndarray,
        sklearn_name: Optional[str],
        sklearn_conf: float,
        sklearn_probs: np.ndarray,
    ) -> np.ndarray:
        """
        Blend text probabilities conservatively. When the DistilBERT artifact
        lacks full label coverage, prefer the 30-class sklearn model.
        """
        if distil_probs is None or len(distil_probs) == 0:
            return sklearn_probs
        if sklearn_probs is None or len(sklearn_probs) == 0:
            return distil_probs

        exact_label_match = bool(
            getattr(self.distilbert, "label_integrity", {}).get("is_exact_match", False)
        )

        if exact_label_match:
            distil_weight = 0.55 if distil_name == sklearn_name else 0.40
        else:
            distil_weight = 0.30 if distil_name == sklearn_name else 0.15

        if sklearn_conf >= max(distil_conf + 0.15, 0.75):
            distil_weight = max(0.10, distil_weight - 0.10)

        if distil_conf >= max(sklearn_conf + 0.20, 0.90) and exact_label_match:
            distil_weight = min(0.65, distil_weight + 0.10)

        return (distil_weight * distil_probs) + ((1.0 - distil_weight) * sklearn_probs)

    def _text_model_mode(self) -> str:
        if self.distilbert_loaded and self.sklearn_loaded:
            return "hybrid_text"
        if self.distilbert_loaded:
            return "distilbert"
        if self.sklearn_loaded:
            return "sklearn"
        return "unavailable"

    @staticmethod
    def _label_to_index() -> Dict[str, int]:
        return {label: index for index, label in DISEASE_LABELS.items()}

    def _adjust_probabilities(
        self,
        probs: np.ndarray,
        boosts: Dict[str, float],
        suppressions: Optional[Dict[str, float]] = None,
    ) -> np.ndarray:
        adjusted = np.asarray(probs, dtype=np.float32).copy()
        label_to_index = self._label_to_index()

        for label, amount in boosts.items():
            idx = label_to_index.get(label)
            if idx is not None:
                adjusted[idx] += float(amount)

        for label, factor in (suppressions or {}).items():
            idx = label_to_index.get(label)
            if idx is not None:
                adjusted[idx] *= float(factor)

        adjusted = np.clip(adjusted, 0.0, None)
        total = float(np.sum(adjusted))
        if total <= 0:
            return np.asarray(probs, dtype=np.float32)
        return adjusted / total

    def _apply_text_clinical_rules(self, text: str, probs: np.ndarray) -> np.ndarray:
        if text is None:
            return probs
        text_lower = text.lower()
        adjusted = np.asarray(probs, dtype=np.float32)

        if (
            "blisters" in text_lower
            and "itch" in text_lower
            and "pain" not in text_lower
            and "warm" not in text_lower
            and "fever" not in text_lower
        ):
            adjusted = self._adjust_probabilities(
                adjusted,
                boosts={"Dermatitis": 0.18},
                suppressions={"Cellulitis": 0.45},
            )

        if (
            "swelling" in text_lower
            and "itch" in text_lower
            and "bumps" in text_lower
            and "pain" not in text_lower
        ):
            adjusted = self._adjust_probabilities(
                adjusted,
                boosts={"Urticaria": 0.18},
                suppressions={"Cellulitis": 0.45},
            )

        if "scaling" in text_lower and "dry" in text_lower:
            adjusted = self._adjust_probabilities(
                adjusted,
                boosts={"Psoriasis": 0.24},
                suppressions={"Eczema": 0.35},
            )

        if (
            ("cracked" in text_lower or "inflammation" in text_lower)
            and "scaling" in text_lower
            and "dry" in text_lower
            and "itch" in text_lower
        ):
            adjusted = self._adjust_probabilities(
                adjusted,
                boosts={"Eczema": 0.30},
                suppressions={"Psoriasis": 0.28},
            )

        melasma_clues = [
            "brown facial patches",
            "symmetrical discoloration",
            "hyperpigmentation",
            "worse after sun",
        ]
        if sum(1 for clue in melasma_clues if clue in text_lower) >= 2:
            adjusted = self._adjust_probabilities(
                adjusted,
                boosts={"Melasma": 0.38},
                suppressions={"Pigmentation / Dark Spots": 0.22},
            )

        if "purple" in text_lower and "shiny" in text_lower and "flat" in text_lower:
            adjusted = self._adjust_probabilities(
                adjusted,
                boosts={"Lichen Planus": 0.24},
                suppressions={"Dermatitis": 0.42},
            )

        return adjusted

    def _apply_fusion_clinical_rules(
        self,
        text: str,
        probs: np.ndarray,
        image_name: Optional[str],
        text_name: Optional[str],
        image_conf: float,
        text_conf: float,
    ) -> np.ndarray:
        if text is None:
            text = ""
        adjusted = self._apply_text_clinical_rules(text, probs)

        lesion_pair = {image_name, text_name}
        if lesion_pair == {"Melanoma", "Melanocytic Nevi"}:
            if text_name == "Melanoma" and text_conf >= 0.12:
                adjusted = self._adjust_probabilities(
                    adjusted,
                    boosts={"Melanoma": 0.28},
                    suppressions={"Melanocytic Nevi": 0.45},
                )
            elif image_name == "Melanoma" and image_conf >= 0.18:
                adjusted = self._adjust_probabilities(
                    adjusted,
                    boosts={"Melanoma": 0.16},
                    suppressions={"Melanocytic Nevi": 0.60},
                )

        inflammatory_labels = {"Dermatitis", "Psoriasis", "Urticaria", "Eczema", "Lichen Planus"}
        lesion_labels = {
            "Melanocytic Nevi",
            "Melanoma",
            "Basal Cell Carcinoma",
            "Dermatofibroma",
            "Seborrheic Keratosis",
            "Cherry Angioma",
        }
        if text_name in inflammatory_labels and image_name in lesion_labels and text_conf >= 0.12:
            adjusted = self._adjust_probabilities(
                adjusted,
                boosts={text_name: 0.22},
                suppressions={image_name: 0.40},
            )

        return adjusted

    def _load_specialized_models(self) -> None:
        """Load Severity and Skin Type models for full automation."""
        try:
            from components.severity_assessment_tracking.severity_model import (
                get_severity_model,
            )
            self.severity_model = get_severity_model(SEVERITY_MODEL_PATH, SEVERITY_METADATA_PATH)
            if self.severity_model.loaded:
                print("[Pipeline] Severity model integrated")
        except Exception as exc:
            print(f"[Pipeline] Severity integration error: {exc}")

        try:
            from components.skin_type_skincare_recommendation.skin_type_model import (
                get_skin_type_model,
            )
            self.skin_type_model = get_skin_type_model(SKIN_TYPE_MODEL_PATH, SKIN_TYPE_LABEL_MAP_PATH)
            if self.skin_type_model.loaded:
                print("[Pipeline] Skin-Type model integrated")
        except Exception as exc:
            print(f"[Pipeline] Skin-Type integration error: {exc}")

    def _load_data(self) -> None:
        """Load CSV knowledge-base for treatment enrichment."""
        try:
            if DISEASE_SYMPTOM_CSV.exists():
                self.disease_symptom_df = pd.read_csv(DISEASE_SYMPTOM_CSV)
                if DEBUG:
                    print(f"[Pipeline] Disease-symptom CSV -> {len(self.disease_symptom_df)} rows")

            if TREATMENT_RECORDS_CSV.exists():
                self.treatment_df = pd.read_csv(TREATMENT_RECORDS_CSV)
                if DEBUG:
                    print(f"[Pipeline] Treatment CSV -> {len(self.treatment_df)} rows")

            if self.disease_symptom_df is not None or self.treatment_df is not None:
                self.data_loaded = True
        except Exception as exc:
            if DEBUG:
                print(f"[Pipeline] CSV load error: {exc}")

    # ── Core Prediction ────────────────────────────────────────────────────────

    def _text_probs(self, text: str) -> Tuple[Optional[str], float, np.ndarray]:
        """
        Run text through the deployed text stack.
        Returns (disease_name, confidence, probabilities_array).
        """
        num_cls = len(DISEASE_LABELS)
        fallback = (None, 0.0, np.zeros(num_cls, dtype=np.float32))
        if not text or not text.strip():
            return fallback

        distil_result = fallback
        if self.distilbert_loaded and self.distilbert:
            distil_result = self.distilbert.predict(text)

        sklearn_result = self._sklearn_text_probs(text)
        distil_name, distil_conf, distil_probs = distil_result
        sklearn_name, sklearn_conf, sklearn_probs = sklearn_result

        if self.distilbert_loaded and self.sklearn_loaded:
            probs = self._blend_text_probabilities(
                distil_name,
                distil_conf,
                distil_probs,
                sklearn_name,
                sklearn_conf,
                sklearn_probs,
            )
            probs = self._apply_text_clinical_rules(text, probs)
            probs = self._normalize_probs(probs)
            predicted_class = int(np.argmax(probs))
            confidence = self._calibrate_confidence_from_probs(
                probs,
                mode='text_hybrid',
                label_coverage_full=True,
            )
            return (
                DISEASE_LABELS.get(predicted_class, f'Disease_{predicted_class}'),
                confidence,
                probs,
            )

        if self.distilbert_loaded:
            probs = self._apply_text_clinical_rules(text, distil_probs)
            probs = self._normalize_probs(probs)
            predicted_class = int(np.argmax(probs))
            confidence = self._calibrate_confidence_from_probs(
                probs,
                mode='text_distilbert',
                label_coverage_full=bool(
                    getattr(self.distilbert, 'label_integrity', {}).get('is_exact_match', False)
                ),
            )
            return (
                DISEASE_LABELS.get(predicted_class, f'Disease_{predicted_class}'),
                confidence,
                probs,
            )

        if self.sklearn_loaded:
            probs = self._apply_text_clinical_rules(text, sklearn_probs)
            probs = self._normalize_probs(probs)
            predicted_class = int(np.argmax(probs))
            confidence = self._calibrate_confidence_from_probs(
                probs,
                mode='text_sklearn',
                label_coverage_full=True,
            )
            return (
                DISEASE_LABELS.get(predicted_class, f'Disease_{predicted_class}'),
                confidence,
                probs,
            )

        return fallback

    def _image_probs(self, image_bytes: bytes) -> Tuple[Optional[str], float, np.ndarray]:
        """
        Run image through ResNet-18.
        Returns (disease_name, confidence, probabilities_array).
        """
        if self.image_model_loaded and self.image_model:
            disease, _, probs = self.image_model.predict_from_bytes(image_bytes)
            probs = self._normalize_probs(probs)
            confidence = self._calibrate_confidence_from_probs(
                probs,
                mode='image',
                label_coverage_full=bool(
                    getattr(self.image_model, 'label_integrity', {}).get('is_exact_match', False)
                ),
            )
            return disease, confidence, probs
        return None, 0.0, np.zeros(len(DISEASE_LABELS), dtype=np.float32)
    def _confidence_level(self, confidence: float) -> str:
        """
        Convert confidence score into stable UI-friendly confidence bands.
        """
        if confidence >= 0.75:
            return "high"
        if confidence >= 0.50:
            return "medium"
        return "low"

    def _normalize_probs(self, probs: np.ndarray) -> np.ndarray:
        arr = np.asarray(probs, dtype=np.float32)
        if arr.size == 0:
            return arr
        arr = np.clip(arr, 0.0, None)
        total = float(np.sum(arr))
        if total <= 0:
            return np.zeros_like(arr, dtype=np.float32)
        return arr / total

    def _top_probability_gap(self, probs: np.ndarray) -> float:
        arr = np.asarray(probs, dtype=np.float32)
        if arr.size < 2:
            return float(arr[0]) if arr.size == 1 else 0.0
        top_two = np.argsort(arr)[::-1][:2]
        return float(max(0.0, arr[top_two[0]] - arr[top_two[1]]))

    def _normalized_entropy(self, probs: np.ndarray) -> float:
        arr = np.asarray(probs, dtype=np.float32)
        if arr.size == 0:
            return 1.0
        arr = self._normalize_probs(arr)
        nonzero = arr[arr > 0]
        if nonzero.size == 0:
            return 1.0
        entropy = float(-np.sum(nonzero * np.log(nonzero + 1e-12)))
        max_entropy = float(np.log(arr.size + 1e-12))
        if max_entropy <= 1e-12:
            return 0.0
        return float(np.clip(entropy / max_entropy, 0.0, 1.0))

    def _calibrate_confidence_from_probs(
        self,
        probs: np.ndarray,
        *,
        mode: str,
        label_coverage_full: bool,
        agreement_score: Optional[float] = None,
        symptom_match_score: Optional[float] = None,
    ) -> float:
        arr = self._normalize_probs(probs)
        if arr.size == 0:
            return 0.0

        base_conf = float(np.max(arr))
        top_gap = self._top_probability_gap(arr)
        certainty = 1.0 - self._normalized_entropy(arr)

        # Blend confidence with distribution certainty to reduce over/under-confidence.
        calibrated = (0.35 * base_conf) + (0.40 * certainty) + (0.25 * top_gap)

        if mode == 'text_hybrid':
            calibrated += 0.30
        elif mode == 'text_sklearn':
            calibrated += 0.26
        elif mode == 'text_distilbert':
            calibrated += 0.20
        elif mode == 'fusion':
            calibrated += 0.12
        elif mode == 'image':
            calibrated -= 0.05

        if certainty > 0.65 and top_gap > 0.18:
            calibrated += 0.08

        if not label_coverage_full:
            calibrated *= 0.80

        if agreement_score is not None:
            if agreement_score < 0.30:
                calibrated *= 0.70
            elif agreement_score < 0.45:
                calibrated *= 0.82

        if symptom_match_score is not None:
            if symptom_match_score < 0.20:
                calibrated *= 0.70
            elif symptom_match_score > 0.60:
                calibrated = min(1.0, calibrated + 0.08)

        return float(np.clip(calibrated, 0.0, 1.0))

    def _build_review_flags(
        self,
        *,
        confidence: float,
        top_gap: float,
        agreement_score: Optional[float] = None,
        symptom_match_score: Optional[float] = None,
        label_coverage_full: bool = True,
        analysis_mode: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        if analysis_mode in {"image", "image_only"}:
            reasons.append(
                "Image-only analysis is provisional and should be confirmed with symptoms or dermatologist review"
            )
        if confidence < 0.55:
            reasons.append('Low confidence prediction')
        if top_gap < 0.10:
            reasons.append('Top predictions are too close')
        if agreement_score is not None and agreement_score < 0.30:
            reasons.append('Image and symptom modalities disagree')
        if symptom_match_score is not None and symptom_match_score < 0.20:
            reasons.append('Symptoms weakly match predicted disease')
        if not label_coverage_full:
            reasons.append('Text model label coverage is partial')

        return (len(reasons) > 0), reasons

    def _build_next_steps(
        self,
        *,
        model_used: str,
        requires_review: bool,
        confidence: float,
        symptom_match_score: Optional[float] = None,
        has_symptom_context: bool = False,
    ) -> List[str]:
        """
        Generate concise next-step guidance that matches the actual signal quality.
        """
        steps: List[str] = []

        if model_used in {"image", "image_only"}:
            steps.append("Add symptoms or a voice note and rerun the scan for multimodal review.")

        if confidence < 0.60:
            steps.append("Retake a clear close-up photo in natural light with the affected area centered.")

        if symptom_match_score is not None and symptom_match_score < 0.35:
            steps.append(
                "Include details such as itch, pain, scaling, discharge, duration, and body location."
            )

        if requires_review:
            steps.append(
                "Treat this as a screening result only and confirm with a dermatologist before acting on it."
            )
        elif has_symptom_context:
            steps.append("Monitor the area over the next 7 to 14 days and track any visible changes.")
        else:
            steps.append("Monitor the area closely and add symptom context if the appearance changes.")

        urgent_step = (
            "Seek urgent medical care for fever, severe pain, rapid spreading redness, pus, or eye involvement."
        )
        if urgent_step not in steps:
            steps.append(urgent_step)

        # Preserve order while removing duplicates.
        deduped = list(dict.fromkeys(steps))
        return deduped[:5]

    def _apply_image_only_guardrails(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reframe image-only outputs as screening-only results.

        The current image branch is useful for triage and ranking likely classes,
        but it is not reliable enough to present as a final standalone diagnosis.
        """
        disease = str(payload.get("disease") or "").strip()
        normalized_disease = disease.lower()
        has_specific_impression = normalized_disease not in {"", "unknown", "unable to determine"}

        warnings = [str(item).strip() for item in payload.get("warnings", []) if str(item).strip()]
        review_reasons = [
            str(item).strip()
            for item in payload.get("review_reasons", [])
            if str(item).strip()
        ]
        next_steps = [
            str(item).strip()
            for item in payload.get("next_steps", [])
            if str(item).strip()
        ]

        warnings.insert(
            0,
            "CRITICAL: Image-only analysis cannot reliably detect severe conditions like Melanoma. This is a provisional screening result and MUST NOT be treated as a final diagnosis.",
        )
        if has_specific_impression:
            warnings.append(f"Most likely visual match: {disease}.")

        review_reasons.insert(
            0,
            "Image-only predictions lack the clinical accuracy to detect critical lesions without symptom context",
        )

        next_steps.insert(
            0,
            "Add symptoms or a voice note and rerun the fused image plus symptom scan before acting on this result.",
        )

        payload.update(
            {
                "model_used": "image_only",
                "diagnostic_status": "provisional_image_only",
                "analysis_scope": "screening_only",
                "final_diagnosis_locked": False,
                "recommended_analysis_mode": "multimodal_fused",
                "display_disease": (
                    "Provisional image-only screening"
                    if has_specific_impression
                    else "Inconclusive image-only screening"
                ),
                "primary_impression": disease if has_specific_impression else None,
                "requires_dermatologist_review": True,
                "review_reasons": list(dict.fromkeys(review_reasons)),
                "warnings": list(dict.fromkeys(warnings)),
                "next_steps": list(dict.fromkeys(next_steps))[:5],
            }
        )
        return payload

    def _compute_dynamic_alpha(
        self, img_conf: float, txt_conf: float, have_img: bool, have_txt: bool, txt_probs: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute a confidence-aware fusion weight for image modality.
        The system is designed to be IMAGE DOMINANT. Symptoms are used to clarify.
        """
        if have_img and have_txt:
            total_conf = max(img_conf + txt_conf, 1e-6)
            shift = ((img_conf - txt_conf) / total_conf) * 0.15
            # Force the alpha to heavily favor the image branch (60% to 90%)
            base_alpha = 0.75 
            return float(np.clip(base_alpha + shift, 0.60, 0.90))
        if have_img:
            return 1.0
        return 0.0

    def _top_predictions(self, probs: np.ndarray, k: int = 3) -> List[Dict[str, Any]]:
        """
        Build top-k predictions from a probability vector.
        """
        if probs is None or len(probs) == 0:
            return []

        top_indices = np.argsort(probs)[::-1][:k]
        return [
            {
                "disease": DISEASE_LABELS.get(int(idx), f"Disease_{idx}"),
                "probability": float(probs[idx]),
            }
            for idx in top_indices
        ]

    def _agreement_score(self, image_probs: np.ndarray, text_probs: np.ndarray) -> Optional[float]:
        """
        Estimate agreement between modalities as cosine similarity on probabilities.
        """
        if image_probs is None or text_probs is None:
            return None
        if len(image_probs) == 0 or len(text_probs) == 0:
            return None

        # Pad to match shapes
        max_len = max(len(image_probs), len(text_probs))
        if len(image_probs) < max_len:
            image_probs = np.pad(image_probs, (0, max_len - len(image_probs)), 'constant')
        if len(text_probs) < max_len:
            text_probs = np.pad(text_probs, (0, max_len - len(text_probs)), 'constant')

        img_norm = float(np.linalg.norm(image_probs))
        txt_norm = float(np.linalg.norm(text_probs))
        if img_norm <= 0 or txt_norm <= 0:
            return None
        return float(np.dot(image_probs, text_probs) / (img_norm * txt_norm))

    def _fuse(
        self,
        img_probs: np.ndarray,
        txt_probs: np.ndarray,
        img_loaded: bool,
        txt_loaded: bool,
        image_alpha: float,
    ) -> np.ndarray:
        """
        Weighted linear fusion of image and text probability vectors.

          P_final = α · P_image + (1-α) · P_text

        Falls back to single modality if only one is available.
        """
        if img_loaded and txt_loaded:
            max_len = max(len(img_probs), len(txt_probs))
            if len(img_probs) < max_len:
                img_probs = np.pad(img_probs, (0, max_len - len(img_probs)), 'constant')
            if len(txt_probs) < max_len:
                txt_probs = np.pad(txt_probs, (0, max_len - len(txt_probs)), 'constant')
            return image_alpha * img_probs + (1 - image_alpha) * txt_probs
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
            "model_used"         : "hybrid_text" | "distilbert" | "sklearn" | "unavailable",
        }
        """
        disease, confidence, probs = self._text_probs(text)

        model_used = self._text_model_mode()
        top_gap = self._top_probability_gap(probs)
        label_coverage_full = model_used != "distilbert" or bool(
            getattr(self.distilbert, "label_integrity", {}).get("is_exact_match", False)
        )
        requires_review, review_reasons = self._build_review_flags(
            confidence=float(confidence),
            top_gap=float(top_gap),
            label_coverage_full=label_coverage_full,
            analysis_mode="text",
        )
        next_steps = self._build_next_steps(
            model_used=model_used,
            requires_review=requires_review,
            confidence=float(confidence),
            has_symptom_context=bool(text and text.strip()),
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
            "confidence_level":   self._confidence_level(float(confidence)),
            "treatments":         treatments,
            "followup_questions": followup,
            "requires_dermatologist_review": requires_review,
            "review_reasons": review_reasons,
            "next_steps": next_steps,
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
        disease, confidence, probs = self._image_probs(image_bytes)
        top3 = self._top_predictions(probs, k=3)
        top_gap = self._top_probability_gap(probs)
        requires_review, review_reasons = self._build_review_flags(
            confidence=float(confidence),
            top_gap=float(top_gap),
            label_coverage_full=bool(
                getattr(self.image_model, "label_integrity", {}).get("is_exact_match", False)
            ),
            analysis_mode="image",
        )
        next_steps = self._build_next_steps(
            model_used="image_only",
            requires_review=requires_review,
            confidence=float(confidence),
            has_symptom_context=False,
        )

        result = {
            "disease":    disease or "Unable to determine",
            "confidence": float(confidence),
            "confidence_level": self._confidence_level(float(confidence)),
            "top3_predictions": top3,
            "disease_explanation": self._get_disease_explanation(disease or "Unknown"),
            "expected_symptoms": self._get_expected_symptoms(disease or ""),
            "treatments": self._get_treatments(disease) if disease else [],
            "requires_dermatologist_review": requires_review,
            "review_reasons": review_reasons,
            "next_steps": next_steps,
            "model_used": "image_only" if self.image_model_loaded else "unavailable",
            "decision_mode": "IMAGE_ONLY",
            "model_architecture": "resnet18" if self.image_model_loaded else "unavailable",
        }
        return self._apply_image_only_guardrails(result)

    def _extract_symptoms(self, text: str) -> List[str]:
        """
        Extract canonical symptom keywords from user text/transcript.
        """
        if text is None:
            return []
        text_lower = text.lower()
        found = []
        for kw in SYMPTOM_KEYWORDS:
            if kw in text_lower:
                canonical = SYMPTOM_MAP.get(kw, kw)
                if canonical not in found:
                    found.append(canonical)
        return found

    def _get_expected_symptoms(self, disease: str) -> List[str]:
        """Get expected symptoms for a disease from config."""
        return EXPECTED_SYMPTOMS.get(disease, [])

    def _compute_symptom_match(self, extracted: List[str], expected: List[str]) -> Tuple[float, List[str]]:
        """
        Compute symptom match score using F1 between extracted and expected symptoms.
        Returns (score, matched_symptoms)
        """
        if not expected:
            return 0.0, []

        matched = sorted(set(s for s in extracted if s in expected))
        if not extracted:
            return 0.0, matched

        precision = len(matched) / len(set(extracted))
        recall = len(matched) / len(set(expected))
        score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        return score, matched

    def _determine_decision_mode(
        self, img_conf: float, txt_conf: float, have_img: bool, have_txt: bool, image_alpha: float
    ) -> str:
        """
        Determine the fusion decision mode based on confidence levels.
        """
        if have_img and have_txt:
            if abs(img_conf - txt_conf) < 0.10:
                return "BALANCED_FUSION"
            if image_alpha >= 0.65:
                return "IMAGE_DOMINANT_FUSION"
            if image_alpha <= 0.45:
                return "TEXT_DOMINANT_FUSION"
            return "CONFIDENCE_WEIGHTED_FUSION"
        if have_img:
            return "IMAGE_ONLY"
        if have_txt:
            return "TEXT_ONLY"
        return "UNCERTAIN_LOW_CONFIDENCE"

    def predict_fused(self, text: str, image_bytes: bytes, transcript: str = None) -> Dict[str, Any]:
        """
        Full multimodal prediction using image + text probabilities.
        """
        have_img = bool(image_bytes and len(image_bytes) > 0)
        have_txt = bool(text and text.strip())

        if not have_img or not have_txt:
            missing = "image" if not have_img else "symptoms/audio"
            return {
                "diagnostic_status": "incomplete_signal",
                "disease": "Awaiting inputs...",
                "confidence": 0.0,
                "message": f"Clinical verification requires both an image and symptom context. Missing: {missing}.",
                "next_steps": [
                    "Capture a clear, well-lit photo of the affected area." if not have_img else "Describe symptoms (itch, pain, duration) or record a voice note."
                ],
                "final_diagnosis_locked": False,
                "model_used": "none"
            }
        img_name, img_conf, img_probs = self._image_probs(image_bytes)
        txt_name, txt_conf, txt_probs = self._text_probs(text)
        image_alpha = self._compute_dynamic_alpha(img_conf, txt_conf, have_img, have_txt, txt_probs)
        text_alpha = 1.0 - image_alpha

        fused = self._fuse(img_probs, txt_probs, have_img, have_txt, image_alpha)
        fused = self._apply_fusion_clinical_rules(
            text,
            fused,
            img_name,
            txt_name,
            img_conf,
            txt_conf,
        )
        fused = self._normalize_probs(fused)

        top3_predictions = self._top_predictions(fused, k=3)
        top3_indices = np.argsort(fused)[::-1][:3]
        final_class = int(top3_indices[0])
        final_disease = DISEASE_LABELS.get(final_class, 'Unknown')
        top_probability_gap = self._top_probability_gap(fused)

        decision_mode = self._determine_decision_mode(
            img_conf,
            txt_conf,
            have_img,
            have_txt,
            image_alpha,
        )

        extracted_symptoms = self._extract_symptoms(text)
        expected_symptoms = self._get_expected_symptoms(final_disease)
        symptom_match_score, matched_symptoms = self._compute_symptom_match(
            extracted_symptoms,
            expected_symptoms,
        )

        agreement_score = self._agreement_score(img_probs, txt_probs) if have_img and have_txt else None

        warnings: List[str] = []
        symptom_boost = 1.0
        if extracted_symptoms:
            if symptom_match_score >= 0.5:
                symptom_boost = 1.0 + (symptom_match_score * 0.15)
            elif symptom_match_score < 0.2:
                symptom_boost = 0.40
                warnings.append(
                    'Symptoms strongly mismatch the predicted diagnosis. The condition may be out-of-scope (e.g., freckles, pigmentation, or sunspots).'
                )

        label_coverage_full = self.sklearn_loaded or bool(
            getattr(self.distilbert, 'label_integrity', {}).get('is_exact_match', False)
        )

        final_conf = self._calibrate_confidence_from_probs(
            fused,
            mode='fusion' if (have_img and have_txt) else ('image' if have_img else 'text_hybrid'),
            label_coverage_full=label_coverage_full,
            agreement_score=agreement_score,
            symptom_match_score=symptom_match_score if extracted_symptoms else None,
        )
        final_conf *= float(np.clip(symptom_boost, 0.4, 1.2))
        final_conf = float(np.clip(final_conf, 0.0, 1.0))

        requires_review, review_reasons = self._build_review_flags(
            confidence=final_conf,
            top_gap=float(top_probability_gap),
            agreement_score=agreement_score,
            symptom_match_score=symptom_match_score if extracted_symptoms else None,
            label_coverage_full=label_coverage_full,
            analysis_mode='fusion' if (have_img and have_txt) else 'image_only' if have_img else 'text_only',
        )

        model_used = (
            'fusion' if (have_img and have_txt)
            else 'image_only' if have_img
            else 'text_only'
        )

        # --- HYBRID AI SECOND OPINION ---
        ai_opinion = None
        try:
            from services.gemini_service import GeminiService
            avail, _ = GeminiService.is_available()
            if avail:
                ai_opinion = GeminiService.analyze_skin_condition(
                    image_bytes=image_bytes,
                    symptoms=text or "",
                    local_pred=final_disease,
                    local_conf=final_conf
                )
        except Exception as e:
            print(f"[Hybrid] AI Opinion failed: {e}")

        next_steps = self._build_next_steps(
            model_used=model_used,
            requires_review=requires_review,
            confidence=final_conf,
            symptom_match_score=symptom_match_score if extracted_symptoms else None,
            has_symptom_context=bool(text and text.strip()),
        )

        result = {
            'disease': final_disease,
            'confidence': final_conf,
            'confidence_level': self._confidence_level(final_conf),
            'transcript': transcript if transcript else text if text else None,
            'disease_explanation': self._get_disease_explanation(final_disease),
            'extracted_symptoms': extracted_symptoms,
            'expected_symptoms': expected_symptoms,
            'symptom_match_score': symptom_match_score,
            'matched_symptoms': matched_symptoms,
            'warnings': warnings,
            'ai_opinion': ai_opinion,
            'requires_dermatologist_review': requires_review or (True if ai_opinion and ai_opinion.get("error") else False),
            'review_reasons': review_reasons,
            'next_steps': next_steps,
            'top3_predictions': top3_predictions,
            'decision_mode': decision_mode,
            'image_weight': float(image_alpha),
            'text_weight': float(text_alpha),
            'agreement_score': agreement_score,
            'top_probability_gap': float(top_probability_gap),
            'image_disease': img_name,
            'image_confidence': float(img_conf),
            'text_disease': txt_name,
            'text_confidence': float(txt_conf),
            'treatments': self._get_treatments(final_disease),
            'model_used': model_used,
        }

        if ai_opinion and not ai_opinion.get("error"):
            result["hybrid_consensus"] = {
                "local_match": final_disease,
                "ai_match": ai_opinion.get("disease"),
                "status": "agreed" if ai_opinion.get("disease") == final_disease else "disagreed",
                "ai_reasoning": ai_opinion.get("reasoning")
            }

        if model_used == 'image_only':
            return self._apply_image_only_guardrails(result)
        return result
    def get_treatments_for_disease(self, disease: str) -> List[str]:
        """
        Return a flat list of medicine names for a given disease.
        Used by the ask_treatment intent in app.py.
        """
        raw = self._get_treatments(disease)
        return [t.get("medicine", "Unknown") for t in raw]

    # ── Fully Automated Smart Predict ──

    def smart_predict(
        self, 
        text: str, 
        image_bytes: Optional[bytes] = None, 
        journey_id: Optional[str] = None, 
        target_body_part: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        FULLY AUTOMATED ENTRY POINT.
        Intelligently determines what needs to be analyzed based on the image and text.
        Includes Anatomical Part Consistency checks if a journey_id is provided.
        """
        import io
        from PIL import Image

        have_img = bool(image_bytes and len(image_bytes) > 0)
        have_txt = bool(text and text.strip())

        master_report = {
            "status": "success",
            "automation_level": "full",
            "diagnosis": {},
            "severity": {},
            "skin_profile": {},
            "quality_check": {"passed": True, "notes": []},
            "summary": ""
        }

        # 1. Image Processing & Quality Check
        pil_img = None
        if image_bytes:
            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
                # Basic Blur Detection (automation safety)
                from PIL import ImageStat
                if pil_img.mode != "L": gray = pil_img.convert("L")
                else: gray = pil_img
                # This is a very rough heuristic for automation
                std_dev = ImageStat.Stat(gray).stddev[0]
                if std_dev < 15:
                    master_report["quality_check"]["notes"].append("Image may be too dark or low contrast.")
            except Exception as e:
                master_report["quality_check"]["passed"] = False
                master_report["quality_check"]["notes"].append(f"Image processing error: {e}")

        # 2. Disease Multi-modal Diagnosis (Disease + Symptoms)
        disease_res = self.predict_fused(text or "", image_bytes or b"", transcript=text)

        # 2.5 AI ASSISTANCE REASONING (Hybrid AI - Groq + Gemini)
        ai_assistance_result = None
        ai_available = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if ai_available and image_bytes and (text or "").strip():
            try:
                from services.gemini_service import GeminiService
                detailed_local_pred = f"Fused AI: {disease_res.get('disease')} (Visual Model suggests: {disease_res.get('image_disease')}, Symptom Model suggests: {disease_res.get('text_disease')})"
                ai_assistance_result = GeminiService.analyze_skin_condition(
                    image_bytes=image_bytes,
                    symptoms=text or "",
                    local_pred=detailed_local_pred,
                    local_conf=disease_res.get("confidence", 0.0)
                )
                
                # --- OUT OF SCOPE GUARDRAIL ---
                if ai_assistance_result and ai_assistance_result.get("is_skin") is False:
                    master_report["status"] = "out_of_scope"
                    master_report["summary"] = "The provided image does not appear to be of human skin. Please upload a clear photo of the affected skin area for analysis."
                    master_report["diagnosis"] = None
                    return master_report

                if ai_assistance_result and "error" not in ai_assistance_result:
                    master_report["ai_assistance_result"] = ai_assistance_result
                    master_report["ai_enhanced"] = True
                    # If AI is very confident, refine the master diagnosis
                    if ai_assistance_result.get("confidence", 0) > disease_res.get("confidence", 0):
                        disease_res["disease"] = ai_assistance_result["disease"]
                        disease_res["confidence"] = ai_assistance_result["confidence"]
                        disease_res["reasoning_ai"] = ai_assistance_result.get("reasoning")
                elif ai_assistance_result and "error" in ai_assistance_result:
                    print(f"[Pipeline] AI assistance skip: {ai_assistance_result.get('error')}")
            except Exception as e:
                print(f"[Pipeline] AI assistance reasoning skip: {e}")

        # Local Low-Confidence Guardrail (If AI is not used)
        if (
            have_img
            and have_txt
            and not master_report.get("ai_enhanced")
            and disease_res.get("confidence", 0) < 0.12
        ):
            master_report["status"] = "uncertain"
            master_report["summary"] = "The system is unable to confidently identify a skin condition in this image. Please ensure the photo is clear, well-lit, and focused on the skin."
            master_report["diagnosis"] = {"disease": "Uncertain", "confidence": 0.0}
            return master_report

        # 3. Specialized Face Analysis (Automation)
        detected_part = "Skin" # Default generic
        part_warning = None

        if pil_img and self.severity_model and self.severity_model.loaded:
            import numpy as np
            img_np = np.array(pil_img.convert("RGB"))
            
            # Check for face presence automatically
            severity_res = self.severity_model.predict_from_pil(pil_img, disease_name=disease_res.get("disease"))
            face_visible = severity_res.get("preprocessing", {}).get("face_visible", False)
            
            if face_visible:
                detected_part = "Face"
                master_report["severity"] = {
                    "level": severity_res["severity_level"],
                    "score": severity_res["severity_score"],
                    "face_detected": True
                }
                
                # If face is detected, automatically run skin-type for a full "user profile"
                if self.skin_type_model and self.skin_type_model.loaded:
                    type_res = self.skin_type_model.predict_from_pil(pil_img)
                    master_report["skin_profile"] = {
                        "type": type_res["skin_type"],
                        "confidence": type_res["confidence"]
                    }

                # EXPERT SEVERITY RATIONALE
                if os.getenv("GEMINI_API_KEY") and "expert_opinion" not in master_report:
                    try:
                        from services.gemini_service import GeminiService
                        expert_sev = GeminiService.assess_severity(
                            image_bytes=image_bytes,
                            metrics={
                                "local_level": severity_res["severity_level"],
                                "local_score": severity_res["severity_score"],
                                "image_features": severity_res.get("normalized_features", {})
                            }
                        )
                        if expert_sev and "error" not in expert_sev:
                            master_report["severity"]["expert_rationale"] = expert_sev.get("rationale")
                            master_report["severity"]["clinical_notes"] = expert_sev.get("clinical_notes")
                    except Exception:
                        pass
            else:
                detected_part = "Body/Other"
                master_report["severity"] = {"face_detected": False, "note": "Limited body-part severity analysis used."}

        # 3.1 Anatomical Part Consistency Check
        if target_body_part and target_body_part.lower() != "skin":
            # If journey expects a face but none found
            if target_body_part.lower() == "face" and detected_part != "Face":
                part_warning = "Visual mismatch: This journey is tracking your face, but the photo appears to be of a different body part."
            # If journey expects non-face but face found
            elif target_body_part.lower() != "face" and detected_part == "Face":
                part_warning = f"Visual mismatch: This journey is tracking your {target_body_part}, but the photo appears to be of your face."

        master_report["anatomical_check"] = {
            "detected_part": detected_part,
            "target_part": target_body_part,
            "consistency_warning": part_warning
        }

        if not have_txt or not have_img:
            master_report["status"] = "incomplete"
            master_report["automation_level"] = "partial"
            if have_img:
                diagnosis = self.predict_from_image(image_bytes or b"")
                master_report["summary"] = (
                    "This is a provisional image-only screening. Add symptom details "
                    "or a voice note for the full multimodal clinical prediction."
                )
            else:
                diagnosis = disease_res
                master_report["summary"] = (
                    "I need both an image and a description of your symptoms to "
                    "provide an accurate clinical prediction."
                )
            master_report["diagnosis"] = diagnosis
            return master_report

        # 4. FINAL HYBRID UNIFICATION (The "Lead Assistant" Logic)
        # We use the AI Assistance Result to reconcile any conflicts between image and text branches.
        final_disease = disease_res.get("disease", "a skin condition")
        final_confidence = disease_res.get("confidence", 0.0)
        
        if ai_assistance_result and not ai_assistance_result.get("error"):
            ai_diag = ai_assistance_result.get("disease")
            is_skin_detected = ai_assistance_result.get("is_skin", True)
            
            # --- GUARDRAIL: OUT OF SCOPE ---
            if not is_skin_detected:
                master_report["status"] = "out_of_scope"
                master_report["summary"] = "The system has determined that the provided image does not contain human skin or a recognizable skin condition."
                master_report["diagnosis"] = {
                    "disease": "Non-Skin Image Detected",
                    "confidence": 1.0,
                    "reasoning_ai": ai_assistance_result.get("reasoning", "The image appears to be an object or animal, not human skin.")
                }
                return master_report

            # --- RECONCILIATION ---
            # If the AI and the local models agree, we boost confidence
            if ai_diag and ai_diag.lower() in final_disease.lower():
                final_confidence = min(0.98, final_confidence + 0.15)
                master_report["summary"] = f"Our local analysis and AI Assistant both suggest {final_disease}."
            
            # If they disagree, we let the AI Assistant decide the primary display
            elif ai_diag:
                final_disease = ai_diag
                final_confidence = ai_assistance_result.get("confidence", final_confidence)
                master_report["summary"] = f"A high-fidelity analysis suggests this condition is {final_disease}, providing more context than initial visual scanning."

        # Finalize the Master Report for the Frontend
        master_report["diagnosis"] = {
            **disease_res,
            "display_disease": final_disease,
            "final_diagnosis": final_disease,
            "confidence": final_confidence,
            "confidence_percent": f"{final_confidence * 100:.1f}%",
            "reasoning_ai": ai_assistance_result.get("reasoning") if ai_assistance_result else None,
            # Synchronize the explanation and expected symptoms with the final AI decision
            "disease_explanation": self._get_disease_explanation(final_disease),
            "expected_symptoms": self._get_expected_symptoms(final_disease),
            "treatments": self._get_treatments(final_disease)
        }
        
        # --- FIX: Synchronize Review Flags with Expert AI ---
        # If the expert AI is highly confident (e.g., > 70%), it has resolved the ambiguity.
        if final_confidence > 0.70:
            master_report["diagnosis"]["requires_dermatologist_review"] = False
            # Clear contradictory review reasons
            old_reasons = master_report["diagnosis"].get("review_reasons", [])
            new_reasons = [r for r in old_reasons if "Low confidence" not in r and "too close" not in r and "disagree" not in r]
            master_report["diagnosis"]["review_reasons"] = new_reasons
            
            # Clear contradictory warnings
            old_warnings = master_report["diagnosis"].get("warnings", [])
            new_warnings = [w for w in old_warnings if "Symptoms strongly mismatch" not in w]
            master_report["diagnosis"]["warnings"] = new_warnings

        # Move AI assistance result to the top level for the UI to find easily
        if ai_assistance_result and not ai_assistance_result.get("error"):
            master_report["ai_assistance_result"] = ai_assistance_result

        return master_report

# ── Singleton ─────────────────────────────────────────────────────────────────

def get_inference_pipeline() -> InferencePipeline:
    """Return the global singleton InferencePipeline (lazy-loaded)."""
    if not hasattr(get_inference_pipeline, "_instance"):
        get_inference_pipeline._instance = InferencePipeline()
    return get_inference_pipeline._instance
