import datetime
import json
import logging
import csv
import os
import shutil
from pathlib import Path

from flask import jsonify, request, send_from_directory

from inference.config import (
    SEVERITY_METADATA_PATH,
    SEVERITY_MODEL_PATH,
    SEVERITY_TRACK_DIR,
    SEVERITY_UPLOADS_DIR,
)

from services.supabase_service import SupabaseService

from . import get_severity_model
from services.gemini_service import GeminiService


logger = logging.getLogger(__name__)


SEVERITY_TRACK_PATH = Path(SEVERITY_TRACK_DIR)
LEGACY_SEVERITY_VISITS_CSV = SEVERITY_TRACK_PATH / "visits.csv"
LEGACY_SEVERITY_WEEKS_JSON = SEVERITY_TRACK_PATH / "_weeks.json"
SEVERITY_VISITS_CSV = SEVERITY_TRACK_PATH / os.getenv(
    "SEVERITY_VISITS_FILENAME",
    "visits.runtime.csv",
)
SEVERITY_WEEKS_JSON = SEVERITY_TRACK_PATH / os.getenv(
    "SEVERITY_WEEKS_FILENAME",
    "_weeks.runtime.json",
)
SEVERITY_VISIT_FIELDS = [
    "timestamp",
    "user_id",
    "journey_id",
    "severity_level",
    "severity_score",
    "confidence",
    "metrics_json",
    "image_path",
]


def _bootstrap_runtime_tracking_files() -> None:
    SEVERITY_TRACK_PATH.mkdir(parents=True, exist_ok=True)

    if (
        SEVERITY_VISITS_CSV != LEGACY_SEVERITY_VISITS_CSV
        and not SEVERITY_VISITS_CSV.exists()
        and LEGACY_SEVERITY_VISITS_CSV.exists()
    ):
        shutil.copyfile(LEGACY_SEVERITY_VISITS_CSV, SEVERITY_VISITS_CSV)

    if (
        SEVERITY_WEEKS_JSON != LEGACY_SEVERITY_WEEKS_JSON
        and not SEVERITY_WEEKS_JSON.exists()
        and LEGACY_SEVERITY_WEEKS_JSON.exists()
    ):
        shutil.copyfile(LEGACY_SEVERITY_WEEKS_JSON, SEVERITY_WEEKS_JSON)


