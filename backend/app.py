"""
SkinAI Flask Backend
====================

Endpoints:
  GET  /api/health             - health check
  GET  /api/status             - model + runtime availability

  POST /api/chat               - conversational diagnosis assistant
  POST /api/analyze            - deprecated safety-blocked image-only endpoint
  POST /api/analyze-fused      - multimodal (image + symptom context) diagnosis
  POST /api/smart-scan         - automated multimodal scan
  POST /api/analyze-skin-care  - skin-type + routine recommendations
  POST /api/analyze-severity   - severity assessment + optional local tracking

  POST /api/profile            - profile helper (Supabase)
  POST /api/journey/start      - start tracking journey (Supabase)
  GET  /api/journey/list       - list journeys (Supabase)

  GET  /api/history            - historical tracking logs (Supabase or CSV fallback)
  GET  /api/stats              - severity trend statistics (Supabase or CSV fallback)
  POST /api/progress           - analyzed check-in log (image or summary)
"""

import datetime
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS


load_dotenv()

# Force UTF-8 console output on Windows to prevent Unicode logging crashes
# (emoji/box characters in startup logs can fail under cp1252).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5001))
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")


logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Ensure `backend/` is importable whether run from repo root or from `backend/`.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from inference.config import (  # noqa: E402
    get_model_status,
)

from components.conversational_diagnosis_assistant.routes import (  # noqa: E402
    register_routes as register_conversational_routes,
)
from components.multimodal_image_audio_diagnosis.routes import (  # noqa: E402
    register_routes as register_multimodal_routes,
)
from components.severity_assessment_tracking.routes import (  # noqa: E402
    register_routes as register_severity_routes,
)
from components.skin_type_skincare_recommendation.routes import (  # noqa: E402
    register_routes as register_skin_type_routes,
)


def _load_validation_summary(models: dict) -> tuple[dict, str | None]:
    """
    Return cached deployment-readiness statuses without forcing heavy model loads.
    """
    report_candidates = [
        BACKEND_DIR / "reports" / "validation_report_quick.json",
        BACKEND_DIR / "reports" / "validation_report.json",
    ]

    for report_path in report_candidates:
        if not report_path.exists():
            continue
        try:
            with open(report_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            summary = payload.get("deployment_readiness")
            if isinstance(summary, dict) and summary:
                return (
                    {
                        "text_component": str(summary.get("text_component", "unknown")),
                        "image_component": str(summary.get("image_component", "unknown")),
                        "fused_component": str(summary.get("fused_component", "unknown")),
                        "skin_type_component": str(summary.get("skin_type_component", "unknown")),
                        "severity_component": str(summary.get("severity_component", "unknown")),
                    },
                    str(report_path),
                )
        except Exception as exc:
            logger.debug("Validation report read failed for %s: %s", report_path, exc)

    fallback = {
        "text_component": (
            "available"
            if (models.get("distilbert_model") or models.get("text_model_legacy"))
            else "missing"
        ),
        "image_component": "available" if models.get("image_model") else "missing",
        "fused_component": (
            "available"
            if models.get("image_model")
            and (models.get("distilbert_model") or models.get("text_model_legacy"))
            else "missing"
        ),
        "skin_type_component": (
            "available"
            if models.get("skin_type_model") and models.get("skin_type_label_map")
            else "missing"
        ),
        "severity_component": (
            "available"
            if models.get("severity_model") and models.get("severity_metadata")
            else "missing"
        ),
    }
    return fallback, None


def _build_pending_issues(validation_summary: dict) -> list[dict[str, str]]:
    summary = validation_summary or {}
    issues: list[dict[str, str]] = []

    # Skin Type Check
    sk_status = summary.get("skin_type_component")
    if sk_status in {"operational_only_unlabeled", "validation_missing"}:
        issues.append(
            {
                "component": "skin_type_skincare_recommendation",
                "severity": "high",
                "code": "skin_type_validation_missing",
                "message": (
                    "Skin-type guidance is operational, but there is no labeled benchmark in the repo "
                    "to support formal accuracy claims."
                ),
                "helper": "backend/tools/validation/benchmark_readiness.py",
            }
        )
    elif sk_status == "not_ready":
        issues.append(
            {
                "component": "skin_type_skincare_recommendation",
                "severity": "medium",
                "code": "skin_type_low_accuracy",
                "message": (
                    "Skin-type benchmark is ready, but accuracy is below the 75% bar for internal testing."
                ),
                "helper": "backend/reports/validation_report.json",
            }
        )

    # Severity Check
    sev_status = summary.get("severity_component")
    if sev_status in {"operational_only_unlabeled", "validation_missing"}:
        issues.append(
            {
                "component": "severity_assessment_tracking",
                "severity": "high",
                "code": "severity_validation_missing",
                "message": (
                    "Severity assessment is operational, but there is no labeled severity benchmark in the repo."
                ),
                "helper": "backend/tools/validation/benchmark_readiness.py",
            }
        )
    elif sev_status == "not_ready":
        issues.append(
            {
                "component": "severity_assessment_tracking",
                "severity": "medium",
                "code": "severity_low_accuracy",
                "message": (
                    "Severity benchmark is ready, but accuracy is below the 75% bar for internal testing."
                ),
                "helper": "backend/reports/validation_report.json",
            }
        )

    return issues


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "service": "skinai-backend",
            "timestamp": datetime.datetime.now().isoformat(),
        }
    )


@app.get("/api/status")
def status():
    # File presence for models/datasets.
    models = get_model_status()
    validation_summary, validation_source = _load_validation_summary(models)
    pending_issues = _build_pending_issues(validation_summary)

    # Keep this endpoint lightweight. It reports artifact readiness and cached
    # validation status instead of force-loading every heavy model on first hit.
    inference_available = bool(
        models.get("image_model")
        and (models.get("distilbert_model") or models.get("text_model_legacy"))
    )
    skin_type_available = bool(
        models.get("skin_type_model") and models.get("skin_type_label_map")
    )
    severity_available = bool(
        models.get("severity_model") and models.get("severity_metadata")
    )

    skin_type_error = None if skin_type_available else "skin-type artifacts missing"
    severity_error = None if severity_available else "severity artifacts missing"

    return jsonify(
        {
            "status": "online",
            "service": "online",
            "models": models,
            "inference_available": inference_available,
            "skin_type_inference_available": skin_type_available,
            "severity_inference_available": severity_available,
            "python_executable": sys.executable,
            "skin_type_model_error": skin_type_error,
            "severity_model_error": severity_error,
            "validation_summary": validation_summary,
            "validation_report_source": validation_source,
            "pending_issues": pending_issues,
            "image_only_endpoint_enabled": False,
            "recommended_paths": {
                "diagnosis": "/api/analyze-fused",
                "smart_scan": "/api/smart-scan",
                "skin_type": "/api/analyze-skin-care",
                "severity": "/api/analyze-severity",
            },
            "default_port": PORT,
            "safety_configuration": {
                "image_only_endpoint_enabled": False,
                "recommended_diagnosis_flow": "multimodal_fused",
            },
            "timestamp": datetime.datetime.now().isoformat(),
        }
    )


# Register component-owned routes.
register_conversational_routes(app)
register_multimodal_routes(app)
register_skin_type_routes(app)
register_severity_routes(app)


if __name__ == "__main__":
    logger.info("Starting backend (%s) on http://%s:%s (debug=%s)", FLASK_ENV, HOST, PORT, FLASK_DEBUG)
    app.run(debug=FLASK_DEBUG, port=PORT, host=HOST)
