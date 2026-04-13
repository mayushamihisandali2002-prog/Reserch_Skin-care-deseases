#!/usr/bin/env python
"""Download HAM10000 dataset zip and extract it.
The script uses the standard library (urllib) to avoid extra dependencies.
"""
import os
import urllib.request
import zipfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]

url = "https://github.com/dermatologist/ham10000/archive/refs/heads/master.zip"
output_dir = (
    BACKEND_DIR
    / "assets"
    / "data"
    / "multimodal_image_audio_diagnosis"
    / "ham10000"
)
output_dir.mkdir(parents=True, exist_ok=True)
zip_path = output_dir / "ham10000.zip"

print(f"[Download] Fetching {url} ...")
urllib.request.urlretrieve(url, zip_path)
print(f"[Download] Saved to {zip_path}")

print("[Extract] Unzipping...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(output_dir)
print("[Extract] Done")
