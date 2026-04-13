from __future__ import annotations

import io
from pathlib import Path
import sys

from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from components.multimodal_image_audio_diagnosis.inference import (  # noqa: E402
    get_inference_pipeline,
)


def test_image_only_requires_review_flag() -> None:
    pipeline = get_inference_pipeline()
    result = pipeline.predict_from_image(b"")
    assert result["requires_dermatologist_review"] is True
    assert result["review_reasons"]
    assert "next_steps" in result
    assert result["diagnostic_status"] == "provisional_image_only"
    assert result["analysis_scope"] == "screening_only"
    assert result["final_diagnosis_locked"] is False
    assert result["recommended_analysis_mode"] == "multimodal_fused"
    assert result["display_disease"]
    assert result["model_used"] == "image_only"
    assert result["warnings"]


def test_text_only_contains_next_steps() -> None:
    pipeline = get_inference_pipeline()
    result = pipeline.predict_from_text("Itchy rash on my arm for 3 days")
    assert "next_steps" in result
    assert isinstance(result["next_steps"], list)


def test_smart_predict_image_only_summary_stays_provisional() -> None:
    pipeline = get_inference_pipeline()
    image = Image.new("RGB", (224, 224), color=(180, 120, 120))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    result = pipeline.smart_predict(text="", image_bytes=buffer.getvalue())
    diagnosis = result["diagnosis"]
    assert diagnosis["diagnostic_status"] == "provisional_image_only"
    assert "provisional" in result["summary"].lower()
