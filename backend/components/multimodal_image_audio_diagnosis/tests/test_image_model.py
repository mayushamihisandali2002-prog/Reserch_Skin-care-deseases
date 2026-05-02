from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image


BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from components.multimodal_image_audio_diagnosis.image_model import (  # noqa: E402
    DISEASE_LABELS,
    get_image_model,
)
from inference.config import IMAGE_MODEL_PATH  # noqa: E402


def _build_test_image_bytes() -> bytes:
    image = Image.new("RGB", (224, 224), color=(200, 100, 100))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_image_model_loads_using_deployed_wrapper() -> None:
    model = get_image_model(IMAGE_MODEL_PATH)

    assert model is not None
    assert model.loaded is True
    assert model.output_classes == len(model.source_label_map)
    assert len(model.target_label_map) == len(DISEASE_LABELS)


def test_image_model_predicts_valid_probability_vector() -> None:
    model = get_image_model(IMAGE_MODEL_PATH)
    disease, confidence, probs = model.predict_from_bytes(_build_test_image_bytes())

    assert model.loaded is True
    assert disease in set(DISEASE_LABELS.values()) | {"Unknown"}
    assert 0.0 <= float(confidence) <= 1.0
    assert probs.shape[0] == len(DISEASE_LABELS)
    assert np.isfinite(probs).all()
    assert np.isclose(float(np.sum(probs)), 1.0, atol=1e-3)
