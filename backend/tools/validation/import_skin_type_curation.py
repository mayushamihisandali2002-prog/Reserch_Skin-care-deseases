"""
Import reviewed skin-type images into the benchmark folders.

The manifest is intentionally manual. A reviewer must decide the target label
for each source image before importing it into the formal benchmark dataset.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from inference.config import SKIN_TYPE_DATASET_DIR, SKIN_TYPE_HF_DATA_DIR  # noqa: E402


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
LABEL_DIRS = {
    "dry": "Dry",
    "oily": "Oily",
    "combination": "Combination",
}


def resolve_source_path(raw_path: str, source_root: Path) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return source_root / raw_path


def unique_destination_path(destination_dir: Path, filename: str) -> Path:
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = destination_dir / filename
    counter = 1
    while candidate.exists():
        candidate = destination_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Import reviewed skin-type images into benchmark folders.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=SKIN_TYPE_DATASET_DIR / "curation_manifest.csv",
        help="CSV manifest with source_path,target_label columns.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=SKIN_TYPE_HF_DATA_DIR,
        help="Base folder for relative source paths.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the manifest without copying files.",
    )
    args = parser.parse_args()

    if not args.manifest.exists():
        print(f"Manifest not found: {args.manifest}")
        return 1

    imported = 0
    skipped = 0
    errors = 0

    with open(args.manifest, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"source_path", "target_label"}
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            print(f"Manifest missing required columns: {', '.join(sorted(missing_columns))}")
            return 1

        for row_number, row in enumerate(reader, start=2):
            raw_source = str(row.get("source_path") or "").strip()
            raw_label = str(row.get("target_label") or "").strip().lower()
            review_status = str(row.get("review_status") or "approved").strip().lower()

            if not raw_source or not raw_label:
                print(f"Row {row_number}: missing source_path or target_label")
                errors += 1
                continue

            if review_status not in {"approved", "accept", "accepted"}:
                skipped += 1
                continue

            destination_label = LABEL_DIRS.get(raw_label)
            if destination_label is None:
                print(
                    f"Row {row_number}: unsupported target_label '{raw_label}'. "
                    "Use dry, oily, or combination."
                )
                errors += 1
                continue

            source_path = resolve_source_path(raw_source, args.source_root)
            if not source_path.exists() or not source_path.is_file():
                print(f"Row {row_number}: source file not found: {source_path}")
                errors += 1
                continue

            if source_path.suffix.lower() not in IMAGE_EXTENSIONS:
                print(f"Row {row_number}: unsupported file type: {source_path.name}")
                errors += 1
                continue

            destination_dir = SKIN_TYPE_DATASET_DIR / destination_label
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_path = unique_destination_path(destination_dir, source_path.name)

            if args.dry_run:
                print(f"DRY RUN: {source_path} -> {destination_path}")
            else:
                shutil.copy2(source_path, destination_path)
                print(f"Imported: {source_path} -> {destination_path}")
            imported += 1

    print(
        f"Completed with imported={imported}, skipped={skipped}, errors={errors}, "
        f"dry_run={args.dry_run}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
