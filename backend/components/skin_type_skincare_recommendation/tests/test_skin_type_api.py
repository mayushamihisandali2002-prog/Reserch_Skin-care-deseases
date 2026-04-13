"""
Smoke test for the skin-type integration endpoint.

Run from backend/:
    python test_skin_type_api.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image


BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from app import app  # noqa: E402
from inference.config import SKIN_TYPE_LABEL_MAP_PATH, SKIN_TYPE_MODEL_PATH  # noqa: E402
from components.skin_type_skincare_recommendation import get_skin_type_model  # noqa: E402


def build_test_image_bytes() -> bytes:
    img = Image.new("RGB", (320, 320), color=(205, 165, 145))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def main() -> int:
    skin_type_model = get_skin_type_model(
        model_path=SKIN_TYPE_MODEL_PATH,
        label_map_path=SKIN_TYPE_LABEL_MAP_PATH,
    )
    if skin_type_model is None or not skin_type_model.loaded:
        detail = None if skin_type_model is None else skin_type_model.load_error
        print(f"[FAIL] Skin-type model not loaded: {detail}")
        return 1

    client = app.test_client()
    payload = {
        "image": (io.BytesIO(build_test_image_bytes()), "test.jpg"),
        "allergies": "fragrance,salicylic_acid_bha",
        "goals": "oil_control,dark_spots",
        "routine_level": "simple",
        "budget": "medium",
        "tight_after_wash": "no",
        "shiny_after_2_3h": "yes",
    }
    response = client.post(
        "/api/analyze-skin-care",
        data=payload,
        content_type="multipart/form-data",
    )

    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(response.get_data(as_text=True))
        return 1

    data = response.get_json() or {}
    required_keys = [
        "skin_type",
        "model_skin_type",
        "questionnaire_adjusted",
        "skin_type_confidence",
        "probabilities",
        "top_predictions",
        "top_probability_gap",
        "user_inputs",
        "recommendations",
        "recommended_ingredients",
        "avoid_ingredients",
        "routine",
        "note",
        "disclaimer",
        "validation_status",
        "analysis_scope",
        "requires_review",
        "review_reasons",
        "next_steps",
        "limitations",
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"[FAIL] Missing keys: {missing}")
        print(data)
        return 1

    print(f"Skin type: {data['skin_type']}")
    print(f"Confidence: {float(data['skin_type_confidence']):.1%}")
    print(f"User inputs: {data['user_inputs']}")
    print(f"Safe ingredients: {data['recommendations'].get('safe_ingredients', [])}")
    print(f"Avoid ingredients: {data['recommendations'].get('avoid_ingredients', [])}")
    print("[PASS] /api/analyze-skin-care integration is working")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
