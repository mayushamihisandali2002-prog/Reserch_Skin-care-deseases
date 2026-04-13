import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from components.multimodal_image_audio_diagnosis.image_model import (
    DEFAULT_LOGIT_BLEND_WEIGHT,
    DEFAULT_LOGIT_TEMPERATURE,
    DEFAULT_PROTOTYPE_BLEND_WEIGHT,
    ResNetImageModel,
)


def _make_model(metadata_path: Path) -> ResNetImageModel:
    model = ResNetImageModel.__new__(ResNetImageModel)
    model.metadata_path = metadata_path
    model.runtime_config = {
        "logit_temperature": DEFAULT_LOGIT_TEMPERATURE,
        "logit_blend_weight": DEFAULT_LOGIT_BLEND_WEIGHT,
        "prototype_blend_weight": DEFAULT_PROTOTYPE_BLEND_WEIGHT,
        "source": "defaults",
    }
    return model


def test_runtime_config_defaults_when_metadata_missing(tmp_path):
    model = _make_model(tmp_path / "missing.json")
    model._load_runtime_config()

    assert model.runtime_config["source"] == "defaults"
    assert model.runtime_config["logit_temperature"] == DEFAULT_LOGIT_TEMPERATURE
    assert model.runtime_config["logit_blend_weight"] == DEFAULT_LOGIT_BLEND_WEIGHT
    assert (
        model.runtime_config["prototype_blend_weight"]
        == DEFAULT_PROTOTYPE_BLEND_WEIGHT
    )


def test_runtime_config_reads_recommended_operating_point(tmp_path):
    metadata_path = tmp_path / "image_model.json"
    metadata_path.write_text(
        json.dumps(
            {
                "recommended_operating_point": {
                    "logit_temperature": 1.2,
                    "logit_blend_weight": 0.8,
                    "prototype_blend_weight": 0.2,
                }
            }
        ),
        encoding="utf-8",
    )
    model = _make_model(metadata_path)

    model._load_runtime_config()

    assert model.runtime_config["logit_temperature"] == 1.2
    assert model.runtime_config["logit_blend_weight"] == 0.8
    assert model.runtime_config["prototype_blend_weight"] == 0.2
    assert model.runtime_config["source"] == str(metadata_path)
