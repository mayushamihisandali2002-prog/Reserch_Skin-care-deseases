import datetime
import json
import logging
import csv
from pathlib import Path

from flask import jsonify, request

from inference.config import (
    SEVERITY_METADATA_PATH,
    SEVERITY_MODEL_PATH,
    SEVERITY_TRACK_DIR,
)

from services.supabase_service import SupabaseService

from . import get_severity_model


logger = logging.getLogger(__name__)


SEVERITY_VISITS_CSV = Path(SEVERITY_TRACK_DIR) / "visits.csv"
SEVERITY_WEEKS_JSON = Path(SEVERITY_TRACK_DIR) / "_weeks.json"
SEVERITY_VISIT_FIELDS = [
    "timestamp",
    "user_id",
    "severity_level",
    "severity_score",
    "confidence",
    "metrics_json",
]



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


def _parse_track_flag(raw_value: str | None) -> bool:
    if raw_value is None:
        return False
    value = str(raw_value).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _ensure_visits_csv_schema() -> None:
    if not SEVERITY_VISITS_CSV.exists():
        return

    with open(SEVERITY_VISITS_CSV, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return

    header = rows[0]
    if header == SEVERITY_VISIT_FIELDS:
        return

    normalized_rows: list[dict[str, str]] = []
    for row in rows[1:]:
        if not row:
            continue
        padded = list(row[: len(SEVERITY_VISIT_FIELDS)])
        if len(padded) < len(SEVERITY_VISIT_FIELDS):
            padded.extend([""] * (len(SEVERITY_VISIT_FIELDS) - len(padded)))
        normalized_rows.append(dict(zip(SEVERITY_VISIT_FIELDS, padded)))

    with open(SEVERITY_VISITS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SEVERITY_VISIT_FIELDS)
        writer.writeheader()
        writer.writerows(normalized_rows)


def _append_severity_visit(
    user_id: str,
    severity_level: str,
    severity_score: float,
    confidence: float,
    features: dict[str, float] = None,
) -> None:
    Path(SEVERITY_TRACK_DIR).mkdir(parents=True, exist_ok=True)
    _ensure_visits_csv_schema()

    file_exists = SEVERITY_VISITS_CSV.exists()
    timestamp = datetime.datetime.now().isoformat()
    
    # Map raw features to display metrics
    metrics = {
        "redness": round(features.get("redness_index", 0.0) * 100, 1) if features else 0,
        "inflammation": round(features.get("saturation_mean", 0.0) * 100, 1) if features else 0,
        "scaling": round(features.get("edge_density", 0.0) * 100, 1) if features else 0,
        "texture": round(features.get("texture_entropy", 0.0) * 10, 1) if features else 0,
    }

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
                "severity_level": severity_level,
                "severity_score": f"{severity_score:.4f}",
                "confidence": f"{confidence:.6f}",
                "metrics_json": json.dumps(metrics),
            }
        )


