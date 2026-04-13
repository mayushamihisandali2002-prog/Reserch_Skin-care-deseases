#!/usr/bin/env python
"""
Append additional symptom sentences from the PubMed dataset to the existing CSV.
This helps the DistilBERT text model learn the new "Pigmentation / Dark Spots" class.
"""
import pandas as pd
from datasets import load_dataset
from tqdm import tqdm
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
SYMPTOM_CSV_PATH = (
    BACKEND_DIR
    / "assets"
    / "data"
    / "conversational_diagnosis_assistant"
    / "disease_symptom_edges_expanded.csv"
)

print("[Data] Loading PubMed abstracts for augmentation...")
try:
    # Load a reasonable chunk of PubMed
    ds = load_dataset("pubmed", split="train[:10000]", trust_remote_code=True)
    
    # We'll map abstracts mentioning "pigmentation", "spots", "melasma", etc. to class 5
    rows = []
    keywords = ["pigmentation", "melasma", "dark spot", "sunspot", "freckle", "lentigo", "hyperpigmentation"]
    
    for title in tqdm(ds["title"], desc="Processing PubMed titles"):
        title_lower = title.lower()
        if any(k in title_lower for k in keywords):
            rows.append({"disease_name": "Pigmentation / Dark Spots", "symptom_name": title})
            
    if rows:
        new_df = pd.DataFrame(rows)
        # Append to the master symptom CSV
        new_df.to_csv(SYMPTOM_CSV_PATH, mode="a", header=False, index=False)
        print(
            f"[Done] Appended {len(rows)} targeted PubMed symptom rows to {SYMPTOM_CSV_PATH}"
        )
    else:
        print("[Info] No matching PubMed rows found in this chunk.")
        
except Exception as e:
    print(f"Error during PubMed augmentation: {e}")
