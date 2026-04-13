"""
Smoke test for the face severity endpoint.

Run from backend/:
    python test_severity_api.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from app import app  # noqa: E402
from inference.config import SEVERITY_METADATA_PATH, SEVERITY_MODEL_PATH  # noqa: E402
from components.severity_assessment_tracking import get_severity_model  # noqa: E402


def build_test_image_bytes() -> bytes:
    # Synthetic skin-like image with mild texture to exercise feature extraction.
    arr = np.full((360, 360, 3), [210, 165, 145], dtype=np.uint8)
    arr[120:200, 120:210, 0] = 235
    arr[120:200, 120:210, 1] = 130
    arr[120:200, 120:210, 2] = 130

    image = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def main() -> int:
    severity_model = get_severity_model(
        model_path=SEVERITY_MODEL_PATH,
        metadata_path=SEVERITY_METADATA_PATH,
    )
    if severity_model is None or not severity_model.loaded:
        detail = None if severity_model is None else severity_model.load_error
        print(f"[FAIL] Severity model not loaded: {detail}")
        return 1

    client = app.test_client()
    payload = {
        "image": (io.BytesIO(build_test_image_bytes()), "severity_test.jpg"),
        "track": "false",
        "user_id": "local-smoke-test",
    }
    response = client.post(
        "/api/analyze-severity",
        data=payload,
        content_type="multipart/form-data",
    )

    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(response.get_data(as_text=True))
        return 1

    data = response.get_json() or {}
    required_keys = [
        "severity_level",
        "severity_score",
        "confidence",
        "confidence_level",
        "probabilities",
        "top_predictions",
        "top_probability_gap",
        "feature_vector",
        "normalized_features",
        "thresholds",
        "preprocessing",
        "validation_status",
        "analysis_scope",
        "requires_review",
        "review_reasons",
        "next_steps",
        "limitations",
        "quality_notes",
        "tracking_requested",
        "tracking_blocked_reason",
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"[FAIL] Missing keys: {missing}")
        print(data)
        return 1

    print(f"Severity level: {data['severity_level']}")
    print(f"Severity score: {data['severity_score']}")
    print(f"Confidence: {float(data['confidence']):.1%}")
    print(f"Tracking enabled: {data.get('tracking_enabled')}")
    print("[PASS] /api/analyze-severity integration is working")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
