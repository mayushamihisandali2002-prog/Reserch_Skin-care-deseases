from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset


BACKEND_DIR = Path(__file__).resolve().parents[3]
SKIN_TYPE_REFERENCE_DATASET_DIR = (
    BACKEND_DIR
    / "assets"
    / "data"
    / "skin_type_skincare_recommendation"
    / "skin_types_hf"
)


def _resolve_label_name(raw_label, label_map: dict[int, str]) -> str:
    if isinstance(raw_label, str):
        return raw_label.strip().lower()
    return label_map.get(int(raw_label), f"class_{raw_label}")


def download_skin_types(
    *,
    dataset_id: str,
    split: str = "train",
    limit_per_class: int = 200,
) -> None:
    print(f"[Data] Downloading skin-type reference dataset: {dataset_id} ({split})")

    output_dir = SKIN_TYPE_REFERENCE_DATASET_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        ds = load_dataset(dataset_id, split=split, streaming=True)
    except Exception as exc:
        raise RuntimeError(
            f"Unable to load dataset '{dataset_id}'. "
            "Provide a valid Hugging Face dataset ID with image and label fields."
        ) from exc

    label_map = {0: "dry", 1: "normal", 2: "oily"}
    counts: dict[str, int] = {}

    for index, item in enumerate(ds):
        if "image" not in item or "label" not in item:
            raise RuntimeError(
                "Dataset samples must contain 'image' and 'label' fields."
            )

        label_name = _resolve_label_name(item["label"], label_map)
        counts.setdefault(label_name, 0)
        if counts[label_name] >= limit_per_class:
            continue

        class_dir = output_dir / label_name
        class_dir.mkdir(parents=True, exist_ok=True)

        image = item["image"]
        image_path = class_dir / f"img_{counts[label_name]}.jpg"
        image.save(image_path)
        counts[label_name] += 1

        if index % 25 == 0:
            print(f"   Progress: {counts}", end="\r")

    print("\n[Done] Skin type reference dataset prepared.")
    print(f"[Saved] {output_dir}")
    print(
        "[Note] This script fills skin_types_hf/ only. "
        "Do not treat these raw files as benchmark data until they are manually curated "
        "into Dry/Oily/Combination under skin_types/."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a raw/reference skin-type dataset into skin_types_hf/."
    )
    parser.add_argument(
        "--dataset-id",
        required=True,
        help="Hugging Face dataset ID with image and label fields.",
    )
    parser.add_argument(
        "--split",
        default="train",
        help="Dataset split to stream. Default: train",
    )
    parser.add_argument(
        "--limit-per-class",
        type=int,
        default=200,
        help="Maximum number of images to save per label. Default: 200",
    )
    args = parser.parse_args()

    download_skin_types(
        dataset_id=args.dataset_id,
        split=args.split,
        limit_per_class=args.limit_per_class,
    )


if __name__ == "__main__":
    main()
