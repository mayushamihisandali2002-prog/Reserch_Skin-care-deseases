import logging
from typing import Any, Optional

from flask import jsonify, request

from services.supabase_service import SupabaseService

from . import get_inference_pipeline
from .audio_transcription import transcribe_uploaded_audio


logger = logging.getLogger(__name__)


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


def register_routes(app) -> None:
    """
    Multimodal image/audio diagnosis routes.
    """

    @app.route("/api/analyze", methods=["POST", "OPTIONS"])
    def analyze():
        """
        Deprecated image-only diagnosis endpoint.
        """
        if request.method == "OPTIONS":
            return "", 204

        image_file = request.files.get("image") or request.files.get("file")

        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        return _symptom_context_required_response(
            "Image-only diagnosis has been turned off because the image model is not clinically reliable on its own."
        )

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

        try:
            pipe = get_inference_pipeline()
        except Exception as exc:
            logger.exception("Inference pipeline unavailable")
            return jsonify({"error": f"Inference pipeline unavailable: {exc}"}), 503

        image_file = request.files.get("image") or request.files.get("file")
        text = request.form.get("text", "").strip()
        audio_file = request.files.get("audio")
        journey_id = request.form.get("journey_id")
        user_id = request.form.get("user_id", "anonymous")

        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        image_bytes = image_file.read()

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

        # Automated Logging
        if user_id != "anonymous" and report.get("diagnosis"):
            try:
                diag = report["diagnosis"]
                SupabaseService.save_skin_analysis(
                    user_id=user_id,
                    image_url="uploaded_via_fused_analyze",
                    predicted_disease=diag.get("disease", "Unknown"),
                    confidence=diag.get("confidence", 0.0),
                    confidence_level=diag.get("confidence_level", "low"),
                    journey_id=journey_id,
                    body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
                    model_used="automated_fused",
                )
            except Exception as exc:
                logger.warning("Auto-log failed: %s", exc)

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

            image_bytes = image_file.read() if image_file else None

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

            # Automated Logging
            if user_id and user_id != "anonymous":
                try:
                    SupabaseService.save_skin_analysis(
                        user_id=user_id,
                        image_url="uploaded_via_smart_scan",
                        predicted_disease=report["diagnosis"]["disease"],
                        confidence=report["diagnosis"]["confidence"],
                        confidence_level=report["diagnosis"]["confidence_level"],
                        treatments=report["diagnosis"].get("treatments"),
                        journey_id=journey_id,
                        body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
                        model_used="smart_scan_fused",
                    )
                except Exception as exc:
                    logger.warning("Failed to auto-log analysis: %s", exc)

            return jsonify(report)
        except Exception as exc:
            logger.exception("Smart scan failed")
            return jsonify(
                {"status": "error", "message": f"Automated analysis failed: {str(exc)}"}
            ), 500

