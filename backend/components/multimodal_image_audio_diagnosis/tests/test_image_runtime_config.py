import json
import shutil
from pathlib import Path
import sys
from uuid import uuid4

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


def _make_local_temp_dir() -> Path:
    temp_root = Path(__file__).resolve().parent / "_runtime_config_tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    test_dir = temp_root / uuid4().hex
    test_dir.mkdir()
    return test_dir


def test_runtime_config_defaults_when_metadata_missing():
    temp_dir = _make_local_temp_dir()
    try:
        model = _make_model(temp_dir / "missing.json")
        model._load_runtime_config()

        assert model.runtime_config["source"] == "defaults"
        assert model.runtime_config["logit_temperature"] == DEFAULT_LOGIT_TEMPERATURE
        assert model.runtime_config["logit_blend_weight"] == DEFAULT_LOGIT_BLEND_WEIGHT
        assert (
            model.runtime_config["prototype_blend_weight"]
            == DEFAULT_PROTOTYPE_BLEND_WEIGHT
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_runtime_config_reads_recommended_operating_point():
    temp_dir = _make_local_temp_dir()
    try:
        metadata_path = temp_dir / "image_model.json"
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
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
