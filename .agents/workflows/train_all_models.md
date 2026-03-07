#!/usr/bin/env python
"""
Workflow to download extra datasets, augment data, and retrain all models.
All steps are marked with // turbo-all so they will be auto‑executed.
"""

# // turbo-all
import subprocess, sys, os

def run(cmd, cwd=None):
    print(f"[Workflow] Running: {cmd}")
    subprocess.run(cmd, cwd=cwd, shell=True, check=True)

# 1. Ensure required packages are installed
run("pip install -U pip")
run("pip install datasets tqdm pillow torchvision timm accelerate")

# 2. Download HAM10000 image dataset
# 2. (Skipped) Download HAM10000 image dataset – not needed / URL unavailable
# run("python download_ham10000.py", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")

# 3. Download additional dermatology image dataset (HuggingFace)
run("python download_additional_images.py", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")

# 4. Augment symptom CSV with PubMed data (already created script)
run("python augment_symptom_data.py", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")

# 5. Download extra PubMed text data (more samples)
run("python download_additional_text.py", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")

# 6. Retrain DistilBERT text model (now 6 classes)
run("python train_distilbert.py --epochs 5", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")

# 7. Retrain ResNet‑18 image model on combined image data
run("python retrain_image_model.py --data-dir assets/data/combined_images --output-dir assets/models --num-classes 6 --epochs 5", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")

# 8. (Optional) Retrain skin‑type model if script exists
if os.path.exists("train_skin_type.py"):
    run("python train_skin_type.py --epochs 6", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")

# 9. Restart backend server to load new checkpoints
# Kill any running app.py process
try:
    subprocess.run("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq app.py\"", shell=True, check=False)
except Exception:
    pass
run("python app.py", cwd="d:/Research/zip skin/Reserch_Skin-care-deseases/backend")
