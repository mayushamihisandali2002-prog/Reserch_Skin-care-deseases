"""
Utilities for aligning model output label spaces to the application's
canonical disease label space.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np


COMMON_DISEASE_ALIASES: dict[str, str] = {
    "pigmentation dark spots": "Pigmentation / Dark Spots",
    "pigmentation spots": "Pigmentation / Dark Spots",
    "dark spots": "Pigmentation / Dark Spots",
    "basal cell carcinoma": "Basal Cell Carcinoma",
    "actinic keratosis": "Actinic Keratosis",
    "alopecia areata": "Alopecia Areata",
    "cherry angioma": "Cherry Angioma",
    "hidradenitis suppurativa": "Hidradenitis Suppurativa",
    "lichen planus": "Lichen Planus",
    "melanocytic nevi": "Melanocytic Nevi",
    "molluscum contagiosum": "Molluscum Contagiosum",
    "pityriasis versicolor": "Pityriasis Versicolor",
    "seborrheic dermatitis": "Seborrheic Dermatitis",
    "seborrheic keratosis": "Seborrheic Keratosis",
    "herpes simplex": "Herpes Simplex",
}


def normalize_label(value: str) -> str:
    lowered = value.strip().lower()
    lowered = lowered.replace("/", " ")
    lowered = lowered.replace("-", " ")
    lowered = lowered.replace("(", " ")
    lowered = lowered.replace(")", " ")
    lowered = lowered.replace("__", "_")
    lowered = lowered.replace("___", "_")
    tokens = [token for token in lowered.replace("_", " ").split() if token]
    return " ".join(tokens)


def build_alias_lookup(target_label_map: Mapping[int, str]) -> dict[str, str]:
    aliases = {normalize_label(label): label for label in target_label_map.values()}
    for alias, canonical in COMMON_DISEASE_ALIASES.items():
        if canonical in target_label_map.values():
            aliases[normalize_label(alias)] = canonical
    return aliases


def canonicalize_label(raw_label: str, target_label_map: Mapping[int, str]) -> str:
    aliases = build_alias_lookup(target_label_map)
    normalized = normalize_label(raw_label)
    return aliases.get(normalized, raw_label.replace("_", " ").strip())


def load_hf_id2label(
    model_dir: Path,
    fallback_label_map: Mapping[int, str],
) -> dict[int, str]:
    config_path = model_dir / "config.json"
    if not config_path.exists():
        return dict(fallback_label_map)

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        id2label = raw.get("id2label", {})
        if not isinstance(id2label, dict) or not id2label:
            return dict(fallback_label_map)

        return {
            int(index): canonicalize_label(str(label), fallback_label_map)
            for index, label in sorted(id2label.items(), key=lambda item: int(item[0]))
        }
    except Exception:
        return dict(fallback_label_map)


def build_dataset_label_map(
    dataset_dir: Path,
    fallback_label_map: Mapping[int, str],
) -> dict[int, str]:
    if not dataset_dir.exists():
        return dict(fallback_label_map)

    class_dirs = sorted(path for path in dataset_dir.iterdir() if path.is_dir())
    if not class_dirs:
        return dict(fallback_label_map)

    return {
        index: canonicalize_label(class_dir.name, fallback_label_map)
        for index, class_dir in enumerate(class_dirs)
    }


def align_probabilities(
    source_probs: np.ndarray,
    source_label_map: Mapping[int, str],
    target_label_map: Mapping[int, str],
) -> np.ndarray:
    aligned = np.zeros(len(target_label_map), dtype=np.float32)
    target_indices = {label: index for index, label in target_label_map.items()}

    for source_index, label in source_label_map.items():
        if source_index >= len(source_probs):
            continue
        target_index = target_indices.get(label)
        if target_index is None:
            continue
        aligned[target_index] += float(source_probs[source_index])

    return aligned


def label_map_coverage(
    source_label_map: Mapping[int, str],
    target_label_map: Mapping[int, str],
) -> dict[str, object]:
    source_labels = set(source_label_map.values())
    target_labels = set(target_label_map.values())
    missing = sorted(target_labels - source_labels)
    extra = sorted(source_labels - target_labels)

    return {
        "source_label_count": len(source_label_map),
        "target_label_count": len(target_label_map),
        "covered_label_count": len(source_labels & target_labels),
        "missing_labels": missing,
        "unexpected_labels": extra,
        "is_exact_match": not missing and not extra,
    }
