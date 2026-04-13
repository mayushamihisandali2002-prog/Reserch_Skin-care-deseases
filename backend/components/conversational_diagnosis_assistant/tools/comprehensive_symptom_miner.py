#!/usr/bin/env python
"""
Comprehensive PubMed data extractor for SkinAI.
Maps medical literature titles to the 6 target disease classes.
"""
import pandas as pd
from datasets import load_dataset
from tqdm import tqdm
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
SYMPTOM_CSV_PATH = (
    BACKEND_DIR
    / "assets"
    / "data"
    / "conversational_diagnosis_assistant"
    / "disease_symptom_edges_expanded.csv"
)

KEYWORDS = {
    "Eczema": ["eczema", "atopic dermatitis", "itchy rash", "xerosis", "filaggrin"],
    "Dermatitis": ["contact dermatitis", "skin irritation", "irritant dermatitis", "seborrheic dermatitis"],
    "Psoriasis": ["psoriasis", "psoriatic", "plaque psoriasis", "scaly skin", "silvery scales"],
    "Acne": ["acne", "pimples", "blackheads", "vulgaris", "comedones", "propionibacterium"],
    "Urticaria": ["urticaria", "hives", "welts", "angioedema"],
    "Pigmentation / Dark Spots": ["pigmentation", "melasma", "dark spot", "sunspot", "freckle", "lentigo", "hyperpigmentation", "ephelides"]
}

def augment():
    print("[Data] Loading large PubMed chunk for multi-class augmentation...")
    try:
        # Load 50,000 titles
        ds = load_dataset("pubmed", split="train[:50000]", trust_remote_code=True)
        
        rows = []
        for title in tqdm(ds["title"], desc="Mining PubMed"):
            title_lower = title.lower()
            found = False
            for class_name, keys in KEYWORDS.items():
                if any(k in title_lower for k in keys):
                    rows.append({"disease_name": class_name, "symptom_name": title})
                    found = True
                    break # Assign to first matching class
        
        if rows:
            new_df = pd.DataFrame(rows)
            # Read current to avoid duplicates? No, just append, training scripts often deduplicate or shuffle.
            new_df.to_csv(SYMPTOM_CSV_PATH, mode="a", header=False, index=False)
            print(f"[Done] Appended {len(rows)} across all classes to {SYMPTOM_CSV_PATH}")
        else:
            print("[Info] No matching rows found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    augment()