def _normalize_confidence_level(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.50:
        return "moderate"
    return "low"


def _sorted_probability_pairs(probabilities: dict[str, float]) -> list[tuple[str, float]]:
    pairs: list[tuple[str, float]] = []
    if not isinstance(probabilities, dict):
        return pairs

    for key, value in probabilities.items():
        try:
            pairs.append((str(key).strip(), float(value)))
        except Exception:
            continue
    pairs.sort(key=lambda item: item[1], reverse=True)
    return pairs


def _top_probability_gap(probabilities: dict[str, float]) -> float:
    pairs = _sorted_probability_pairs(probabilities)
    if len(pairs) < 2:
        return pairs[0][1] if pairs else 0.0
    return max(0.0, float(pairs[0][1]) - float(pairs[1][1]))


def _top_predictions(probabilities: dict[str, float], limit: int = 3) -> list[dict[str, float | str]]:
    pairs = _sorted_probability_pairs(probabilities)[:limit]
    return [
        {
            "label": label,
            "probability": round(float(probability), 4),
        }
        for label, probability in pairs
    ]


def _build_severity_review(
    *,
    confidence: float,
    top_gap: float,
    face_visible: object,
    consistency_warning: str | None,
) -> tuple[bool, list[str], list[str], str]:
    reasons: list[str] = []
    next_steps: list[str] = []

    if face_visible is False:
        reasons.append("No face detected, but this model is calibrated for face images")
    if confidence < 0.45:
        reasons.append("Low severity confidence")
    if top_gap < 0.12:
        reasons.append("Severity class probabilities are too close")
    if consistency_warning:
        reasons.append("Model class and score-derived level disagreed")

    if face_visible is False:
        analysis_scope = "face_model_out_of_scope"
        next_steps.append("Upload a clear front-facing photo before using severity grading or tracking.")
    else:
        analysis_scope = "severity_screening_only"

    if confidence < 0.45 or top_gap < 0.12:
        next_steps.append("Retake the photo in even light with the full affected facial area clearly visible.")
    next_steps.append("Use this result as a screening/tracking aid only, not a standalone clinical decision.")
    next_steps.append("If redness, swelling, pain, discharge, or rapid worsening is present, seek clinician review.")

    return (
        len(reasons) > 0,
        reasons,
        list(dict.fromkeys(next_steps))[:4],
        analysis_scope,
    )


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _normalize_severity_level(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "medium":
        return "moderate"
    if normalized in {"mild", "moderate", "severe"}:
        return normalized
    return "moderate"


def _parse_track_flag(raw_value: str | None) -> bool:
    if raw_value is None:
        return False
    value = str(raw_value).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _severity_metrics_from_features(features: dict[str, float] | None = None) -> dict[str, float]:
    feature_map = features or {}
    return {
        "redness": round(_safe_float(feature_map.get("redness_index"), 0.0) * 100, 1),
        "inflammation": round(_safe_float(feature_map.get("saturation_mean"), 0.0) * 100, 1),
        "scaling": round(_safe_float(feature_map.get("edge_density"), 0.0) * 100, 1),
        "texture": round(_safe_float(feature_map.get("texture_entropy"), 0.0) * 10, 1),
    }


def _parse_metrics_json(value: object) -> dict[str, float]:
    if isinstance(value, dict):
        raw = value
    else:
        try:
            raw = json.loads(str(value or "{}"))
        except Exception:
            raw = {}

    return {
        "redness": round(_safe_float(raw.get("redness"), 0.0), 1),
        "inflammation": round(_safe_float(raw.get("inflammation"), 0.0), 1),
        "scaling": round(_safe_float(raw.get("scaling"), 0.0), 1),
        "texture": round(_safe_float(raw.get("texture"), 0.0), 1),
    }


def _normalize_user_and_journey_ids(
    user_id: object,
    journey_id: object = None,
) -> tuple[str, str | None]:
    normalized_user_id = str(user_id or "anonymous").strip() or "anonymous"
    normalized_journey_id = str(journey_id or "").strip() or None
    return normalized_user_id, normalized_journey_id


def _row_timestamp(row: dict) -> str:
    return str(row.get("captured_at") or row.get("timestamp") or "")


def _ensure_visits_csv_schema() -> None:
    _bootstrap_runtime_tracking_files()
    if not SEVERITY_VISITS_CSV.exists():
        return

    with open(SEVERITY_VISITS_CSV, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return

    normalized_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        if not row:
            continue

        if len(row) == 6:
            normalized_rows.append(
                {
                    "timestamp": row[0],
                    "user_id": row[1],
                    "journey_id": "",
                    "severity_level": row[2],
                    "severity_score": row[3],
                    "confidence": row[4],
                    "metrics_json": row[5],
                    "image_path": "",
                }
            )
            continue

        if len(row) == 7:
            normalized_rows.append(
                {
                    "timestamp": row[0],
                    "user_id": row[1],
                    "journey_id": row[2],
                    "severity_level": row[3],
                    "severity_score": row[4],
                    "confidence": row[5],
                    "metrics_json": row[6],
                    "image_path": "",
                }
            )
            continue

        padded = list(row[: len(SEVERITY_VISIT_FIELDS)])
        if len(padded) < len(SEVERITY_VISIT_FIELDS):
            padded.extend([""] * (len(SEVERITY_VISIT_FIELDS) - len(padded)))

        journey_id = padded[2]
        severity_level = padded[3]
        severity_score = padded[4]
        confidence = padded[5]
        metrics_json = padded[6]

        looks_shifted = (
            str(journey_id).strip().lower() in {"mild", "moderate", "severe"}
            and str(severity_level).strip() != ""
            and str(confidence).strip() == ""
        )
        if looks_shifted:
            journey_id = ""
            severity_level = padded[2]
            severity_score = padded[3]
            confidence = padded[4]
            metrics_json = padded[5] or padded[6]

        normalized_rows.append(
            {
                "timestamp": padded[0],
                "user_id": padded[1],
                "journey_id": journey_id,
                "severity_level": severity_level,
                "severity_score": severity_score,
                "confidence": confidence,
                "metrics_json": metrics_json,
                "image_path": padded[7] if len(padded) > 7 else "",
            }
        )

    with open(SEVERITY_VISITS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SEVERITY_VISIT_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_rows)


def _append_severity_visit(
    user_id: str,
    severity_level: str,
    severity_score: float,
    confidence: float,
    journey_id: str | None = None,
    features: dict[str, float] = None,
    metrics: dict[str, float] | None = None,
    metadata: dict | None = None,
    image_path: str = "",
) -> dict[str, str]:
    user_id, journey_id = _normalize_user_and_journey_ids(user_id, journey_id)
    normalized_level = _normalize_severity_level(severity_level)
    timestamp = datetime.datetime.now().isoformat()
    persisted_metrics = _parse_metrics_json(metrics) if metrics is not None else _severity_metrics_from_features(features)
    persisted_metadata = metadata or {}

    if user_id and user_id != "anonymous":
        try:
            SupabaseService.save_severity_visit(
                user_id=user_id,
                journey_id=journey_id,
                severity_level=normalized_level,
                severity_score=severity_score,
                confidence=confidence,
                metrics=persisted_metrics,
                metadata={**persisted_metadata, "image_path": image_path},
                captured_at=timestamp,
            )
            return {"storage_backend": "supabase", "timestamp": timestamp}
        except Exception as exc:
            logger.warning("Supabase severity visit save failed, falling back to CSV: %s", exc)

    SEVERITY_TRACK_PATH.mkdir(parents=True, exist_ok=True)
    _ensure_visits_csv_schema()

    file_exists = SEVERITY_VISITS_CSV.exists()

    with open(SEVERITY_VISITS_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=SEVERITY_VISIT_FIELDS,
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": timestamp,
                "user_id": user_id,
                "journey_id": journey_id or "",
                "severity_level": normalized_level,
                "severity_score": f"{severity_score:.4f}",
                "confidence": f"{confidence:.6f}",
                "metrics_json": json.dumps(persisted_metrics),
                "image_path": image_path,
            }
        )
    return {"storage_backend": "csv", "timestamp": timestamp}


def _load_csv_severity_rows(user_id: str, journey_id: str | None = None) -> list[dict]:
    if not SEVERITY_VISITS_CSV.exists():
        return []

    _ensure_visits_csv_schema()
    rows: list[dict] = []
    with open(SEVERITY_VISITS_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("user_id") or "anonymous") != user_id:
                continue
            if journey_id and (row.get("journey_id") or "").strip() != journey_id:
                continue
            rows.append(row)
    return rows


def _load_severity_rows(user_id: str, journey_id: str | None = None) -> tuple[list[dict], str]:
    if user_id and user_id != "anonymous":
        try:
            supabase_rows = SupabaseService.get_severity_visits(
                user_id=user_id,
                journey_id=journey_id,
            )
            if supabase_rows:
                return supabase_rows, "supabase"
        except Exception as exc:
            logger.warning("Supabase severity history unavailable, falling back to CSV: %s", exc)

    return _load_csv_severity_rows(user_id, journey_id=journey_id), "csv"


def _build_severity_tracking_summary(user_id: str, journey_id: str | None = None) -> dict:
    rows, storage_backend = _load_severity_rows(user_id, journey_id=journey_id)
    if not rows:
        return {
            "visits_count": 0,
            "improvement_percent": 0.0,
            "weekly_trend": [],
            "latest_visit": None,
            "storage_backend": storage_backend,
            "storage_fallback_used": storage_backend != "supabase",
            "files": {
                "visits_csv": str(SEVERITY_VISITS_CSV),
                "weeks_json": str(SEVERITY_WEEKS_JSON),
            } if storage_backend == "csv" else {},
        }

    rows.sort(key=_row_timestamp)

    first_score = _safe_float(rows[0].get("severity_score"), 0.0)
    latest_score = _safe_float(rows[-1].get("severity_score"), 0.0)
    improvement_percent = ((first_score - latest_score) / first_score) * 100.0 if first_score > 0 else 0.0

    week_scores: dict[str, list[float]] = {}
    for row in rows:
        ts = _row_timestamp(row)
        score = _safe_float(row.get("severity_score"), 0.0)
        try:
            dt = datetime.datetime.fromisoformat(ts)
            iso = dt.isocalendar()
            week_key = f"{iso.year}-W{iso.week:02d}"
        except Exception:
            week_key = "unknown-week"
        week_scores.setdefault(week_key, []).append(score)

    weekly_trend = []
    for week_key in sorted(week_scores.keys()):
        scores = week_scores[week_key]
        avg_score = float(sum(scores) / max(1, len(scores)))
        weekly_trend.append({"week": week_key, "avg_severity_score": round(avg_score, 2)})

    if storage_backend == "csv":
        payload = {
            "updated_at": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "weekly_trend": weekly_trend,
        }
        SEVERITY_TRACK_PATH.mkdir(parents=True, exist_ok=True)
        with open(SEVERITY_WEEKS_JSON, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    latest = rows[-1]
    return {
        "visits_count": len(rows),
        "improvement_percent": round(float(improvement_percent), 2),
        "weekly_trend": weekly_trend,
        "latest_visit": {
            "timestamp": _row_timestamp(latest),
            "severity_level": latest.get("severity_level"),
            "severity_score": round(_safe_float(latest.get("severity_score"), 0.0), 2),
            "confidence": round(_safe_float(latest.get("confidence"), 0.0), 4),
        },
        "storage_backend": storage_backend,
        "storage_fallback_used": storage_backend != "supabase",
        "files": {
            "visits_csv": str(SEVERITY_VISITS_CSV),
            "weeks_json": str(SEVERITY_WEEKS_JSON),
        } if storage_backend == "csv" else {},
    }


def _load_real_history(user_id: str, journey_id: str | None = None) -> tuple[list[dict], str]:
    """Read severity visits from persistent storage and format for frontend history."""
    rows, storage_backend = _load_severity_rows(user_id, journey_id=journey_id)
    if not rows:
        return [], storage_backend

    history: list[dict] = []
    try:
        rows.sort(key=_row_timestamp)
        recent_rows = rows[-10:]
        start_index = len(rows) - len(recent_rows)
        for i, row in enumerate(recent_rows):
            ts = _row_timestamp(row)
            metrics = _parse_metrics_json(row.get("metrics_json"))
            saved_path = row.get("image_path")
            image_url = f"/api/severity/uploads/{os.path.basename(saved_path)}" if saved_path else "assets/images/severity_log.png"
            
            history.append({
                "week": f"Visit {start_index + i + 1}",
                "date": ts.split("T")[0] if "T" in ts else ts,
                "image_url": image_url,
                "status": row.get("severity_level", "Unknown"),
                "score": int(round(_safe_float(row.get("severity_score")))),
                "metrics": metrics,
            })
    except Exception as exc:
        logger.error("Failed to load real severity history: %s", exc)
        return [], storage_backend

    return history, storage_backend


def register_routes(app) -> None:
    """
    Severity assessment and tracking routes.
    """

    @app.route("/api/analyze-severity", methods=["POST", "OPTIONS"])
    def analyze_severity():
        if request.method == "OPTIONS":
            return "", 204

        model = get_severity_model(
            model_path=SEVERITY_MODEL_PATH,
            metadata_path=SEVERITY_METADATA_PATH,
        )
        if model is None or not model.loaded:
            try:
                model = get_severity_model(
                    model_path=SEVERITY_MODEL_PATH,
                    metadata_path=SEVERITY_METADATA_PATH,
                    force_reload=True,
                )
            except Exception:
                model = None

        if model is None or not model.loaded:
            return jsonify(
                {
                    "error": "Severity model unavailable",
                    "detail": None if model is None else model.load_error,
                }
            ), 503

        image_file = request.files.get("image") or request.files.get("file")
        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        filename = (image_file.filename or "").strip()
        suffix = Path(filename).suffix.lower()
        allowed_suffixes = {".jpg", ".jpeg", ".png"}
        if suffix and suffix not in allowed_suffixes:
            return jsonify(
                {
                    "error": "Unsupported image format",
                    "detail": "Allowed formats: .jpg, .jpeg, .png",
                }
            ), 400

        try:
            image_data = image_file.read()
            prediction = model.predict_from_bytes(image_data)
        except Exception as exc:
            msg = str(exc)
            if "cannot identify image file" in msg.lower():
                return jsonify({"error": "Invalid image file format", "detail": msg}), 400
            logger.exception("Severity prediction failed")
            return jsonify({"error": f"Severity prediction failed: {exc}"}), 500

        # Save image for tracking if enabled
        saved_image_path = ""
        tracking_requested = _parse_track_flag(request.form.get("track") or request.args.get("track"))
        if tracking_requested:
            try:
                SEVERITY_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_user = "".join([c for c in (request.form.get("user_id") or "anon") if c.isalnum()])
                unique_name = f"{ts_str}_{safe_user}{suffix or '.jpg'}"
                dest_path = SEVERITY_UPLOADS_DIR / unique_name
                with open(dest_path, "wb") as f:
                    f.write(image_data)
                saved_image_path = f"uploads/severity/{unique_name}"
                logger.info("Saved severity tracking image to %s", saved_image_path)
            except Exception as e:
                logger.warning("Failed to save tracking image: %s", e)

        severity_level = str(prediction.get("severity_level", "Moderate"))
        severity_score = _safe_float(prediction.get("severity_score"), 0.0)
        confidence = _safe_float(prediction.get("confidence"), 0.0)
        probabilities = prediction.get("probabilities", {}) or {}
        top_gap = _top_probability_gap(probabilities)
        top_predictions = _top_predictions(probabilities)
        preprocessing = prediction.get("preprocessing", {}) or {}
        face_visible = preprocessing.get("face_visible")
        consistency_warning = prediction.get("consistency_warning")
        requires_review, review_reasons, next_steps, analysis_scope = _build_severity_review(
            confidence=confidence,
            top_gap=top_gap,
            face_visible=face_visible,
            consistency_warning=consistency_warning,
        )
        confidence_level = _normalize_confidence_level(confidence)
        limitations = [
            "No labeled image-level severity benchmark is stored locally for this model, so only operational reliability checks are available.",
            "This severity model is calibrated primarily for frontal face images and becomes unreliable outside that scope.",
            "Use the result for screening and trend tracking support, not as a standalone clinical decision.",
        ]

        tracking_requested = _parse_track_flag(request.form.get("track") or request.args.get("track"))
        user_id, journey_id = _normalize_user_and_journey_ids(
            request.form.get("user_id") or request.args.get("user_id") or "anonymous",
            request.form.get("journey_id") or request.args.get("journey_id"),
        )
        tracking_enabled = tracking_requested and face_visible is not False
        tracking_blocked_reason = None
        if tracking_requested and not tracking_enabled:
            tracking_blocked_reason = (
                "Tracking was skipped because no face was detected in the uploaded image."
            )

        tracking = None
        tracking_backend = None
        if tracking_enabled:
            try:
                persistence = _append_severity_visit(
                    user_id=user_id,
                    journey_id=journey_id,
                    severity_level=severity_level,
                    severity_score=severity_score,
                    confidence=confidence,
                    features=prediction.get("normalized_features"),
                    metadata={"source": "severity_model"},
                    image_path=saved_image_path,
                )
                tracking = _build_severity_tracking_summary(user_id, journey_id=journey_id)
                tracking_backend = tracking.get("storage_backend") or persistence.get("storage_backend")
            except Exception as exc:
                logger.exception("Severity tracking update failed")
                tracking = {
                    "error": f"Failed to update tracking data: {exc}",
                    "storage_backend": "csv",
                    "files": {
                        "visits_csv": str(SEVERITY_VISITS_CSV),
                        "weeks_json": str(SEVERITY_WEEKS_JSON),
                    },
                }
                tracking_backend = tracking.get("storage_backend")

        # --- SMART GUARD: Fetch baseline visit & run multimodal analysis ---
        severity_metrics = _severity_metrics_from_features(prediction.get("normalized_features"))

        # Fetch existing visits for this journey to determine baseline
        journey_rows: list[dict] = []
        if journey_id:
            journey_rows, _ = _load_severity_rows(user_id, journey_id=journey_id)
            journey_rows.sort(key=_row_timestamp)

        visit_number = len(journey_rows) + 1  # current visit will be #N+1

        # Load baseline image bytes if this is NOT the first visit
        baseline_image_bytes = None
        baseline_level = ""
        baseline_score = 0.0
        if journey_rows:
            baseline_row = journey_rows[0]
            baseline_level = baseline_row.get("severity_level", "")
            baseline_score = _safe_float(baseline_row.get("severity_score"), 0.0)
            baseline_img_path = baseline_row.get("image_path", "")
            if baseline_img_path:
                try:
                    full_path = SEVERITY_UPLOADS_DIR / os.path.basename(baseline_img_path)
                    if full_path.exists():
                        baseline_image_bytes = full_path.read_bytes()
                except Exception as _bimg_err:
                    logger.warning("Could not load baseline image: %s", _bimg_err)

        # Fetch journey metadata for body part lock
        journey_title = request.form.get("journey_title") or request.args.get("journey_title") or ""
        target_body_part = request.form.get("body_part") or request.args.get("body_part") or ""

        # Run the Master Multimodal Smart Guard
        smart_guard = {}
        try:
            smart_guard = GeminiService.analyze_tracking_context(
                current_image_bytes=image_data,
                current_level=severity_level,
                current_metrics=severity_metrics,
                journey_title=journey_title,
                target_body_part=target_body_part,
                baseline_image_bytes=baseline_image_bytes,
                baseline_level=baseline_level,
                baseline_score=baseline_score,
                current_score=severity_score,
                visit_number=visit_number,
            )
        except Exception as _sg_err:
            logger.warning("Smart Guard call failed: %s", _sg_err)

        # Block tracking if body part is inconsistent (wrong spot warning)
        is_consistent = smart_guard.get("is_consistent_with_journey", True)
        needs_clarification = smart_guard.get("needs_clarification", False)
        if tracking_enabled and not is_consistent:
            tracking_enabled = False
            tracking_blocked_reason = (
                smart_guard.get("consistency_warning")
                or "Tracking blocked: the uploaded image does not match the journey's target body part."
            )

        tracking = None
        tracking_backend = None
        if tracking_enabled:
            try:
                persistence = _append_severity_visit(
                    user_id=user_id,
                    journey_id=journey_id,
                    severity_level=severity_level,
                    severity_score=severity_score,
                    confidence=confidence,
                    features=prediction.get("normalized_features"),
                    metadata={"source": "severity_model", "body_part": smart_guard.get("identified_body_part", "")},
                    image_path=saved_image_path,
                )
                tracking = _build_severity_tracking_summary(user_id, journey_id=journey_id)
                tracking_backend = tracking.get("storage_backend") or persistence.get("storage_backend")
            except Exception as exc:
                logger.exception("Severity tracking update failed")
                tracking = {
                    "error": f"Failed to update tracking data: {exc}",
                    "storage_backend": "csv",
                    "files": {
                        "visits_csv": str(SEVERITY_VISITS_CSV),
                        "weeks_json": str(SEVERITY_WEEKS_JSON),
                    },
                }
                tracking_backend = tracking.get("storage_backend")

        return jsonify(
            {
                "severity_level": severity_level,
                "severity_score": round(severity_score, 2),
                "confidence": confidence,
                "confidence_level": confidence_level,
                # --- Smart Guard outputs ---
                "identified_body_part": smart_guard.get("identified_body_part", "Unknown"),
                "is_consistent_with_journey": is_consistent,
                "needs_clarification": needs_clarification,
                "clarification_question": smart_guard.get("clarification_question"),
                "clinical_rationale": smart_guard.get("clinical_rationale", ""),
                "healing_insight": smart_guard.get("healing_insight"),
                "baseline_image_url": f"/api/severity/uploads/{Path(baseline_img_path).name}" if baseline_img_path else None,
                "severity_delta": smart_guard.get("severity_delta"),
                "biomarkers": severity_metrics,
                # --- Standard outputs ---
                "probabilities": probabilities,
                "top_predictions": top_predictions,
                "top_probability_gap": round(float(top_gap), 4),
                "score_based_level": prediction.get("score_based_level"),
                "thresholds": prediction.get("thresholds", {}),
                "feature_vector": prediction.get("feature_vector", {}),
                "normalized_features": prediction.get("normalized_features", {}),
                "preprocessing": preprocessing,
                "validation_status": "operational_only_unlabeled",
                "analysis_scope": analysis_scope,
                "requires_review": requires_review,
                "review_reasons": review_reasons,
                "next_steps": next_steps,
                "limitations": limitations,
                "consistency_warning": smart_guard.get("consistency_warning") or consistency_warning,
                "quality_notes": prediction.get("quality_notes", []),
                "severity_class": severity_level,
                "score": round(severity_score, 2),
                "tracking_requested": tracking_requested,
                "tracking_enabled": tracking_enabled,
                "tracking_blocked_reason": tracking_blocked_reason,
                "journey_id": journey_id,
                "visit_number": visit_number,
                "current_image_url": f"/api/severity/{saved_image_path}" if saved_image_path else None,
                "tracking": tracking,
                "tracking_backend": tracking_backend,
                "tracking_files": {
                    "visits_csv": str(SEVERITY_VISITS_CSV),
                    "weeks_json": str(SEVERITY_WEEKS_JSON),
                } if tracking_backend == "csv" else {},
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )


    @app.route("/api/profile", methods=["POST"])
    def update_profile():
        """Update user personal details for automation."""
        try:
            data = request.json or {}
            user_id = data.get("user_id")
            if not user_id:
                return jsonify({"status": "error", "message": "user_id is required"}), 400

            profile = SupabaseService.update_user_profile(user_id, data)
            return jsonify(
                {"status": "success", "message": "Profile updated successfully", "profile": profile}
            )
        except Exception as exc:
            logger.exception("Profile update failed")
            return jsonify({"status": "error", "message": str(exc)}), 500

    @app.route("/api/journey/start", methods=["POST"])
    def start_journey():
        """Log the beginning of a skin journey (e.g., 'Forehead Acne Tracking')."""
        try:
            data = request.json or {}
            user_id = data.get("user_id")
            title = data.get("title")
            body_part = data.get("body_part", "Face")
            frequency = data.get("frequency", "weekly")

            if not user_id or not title:
                return jsonify({"status": "error", "message": "user_id and title are required"}), 400

            journey = SupabaseService.create_journey(user_id, title, body_part, frequency)
            return jsonify(
                {"status": "success", "message": "Tracking journey started", "journey": journey}
            )
        except Exception as exc:
            logger.exception("Journey start failed")
            return jsonify({"status": "error", "message": str(exc)}), 500

    @app.route("/api/journey/list", methods=["GET"])
    def list_journeys():
        """List all progress tracking journeys for a user."""
        try:
            user_id = request.args.get("user_id")
            if not user_id:
                return jsonify({"status": "error", "message": "user_id is required"}), 400

            journeys = SupabaseService.get_user_journeys(user_id)
            return jsonify({"status": "success", "journeys": journeys})
        except Exception as exc:
            logger.exception("Listing journeys failed")
            return jsonify({"status": "error", "message": str(exc)}), 500

    @app.route("/api/history", methods=["GET"])
    def history():
        user_id = request.args.get("user_id")
        journey_id = request.args.get("journey_id")
        if not user_id or user_id == "anonymous":
            return jsonify({"error": "user_id parameter is required for history retrieval"}), 400
        
        real_data, _ = _load_real_history(user_id, journey_id=journey_id)
        if not real_data:
            return jsonify([]) # Honestly return empty if no real visits
        return jsonify(real_data)

    @app.route("/api/severity/uploads/<filename>", methods=["GET"])
    def serve_severity_image(filename):
        """Serve uploaded severity tracking images."""
        return send_from_directory(SEVERITY_UPLOADS_DIR, filename)

    @app.route("/api/stats", methods=["GET"])
    def stats():
        user_id = request.args.get("user_id")
        journey_id = request.args.get("journey_id")
        if not user_id or user_id == "anonymous":
            return jsonify({"error": "user_id parameter is required for statistics retrieval"}), 400
        
        real_history, storage_backend = _load_real_history(user_id, journey_id=journey_id)
        
        if not real_history:
            return jsonify({
                "labels": ["Redness", "Inflammation", "Scaling", "Texture"],
                "values": [0, 0, 0, 0],
                "note": "No tracking data available yet.",
                "storage_backend": storage_backend,
            })

        # Average the metrics across all visits
        avg_metrics = {"redness": 0.0, "inflammation": 0.0, "scaling": 0.0, "texture": 0.0}
        for entry in real_history:
            m = entry.get("metrics", {})
            for k in avg_metrics:
                avg_metrics[k] += m.get(k, 0.0)
        
        count = len(real_history)
        return jsonify({
            "labels": ["Redness", "Inflammation", "Scaling", "Texture"],
            "values": [
                round(avg_metrics["redness"] / count, 1),
                round(avg_metrics["inflammation"] / count, 1),
                round(avg_metrics["scaling"] / count, 1),
                round(avg_metrics["texture"] / count, 1),
            ],
            "storage_backend": storage_backend,
        })

    @app.route("/api/progress", methods=["POST"])
    def add_progress():
        """
        Log current severity and generate a real tracking entry.
        Supports:
        - Multipart: 'image' file + optional 'user_id' and 'journey_id'
        - JSON: {'score': float, 'level': str, 'user_id': str} (legacy fallback)
        """
        user_id = "anonymous"
        
        # 1. Handle Multipart Image (Real Analysis Check-in)
        if 'image' in request.files or 'file' in request.files:
            image_file = request.files.get("image") or request.files.get("file")
            user_id, journey_id = _normalize_user_and_journey_ids(
                request.form.get("user_id", "anonymous"),
                request.form.get("journey_id"),
            )
            
            try:
                model = get_severity_model(
                    model_path=SEVERITY_MODEL_PATH,
                    metadata_path=SEVERITY_METADATA_PATH,
                )
                if model is None or not model.loaded:
                    return jsonify({"error": "Severity model unavailable"}), 503
                
                try:
                    prediction = model.predict_from_bytes(image_file.read())
                except Exception as exc:
                    msg = str(exc)
                    if "cannot identify image file" in msg.lower():
                        return jsonify({"error": "Invalid image file format", "detail": msg}), 400
                    raise exc
                
                severity_level = str(prediction.get("severity_level", "Moderate"))
                severity_score = float(prediction.get("severity_score", 0.0))
                confidence = float(prediction.get("confidence", 0.0))
                
                # Persistence
                persistence = _append_severity_visit(
                    user_id=user_id,
                    journey_id=journey_id,
                    severity_level=severity_level,
                    severity_score=severity_score,
                    confidence=confidence,
                    features=prediction.get("normalized_features"),
                    metadata={"source": "progress_image_checkin"},
                )
                
                return jsonify({
                    "status": "success",
                    "message": "Weekly check-in analyzed and logged successfully.",
                    "severity_level": severity_level,
                    "severity_score": round(severity_score, 2),
                    "analysis": f"Severity {severity_level} ({(severity_score):.1f}%) recorded.",
                    "journey_id": journey_id,
                    "tracking_backend": persistence.get("storage_backend"),
                })
            except Exception as exc:
                logger.exception("In-flow progress analysis failed")
                return jsonify({"status": "error", "message": str(exc)}), 500

        # 2. Handle JSON Summary (Confirmation loop)
        data = request.json or {}
        user_id, journey_id = _normalize_user_and_journey_ids(
            data.get("user_id", "anonymous"),
            data.get("journey_id"),
        )
        score = data.get("score")
        level = data.get("level")
        
        if score is not None and level is not None:
             try:
                 severity_score = _safe_float(score)
                 confidence = _safe_float(data.get("confidence"), 0.0)
                 metrics = _parse_metrics_json(data.get("metrics") or data.get("metrics_json") or {})
                 persistence = _append_severity_visit(
                     user_id=user_id,
                     journey_id=journey_id,
                     severity_level=str(level),
                     severity_score=severity_score,
                     confidence=confidence,
                     metrics=metrics,
                     metadata={"source": "progress_confirmation"},
                 )
                 return jsonify({
                     "status": "success",
                     "message": "Visit confirmed and logged to journey.",
                     "details": f"Severity {_normalize_severity_level(level)} ({severity_score:.1f}%) recorded.",
                     "journey_id": journey_id,
                     "tracking_backend": persistence.get("storage_backend"),
                 })
             except Exception as exc:
                 logger.exception("Manual progress confirmation save failed")
                 return jsonify({"status": "error", "message": str(exc)}), 500
             
        return jsonify({
            "status": "info",
            "message": "To log new progress, please upload a clear photo of the area.",
            "action_required": "image_required"
        })
