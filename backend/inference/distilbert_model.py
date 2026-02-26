"""
DistilBERT Text Classification Model
======================================
Fine-tuned DistilBertForSequenceClassification for skin disease prediction.

Model path : best_model/best_model/
             (contains model.safetensors, tokenizer.json, config.json, vocab.txt)

Input  : User symptom text string
Output : (disease_name, confidence, probabilities_array[5])
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Optional, Tuple

# ── Disease label mapping ─────────────────────────────────────────────────────
# Must match the id2label in best_model/best_model/config.json
DISEASE_LABELS: dict[int, str] = {
    0: "Eczema",
    1: "Dermatitis",
    2: "Psoriasis",
    3: "Acne",
    4: "Urticaria",
}
NUM_CLASSES = len(DISEASE_LABELS)


class DistilBertTextModel:
    """
    Wraps a fine-tuned DistilBERT model for skin disease classification.

    Usage
    -----
    model = DistilBertTextModel(Path("best_model/best_model"))
    disease, conf, probs = model.predict("I have itchy red patches on my arms")
    """

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir
        self.tokenizer = None
        self.model = None
        self.loaded = False
        self._load()

    # ── Loading ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load tokenizer + model from the HuggingFace directory."""
        try:
            from transformers import (
                DistilBertTokenizerFast,
                DistilBertForSequenceClassification,
            )
            import torch  # noqa: F401 – verify torch is available

            if not self.model_dir.exists():
                print(f"[DistilBERT] ❌ Directory not found: {self.model_dir}")
                return

            print(f"[DistilBERT] Loading tokenizer …")
            self.tokenizer = DistilBertTokenizerFast.from_pretrained(
                str(self.model_dir)
            )

            print(f"[DistilBERT] Loading model weights …")
            self.model = DistilBertForSequenceClassification.from_pretrained(
                str(self.model_dir)
            )
            self.model.eval()

            n_labels = getattr(self.model.config, "num_labels", NUM_CLASSES)
            self.loaded = True
            print(f"[DistilBERT] ✅ Ready — {n_labels} disease classes")

        except ImportError as exc:
            print(f"[DistilBERT] ❌ 'transformers' not installed: {exc}")
        except Exception as exc:
            print(f"[DistilBERT] ❌ Load error: {exc}")

    # ── Inference ──────────────────────────────────────────────────────────────

    def predict(self, text: str) -> Tuple[str, float, np.ndarray]:
        """
        Predict disease from symptom text.

        Parameters
        ----------
        text : user symptom description

        Returns
        -------
        (disease_name, confidence_0_to_1, probabilities_array[NUM_CLASSES])
        """
        fallback = ("Unknown", 0.0, np.zeros(NUM_CLASSES))
        if not self.loaded or not text.strip():
            return fallback

        try:
            import torch
            import torch.nn.functional as F

            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True,
            )

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits  # shape: (1, num_labels)
                probs: np.ndarray = F.softmax(logits, dim=-1)[0].numpy()

            predicted_class = int(np.argmax(probs))
            confidence = float(probs[predicted_class])
            disease_name = DISEASE_LABELS.get(predicted_class, f"Disease_{predicted_class}")

            return disease_name, confidence, probs

        except Exception as exc:
            print(f"[DistilBERT] ⚠️ Prediction error: {exc}")
            return fallback


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[DistilBertTextModel] = None


def get_distilbert_model(model_dir: Path) -> DistilBertTextModel:
    """Return the singleton DistilBERT model (lazy-loaded on first call)."""
    global _instance
    if _instance is None:
        _instance = DistilBertTextModel(model_dir)
    return _instance
