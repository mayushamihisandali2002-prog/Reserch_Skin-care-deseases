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

sys.path.insert(0, str(Path(__file__).parent))

from app import app, severity_model  # noqa: E402


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
        "probabilities",
        "feature_vector",
        "normalized_features",
        "thresholds",
        "preprocessing",
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
