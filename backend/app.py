"""
SkinAI Flask Backend
====================

Endpoints:
  GET  /api/health             - health check
  GET  /api/status             - model + runtime availability

  POST /api/chat               - conversational diagnosis assistant
  POST /api/analyze            - image-only diagnosis
  POST /api/analyze-fused      - multimodal (image + text) diagnosis
  POST /api/smart-scan         - automated multimodal scan
  POST /api/analyze-skin-care  - skin-type + routine recommendations
  POST /api/analyze-severity   - severity assessment + optional local tracking

  POST /api/profile            - profile helper (Supabase)
  POST /api/journey/start      - start tracking journey (Supabase)
  GET  /api/journey/list       - list journeys (Supabase)

  GET  /api/history            - historical tracking logs (CSV-backed)
  GET  /api/stats              - severity trend statistics (CSV-backed)
  POST /api/progress           - analyzed check-in log (image or summary)
"""

import datetime
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
PORT = int(os.getenv("PORT", 5000))
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
    SEVERITY_METADATA_PATH,
    SEVERITY_MODEL_PATH,
    SKIN_TYPE_LABEL_MAP_PATH,
    SKIN_TYPE_MODEL_PATH,
    get_model_status,
)

from components.multimodal_image_audio_diagnosis import get_inference_pipeline  # noqa: E402
from components.severity_assessment_tracking import get_severity_model  # noqa: E402
from components.skin_type_skincare_recommendation import get_skin_type_model  # noqa: E402

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


app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers="*",
    methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
)


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

    # Runtime availability (best-effort; heavy models load lazily on first call).
    inference_available = False
    skin_type_available = False
    severity_available = False
    skin_type_error = None
    severity_error = None

    try:
        pipe = get_inference_pipeline()
        inference_available = pipe is not None
    except Exception as exc:
        logger.debug("Inference availability check failed: %s", exc)

    try:
        skin_model = get_skin_type_model(
            model_path=SKIN_TYPE_MODEL_PATH,
            label_map_path=SKIN_TYPE_LABEL_MAP_PATH,
        )
        skin_type_available = bool(skin_model and getattr(skin_model, "loaded", False))
        if not skin_type_available and skin_model is not None:
            skin_type_error = getattr(skin_model, "load_error", None)
    except Exception as exc:
        skin_type_error = str(exc)

    try:
        sev_model = get_severity_model(
            model_path=SEVERITY_MODEL_PATH,
            metadata_path=SEVERITY_METADATA_PATH,
        )
        severity_available = bool(sev_model and getattr(sev_model, "loaded", False))
        if not severity_available and sev_model is not None:
            severity_error = getattr(sev_model, "load_error", None)
    except Exception as exc:
        severity_error = str(exc)

    return jsonify(
        {
            "service": "online",
            "models": models,
            "inference_available": inference_available,
            "skin_type_inference_available": skin_type_available,
            "severity_inference_available": severity_available,
            "python_executable": sys.executable,
            "skin_type_model_error": skin_type_error,
            "severity_model_error": severity_error,
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

