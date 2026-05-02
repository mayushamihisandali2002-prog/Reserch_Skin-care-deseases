import os
import json
import csv
import joblib
import numpy as np
from pathlib import Path
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Import the model for feature extraction
import sys
BACKEND_DIR = Path(r"d:\Research\zip skin\Reserch_Skin-care-deseases\backend")
sys.path.append(str(BACKEND_DIR))

from components.severity_assessment_tracking.severity_model import SeverityModel

# Paths
DATA_DIR = BACKEND_DIR / "assets" / "data" / "severity_assessment_tracking" / "severity_benchmark"
MODEL_DIR = BACKEND_DIR / "assets" / "models" / "severity_assessment_tracking" / "severity"
DEFAULT_MODEL_PATH = MODEL_DIR / "severity_model.joblib"
DEFAULT_META_PATH = MODEL_DIR / "metadata.json"

def retrain_severity():
    print("[Severity] Starting retraining...")
    
    # 1. Initialize model to use its feature extraction
    temp_model = SeverityModel(DEFAULT_MODEL_PATH, DEFAULT_META_PATH)
    if not temp_model.loaded:
        print(f"Error loading model: {temp_model.load_error}")
        return
    
    # 2. Load labels
    labels_path = DATA_DIR / "labels.csv"
    if not labels_path.exists():
        print(f"Error: labels.csv not found at {labels_path}")
        return

    X = []
    y = []
    
    with open(labels_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_rel_ptr = row["image_path"]
            label = row["severity_level"]
            img_path = DATA_DIR / img_rel_ptr
            
            if not img_path.exists():
                print(f"Warning: Image {img_path} not found")
                continue
            
            try:
                with Image.open(img_path) as img:
                    # Use internal feature extraction
                    # We need to mimic the View-based extraction
                    resized = temp_model._resize_keep_aspect(img.convert("RGB"), 256)
                    cropped = temp_model._center_crop(resized, 224)
                    rgb_na = np.array(cropped, dtype=np.uint8)
                    rgb_na, _ = temp_model._apply_clahe_or_fallback(rgb_na)
                    
                    raw_features = temp_model._extract_features(rgb_na)
                    norm_features = temp_model._normalize_features(raw_features)
                    
                    feature_vector = [norm_features[col] for col in temp_model.feature_cols]
                    X.append(feature_vector)
                    y.append(label)
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

    if not X:
        print("No training data gathered.")
        return

    X = np.array(X)
    y = np.array(y)
    
    print(f"[Severity] Gathered {len(X)} samples with {X.shape[1]} features.")
    
    # 3. Train RandomForest
    # We'll use a small forest given the small dataset
    rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    rf.fit(X, y)
    
    y_pred = rf.predict(X)
    acc = accuracy_score(y, y_pred)
    print(f"[Severity] Training Accuracy: {acc*100:.2f}%")
    
    # 4. Save
    joblib.dump(rf, DEFAULT_MODEL_PATH)
    print(f"[Severity] Model saved to {DEFAULT_MODEL_PATH}")
    
    # Update metadata if needed (min/max/thresholds)
    # For now we'll keep the existing metadata structure
    print("[Severity] Retraining complete.")

if __name__ == "__main__":
    retrain_severity()
