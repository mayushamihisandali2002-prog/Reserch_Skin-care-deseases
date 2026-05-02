from __future__ import annotations

import csv
import importlib
import io
import shutil
import sys
from pathlib import Path

from PIL import Image


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
TEST_TMP_DIR = BACKEND_DIR / "assets" / "cache" / "pytest_benchmark_tools"

sys.path.insert(0, str(BACKEND_DIR))

from tools.validation import benchmark_readiness  # noqa: E402


def _reset_tmp_dir() -> Path:
    if TEST_TMP_DIR.exists():
        shutil.rmtree(TEST_TMP_DIR)
    TEST_TMP_DIR.mkdir(parents=True, exist_ok=True)
    return TEST_TMP_DIR


def _write_test_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (32, 32), color=(200, 160, 140))
    image.save(path, format="JPEG")


def test_benchmark_readiness_reports_current_missing_benchmarks() -> None:
    report = benchmark_readiness.build_report()

    assert report["ready"] is False
    assert report["skin_type_benchmark"]["ready"] is False
    assert report["severity_benchmark"]["ready"] is False
    assert report["skin_type_benchmark"]["class_image_counts"]["Dry"] == 0
    assert "labels.csv is missing." in report["severity_benchmark"]["issues"]


def test_benchmark_readiness_validates_complete_synthetic_benchmarks() -> None:
    tmp_dir = _reset_tmp_dir()
    skin_root = tmp_dir / "skin_types"
    severity_root = tmp_dir / "severity_benchmark"

    for class_name in ("Dry", "Oily", "Combination"):
        _write_test_image(skin_root / class_name / f"{class_name.lower()}_1.jpg")

    _write_test_image(severity_root / "images" / "mild_1.jpg")
    _write_test_image(severity_root / "images" / "moderate_1.jpg")
    _write_test_image(severity_root / "images" / "severe_1.jpg")
    (severity_root / "labels.csv").write_text(
        "\n".join(
            [
                "image_path,severity_level",
                "images/mild_1.jpg,mild",
                "images/moderate_1.jpg,moderate",
                "images/severe_1.jpg,severe",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    original_skin_dir = benchmark_readiness.SKIN_TYPE_DATASET_DIR
    original_severity_dir = benchmark_readiness.SEVERITY_BENCHMARK_DIR
    original_severity_labels = benchmark_readiness.SEVERITY_LABELS_PATH
    try:
        benchmark_readiness.SKIN_TYPE_DATASET_DIR = skin_root
        benchmark_readiness.SEVERITY_BENCHMARK_DIR = severity_root
        benchmark_readiness.SEVERITY_LABELS_PATH = severity_root / "labels.csv"

        report = benchmark_readiness.build_report()
        assert report["ready"] is True
        assert report["skin_type_benchmark"]["ready"] is True
        assert report["severity_benchmark"]["ready"] is True
        assert report["severity_benchmark"]["valid_rows"] == 3
    finally:
        benchmark_readiness.SKIN_TYPE_DATASET_DIR = original_skin_dir
        benchmark_readiness.SEVERITY_BENCHMARK_DIR = original_severity_dir
        benchmark_readiness.SEVERITY_LABELS_PATH = original_severity_labels


def test_import_skin_type_curation_copies_reviewed_images() -> None:
    tmp_dir = _reset_tmp_dir()
    source_root = tmp_dir / "source"
    benchmark_root = tmp_dir / "benchmark"
    manifest_path = tmp_dir / "curation_manifest.csv"

    source_image = source_root / "approved" / "candidate.jpg"
    _write_test_image(source_image)

    with open(manifest_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_path", "target_label", "review_status", "reviewer", "notes"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "source_path": str(source_image.relative_to(source_root)),
                "target_label": "dry",
                "review_status": "approved",
                "reviewer": "qa",
                "notes": "synthetic test image",
            }
        )

    module = importlib.import_module("tools.validation.import_skin_type_curation")
    original_dataset_dir = module.SKIN_TYPE_DATASET_DIR
    original_source_root = module.SKIN_TYPE_HF_DATA_DIR
    original_argv = sys.argv[:]
    original_stdout = sys.stdout
    capture = io.StringIO()
    try:
        module.SKIN_TYPE_DATASET_DIR = benchmark_root
        module.SKIN_TYPE_HF_DATA_DIR = source_root
        sys.argv = [
            "import_skin_type_curation.py",
            "--manifest",
            str(manifest_path),
            "--source-root",
            str(source_root),
        ]
        sys.stdout = capture
        exit_code = module.main()
    finally:
        sys.argv = original_argv
        sys.stdout = original_stdout
        module.SKIN_TYPE_DATASET_DIR = original_dataset_dir
        module.SKIN_TYPE_HF_DATA_DIR = original_source_root

    assert exit_code == 0
    imported_image = benchmark_root / "Dry" / "candidate.jpg"
    assert imported_image.exists()
    assert "Imported:" in capture.getvalue()