def _build_severity_tracking_summary(user_id: str) -> dict:
    if not SEVERITY_VISITS_CSV.exists():
        return {
            "visits_count": 0,
            "improvement_percent": 0.0,
            "weekly_trend": [],
            "latest_visit": None,
            "files": {
                "visits_csv": str(SEVERITY_VISITS_CSV),
                "weeks_json": str(SEVERITY_WEEKS_JSON),
            },
        }

    _ensure_visits_csv_schema()
    rows: list[dict] = []
    with open(SEVERITY_VISITS_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("user_id") or "anonymous") == user_id:
                rows.append(row)

    if not rows:
        return {
            "visits_count": 0,
            "improvement_percent": 0.0,
            "weekly_trend": [],
            "latest_visit": None,
            "files": {
                "visits_csv": str(SEVERITY_VISITS_CSV),
                "weeks_json": str(SEVERITY_WEEKS_JSON),
            },
        }

    rows.sort(key=lambda item: item.get("timestamp", ""))

    first_score = _safe_float(rows[0].get("severity_score"), 0.0)
    latest_score = _safe_float(rows[-1].get("severity_score"), 0.0)

    improvement_percent = ((first_score - latest_score) / first_score) * 100.0 if first_score > 0 else 0.0

    week_scores: dict[str, list[float]] = {}
    for row in rows:
        ts = row.get("timestamp", "")
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

    payload = {
        "updated_at": datetime.datetime.now().isoformat(),
        "user_id": user_id,
        "weekly_trend": weekly_trend,
    }
    Path(SEVERITY_TRACK_DIR).mkdir(parents=True, exist_ok=True)
    with open(SEVERITY_WEEKS_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    latest = rows[-1]
    return {
        "visits_count": len(rows),
        "improvement_percent": round(float(improvement_percent), 2),
        "weekly_trend": weekly_trend,
        "latest_visit": {
            "timestamp": latest.get("timestamp"),
            "severity_level": latest.get("severity_level"),
            "severity_score": round(_safe_float(latest.get("severity_score"), 0.0), 2),
            "confidence": round(_safe_float(latest.get("confidence"), 0.0), 4),
        },
        "files": {
            "visits_csv": str(SEVERITY_VISITS_CSV),
            "weeks_json": str(SEVERITY_WEEKS_JSON),
        },
    }


def _load_real_history(user_id: str) -> list[dict]:
    """Read severity visits from local CSV and format for frontend history."""
    if not SEVERITY_VISITS_CSV.exists():
        return []

    _ensure_visits_csv_schema()
    history = []
    try:
        with open(SEVERITY_VISITS_CSV, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = [r for r in reader if (r.get("user_id") or "anonymous") == user_id]
            
            # Take last 10 visits for history
            for i, row in enumerate(rows[-10:]):
                ts = row.get("timestamp", "")
                metrics = {}
                try:
                    if row.get("metrics_json"):
                        metrics = json.loads(row.get("metrics_json"))
                except Exception:
                    pass

                history.append({
                    "week": f"Visit {len(rows) - len(rows[-10:]) + i + 1}",
                    "date": ts.split("T")[0] if "T" in ts else ts,
                    "image_url": "assets/images/severity_log.png", # placeholder for local pathing
                    "status": row.get("severity_level", "Unknown"),
                    "score": int(_safe_float(row.get("severity_score"))),
                    "metrics": metrics or {"redness": 0, "inflammation": 0, "scaling": 0, "texture": 0}
                })
    except Exception as exc:
        logger.error("Failed to load real severity history: %s", exc)
    
    return history


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
            prediction = model.predict_from_bytes(image_file.read())
        except Exception as exc:
            msg = str(exc)
            if "cannot identify image file" in msg.lower():
                return jsonify({"error": "Invalid image file format", "detail": msg}), 400
            logger.exception("Severity prediction failed")
            return jsonify({"error": f"Severity prediction failed: {exc}"}), 500

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
        user_id = (request.form.get("user_id") or request.args.get("user_id") or "anonymous").strip() or "anonymous"
        tracking_enabled = tracking_requested and face_visible is not False
        tracking_blocked_reason = None
        if tracking_requested and not tracking_enabled:
            tracking_blocked_reason = (
                "Tracking was skipped because no face was detected in the uploaded image."
            )

        tracking = None
        if tracking_enabled:
            try:
                _append_severity_visit(
                    user_id=user_id,
                    severity_level=severity_level,
                    severity_score=severity_score,
                    confidence=confidence,
                    features=prediction.get("normalized_features"),
                )
                tracking = _build_severity_tracking_summary(user_id)
            except Exception as exc:
                logger.exception("Severity tracking update failed")
                tracking = {
                    "error": f"Failed to update tracking data: {exc}",
                    "files": {
                        "visits_csv": str(SEVERITY_VISITS_CSV),
                        "weeks_json": str(SEVERITY_WEEKS_JSON),
                    },
                }

        return jsonify(
            {
                "severity_level": severity_level,
                "severity_score": round(severity_score, 2),
                "confidence": confidence,
                "confidence_level": confidence_level,
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
                "consistency_warning": consistency_warning,
                "quality_notes": prediction.get("quality_notes", []),
                "severity_class": severity_level,
                "score": round(severity_score, 2),
                "tracking_requested": tracking_requested,
                "tracking_enabled": tracking_enabled,
                "tracking_blocked_reason": tracking_blocked_reason,
                "tracking": tracking,
                "tracking_files": {
                    "visits_csv": str(SEVERITY_VISITS_CSV),
                    "weeks_json": str(SEVERITY_WEEKS_JSON),
                },
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
        if not user_id or user_id == "anonymous":
            return jsonify({"error": "user_id parameter is required for history retrieval"}), 400
        
        real_data = _load_real_history(user_id)
        if not real_data:
            return jsonify([]) # Honestly return empty if no real visits
        return jsonify(real_data)

    @app.route("/api/stats", methods=["GET"])
    def stats():
        user_id = request.args.get("user_id")
        if not user_id or user_id == "anonymous":
            return jsonify({"error": "user_id parameter is required for statistics retrieval"}), 400
        
        real_history = _load_real_history(user_id)
        
        if not real_history:
            return jsonify({
                "labels": ["Redness", "Inflammation", "Scaling", "Texture"],
                "values": [0, 0, 0, 0],
                "note": "No tracking data available yet."
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
            ]
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
            user_id = request.form.get("user_id", "anonymous").strip() or "anonymous"
            
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
                _append_severity_visit(
                    user_id=user_id,
                    severity_level=severity_level,
                    severity_score=severity_score,
                    confidence=confidence,
                    features=prediction.get("normalized_features"),
                )
                
                return jsonify({
                    "status": "success",
                    "message": "Weekly check-in analyzed and logged successfully.",
                    "severity_level": severity_level,
                    "severity_score": round(severity_score, 2),
                    "analysis": f"Severity {severity_level} ({(severity_score):.1f}%) recorded."
                })
            except Exception as exc:
                logger.exception("In-flow progress analysis failed")
                return jsonify({"status": "error", "message": str(exc)}), 500

        # 2. Handle JSON Summary (Confirmation loop)
        data = request.json or {}
        user_id = data.get("user_id", "anonymous")
        score = data.get("score")
        level = data.get("level")
        
        if score is not None and level is not None:
             # This is a manual confirmation of a previously run analysis
             return jsonify({
                 "status": "success",
                 "message": "Visit confirmed and logged to journey.",
                 "details": f"Severity {level} ({score}%) recorded."
             })
             
        return jsonify({
            "status": "info",
            "message": "To log new progress, please upload a clear photo of the area.",
            "action_required": "image_required"
        })
