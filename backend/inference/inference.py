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
)
from .knowledge_base import SYMPTOM_KEYWORDS, SYMPTOM_MAP


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

    def _load_specialized_models(self) -> None:
        """Load Severity and Skin Type models for full automation."""
        try:
            from .severity_model import get_severity_model
            self.severity_model = get_severity_model(SEVERITY_MODEL_PATH, SEVERITY_METADATA_PATH)
            if self.severity_model.loaded:
                print("[Pipeline] ✅ Severity model integrated")
        except Exception as exc:
            print(f"[Pipeline] Severity integration error: {exc}")

        try:
            from .skin_type_model import get_skin_type_model
            self.skin_type_model = get_skin_type_model(SKIN_TYPE_MODEL_PATH, SKIN_TYPE_LABEL_MAP_PATH)
            if self.skin_type_model.loaded:
                print("[Pipeline] ✅ Skin-Type model integrated")
        except Exception as exc:
            print(f"[Pipeline] Skin-Type integration error: {exc}")

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

    def _confidence_level(self, confidence: float) -> str:
        """
        Convert confidence score into stable UI-friendly confidence bands.
        """
        if confidence >= 0.75:
            return "high"
        if confidence >= 0.50:
            return "moderate"
        return "low"

    def _compute_dynamic_alpha(
        self, img_conf: float, txt_conf: float, have_img: bool, have_txt: bool, txt_probs: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute dynamic fusion weight for image modality.
        User requested 50/50 fusion. However, if text detects Pigmentation/Dark Spots (Class 5),
        since Image model lacks this class natively, we defer to Text.
        """
        if have_img and have_txt:
            return 0.50
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
        disease, confidence, probs = self._image_probs(image_bytes)
        top3 = self._top_predictions(probs, k=3)

        return {
            "disease":    disease or "Unable to determine",
            "confidence": float(confidence),
            "confidence_level": self._confidence_level(float(confidence)),
            "top3_predictions": top3,
            "disease_explanation": self._get_disease_explanation(disease or "Unknown"),
            "expected_symptoms": self._get_expected_symptoms(disease or ""),
            "treatments": self._get_treatments(disease) if disease else [],
            "model_used": "resnet" if self.image_model_loaded else "unavailable",
        }

    def _extract_symptoms(self, text: str) -> List[str]:
        """
        Extract canonical symptom keywords from user text/transcript.
        """
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
        Full multimodal prediction: ResNet-18 image + DistilBERT text → fusion.

        Fusion formula:
            P_final = 0.6 · P_image + 0.4 · P_text

        Returns comprehensive structured output with:
        - Final diagnosis and confidence
        - ASR transcript (if provided)
        - Extracted vs expected symptoms with match score
        - Top-3 predictions
        - Decision mode explanation
        """
        img_name, img_conf, img_probs = self._image_probs(image_bytes)
        txt_name, txt_conf, txt_probs = self._text_probs(text)

        have_img = self.image_model_loaded and img_conf > 0
        have_txt = (self.distilbert_loaded or self.sklearn_loaded) and txt_conf > 0

        image_alpha = self._compute_dynamic_alpha(img_conf, txt_conf, have_img, have_txt, txt_probs)
        text_alpha = 1.0 - image_alpha
        fused = self._fuse(img_probs, txt_probs, have_img, have_txt, image_alpha)

        top3_predictions = self._top_predictions(fused, k=3)
        top3_indices = np.argsort(fused)[::-1][:3]
        final_class = int(top3_indices[0])
        base_conf = float(fused[final_class])
        
        # Calibration based on modality agreement
        agreement_score = self._agreement_score(img_probs, txt_probs) if have_img and have_txt else 1.0
        
        # Penalize confidence if models strongly disagree
        if agreement_score is not None and agreement_score < 0.3:
            calibration_factor = 0.7  # 30% reduction for disagreement
        else:
            calibration_factor = 1.0

        second_conf = float(fused[top3_indices[1]]) if len(top3_indices) > 1 else 0.0
        top_probability_gap = max(0.0, base_conf - second_conf)
        
        final_disease = DISEASE_LABELS.get(final_class, "Unknown")

        # Decision mode
        decision_mode = self._determine_decision_mode(
            img_conf, txt_conf, have_img, have_txt, image_alpha
        )

        # ── Symptom analysis ──
        extracted_symptoms = self._extract_symptoms(text)
        expected_symptoms = self._get_expected_symptoms(final_disease)
        symptom_match_score, matched_symptoms = self._compute_symptom_match(
            extracted_symptoms, expected_symptoms
        )
        agreement_score = self._agreement_score(img_probs, txt_probs) if have_img and have_txt else None

        # ── Advanced Adaptive Calibration ──
        # 1. Symptom Match Adjustment
        symptom_boost = 1.0
        warnings = []
        if len(extracted_symptoms) > 0:
            if symptom_match_score >= 0.5:
                symptom_boost = 1.0 + (symptom_match_score * 0.15)
            elif symptom_match_score < 0.2:
                # Heavy penalty if symptoms strongly contradict diagnosis classes
                symptom_boost = 0.40
                warnings.append("Symptoms strongly mismatch the predicted diagnosis. The condition may be out-of-scope (e.g., Freckles, Pigmentation, or Sunspots).")

        # Final calibrated confidence factoring in modality agreement and symptom matching
        calibrated_conf = base_conf * (0.85 + 0.15 * top_probability_gap) * calibration_factor * symptom_boost
        final_conf = float(np.clip(calibrated_conf, 0.0, 1.0))
        model_used = (
            "fusion"     if (have_img and have_txt) else
            "image_only" if have_img else
            "text_only"
        )

        return {
            # Core prediction
            "disease":          final_disease,
            "confidence":       final_conf,
            "confidence_level": self._confidence_level(final_conf),
            "transcript":       transcript or text if text else "",

            # ASR transcript
            "transcript":       transcript if transcript else text if text else None,

            # Disease explanation
            "disease_explanation": self._get_disease_explanation(final_disease),

            # Symptom analysis
            "extracted_symptoms": extracted_symptoms,
            "expected_symptoms":  expected_symptoms,
            "symptom_match_score": symptom_match_score,
            "matched_symptoms":   matched_symptoms,
            
            # Additional warnings explicitly for UI
            "warnings":         warnings,

            # Top-3 predictions
            "top3_predictions":   top3_predictions,

            # Decision explanation
            "decision_mode":      decision_mode,
            "image_weight":       float(image_alpha),
            "text_weight":        float(text_alpha),
            "agreement_score":    agreement_score,
            "top_probability_gap": float(top_probability_gap),

            # Component outputs
            "image_disease":    img_name,
            "image_confidence": img_conf,
            "text_disease":     txt_name,
            "text_confidence":  txt_conf,

            # Treatments & model info
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

        master_report = {
            "status": "success",
            "automation_level": "full",
            "diagnosis": None,
            "severity": None,
            "skin_profile": None,
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
        master_report["diagnosis"] = disease_res

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

        # 4. Generate Automation Summary
        diag = disease_res.get("disease", "a skin condition")
        conf = disease_res.get("confidence_level", "low")
        
        has_text = bool(text and text.strip())
        has_image = bool(image_bytes)
        
        if has_text and has_image:
            summary = f"I've analyzed your image and symptoms, and detected {diag}. "
        elif has_text:
            summary = f"I've analyzed your symptoms and detected {diag}. "
        else:
            summary = f"I've analyzed your image and detected {diag}. "

        
        severity_data = master_report.get("severity")
        if severity_data and "level" in severity_data:
            sev = severity_data["level"]
            summary += f"The condition appears to be in a {sev} stage. "
        elif severity_data and not severity_data.get("face_detected", True):
            summary += "I analyzed the image for severity, though the specific facial severity metrics were limited. "
            
        profile_data = master_report.get("skin_profile")
        if profile_data and "type" in profile_data:
            st = profile_data["type"]
            summary += f"For your {st} skin, I've adjusted the recommendations below."
        elif not profile_data and detected_part == "Face":
             summary += "I've also included general skin-type guidance for your facial analysis."

        master_report["summary"] = summary
        return master_report

# ── Singleton ─────────────────────────────────────────────────────────────────

def get_inference_pipeline() -> InferencePipeline:
    """Return the global singleton InferencePipeline (lazy-loaded)."""
    if not hasattr(get_inference_pipeline, "_instance"):
        get_inference_pipeline._instance = InferencePipeline()
    return get_inference_pipeline._instance
