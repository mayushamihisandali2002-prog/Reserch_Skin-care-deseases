"""
Benchmark preflight checks for the remaining validation gaps.

This script does not fabricate labels or scores. It only reports whether the
skin-type and severity benchmark folders are populated and structurally valid.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from inference.config import SEVERITY_DATA_DIR, SKIN_TYPE_DATASET_DIR  # noqa: E402


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
EXPECTED_SKIN_TYPE_DIRS = ("Dry", "Oily", "Combination")
EXPECTED_SEVERITY_LEVELS = {"mild", "moderate", "severe"}
SEVERITY_BENCHMARK_DIR = SEVERITY_DATA_DIR / "severity_benchmark"
SEVERITY_LABELS_PATH = SEVERITY_BENCHMARK_DIR / "labels.csv"


def iter_images(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [
        file_path
        for file_path in sorted(path.iterdir())
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def check_skin_type_benchmark() -> dict[str, Any]:
    class_counts: dict[str, int] = {}
    missing_dirs: list[str] = []
    empty_dirs: list[str] = []

    for class_name in EXPECTED_SKIN_TYPE_DIRS:
        class_dir = SKIN_TYPE_DATASET_DIR / class_name
        if not class_dir.exists():
            missing_dirs.append(class_name)
            class_counts[class_name] = 0
            continue
        class_counts[class_name] = len(iter_images(class_dir))
        if class_counts[class_name] == 0:
            empty_dirs.append(class_name)

    ready = not missing_dirs and not empty_dirs
    issues: list[str] = []
    if missing_dirs:
        issues.append(
            "Missing class folders: " + ", ".join(missing_dirs)
        )
    if empty_dirs:
        issues.append(
            "No labeled images found in: " + ", ".join(empty_dirs)
        )

    return {
        "ready": ready,
        "dataset_dir": str(SKIN_TYPE_DATASET_DIR),
        "expected_class_dirs": list(EXPECTED_SKIN_TYPE_DIRS),
        "class_image_counts": class_counts,
        "issues": issues,
        "next_steps": [
            "Place real labeled images into Dry, Oily, and Combination.",
            "Re-run backend/tools/validation/evaluate_models.py after the folders are populated.",
        ],
    }


def _resolve_severity_image_path(rel_path: str) -> Path:
    direct = SEVERITY_BENCHMARK_DIR / rel_path
    nested = SEVERITY_BENCHMARK_DIR / "images" / rel_path
    return direct if direct.exists() else nested


def check_severity_benchmark() -> dict[str, Any]:
    issues: list[str] = []
    valid_rows = 0
    invalid_rows: list[dict[str, Any]] = []

    if not SEVERITY_LABELS_PATH.exists():
        return {
            "ready": False,
            "benchmark_dir": str(SEVERITY_BENCHMARK_DIR),
            "labels_manifest": str(SEVERITY_LABELS_PATH),
            "valid_rows": 0,
            "issues": ["labels.csv is missing."],
            "next_steps": [
                "Create labels.csv from labels.template.csv.",
                "Add one row per labeled image using image_path and severity_level.",
            ],
        }

    with open(SEVERITY_LABELS_PATH, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        required = {"image_path", "severity_level"}
        if not required.issubset(fieldnames):
            missing = sorted(required - fieldnames)
            return {
                "ready": False,
                "benchmark_dir": str(SEVERITY_BENCHMARK_DIR),
                "labels_manifest": str(SEVERITY_LABELS_PATH),
                "valid_rows": 0,
                "issues": [f"labels.csv is missing required columns: {', '.join(missing)}"],
                "next_steps": [
                    "Use the exact columns: image_path,severity_level",
                ],
            }

        for row_number, row in enumerate(reader, start=2):
            image_path = str(row.get("image_path") or "").strip()
            severity_level = str(row.get("severity_level") or "").strip().lower()
            resolved_path = _resolve_severity_image_path(image_path) if image_path else None

            row_errors: list[str] = []
            if not image_path:
                row_errors.append("missing image_path")
            elif not resolved_path or not resolved_path.exists():
                row_errors.append("image file not found")
            elif resolved_path.suffix.lower() not in IMAGE_EXTENSIONS:
                row_errors.append("unsupported image extension")

            if severity_level not in EXPECTED_SEVERITY_LEVELS:
                row_errors.append("invalid severity_level")

            if row_errors:
                invalid_rows.append(
                    {
                        "row": row_number,
                        "image_path": image_path,
                        "severity_level": severity_level,
                        "errors": row_errors,
                    }
                )
                continue

            valid_rows += 1

    if valid_rows == 0:
        issues.append("labels.csv exists, but it does not contain any valid benchmark rows.")
    if invalid_rows:
        issues.append(f"{len(invalid_rows)} invalid manifest rows detected.")

    return {
        "ready": valid_rows > 0 and not invalid_rows,
        "benchmark_dir": str(SEVERITY_BENCHMARK_DIR),
        "labels_manifest": str(SEVERITY_LABELS_PATH),
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows[:20],
        "issues": issues,
        "next_steps": [
            "Store the benchmark images under severity_benchmark/images.",
            "Label each image as mild, moderate, or severe in labels.csv.",
            "Re-run backend/tools/validation/evaluate_models.py after the manifest is valid.",
        ],
    }


def build_report() -> dict[str, Any]:
    skin_type = check_skin_type_benchmark()
    severity = check_severity_benchmark()
    return {
        "ready": bool(skin_type["ready"] and severity["ready"]),
        "skin_type_benchmark": skin_type,
        "severity_benchmark": severity,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check benchmark readiness for pending validation components.")
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_DIR / "reports" / "benchmark_readiness.json",
        help="Optional JSON output path.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when any benchmark is still incomplete.",
    )
    args = parser.parse_args()

    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    skin_ready = report["skin_type_benchmark"]["ready"]
    severity_ready = report["severity_benchmark"]["ready"]
    print(f"Skin-type benchmark ready: {skin_ready}")
    print(f"Severity benchmark ready: {severity_ready}")
    print(f"Report written to: {args.output}")

    if args.strict and not report["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
