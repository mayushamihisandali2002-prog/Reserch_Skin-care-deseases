"""
Artifact-aware DistilBERT text classifier for skin disease prediction.

The live Hugging Face checkpoint may expose fewer labels than the application's
canonical disease universe. This wrapper loads the checkpoint's own id2label
mapping and aligns probabilities into the canonical label space so the rest of
the application can fuse text and image outputs safely.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from inference.config import DISEASE_LABELS as TARGET_DISEASE_LABELS
from inference.label_space import (
    align_probabilities,
    label_map_coverage,
    load_hf_id2label,
)


DISEASE_LABELS: dict[int, str] = dict(TARGET_DISEASE_LABELS)
NUM_CLASSES = len(DISEASE_LABELS)


class DistilBertTextModel:
    """
    Wraps a fine-tuned DistilBERT sequence classifier.
    """

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir
        self.tokenizer = None
        self.model = None
        self.loaded = False

        self.source_label_map: dict[int, str] = dict(DISEASE_LABELS)
        self.target_label_map: dict[int, str] = dict(DISEASE_LABELS)
        self.label_integrity: dict[str, object] = {}

        self._load()

    def _load(self) -> None:
        try:
            from transformers import (
                DistilBertForSequenceClassification,
                DistilBertTokenizerFast,
            )

            if not self.model_dir.exists():
                print(f"[DistilBERT] Missing model directory: {self.model_dir}")
                return

            self.tokenizer = DistilBertTokenizerFast.from_pretrained(str(self.model_dir))
            self.model = DistilBertForSequenceClassification.from_pretrained(
                str(self.model_dir)
            )
            self.model.eval()

            self.source_label_map = load_hf_id2label(
                self.model_dir,
                fallback_label_map=self.target_label_map,
            )
            self.label_integrity = label_map_coverage(
                self.source_label_map,
                self.target_label_map,
            )

            output_labels = int(
                getattr(self.model.config, "num_labels", len(self.source_label_map))
            )
            self.loaded = True

            print(
                "[DistilBERT] Ready "
                f"(artifact_labels={len(self.source_label_map)}, "
                f"model_outputs={output_labels}, "
                f"canonical_labels={len(self.target_label_map)})"
            )
            if not self.label_integrity.get("is_exact_match", False):
                print(
                    "[DistilBERT] Label-space warning: "
                    f"missing={self.label_integrity.get('missing_labels', [])}"
                )

        except ImportError as exc:
            print(f"[DistilBERT] transformers not installed: {exc}")
        except Exception as exc:
            print(f"[DistilBERT] Load error: {exc}")

    def predict(self, text: str) -> Tuple[str, float, np.ndarray]:
        """
        Predict disease from symptom text and return canonical-space probabilities.
        """
        fallback = ("Unknown", 0.0, np.zeros(NUM_CLASSES, dtype=np.float32))
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
                source_probs: np.ndarray = (
                    F.softmax(outputs.logits, dim=-1)[0].cpu().numpy()
                )

            probs = align_probabilities(
                source_probs,
                self.source_label_map,
                self.target_label_map,
            )

            predicted_class = int(np.argmax(probs))
            confidence = float(probs[predicted_class])
            disease_name = self.target_label_map.get(
                predicted_class,
                f"Disease_{predicted_class}",
            )

            return disease_name, confidence, probs

        except Exception as exc:
            print(f"[DistilBERT] Prediction error: {exc}")
            return fallback


_instance: Optional[DistilBertTextModel] = None


def get_distilbert_model(model_dir: Path) -> DistilBertTextModel:
    global _instance
    if _instance is None:
        _instance = DistilBertTextModel(model_dir)
    return _instance
