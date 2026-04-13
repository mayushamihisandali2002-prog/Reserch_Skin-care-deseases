"""
Artifact-aware ResNet image classifier for skin disease prediction.

The training script uses torchvision's ImageFolder class indexing, which means
label order is dataset-directory dependent. This wrapper derives the source
label order from the research dataset directories and aligns probabilities into
the application's canonical disease space before returning results.
"""

from __future__ import annotations

from collections import OrderedDict
from io import BytesIO
import json
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from inference.config import (
    DISEASE_LABELS as TARGET_DISEASE_LABELS,
    RESEARCH_DATASET_DIR,
)
from inference.label_space import (
    align_probabilities,
    build_dataset_label_map,
    label_map_coverage,
)


DISEASE_LABELS: dict[int, str] = dict(TARGET_DISEASE_LABELS)
NUM_CLASSES = len(DISEASE_LABELS)

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
IMAGE_SIZE = 224
DEFAULT_LOGIT_TEMPERATURE = 0.9
DEFAULT_LOGIT_BLEND_WEIGHT = 0.95
DEFAULT_PROTOTYPE_BLEND_WEIGHT = 0.05


class ResNetImageModel:
    """
    Wraps the deployed ResNet image model for skin disease classification.
    """

    def __init__(self, model_path: Path, dataset_dir: Optional[Path] = None) -> None:
        self.model_path = model_path
        self.dataset_dir = dataset_dir or RESEARCH_DATASET_DIR
        self.metadata_path = self.model_path.with_suffix(".json")
        self.prototype_cache_path = self.model_path.with_name(
            f"{self.model_path.stem}_prototypes.npz"
        )

        self.model = None
        self.transform = None
        self.loaded = False

        self.source_label_map: dict[int, str] = dict(DISEASE_LABELS)
        self.target_label_map: dict[int, str] = dict(DISEASE_LABELS)
        self.label_integrity: dict[str, object] = {}
        self.output_classes = 0
        self.source_prototypes: Optional[np.ndarray] = None
        self.prototype_counts: Optional[np.ndarray] = None
        self.runtime_config = {
            "logit_temperature": DEFAULT_LOGIT_TEMPERATURE,
            "logit_blend_weight": DEFAULT_LOGIT_BLEND_WEIGHT,
            "prototype_blend_weight": DEFAULT_PROTOTYPE_BLEND_WEIGHT,
            "source": "defaults",
        }

        self._load()

    def _infer_output_classes(self, state_dict: dict[str, object]) -> int:
        for key in ("fc.weight", "module.fc.weight"):
            value = state_dict.get(key)
            if value is not None and hasattr(value, "shape"):
                return int(value.shape[0])
        return len(self.source_label_map)

    def _load(self) -> None:
        try:
            import torch
            import torchvision.models as models
            import torchvision.transforms as transforms

            if not self.model_path.exists():
                print(f"[ResNet] Missing model file: {self.model_path}")
                return

            checkpoint = torch.load(
                str(self.model_path),
                map_location=torch.device("cpu"),
                weights_only=False,
            )

            self.source_label_map = build_dataset_label_map(
                self.dataset_dir,
                fallback_label_map=self.target_label_map,
            )
            self.label_integrity = label_map_coverage(
                self.source_label_map,
                self.target_label_map,
            )

            if isinstance(checkpoint, (OrderedDict, dict)):
                state_dict = dict(checkpoint)
                if any(key.startswith("module.") for key in state_dict):
                    state_dict = {
                        key.replace("module.", "", 1): value
                        for key, value in state_dict.items()
                    }

                self.output_classes = self._infer_output_classes(state_dict)
                if len(self.source_label_map) != self.output_classes:
                    raise ValueError(
                        "Image label map count does not match checkpoint outputs "
                        f"({len(self.source_label_map)} vs {self.output_classes})"
                    )

                self.model = models.resnet18(weights=None)
                self.model.fc = torch.nn.Linear(
                    self.model.fc.in_features,
                    self.output_classes,
                )
                self.model.load_state_dict(state_dict)
            else:
                self.model = checkpoint
                self.output_classes = int(getattr(self.model.fc, "out_features", NUM_CLASSES))

            self.model.eval()
            self.transform = transforms.Compose(
                [
                    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=IMAGENET_MEAN,
                        std=IMAGENET_STD,
                    ),
                ]
            )
            self._load_or_build_prototypes()
            self._load_runtime_config()
            self.loaded = True

            print(
                "[ResNet] Ready "
                f"(artifact_labels={len(self.source_label_map)}, "
                f"model_outputs={self.output_classes}, "
                f"canonical_labels={len(self.target_label_map)})"
            )
            print(
                "[ResNet] Operating point "
                f"(temp={self.runtime_config['logit_temperature']}, "
                f"logit_weight={self.runtime_config['logit_blend_weight']}, "
                f"prototype_weight={self.runtime_config['prototype_blend_weight']}, "
                f"source={self.runtime_config['source']})"
            )
            if not self.label_integrity.get("is_exact_match", False):
                print(
                    "[ResNet] Label-space warning: "
                    f"missing={self.label_integrity.get('missing_labels', [])}"
                )

        except ImportError as exc:
            print(f"[ResNet] torch/torchvision not installed: {exc}")
        except Exception as exc:
            print(f"[ResNet] Load error: {exc}")

    def _load_runtime_config(self) -> None:
        if not self.metadata_path.exists():
            return

        try:
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[ResNet] Metadata load error: {exc}")
            return

        operating_point = metadata.get("recommended_operating_point") or {}
        legacy_blend = metadata.get("recommended_blend") or {}

        logit_temperature = float(
            operating_point.get(
                "logit_temperature",
                self.runtime_config["logit_temperature"],
            )
        )
        logit_weight = float(
            operating_point.get(
                "logit_blend_weight",
                legacy_blend.get(
                    "alpha_logits",
                    self.runtime_config["logit_blend_weight"],
                ),
            )
        )
        prototype_weight = float(
            operating_point.get(
                "prototype_blend_weight",
                max(0.0, 1.0 - logit_weight),
            )
        )

        if logit_temperature <= 0:
            logit_temperature = self.runtime_config["logit_temperature"]

        total_weight = logit_weight + prototype_weight
        if total_weight <= 0:
            logit_weight = self.runtime_config["logit_blend_weight"]
            prototype_weight = self.runtime_config["prototype_blend_weight"]
            total_weight = logit_weight + prototype_weight

        self.runtime_config = {
            "logit_temperature": round(float(logit_temperature), 4),
            "logit_blend_weight": round(float(logit_weight / total_weight), 4),
            "prototype_blend_weight": round(float(prototype_weight / total_weight), 4),
            "source": str(self.metadata_path),
        }

    def _forward_logits_and_features(self, tensor, torch):
        x = self.model.conv1(tensor)
        x = self.model.bn1(x)
        x = self.model.relu(x)
        x = self.model.maxpool(x)
        x = self.model.layer1(x)
        x = self.model.layer2(x)
        x = self.model.layer3(x)
        x = self.model.layer4(x)
        x = self.model.avgpool(x)
        features = torch.flatten(x, 1)
        logits = self.model.fc(features)
        return logits, features

    def _load_or_build_prototypes(self) -> None:
        if not self.dataset_dir.exists():
            return

        expected_labels = [
            self.source_label_map[idx] for idx in range(len(self.source_label_map))
        ]

        try:
            if self.prototype_cache_path.exists():
                cached = np.load(self.prototype_cache_path, allow_pickle=False)
                cached_labels = cached["labels"].tolist()
                prototypes = cached["prototypes"].astype(np.float32)
                counts = cached["counts"].astype(np.int32)
                if (
                    cached_labels == expected_labels
                    and prototypes.shape[0] == self.output_classes
                ):
                    self.source_prototypes = prototypes
                    self.prototype_counts = counts
                    print("[ResNet] Prototype cache loaded")
                    return
        except Exception as exc:
            print(f"[ResNet] Prototype cache load error: {exc}")

        self._build_prototypes(expected_labels)

    def _build_prototypes(self, expected_labels: list[str]) -> None:
        try:
            import torch
            from torch.utils.data import DataLoader
            from torchvision import datasets

            dataset = datasets.ImageFolder(root=str(self.dataset_dir), transform=self.transform)
            if len(dataset.classes) != self.output_classes:
                print(
                    "[ResNet] Prototype build skipped: class count mismatch "
                    f"({len(dataset.classes)} vs {self.output_classes})"
                )
                return

            loader = DataLoader(dataset, batch_size=16, shuffle=False, num_workers=0)
            prototype_sums = None
            counts = np.zeros(self.output_classes, dtype=np.int32)

            with torch.no_grad():
                for images, labels in loader:
                    _, features = self._forward_logits_and_features(images, torch)
                    feature_batch = features.cpu().numpy().astype(np.float32)
                    label_batch = labels.cpu().numpy().astype(np.int64)

                    if prototype_sums is None:
                        prototype_sums = np.zeros(
                            (self.output_classes, feature_batch.shape[1]),
                            dtype=np.float64,
                        )

                    norms = np.linalg.norm(feature_batch, axis=1, keepdims=True)
                    normalized = feature_batch / np.clip(norms, 1e-8, None)

                    for feature_vec, label_idx in zip(normalized, label_batch):
                        prototype_sums[int(label_idx)] += feature_vec
                        counts[int(label_idx)] += 1

            if prototype_sums is None or not np.all(counts > 0):
                print("[ResNet] Prototype build skipped: insufficient features")
                return

            prototypes = prototype_sums / counts[:, None]
            prototype_norms = np.linalg.norm(prototypes, axis=1, keepdims=True)
            prototypes = prototypes / np.clip(prototype_norms, 1e-8, None)
            self.source_prototypes = prototypes.astype(np.float32)
            self.prototype_counts = counts
            np.savez(
                self.prototype_cache_path,
                prototypes=self.source_prototypes,
                counts=self.prototype_counts,
                labels=np.asarray(expected_labels, dtype="<U64"),
            )
            print("[ResNet] Prototype cache built")
        except Exception as exc:
            print(f"[ResNet] Prototype build error: {exc}")

    def _prototype_probabilities(self, feature_vector: np.ndarray) -> Optional[np.ndarray]:
        if self.source_prototypes is None:
            return None

        vector = np.asarray(feature_vector, dtype=np.float32)
        norm = float(np.linalg.norm(vector))
        if norm <= 0:
            return None

        normalized = vector / norm
        similarities = self.source_prototypes @ normalized
        scaled = similarities * 12.0
        scaled -= float(np.max(scaled))
        exp_scores = np.exp(scaled)
        total = float(np.sum(exp_scores))
        if total <= 0:
            return None
        return (exp_scores / total).astype(np.float32)

    def predict_from_pil(
        self,
        pil_image,
        use_tta: bool = False,
    ) -> Tuple[str, float, np.ndarray]:
        fallback = ("Unknown", 0.0, np.zeros(NUM_CLASSES, dtype=np.float32))
        if not self.loaded:
            return fallback

        try:
            import torch
            import torch.nn.functional as F
            from PIL import Image

            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            views = [pil_image]
            if use_tta:
                views.extend(
                    [
                        pil_image.transpose(Image.FLIP_LEFT_RIGHT),
                    ]
                )

            aligned_probs_per_view = []
            for image in views:
                tensor = self.transform(image).unsqueeze(0)
                with torch.no_grad():
                    logits, features = self._forward_logits_and_features(tensor, torch)

                temperature = max(
                    float(self.runtime_config.get("logit_temperature", 1.0)),
                    1e-6,
                )
                scaled_logits = logits / temperature
                source_probs = (
                    F.softmax(scaled_logits, dim=-1)[0].cpu().numpy().astype(np.float32)
                )
                prototype_probs = self._prototype_probabilities(
                    features[0].cpu().numpy().astype(np.float32)
                )
                prototype_weight = float(
                    self.runtime_config.get("prototype_blend_weight", 0.0)
                )
                logit_weight = float(
                    self.runtime_config.get("logit_blend_weight", 1.0)
                )
                if prototype_probs is not None and prototype_weight > 0:
                    source_probs = (
                        (logit_weight * source_probs)
                        + (prototype_weight * prototype_probs)
                    )
                    source_probs = source_probs / np.clip(np.sum(source_probs), 1e-8, None)

                aligned_probs_per_view.append(
                    align_probabilities(
                        source_probs,
                        self.source_label_map,
                        self.target_label_map,
                    )
                )

            probs = np.mean(np.stack(aligned_probs_per_view, axis=0), axis=0)

            predicted_class = int(np.argmax(probs))
            confidence = float(probs[predicted_class])
            disease_name = self.target_label_map.get(
                predicted_class,
                f"Disease_{predicted_class}",
            )

            return disease_name, confidence, probs

        except Exception as exc:
            print(f"[ResNet] Prediction error: {exc}")
            return fallback

    def predict_from_bytes(self, image_bytes: bytes) -> Tuple[str, float, np.ndarray]:
        try:
            from PIL import Image

            with Image.open(BytesIO(image_bytes)) as pil_image:
                return self.predict_from_pil(pil_image, use_tta=False)
        except Exception as exc:
            print(f"[ResNet] Bytes-to-image error: {exc}")
            return "Unknown", 0.0, np.zeros(NUM_CLASSES, dtype=np.float32)


_instance: Optional[ResNetImageModel] = None


def get_image_model(
    model_path: Path,
    dataset_dir: Optional[Path] = None,
) -> ResNetImageModel:
    global _instance
    if _instance is None:
        _instance = ResNetImageModel(model_path=model_path, dataset_dir=dataset_dir)
    return _instance
