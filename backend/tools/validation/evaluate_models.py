"""
Validation runner for the four core project components.

Goals:
1. Validate artifact integrity and label-space consistency.
2. Benchmark disease models on the research dataset.
3. Refuse to fabricate accuracy metrics for components that lack labeled data.
4. Produce a dermatologist-facing readiness summary.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from inference.config import (  # noqa: E402
    DISEASE_LABELS,
    DISTILBERT_MODEL_DIR,
    IMAGE_MODEL_PATH,
    RESEARCH_DATASET_DIR,
    SEVERITY_METADATA_PATH,
    SEVERITY_MODEL_PATH,
    SEVERITY_TRACK_DIR,
    SKIN_TYPE_LABEL_MAP_PATH,
    SKIN_TYPE_MODEL_PATH,
    SKIN_TYPE_DATASET_DIR,
)
from inference.label_space import canonicalize_label  # noqa: E402
from components.conversational_diagnosis_assistant.distilbert_model import (  # noqa: E402
    get_distilbert_model,
)
from components.conversational_diagnosis_assistant.knowledge_base import (  # noqa: E402
    EXPECTED_SYMPTOMS,
)
from components.multimodal_image_audio_diagnosis.image_model import (  # noqa: E402
    get_image_model,
)
from components.multimodal_image_audio_diagnosis.inference import (  # noqa: E402
    InferencePipeline,
)
from components.severity_assessment_tracking.severity_model import (  # noqa: E402
    get_severity_model,
)
from components.skin_type_skincare_recommendation.skin_type_model import (  # noqa: E402
    get_skin_type_model,
)


TARGET_INDEX = {label: index for index, label in DISEASE_LABELS.items()}


def confidence_summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "min": None, "max": None}
    return {
        "mean": round(float(statistics.fmean(values)), 4),
        "median": round(float(statistics.median(values)), 4),
        "min": round(float(min(values)), 4),
        "max": round(float(max(values)), 4),
    }


def expected_calibration_error(
    confidences: list[float],
    correctness: list[int],
    num_bins: int = 10,
) -> float | None:
    if not confidences or len(confidences) != len(correctness):
        return None

    ece = 0.0
    total = len(confidences)
    for bin_index in range(num_bins):
        lower = bin_index / num_bins
        upper = (bin_index + 1) / num_bins
        indices = [
            idx
            for idx, value in enumerate(confidences)
            if lower <= value < upper or (bin_index == num_bins - 1 and value == 1.0)
        ]
        if not indices:
            continue
        bin_conf = statistics.fmean(confidences[idx] for idx in indices)
        bin_acc = statistics.fmean(correctness[idx] for idx in indices)
        ece += (len(indices) / total) * abs(bin_acc - bin_conf)
    return round(float(ece), 4)


def multiclass_brier_score(probabilities: np.ndarray, true_index: int) -> float:
    target = np.zeros_like(probabilities, dtype=np.float32)
    if 0 <= true_index < len(target):
        target[true_index] = 1.0
    return float(np.mean((probabilities - target) ** 2))


def top_k_hit(probabilities: np.ndarray, true_label: str, k: int) -> bool:
    if probabilities.size == 0:
        return False
    top_indices = np.argsort(probabilities)[::-1][:k]
    labels = [DISEASE_LABELS.get(int(index), f"Disease_{index}") for index in top_indices]
    return true_label in labels


def iter_class_images(dataset_dir: Path, max_per_class: int) -> Iterable[tuple[str, Path]]:
    for class_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
        true_label = canonicalize_label(class_dir.name, DISEASE_LABELS)
        files = sorted(
            file_path
            for file_path in class_dir.iterdir()
            if file_path.is_file()
            and file_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        if max_per_class > 0:
            files = files[:max_per_class]
        for file_path in files:
            yield true_label, file_path


def collect_unlabeled_images(dataset_dir: Path, max_images: int) -> list[Path]:
    images: list[Path] = []
    if not dataset_dir.exists():
        return images

    for class_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
        for file_path in sorted(class_dir.iterdir()):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ):
                images.append(file_path)
                if len(images) >= max_images:
                    return images
    return images


def dataset_has_images(dataset_dir: Path) -> bool:
    if not dataset_dir.exists():
        return False
    for class_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
        for file_path in class_dir.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ):
                return True
    return False


def build_symptom_prompts() -> list[tuple[str, str]]:
    prompts: list[tuple[str, str]] = []
    templates = [
        "I have {symptoms} on my skin.",
        "My skin shows {symptoms}.",
        "I noticed {symptoms} for the last few days.",
    ]
    for disease in DISEASE_LABELS.values():
        symptoms = EXPECTED_SYMPTOMS.get(disease, [])
        symptom_words = [str(item).strip() for item in symptoms if str(item).strip()]
        if len(symptom_words) < 3:
            continue
        # Keep more symptom detail so closely related diseases such as
        # eczema and psoriasis are not collapsed into the same prompt.
        selected = symptom_words[: min(6, len(symptom_words))]
        joined = ", ".join(selected[:-1]) + f", and {selected[-1]}"
        for template in templates:
            prompts.append((disease, template.format(symptoms=joined)))
    return prompts


def readiness_status(
    *,
    loaded: bool,
    validation_available: bool,
    top1_accuracy: float | None,
    ece: float | None = None,
    exact_label_match: bool | None = None,
) -> str:
    if not loaded:
        return "not_loaded"
    if not validation_available:
        return "validation_missing"
    if exact_label_match is False:
        return "not_ready"
    if top1_accuracy is None:
        return "not_ready"
    if top1_accuracy < 0.75:
        return "not_ready"
    if ece is not None and ece > 0.15:
        return "needs_calibration"
    return "ready_for_internal_testing"


def evaluate_text_model(pipeline: InferencePipeline, text_model: Any) -> dict[str, Any]:
    prompts = build_symptom_prompts()
    exact_hits = 0
    top3_hits = 0
    confidences: list[float] = []
    correctness: list[int] = []
    brier_scores: list[float] = []
    per_class_totals: Counter[str] = Counter()
    per_class_hits: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []

    for expected, prompt in prompts:
        predicted, confidence, probabilities = pipeline._text_probs(prompt)
        expected_name = canonicalize_label(expected, DISEASE_LABELS)
        predicted_name = canonicalize_label(predicted, DISEASE_LABELS)
        true_index = TARGET_INDEX[expected_name]

        per_class_totals[expected_name] += 1
        confidences.append(float(confidence))

        is_exact = predicted_name == expected_name
        correctness.append(1 if is_exact else 0)
        brier_scores.append(multiclass_brier_score(np.asarray(probabilities), true_index))

        if is_exact:
            exact_hits += 1
            per_class_hits[expected_name] += 1
        if top_k_hit(np.asarray(probabilities), expected_name, 3):
            top3_hits += 1
        if not is_exact and len(failures) < 20:
            failures.append(
                {
                    "expected": expected_name,
                    "predicted": predicted_name,
                    "confidence": round(float(confidence), 4),
                    "prompt": prompt,
                }
            )

    per_class_accuracy = {
        label: round(per_class_hits[label] / total, 4)
        for label, total in sorted(per_class_totals.items())
        if total > 0
    }

    ece = expected_calibration_error(confidences, correctness)
    top1 = round(exact_hits / len(prompts), 4) if prompts else None
    runtime_exact_label_match = (
        True if pipeline.sklearn_loaded else text_model.label_integrity.get("is_exact_match")
    )
    runtime_label_integrity = {
        "runtime_mode": pipeline._text_model_mode(),
        "is_exact_match": bool(runtime_exact_label_match),
        "distilbert_exact_match": bool(
            text_model.label_integrity.get("is_exact_match", False)
        ),
        "uses_full_label_support_model": bool(pipeline.sklearn_loaded),
    }

    return {
        "status": readiness_status(
            loaded=bool(pipeline.distilbert_loaded or pipeline.sklearn_loaded),
            validation_available=bool(prompts),
            top1_accuracy=top1,
            ece=ece,
            exact_label_match=runtime_exact_label_match,
        ),
        "loaded": bool(pipeline.distilbert_loaded or pipeline.sklearn_loaded),
        "runtime_text_stack": {
            "distilbert_loaded": bool(pipeline.distilbert_loaded),
            "sklearn_loaded": bool(pipeline.sklearn_loaded),
            "mode": pipeline._text_model_mode(),
        },
        "runtime_label_integrity": runtime_label_integrity,
        "prompt_count": len(prompts),
        "top1_accuracy": top1,
        "top3_accuracy": round(top3_hits / len(prompts), 4) if prompts else None,
        "ece": ece,
        "mean_brier_score": round(float(statistics.fmean(brier_scores)), 4)
        if brier_scores
        else None,
        "confidence": confidence_summary(confidences),
        "artifact_label_integrity": text_model.label_integrity,
        "artifact_output_labels": len(getattr(text_model, "source_label_map", {})),
        "canonical_output_labels": len(getattr(text_model, "target_label_map", {})),
        "per_class_accuracy": per_class_accuracy,
        "sample_failures": failures,
    }


def evaluate_image_model(image_model: Any, dataset_dir: Path, max_per_class: int) -> dict[str, Any]:
    total = 0
    exact_hits = 0
    top3_hits = 0
    confidences: list[float] = []
    correctness: list[int] = []
    brier_scores: list[float] = []
    per_class_totals: Counter[str] = Counter()
    per_class_hits: Counter[str] = Counter()
    confusion_pairs: Counter[tuple[str, str]] = Counter()

    for true_label, file_path in iter_class_images(dataset_dir, max_per_class=max_per_class):
        with Image.open(file_path) as image:
            predicted, confidence, probabilities = image_model.predict_from_pil(
                image,
                use_tta=False,
            )

        predicted_name = canonicalize_label(predicted, DISEASE_LABELS)
        true_index = TARGET_INDEX[true_label]

        total += 1
        per_class_totals[true_label] += 1
        confidences.append(float(confidence))

        is_exact = predicted_name == true_label
        correctness.append(1 if is_exact else 0)
        brier_scores.append(multiclass_brier_score(np.asarray(probabilities), true_index))

        if is_exact:
            exact_hits += 1
            per_class_hits[true_label] += 1
        else:
            confusion_pairs[(true_label, predicted_name)] += 1

        if top_k_hit(np.asarray(probabilities), true_label, 3):
            top3_hits += 1

    per_class_accuracy = {
        label: round(per_class_hits[label] / total_count, 4)
        for label, total_count in sorted(per_class_totals.items())
        if total_count > 0
    }
    common_confusions = [
        {"true": true_label, "predicted": predicted_label, "count": count}
        for (true_label, predicted_label), count in confusion_pairs.most_common(15)
    ]

    ece = expected_calibration_error(confidences, correctness)
    top1 = round(exact_hits / total, 4) if total else None

    return {
        "status": readiness_status(
            loaded=bool(image_model.loaded),
            validation_available=total > 0,
            top1_accuracy=top1,
            ece=ece,
            exact_label_match=image_model.label_integrity.get("is_exact_match"),
        ),
        "loaded": bool(image_model.loaded),
        "dataset_dir": str(dataset_dir),
        "images_evaluated": total,
        "max_images_per_class": max_per_class,
        "top1_accuracy": top1,
        "top3_accuracy": round(top3_hits / total, 4) if total else None,
        "ece": ece,
        "mean_brier_score": round(float(statistics.fmean(brier_scores)), 4)
        if brier_scores
        else None,
        "confidence": confidence_summary(confidences),
        "artifact_label_integrity": image_model.label_integrity,
        "artifact_output_labels": len(getattr(image_model, "source_label_map", {})),
        "canonical_output_labels": len(getattr(image_model, "target_label_map", {})),
        "runtime_operating_point": getattr(image_model, "runtime_config", {}),
        "per_class_accuracy": per_class_accuracy,
        "top_confusions": common_confusions,
    }


def evaluate_fused_component(
    pipeline: InferencePipeline,
    dataset_dir: Path,
    max_per_class: int,
) -> dict[str, Any]:
    total = 0
    exact_hits = 0
    top3_hits = 0
    confidences: list[float] = []
    decision_modes: Counter[str] = Counter()
    failures: list[dict[str, Any]] = []

    prompt_by_label = {}
    for label, prompt in build_symptom_prompts():
        prompt_by_label.setdefault(label, prompt)

    for true_label, file_path in iter_class_images(dataset_dir, max_per_class=max_per_class):
        prompt = prompt_by_label.get(true_label)
        if not prompt:
            continue

        image_bytes = file_path.read_bytes()
        img_name, img_conf, img_probs = pipeline._image_probs(image_bytes)
        txt_name, txt_conf, txt_probs = pipeline._text_probs(prompt)
        have_img = pipeline.image_model_loaded and img_conf > 0
        have_txt = (pipeline.distilbert_loaded or pipeline.sklearn_loaded) and txt_conf > 0

        image_alpha = pipeline._compute_dynamic_alpha(
            img_conf,
            txt_conf,
            have_img,
            have_txt,
            txt_probs,
        )
        fused_probs = pipeline._fuse(
            img_probs,
            txt_probs,
            have_img,
            have_txt,
            image_alpha,
        )
        fused_probs = pipeline._apply_fusion_clinical_rules(
            prompt,
            fused_probs,
            img_name,
            txt_name,
            img_conf,
            txt_conf,
        )
        top_indices = np.argsort(fused_probs)[::-1][:3]
        predicted = DISEASE_LABELS.get(int(top_indices[0]), "Unknown")
        confidence = float(fused_probs[top_indices[0]])
        decision_mode = pipeline._determine_decision_mode(
            img_conf,
            txt_conf,
            have_img,
            have_txt,
            image_alpha,
        )

        total += 1
        confidences.append(confidence)
        decision_modes[decision_mode] += 1

        if predicted == true_label:
            exact_hits += 1
        elif len(failures) < 20:
            failures.append(
                {
                    "expected": true_label,
                    "predicted": predicted,
                    "confidence": round(confidence, 4),
                    "decision_mode": decision_mode,
                    "image_prediction": img_name,
                    "text_prediction": txt_name,
                    "file": str(file_path),
                }
            )

        if top_k_hit(np.asarray(fused_probs), true_label, 3):
            top3_hits += 1

    top1 = round(exact_hits / total, 4) if total else None

    return {
        "status": readiness_status(
            loaded=bool(
                pipeline.image_model_loaded
                and (pipeline.distilbert_loaded or pipeline.sklearn_loaded)
            ),
            validation_available=total > 0,
            top1_accuracy=top1,
        ),
        "available": bool(
            pipeline.image_model_loaded
            and (pipeline.distilbert_loaded or pipeline.sklearn_loaded)
        ),
        "samples_evaluated": total,
        "max_images_per_class": max_per_class,
        "top1_accuracy": top1,
        "top3_accuracy": round(top3_hits / total, 4) if total else None,
        "confidence": confidence_summary(confidences),
        "decision_modes": dict(sorted(decision_modes.items())),
        "sample_failures": failures,
    }


def evaluate_skin_type_component(
    model: Any,
    dataset_dir: Path,
) -> dict[str, Any]:
    class_dirs = (
        sorted(path for path in dataset_dir.iterdir() if path.is_dir())
        if dataset_dir.exists()
        else []
    )
    label_map = getattr(model, "label_map", {})
    valid_skin_types = {str(label).strip().replace("_", " ").title() for label in label_map.keys()}

    if not class_dirs:
        sampled_images = collect_unlabeled_images(RESEARCH_DATASET_DIR, max_images=60)
        if not sampled_images:
            return {
                "status": "validation_missing",
                "loaded": bool(model.loaded),
                "validation_available": False,
                "note": (
                    "No labeled skin-type image dataset is stored locally and no fallback "
                    "sample images were available for operational checks."
                ),
                "label_map": label_map,
            }

        valid_output = 0
        confidence_valid = 0
        prediction_counts: Counter[str] = Counter()
        failures: list[dict[str, Any]] = []
        confidences: list[float] = []

        for file_path in sampled_images:
            with Image.open(file_path) as image:
                result = model.predict_from_pil(image)
            predicted = str(result.get("skin_type", "Unknown")).strip()
            confidence = float(result.get("confidence", 0.0))
            prediction_counts[predicted] += 1
            confidences.append(confidence)

            if predicted in valid_skin_types:
                valid_output += 1
            if 0.0 <= confidence <= 1.0:
                confidence_valid += 1

            if (predicted not in valid_skin_types or not (0.0 <= confidence <= 1.0)) and len(failures) < 15:
                failures.append(
                    {
                        "file": str(file_path),
                        "predicted": predicted,
                        "confidence": round(confidence, 4),
                    }
                )

        output_valid_rate = valid_output / len(sampled_images)
        confidence_valid_rate = confidence_valid / len(sampled_images)
        operational_pass = (
            bool(model.loaded)
            and output_valid_rate >= 0.98
            and confidence_valid_rate >= 1.0
        )

        return {
            "status": "operational_only_unlabeled" if operational_pass else "not_ready",
            "loaded": bool(model.loaded),
            "validation_available": False,
            "note": (
                "No labeled skin-type benchmark is available. Reported metrics are "
                "operational reliability checks only."
            ),
            "operational_check": {
                "samples_tested": len(sampled_images),
                "output_valid_rate": round(output_valid_rate, 4),
                "confidence_valid_rate": round(confidence_valid_rate, 4),
                "prediction_distribution": dict(sorted(prediction_counts.items())),
            },
            "confidence": confidence_summary(confidences),
            "label_map": label_map,
            "sample_failures": failures,
        }

    total = 0
    exact_hits = 0
    confidences: list[float] = []
    failures: list[dict[str, Any]] = []

    for class_dir in class_dirs:
        expected = class_dir.name.strip().replace("_", " ").title()
        for file_path in sorted(class_dir.iterdir()):
            if not file_path.is_file() or file_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            with Image.open(file_path) as image:
                result = model.predict_from_pil(image)
            predicted = str(result.get("skin_type", "Unknown"))
            confidence = float(result.get("confidence", 0.0))

            total += 1
            confidences.append(confidence)
            if predicted == expected:
                exact_hits += 1
            elif len(failures) < 20:
                failures.append(
                    {
                        "expected": expected,
                        "predicted": predicted,
                        "confidence": round(confidence, 4),
                        "file": str(file_path),
                    }
                )

    top1 = round(exact_hits / total, 4) if total else None
    return {
        "status": readiness_status(
            loaded=bool(model.loaded),
            validation_available=total > 0,
            top1_accuracy=top1,
        ),
        "loaded": bool(model.loaded),
        "validation_available": True,
        "samples_evaluated": total,
        "top1_accuracy": top1,
        "confidence": confidence_summary(confidences),
        "label_map": label_map,
        "sample_failures": failures,
    }


def evaluate_severity_component(
    model: Any,
    tracking_dir: Path,
) -> dict[str, Any]:
    visits_path = tracking_dir / "visits.csv"
    rows = 0
    if visits_path.exists():
        try:
            rows = max(0, len(visits_path.read_text(encoding="utf-8").splitlines()) - 1)
        except Exception:
            rows = 0

    threshold_valid = float(model.threshold_q1) < float(model.threshold_q2)
    expected_levels = [str(level).strip().lower() for level in getattr(model, "severity_levels", [])]

    artifact_checks = {
        "threshold_order_valid": threshold_valid,
        "severity_levels": expected_levels,
        "feature_columns": list(getattr(model, "feature_cols", [])),
        "tracking_history_rows": rows,
    }

    sampled_images = collect_unlabeled_images(RESEARCH_DATASET_DIR, max_images=60)
    if not sampled_images:
        return {
            "status": "validation_missing",
            "loaded": bool(model.loaded),
            "validation_available": False,
            "note": (
                "No labeled image-level severity benchmark is stored locally and no "
                "fallback sample images were available for operational checks."
            ),
            "artifact_checks": artifact_checks,
        }

    valid_schema = 0
    confidence_valid = 0
    agreement_count = 0
    face_visible_count = 0
    severity_levels: Counter[str] = Counter()
    confidences: list[float] = []
    failures: list[dict[str, Any]] = []

    for file_path in sampled_images:
        with Image.open(file_path) as image:
            result = model.predict_from_pil(image)

        level = str(result.get("severity_level", "")).strip().lower()
        score_level = str(result.get("score_based_level", "")).strip().lower()
        confidence = float(result.get("confidence", 0.0))
        face_visible = result.get("preprocessing", {}).get("face_visible", None)

        has_required_fields = (
            "severity_level" in result
            and "severity_score" in result
            and "confidence" in result
            and "preprocessing" in result
        )
        if has_required_fields:
            valid_schema += 1
        if 0.0 <= confidence <= 1.0:
            confidence_valid += 1
        if level == score_level:
            agreement_count += 1
        if face_visible is True:
            face_visible_count += 1
        confidences.append(confidence)
        severity_levels[level] += 1

        if (not has_required_fields or not (0.0 <= confidence <= 1.0)) and len(failures) < 15:
            failures.append(
                {
                    "file": str(file_path),
                    "severity_level": result.get("severity_level"),
                    "score_based_level": result.get("score_based_level"),
                    "confidence": round(confidence, 4),
                }
            )

    sample_count = len(sampled_images)
    schema_rate = valid_schema / sample_count
    confidence_rate = confidence_valid / sample_count
    agreement_rate = agreement_count / sample_count
    face_visible_rate = face_visible_count / sample_count

    operational_pass = (
        bool(model.loaded)
        and threshold_valid
        and schema_rate >= 1.0
        and confidence_rate >= 1.0
        and agreement_rate >= 0.85
    )

    return {
        "status": "operational_only_unlabeled" if operational_pass else "not_ready",
        "loaded": bool(model.loaded),
        "validation_available": False,
        "note": (
            "No labeled image-level severity benchmark is available. Reported metrics "
            "are operational reliability checks only."
        ),
        "artifact_checks": artifact_checks,
        "operational_check": {
            "samples_tested": sample_count,
            "schema_valid_rate": round(schema_rate, 4),
            "confidence_valid_rate": round(confidence_rate, 4),
            "model_score_agreement_rate": round(agreement_rate, 4),
            "face_visible_rate": round(face_visible_rate, 4),
            "severity_distribution": dict(sorted(severity_levels.items())),
        },
        "confidence": confidence_summary(confidences),
        "sample_failures": failures,
    }


def build_report(
    image_limit: int,
    fused_limit: int,
) -> dict[str, Any]:
    text_model = get_distilbert_model(DISTILBERT_MODEL_DIR)
    image_model = get_image_model(IMAGE_MODEL_PATH, dataset_dir=RESEARCH_DATASET_DIR)
    skin_type_model = get_skin_type_model(SKIN_TYPE_MODEL_PATH, SKIN_TYPE_LABEL_MAP_PATH)
    severity_model = get_severity_model(SEVERITY_MODEL_PATH, SEVERITY_METADATA_PATH)
    pipeline = InferencePipeline()

    text_component = evaluate_text_model(pipeline, text_model)
    image_component = evaluate_image_model(
        image_model,
        RESEARCH_DATASET_DIR,
        max_per_class=image_limit,
    )
    fused_component = evaluate_fused_component(
        pipeline,
        RESEARCH_DATASET_DIR,
        max_per_class=fused_limit,
    )
    skin_type_component = evaluate_skin_type_component(
        skin_type_model,
        SKIN_TYPE_DATASET_DIR,
    )
    severity_component = evaluate_severity_component(
        severity_model,
        SEVERITY_TRACK_DIR,
    )

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "dataset_availability": {
            "research_dataset_exists": dataset_has_images(RESEARCH_DATASET_DIR),
            "skin_type_dataset_exists": dataset_has_images(SKIN_TYPE_DATASET_DIR),
            "severity_tracking_exists": SEVERITY_TRACK_DIR.exists(),
        },
        "limits": {
            "image_max_per_class": image_limit,
            "fused_max_per_class": fused_limit,
        },
        "artifact_integrity": {
            "text_label_integrity": text_component.get("artifact_label_integrity", {}),
            "text_runtime_label_integrity": text_component.get("runtime_label_integrity", {}),
            "image_label_integrity": image_component.get("artifact_label_integrity", {}),
            "skin_type_label_map": skin_type_component.get("label_map", {}),
            "severity_artifact_checks": severity_component.get("artifact_checks", {}),
        },
        "text_component": text_component,
        "image_component": image_component,
        "fused_component": fused_component,
        "skin_type_component": skin_type_component,
        "severity_component": severity_component,
        "deployment_readiness": {
            "text_component": text_component["status"],
            "image_component": image_component["status"],
            "fused_component": fused_component["status"],
            "skin_type_component": skin_type_component["status"],
            "severity_component": severity_component["status"],
        },
    }


def print_summary(report: dict[str, Any]) -> None:
    text = report["text_component"]
    image = report["image_component"]
    fused = report["fused_component"]
    skin_type = report["skin_type_component"]
    severity = report["severity_component"]

    print("\n=== MODEL VALIDATION SUMMARY ===")
    print(
        f"Text: status={text['status']} top1={text.get('top1_accuracy')} "
        f"top3={text.get('top3_accuracy')} ece={text.get('ece')}"
    )
    print(
        f"Image: status={image['status']} top1={image.get('top1_accuracy')} "
        f"top3={image.get('top3_accuracy')} ece={image.get('ece')}"
    )
    print(
        f"Fused: status={fused['status']} top1={fused.get('top1_accuracy')} "
        f"top3={fused.get('top3_accuracy')}"
    )
    print(f"Skin type: status={skin_type['status']} note={skin_type.get('note')}")
    print(f"Severity: status={severity['status']} note={severity.get('note')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SkinAI model components.")
    parser.add_argument(
        "--image-max-per-class",
        type=int,
        default=40,
        help="Number of research_dataset images per class for image-only evaluation.",
    )
    parser.add_argument(
        "--fused-max-per-class",
        type=int,
        default=8,
        help="Number of research_dataset images per class for fused evaluation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_DIR / "reports" / "validation_report.json",
        help="Path to save the JSON validation report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        image_limit=args.image_max_per_class,
        fused_limit=args.fused_max_per_class,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print_summary(report)
    print(f"\nSaved report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
