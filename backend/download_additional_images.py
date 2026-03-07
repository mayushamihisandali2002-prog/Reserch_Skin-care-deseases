#!/usr/bin/env python
"""
Populate the training dataset by copying images from the local DermNet archive.
DermNet is located at: d:/Research/archive_images2/train/
"""
import shutil
import os
from pathlib import Path
from tqdm import tqdm

SOURCE_ROOT = Path("d:/Research/archive_images2/train")
DEST_ROOT = Path("d:/Research/zip skin/Reserch_Skin-care-deseases/assets/data/combined_images")

# Clean existing destination to avoid confusion
if DEST_ROOT.exists():
    shutil.rmtree(DEST_ROOT)
DEST_ROOT.mkdir(parents=True, exist_ok=True)

# 0: Eczema, 1: Dermatitis, 2: Psoriasis, 3: Acne, 4: Urticaria, 5: Pigmentation
MAPPING = {
    "Eczema Photos": 0,
    "Atopic Dermatitis Photos": 1,
    "Poison Ivy Photos and other Contact Dermatitis": 1,
    "Psoriasis pictures Lichen Planus and related diseases": 2,
    "Acne and Rosacea Photos": 3,
    "Urticaria Hives": 4,
    "Light Diseases and Disorders of Pigmentation": 5,
}

# Folder names (Windows safe)
FOLDER_NAMES = {
    0: "Eczema",
    1: "Dermatitis",
    2: "Psoriasis",
    3: "Acne",
    4: "Urticaria",
    5: "Pigmentation_Dark_Spots",
}

print(f"[Populate] Copying images from {SOURCE_ROOT} to {DEST_ROOT}...")

for source_folder, label_id in MAPPING.items():
    source_dir = SOURCE_ROOT / source_folder
    if not source_dir.exists():
        print(f"[Warning] Source folder not found: {source_folder}")
        continue
        
    dest_name = FOLDER_NAMES[label_id]
    dest_dir = DEST_ROOT / dest_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all jpg/jpeg files
    files = list(source_dir.glob("*.jpg")) + list(source_dir.glob("*.jpeg"))
    print(f"[Process] Copying {len(files)} images for {dest_name}...")
    
    for f in tqdm(files, desc=f"Copying {dest_name}"):
        shutil.copy2(f, dest_dir / f.name)

print("[Done] Training dataset ready!")
