import logging

from flask import jsonify, request

from services.supabase_service import SupabaseService

from . import get_inference_pipeline
from .audio_transcription import transcribe_uploaded_audio


logger = logging.getLogger(__name__)


def register_routes(app) -> None:
    """
    Multimodal image/audio diagnosis routes.
    """

    @app.route("/api/analyze", methods=["POST", "OPTIONS"])
    def analyze():
        """
        Image-only skin disease diagnosis via the automated smart_predict pipeline.
        """
        if request.method == "OPTIONS":
            return "", 204

        try:
            pipe = get_inference_pipeline()
        except Exception as exc:
            logger.exception("Inference pipeline unavailable")
            return jsonify({"error": f"Inference pipeline unavailable: {exc}"}), 503

        image_file = request.files.get("image") or request.files.get("file")
        journey_id = request.form.get("journey_id")
        user_id = request.form.get("user_id", "anonymous")

        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        image_bytes = image_file.read()

        # Journey context lookup
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
                text="",
                image_bytes=image_bytes,
                journey_id=journey_id,
                target_body_part=target_part,
            )
        except Exception as exc:
            msg = str(exc)
            if "cannot identify image file" in msg.lower():
                return jsonify({"error": "Invalid image file format", "detail": msg}), 400
            logger.exception("Image prediction failed")
            return jsonify({"error": f"Analysis failed: {exc}"}), 500

        # Automated Logging
        if user_id != "anonymous":
            try:
                SupabaseService.save_skin_analysis(
                    user_id=user_id,
                    image_url="uploaded_via_analyze",
                    predicted_disease=report["diagnosis"]["disease"],
                    confidence=report["diagnosis"]["confidence"],
                    confidence_level=report["diagnosis"]["confidence_level"],
                    journey_id=journey_id,
                    body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
                    model_used="automated_analyze",
                )
            except Exception as exc:
                logger.warning("Auto-log failed: %s", exc)

        return jsonify(report)

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
        if audio_file and not text:
            transcript, _, _ = transcribe_uploaded_audio(audio_file)

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

