import logging
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from components.conversational_diagnosis_assistant.knowledge_base import (
    build_system_summary,
    treatment_suggestions_for_confidence,
    validate_skin_condition_keywords,
)

from services.gemini_skin_analysis import (
    GeminiSkinAnalysisError,
    analyze_skin_image_bytes,
    build_frontend_report,
    gemini_enabled,
)
from services.supabase_service import SupabaseService

from . import get_inference_pipeline
from .audio_transcription import transcribe_uploaded_audio


logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SCAN_DATA_DIR = BACKEND_ROOT / "assets" / "data" / "multimodal_image_audio_diagnosis"
SCAN_UPLOAD_DIR = SCAN_DATA_DIR / "uploads"
SCAN_HISTORY_FILE = SCAN_DATA_DIR / "scan_history.json"
ALLOWED_SCAN_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _local_fallback_enabled() -> bool:
    return os.getenv("ENABLE_LOCAL_FALLBACK", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _symptom_context_required_response(
    detail: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
):
    payload: dict[str, Any] = {
        "status": "requires_symptom_context",
        "error": "Image-only diagnosis is disabled for safety",
        "message": (
            "The current image model is not reliable enough for standalone diagnosis. "
            "Add typed symptoms or a voice note and use the fused image plus symptom flow."
        ),
        "recommended_analysis_mode": "multimodal_fused",
        "analysis_scope": "multimodal_required",
        "next_steps": [
            "Add symptom details such as itch, pain, scaling, discharge, duration, and body location.",
            "Upload a clearer voice note or type the symptoms manually if transcription fails.",
            "Use dermatologist review for urgent, bleeding, fast-changing, or suspicious lesions.",
        ],
    }
    if detail:
        payload["detail"] = detail
    if extra:
        payload.update(extra)
    return jsonify(payload), 422


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def _accuracy_percent(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        return 0.0
    if 0.0 <= number <= 1.0:
        return number * 100.0
    return max(0.0, min(100.0, number))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _scan_image_extension(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix in ALLOWED_SCAN_IMAGE_EXTENSIONS else ".jpg"


def _save_scan_image(image_bytes: bytes, original_filename: str) -> dict[str, str]:
    SCAN_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = secure_filename(original_filename or "scan.jpg")
    extension = _scan_image_extension(safe_name)
    stored_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{extension}"
    stored_path = SCAN_UPLOAD_DIR / stored_name
    stored_path.write_bytes(image_bytes)
    return {
        "image_url": f"/api/scan/uploads/{stored_name}",
        "image_storage_path": str(stored_path),
        "image_filename": stored_name,
        "original_filename": safe_name or original_filename or "scan.jpg",
    }


def _load_local_scan_history() -> list[dict[str, Any]]:
    if not SCAN_HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(SCAN_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Could not read scan history JSON", exc_info=True)
        return []
    return data if isinstance(data, list) else []


def _append_local_scan_history(entry: dict[str, Any]) -> None:
    SCAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = _load_local_scan_history()
    history.insert(0, _json_safe(entry))
    SCAN_HISTORY_FILE.write_text(
        json.dumps(history[:500], indent=2),
        encoding="utf-8",
    )


def _persist_scan_result(
    report: dict[str, Any],
    *,
    user_id: str,
    journey_id: str | None,
    image_info: dict[str, str],
    transcript: str,
    model_used: str,
    body_part_detected: str | None = None,
) -> dict[str, Any]:
    diagnosis = report.get("diagnosis") if isinstance(report.get("diagnosis"), dict) else {}
    report["image_url"] = image_info["image_url"]
    report["image_storage_path"] = image_info["image_storage_path"]
    if diagnosis is not None:
        diagnosis["image_url"] = image_info["image_url"]
        diagnosis["image_storage_path"] = image_info["image_storage_path"]

    analysis_id = uuid.uuid4().hex
    created_at = _utc_now_iso()
    report["analysis_id"] = analysis_id
    report["scan_history_saved"] = True
    report["scan_history_source"] = "local_json"

    history_entry = {
        "id": analysis_id,
        "created_at": created_at,
        "user_id": user_id or "anonymous",
        "journey_id": journey_id,
        "image_url": image_info["image_url"],
        "image_storage_path": image_info["image_storage_path"],
        "transcript": transcript,
        "predicted_disease": diagnosis.get("display_disease")
        or diagnosis.get("final_diagnosis")
        or diagnosis.get("disease")
        or "Unknown",
        "confidence": diagnosis.get("confidence", 0.0),
        "confidence_level": diagnosis.get("confidence_level", "low"),
        "mismatch_detected": _to_bool(diagnosis.get("mismatch_detected")),
        "model_used": diagnosis.get("model_used") or model_used,
        "response": report,
    }
    _append_local_scan_history(history_entry)

    if user_id and user_id != "anonymous" and diagnosis:
        try:
            saved = SupabaseService.save_skin_analysis(
                user_id=user_id,
                image_url=image_info["image_url"],
                predicted_disease=history_entry["predicted_disease"],
                confidence=history_entry["confidence"],
                confidence_level=history_entry["confidence_level"],
                all_predictions=_json_safe(report),
                treatments=diagnosis.get("treatments"),
                symptoms_description=transcript,
                journey_id=journey_id,
                body_part_detected=body_part_detected,
                model_used=history_entry["model_used"],
                image_metadata=image_info,
            )
            if saved and saved.get("id"):
                report["skin_analysis_id"] = saved["id"]
                report["scan_history_source"] = "supabase_and_local_json"
                SupabaseService.save_diagnosis(
                    user_id=user_id,
                    disease_name=history_entry["predicted_disease"],
                    confidence=history_entry["confidence"],
                    diagnosis_type="fused",
                    skin_analysis_id=saved["id"],
                )
        except Exception as exc:
            logger.warning("Scan history Supabase save failed: %s", exc)

    return report


def _scan_history_from_supabase(user_id: str, journey_id: str | None, limit: int) -> list[dict[str, Any]]:
    if not user_id or user_id == "anonymous":
        return []
    try:
        rows = SupabaseService.get_user_analyses(
            user_id=user_id,
            limit=limit,
            journey_id=journey_id,
        )
    except Exception as exc:
        logger.warning("Supabase scan history unavailable: %s", exc)
        return []

    history: list[dict[str, Any]] = []
    for row in rows or []:
        response = row.get("all_predictions")
        if isinstance(response, str):
            try:
                parsed_response = json.loads(response)
                response = parsed_response if isinstance(parsed_response, dict) else None
            except Exception:
                response = None
        disease = row.get("predicted_disease") or "Unknown"
        confidence = row.get("confidence") or 0.0
        confidence_level = row.get("confidence_level") or "low"
        image_url = row.get("image_url")
        transcript = row.get("symptoms_description")
        if not isinstance(response, dict):
            response = {
                "image_url": image_url,
                "summary": (
                    f"Saved prediction history for {disease}. "
                    f"Symptom context: {transcript or 'not recorded'}. "
                    "This record was created before full response storage was enabled."
                ),
                "diagnosis": {
                    "disease": disease,
                    "display_disease": disease,
                    "final_diagnosis": disease,
                    "confidence": confidence,
                    "confidence_level": confidence_level,
                    "mismatch_detected": False,
                    "transcript": transcript,
                    "image_url": image_url,
                    "model_used": row.get("model_used") or "history_record",
                    "treatments": [],
                    "recommended_treatments": [],
                    "medical_disclaimer": "This is not a medical diagnosis",
                },
            }
        elif image_url:
            response.setdefault("image_url", image_url)
            diagnosis = response.get("diagnosis")
            if isinstance(diagnosis, dict):
                diagnosis.setdefault("image_url", image_url)
                diagnosis.setdefault("transcript", transcript)
        history.append(
            {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "user_id": row.get("user_id"),
                "journey_id": row.get("journey_id"),
                "image_url": image_url,
                "transcript": transcript,
                "predicted_disease": disease,
                "confidence": confidence,
                "confidence_level": confidence_level,
                "mismatch_detected": _to_bool(
                    response.get("diagnosis", {}).get("mismatch_detected")
                    if isinstance(response.get("diagnosis"), dict)
                    else False
                ),
                "model_used": row.get("model_used"),
                "source": "supabase",
                "response": response,
            }
        )
    return history


def _scan_history_response(user_id: str, journey_id: str | None, limit: int) -> list[dict[str, Any]]:
    local_history = [
        {**entry, "source": entry.get("source", "local_json")}
        for entry in _load_local_scan_history()
        if (not user_id or entry.get("user_id") == user_id)
        and (not journey_id or entry.get("journey_id") == journey_id)
    ]
    supabase_history = _scan_history_from_supabase(user_id, journey_id, limit)
    combined = supabase_history + local_history
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in combined:
        key = str(item.get("id") or item.get("created_at") or len(deduped))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return sorted(
        deduped,
        key=lambda item: str(item.get("created_at") or ""),
        reverse=True,
    )[:limit]


def _apply_backend_summary(report: dict[str, Any], transcript: str) -> dict[str, Any]:
    diagnosis = report.get("diagnosis") if isinstance(report.get("diagnosis"), dict) else {}
    raw = report.get("raw_gemini_result") if isinstance(report.get("raw_gemini_result"), dict) else {}

    image_accuracy = _accuracy_percent(
        diagnosis.get("image_accuracy")
        or raw.get("image_accuracy")
        or diagnosis.get("image_confidence")
    )
    text_accuracy = _accuracy_percent(
        diagnosis.get("text_accuracy")
        or raw.get("text_accuracy")
        or diagnosis.get("symptom_match_score")
        or diagnosis.get("text_confidence")
    )
    mismatch_detected = _to_bool(
        diagnosis.get("mismatch_detected")
        if "mismatch_detected" in diagnosis
        else raw.get("mismatch_detected")
    )

    condition = (
        diagnosis.get("display_disease")
        or diagnosis.get("final_diagnosis")
        or diagnosis.get("disease")
        or raw.get("most_likely_condition")
        or "the possible condition"
    )
    condition_text = str(condition).replace("_", " ").strip().title()

    # When the model does not expose accuracy scores, fall back to conservative
    # backend signals so the CSV rule still drives the visible System Summary.
    if image_accuracy <= 0:
        image_correct: bool | None = None if condition_text.lower() == "uncertain" else True
    else:
        image_correct = image_accuracy >= 60.0
    if text_accuracy <= 0:
        text_correct = False if mismatch_detected else None
    else:
        text_correct = text_accuracy >= 50.0

    summary_payload = build_system_summary(
        condition=condition_text,
        transcript=transcript,
        image_correct=image_correct,
        text_correct=text_correct,
        mismatch_detected=mismatch_detected,
        image_accuracy=image_accuracy,
        text_accuracy=text_accuracy,
    )

    report["summary"] = summary_payload["summary"]
    report["backend_summary_logic"] = {
        "source": summary_payload["source"],
        "knowledge_file": "components/conversational_diagnosis_assistant/knowledge_base.py",
        "case_id": summary_payload["case_id"],
        "condition": summary_payload["condition"],
        "matched_terms": summary_payload["matched_terms"],
        "image_correct": image_correct,
        "text_correct": text_correct,
        "mismatch_detected": mismatch_detected,
        "image_accuracy": round(image_accuracy, 2),
        "text_accuracy": round(text_accuracy, 2),
        "final_result_source": "ai_analysis",
    }
    if diagnosis is not None:
        diagnosis["mismatch_detected"] = mismatch_detected
        diagnosis["image_accuracy"] = round(image_accuracy)
        diagnosis["text_accuracy"] = round(text_accuracy)
    return report


def _apply_treatment_policy(report: dict[str, Any]) -> dict[str, Any]:
    diagnosis = report.get("diagnosis") if isinstance(report.get("diagnosis"), dict) else None
    if diagnosis is None:
        return report

    mismatch_detected = _to_bool(diagnosis.get("mismatch_detected"))
    if mismatch_detected:
        diagnosis["treatments"] = []
        diagnosis["recommended_treatments"] = []
        diagnosis["treatment_policy"] = {
            "source": "backend_python_knowledge_base",
            "condition": (
                diagnosis.get("display_disease")
                or diagnosis.get("final_diagnosis")
                or diagnosis.get("disease")
                or "Unknown"
            ),
            "confidence": round(_accuracy_percent(diagnosis.get("confidence")) / 100.0, 4),
            "threshold": 0.60,
            "include_treatments": False,
            "blocked_by_mismatch": True,
            "reason": (
                "Image and symptom text are mismatched; treatment suggestions are hidden."
            ),
        }
        return report

    condition = (
        diagnosis.get("display_disease")
        or diagnosis.get("final_diagnosis")
        or diagnosis.get("disease")
        or "Unknown"
    )
    confidence = _accuracy_percent(diagnosis.get("confidence")) / 100.0
    treatment_payload = treatment_suggestions_for_confidence(
        condition=str(condition),
        confidence=confidence,
        threshold=0.60,
    )

    treatments = treatment_payload["treatments"]
    diagnosis["treatments"] = treatments
    diagnosis["recommended_treatments"] = treatments
    diagnosis["treatment_policy"] = {
        "source": treatment_payload["source"],
        "condition": treatment_payload["condition"],
        "confidence": round(treatment_payload["confidence"], 4),
        "threshold": treatment_payload["threshold"],
        "include_treatments": treatment_payload["include_treatments"],
        "blocked_by_mismatch": False,
        "reason": (
            "Confidence is 60% or higher; treatment suggestions are included."
            if treatment_payload["include_treatments"]
            else "Confidence is below 60%; treatment suggestions are hidden."
        ),
    }
    return report


def register_routes(app) -> None:
    """
    Multimodal image/audio diagnosis routes.
    """

    @app.route("/api/analyze", methods=["POST", "OPTIONS"])
    def analyze():
        """
        Deprecated image-only diagnosis endpoint.
        """


        image_file = request.files.get("image") or request.files.get("file")

        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        return _symptom_context_required_response(
            "Image-only diagnosis has been turned off because the image model is not clinically reliable on its own."
        )

    @app.route("/api/scan/uploads/<path:filename>", methods=["GET"])
    def scan_upload(filename: str):
        return send_from_directory(SCAN_UPLOAD_DIR, filename)

    @app.route("/api/scan-history", methods=["GET"])
    def scan_history():
        user_id = request.args.get("user_id", "").strip()
        journey_id = request.args.get("journey_id", "").strip() or None
        try:
            limit = max(1, min(100, int(request.args.get("limit", "50"))))
        except ValueError:
            limit = 50
        return jsonify(_scan_history_response(user_id, journey_id, limit))

    @app.route("/api/analyze-fused", methods=["POST", "OPTIONS"])
    def analyze_fused():
        """
        Multimodal diagnosis: image + text -> fused result.
        Accepts multipart/form-data:
        - 'image' file
        - 'text' field (transcribed speech from frontend)
        Optionally accepts 'audio' file for server-side transcription.
        """
        if request.method == "OPTIONS":
            return "", 204

        image_file = request.files.get("image") or request.files.get("file")
        text = request.form.get("text", "").strip()
        audio_file = request.files.get("audio")
        journey_id = request.form.get("journey_id")
        user_id = request.form.get("user_id", "anonymous")

        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        image_bytes = image_file.read()
        image_info = _save_scan_image(image_bytes, image_file.filename or "scan.jpg")

        transcript = text
        transcription_status = "frontend_text" if text else "not_requested"
        transcription_error = None
        if audio_file and not text:
            transcript, transcription_status, transcription_error = transcribe_uploaded_audio(
                audio_file
            )

        if not transcript.strip():
            detail = (
                transcription_error
                or "No usable symptom description was received. Add typed symptoms or upload a clearer voice note."
            )
            return _symptom_context_required_response(
                detail,
                extra={
                    "transcription_status": transcription_status,
                    "transcription_error": transcription_error,
                },
            )

        keyword_validation = validate_skin_condition_keywords(transcript)
        if not keyword_validation["valid"]:
            return jsonify(
                {
                    "status": "validation_error",
                    "error_message": "Minimum keywords are four.",
                    "message": "Minimum keywords are four.",
                    "validation_mode": keyword_validation["validation_mode"],
                    "mismatch_symptoms_allowed": keyword_validation[
                        "mismatch_symptoms_allowed"
                    ],
                    "minimum_keywords": keyword_validation["minimum_keywords"],
                    "keyword_count": keyword_validation["keyword_count"],
                    "matched_keywords": keyword_validation["matched_keywords"],
                    "matched_conditions": keyword_validation["matched_conditions"],
                    "analysis_scope": "skin_condition_keyword_validation",
                    "medical_disclaimer": "This is not a medical diagnosis",
                }
            )

        enable_fallback = _local_fallback_enabled()
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if gemini_enabled() and os.getenv("GEMINI_API_KEY"):
            logger.info("Gemini analyzer used")
            try:
                gemini_result = analyze_skin_image_bytes(
                    image_bytes=image_bytes,
                    symptoms=transcript,
                    model=gemini_model,
                )
                report = build_frontend_report(
                    gemini_result,
                    transcript=transcript,
                    transcription_status=transcription_status,
                    transcription_error=transcription_error,
                    model=gemini_model,
                )
                report = _apply_treatment_policy(_apply_backend_summary(report, transcript))
                report = _persist_scan_result(
                    report,
                    user_id=user_id,
                    journey_id=journey_id,
                    image_info=image_info,
                    transcript=transcript,
                    model_used=diag.get("model_used", "gemini") if (diag := report.get("diagnosis")) else "gemini",
                    body_part_detected=None,
                )

                return jsonify(report)
            except GeminiSkinAnalysisError as exc:
                logger.warning("Gemini analysis failed: %s", exc)
                if not enable_fallback:
                    logger.info("Local fallback disabled")
                    return jsonify({
                        "status": "error",
                        "most_likely_condition": "uncertain",
                        "model_used": "gemini_failed",
                        "fallback_used": False,
                        "medical_disclaimer": "This is not a medical diagnosis",
                        "error": f"Gemini analysis failed: {exc}"
                    }), 502
                
                logger.info("Local fallback used")

        elif not enable_fallback:
             logger.info("Local fallback disabled")
             return jsonify({
                "status": "error",
                "most_likely_condition": "uncertain",
                "model_used": "gemini_missing",
                "fallback_used": False,
                "medical_disclaimer": "This is not a medical diagnosis",
                "error": "Gemini API key is missing and local fallback is disabled."
            }), 400
        else:
            logger.info("Local fallback used")

        # Journey target lookup
        target_part = "Skin"
        if journey_id:
            try:
                db_part = SupabaseService.get_journey_part(journey_id)
                if db_part:
                    target_part = db_part
            except Exception:
                pass

        try:
            pipe = get_inference_pipeline()
        except Exception as exc:
            logger.exception("Inference pipeline unavailable")
            return jsonify({"error": f"Inference pipeline unavailable: {exc}"}), 503

        try:
            report = pipe.smart_predict(
                text=transcript,
                image_bytes=image_bytes,
                journey_id=journey_id,
                target_body_part=target_part,
            )
        except Exception as exc:
            msg = str(exc)
            if "cannot identify image file" in msg.lower():
                return jsonify({"error": "Invalid image file format", "detail": msg}), 400
            logger.exception("Fused prediction failed")
            return jsonify({"error": f"Fused analysis failed: {exc}"}), 500

        if report.get("diagnosis"):
            report["diagnosis"]["transcript"] = transcript
            report["diagnosis"]["transcription_status"] = transcription_status
            report["diagnosis"]["transcription_error"] = transcription_error
            report["diagnosis"]["fallback_used"] = True
            report["diagnosis"]["medical_disclaimer"] = "This is not a medical diagnosis"
            if "model_used" not in report["diagnosis"]:
                report["diagnosis"]["model_used"] = "local_fallback"
        report = _apply_treatment_policy(_apply_backend_summary(report, transcript))
        report = _persist_scan_result(
            report,
            user_id=user_id,
            journey_id=journey_id,
            image_info=image_info,
            transcript=transcript,
            model_used="automated_fused",
            body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
        )

        return jsonify(report)

    @app.route("/api/smart-scan", methods=["POST", "OPTIONS"])
    def smart_scan():
        """
        Fully automated multi-modal scan.
        Coordinates models to provide a comprehensive skin health report.
        """
        if request.method == "OPTIONS":
            return "", 204

        try:
            image_file = request.files.get("image") or request.files.get("file")
            text_input = (
                request.form.get("text", "").strip()
                or request.form.get("message", "").strip()
            )
            user_id = request.form.get("user_id", "anonymous")
            journey_id = request.form.get("journey_id")

            if not image_file and not text_input:
                return jsonify(
                    {"error": "Automation requires at least an image or a symptom description."}
                ), 400

            if image_file and not text_input:
                return _symptom_context_required_response(
                    "Smart scan no longer accepts image-only diagnosis. Add symptom text or use the fused voice workflow."
                )

            keyword_validation = validate_skin_condition_keywords(text_input)
            if not keyword_validation["valid"]:
                return jsonify(
                    {
                        "status": "validation_error",
                        "error_message": "Minimum keywords are four.",
                        "message": "Minimum keywords are four.",
                        "validation_mode": keyword_validation["validation_mode"],
                        "mismatch_symptoms_allowed": keyword_validation[
                            "mismatch_symptoms_allowed"
                        ],
                        "minimum_keywords": keyword_validation["minimum_keywords"],
                        "keyword_count": keyword_validation["keyword_count"],
                        "matched_keywords": keyword_validation["matched_keywords"],
                        "matched_conditions": keyword_validation["matched_conditions"],
                        "analysis_scope": "skin_condition_keyword_validation",
                        "medical_disclaimer": "This is not a medical diagnosis",
                    }
                )

            image_bytes = image_file.read() if image_file else None
            image_info = (
                _save_scan_image(image_bytes, image_file.filename or "scan.jpg")
                if image_bytes and image_file
                else None
            )

            enable_fallback = _local_fallback_enabled()
            gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

            if gemini_enabled() and os.getenv("GEMINI_API_KEY"):
                logger.info("Gemini analyzer used (smart-scan)")
                try:
                    gemini_result = analyze_skin_image_bytes(
                        image_bytes=image_bytes,
                        symptoms=text_input,
                        model=gemini_model,
                    )
                    report = build_frontend_report(
                        gemini_result,
                        transcript=text_input,
                        transcription_status="smart_scan_text",
                        model=gemini_model,
                    )
                    report = _apply_treatment_policy(_apply_backend_summary(report, text_input))
                    if image_info:
                        report = _persist_scan_result(
                            report,
                            user_id=user_id,
                            journey_id=journey_id,
                            image_info=image_info,
                            transcript=text_input,
                            model_used="smart_scan_gemini",
                            body_part_detected=None,
                        )

                    return jsonify(report)
                except GeminiSkinAnalysisError as exc:
                    logger.warning("Smart-scan Gemini failed: %s", exc)
                    if not enable_fallback:
                        logger.info("Local fallback disabled (smart-scan)")
                        return jsonify({
                            "status": "error",
                            "most_likely_condition": "uncertain",
                            "model_used": "gemini_failed",
                            "fallback_used": False,
                            "medical_disclaimer": "This is not a medical diagnosis",
                            "error": f"Gemini analysis failed: {exc}"
                        }), 502
                    logger.info("Local fallback used (smart-scan)")

            elif not enable_fallback:
                logger.info("Local fallback disabled (smart-scan)")
                return jsonify({
                    "status": "error",
                    "most_likely_condition": "uncertain",
                    "model_used": "gemini_missing",
                    "fallback_used": False,
                    "medical_disclaimer": "This is not a medical diagnosis",
                    "error": "Gemini API key is missing and local fallback is disabled."
                }), 400
            else:
                logger.info("Local fallback used (smart-scan)")

            # Journey Context Lookup
            target_part = "Skin"
            if journey_id:
                try:
                    db_target_part = SupabaseService.get_journey_part(journey_id)
                    if db_target_part:
                        target_part = db_target_part
                except Exception:
                    logger.warning("Could not fetch target part for journey %s", journey_id)

            pipe = get_inference_pipeline()
            report = pipe.smart_predict(
                text=text_input,
                image_bytes=image_bytes,
                journey_id=journey_id,
                target_body_part=target_part,
            )

            if report.get("diagnosis"):
                report["diagnosis"]["fallback_used"] = True
                report["diagnosis"]["medical_disclaimer"] = "This is not a medical diagnosis"
                if "model_used" not in report["diagnosis"]:
                    report["diagnosis"]["model_used"] = "local_fallback_smart_scan"
            report = _apply_treatment_policy(_apply_backend_summary(report, text_input))
            if image_info:
                report = _persist_scan_result(
                    report,
                    user_id=user_id,
                    journey_id=journey_id,
                    image_info=image_info,
                    transcript=text_input,
                    model_used="smart_scan_fused_fallback",
                    body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
                )

            return jsonify(report)

        except Exception as exc:
            logger.exception("Smart scan failed")
            return jsonify(
                {"status": "error", "message": f"Automated analysis failed: {str(exc)}"}
            ), 500
