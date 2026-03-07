import pandas as pd
import pickle
import numpy as np
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from pathlib import Path
from collections import Counter

# Class mapping from the main training script
ID2LABEL = {
    0: "Eczema", 1: "Dermatitis", 2: "Psoriasis", 3: "Acne", 4: "Urticaria", 
    5: "Pigmentation / Dark Spots", 6: "Ringworm", 7: "Rosacea", 8: "Shingles",
    9: "Vitiligo", 10: "Impetigo", 11: "Molluscum Contagiosum", 12: "Folliculitis",
    13: "Scabies", 14: "Warts", 15: "Seborrheic Dermatitis", 16: "Lichen Planus",
    17: "Cellulitis", 18: "Herpes Simplex", 19: "Pityriasis Versicolor"
}

def retrain_fallback_model():
    print("=" * 40)
    print("RETRAINING FALLBACK SKLEARN MODEL")
    print("=" * 40)
    
    # Load the same training data or use the same logic
    data_path = Path("assets/data/disease_symptom_edges_expanded.csv")
    if not data_path.exists():
        print(f"Error: {data_path} not found.")
        return
        
    df = pd.read_csv(data_path)
    
    # Simple mapping for common names in CSV
    DISEASE_MAPPING = {
        "Eczema": 0, "Atopic dermatitis": 0,
        "Dermatitis": 1, "Contact dermatitis": 1,
        "Psoriasis": 2, "Plaque psoriasis": 2,
        "Acne": 3, "Acne vulgaris": 3,
        "Urticaria": 4, "Hives": 4,
        "Pigmentation": 5, "Dark Spots": 5, "Melasma": 29, "Freckles": 5,
        "Ringworm": 6, "Tinea": 6,
        "Rosacea": 7,
        "Shingles": 8, "Herpes zoster": 8,
        "Vitiligo": 9,
        "Impetigo": 10,
        "Molluscum": 11,
        "Folliculitis": 12,
        "Scabies": 13,
        "Warts": 14, "Verruca": 14,
        "Seborrheic dermatitis": 15, "Dandruff": 15,
        "Lichen": 16,
        "Cellulitis": 17,
        "Herpes simplex": 18, "Cold sore": 18,
        "Versicolor": 19,
        "Melanoma": 20, "Basal Cell Carcinoma": 21, "Actinic Keratosis": 22,
        "Seborrheic Keratosis": 23, "Dermatofibroma": 24, "Cherry Angioma": 25,
        "Nevi": 26, "Hidradenitis": 27, "Alopecia": 28
    }
    
    X = []
    y = []
    
    # 1. Existing data from CSV (includes added diseases)
    # Check if CSV has been updated with these names
    for _, row in df.iterrows():
        disease = str(row['disease_name'])
        symptom = str(row['symptom_name'])
        
        found = False
        for key, val in DISEASE_MAPPING.items():
            if key.lower() in disease.lower():
                X.append(symptom)
                y.append(val)
                found = True
                break
            
    # 2. Add synthetic data for Pigmentation (class 5)
    pigmentation_symptoms = ["dark spots", "brown spots", "flat spots", "pigmentation", "sunspots", "freckles", "dark patches", "discoloration", "melanin spots", "sun damage", "darkened skin", "age spots"]
    for s in pigmentation_symptoms:
        for _ in range(20):
            X.append(s)
            y.append(5)
            
    # 3. Add synthetic for all new classes
    new_symptoms = {
        6: ["ring-shaped rash", "circular rash", "round patch", "clear center", "ring on skin", "fungal ring", "scaly border"],
        7: ["facial redness", "flushing", "visible blood vessels", "red face", "hot face", "broken capillaries", "redness on cheeks"],
        8: ["painful blisters", "band of rash", "stinging pain", "fluid-filled bumps", "shooting pain", "burning rash", "nerve pain"],
        9: ["white patches", "loss of pigment", "depigmentation", "milky white skin", "pale spots"],
        10: ["honey-colored crust", "yellow crust", "blisters with pus", "weeping sores", "golden crust"],
        11: ["pearly bumps", "dimpled papules", "umbilicated bumps", "painless smooth spots", "skin-colored bumps"],
        12: ["inflamed hair follicles", "pustules around hair", "shaving bumps", "itchy hair bulbs", "red bumps with hair"],
        13: ["intense itching at night", "burrows in skin", "itchy web spaces", "tiny grey lines", "severe nocturnal itch"],
        14: ["rough papules", "verruca", "cauliflower-like growth", "fleshy bumps", "black dots in bump"],
        15: ["scalp flaking", "dandruff", "greasy scale", "flaky eyebrows", "yellowish oily flakes"],
        16: ["purple papules", "flat-topped bumps", "wickham striae", "polygon-shaped spots", "violaceous rash"],
        17: ["red hot skin", "spreading redness", "swollen tender skin", "fever with skin rash", "deep skin pain"],
        18: ["cold sores", "lip blisters", "tingling before blisters", "grouped vesicles on lips", "fever blisters"],
        19: ["discolored patches", "fine scales", "fawn-colored spots", "tinea versicolor", "patchy skin color"],
        20: ["assymetrical mole", "border irregularity", "changing mole color", "bleeding mole", "growing spot"],
        21: ["pearly bump", "pink growth", "sore that bleeds easily", "translucent skin bump"],
        22: ["rough scaly patch", "sandpaper skin texture", "pink precancer spot", "sun damaged spot"],
        23: ["waxy brown bump", "pasted on growth", "crusty black spot", "raised age spot"],
        24: ["hard brown lump", "dimple when pinched", "firm bump on leg"],
        25: ["bright red bump", "cherry red small spot", "red mole"],
        26: ["normal brown mole", "round even spot", "stable skin spot"],
        27: ["painful boils armpit", "groin abscess", "recurrent cysts groin", "tunneling sores"],
        28: ["patchy hair loss", "sudden bald spot", "round hairless area"],
        29: ["facial hyperpigmentation", "brown mask pregnant", "dark patches cheeks"]
    }
    for label_id, symptoms in new_symptoms.items():
        for s in symptoms:
            for _ in range(20):
                X.append(s)
                y.append(label_id)

    # 4. Add some common phrases
    base_symptoms = {
        0: ["itchy patches", "flaky skin"], 
        1: ["skin reaction", "inflamed skin"], 
        2: ["silvery scale", "dry patches"], 
        3: ["oily breakout", "pimples"], 
        4: ["raised wheals", "hives"]
    }
    for label_id, symptoms in base_symptoms.items():
        for s in symptoms:
            for _ in range(20):
                X.append(s)
                y.append(label_id)

    print(f"Total samples: {len(X)}")
    print(f"Class distribution: {Counter(y)}")
    
    # Train pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english')),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    
    pipeline.fit(X, y)
    
    # Save components separately as expected by inference.py
    models_dir = Path("assets/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    with open(models_dir / "text_model.pkl", "wb") as f:
        pickle.dump(pipeline.named_steps['clf'], f)
    with open(models_dir / "vectorizer.pkl", "wb") as f:
        pickle.dump(pipeline.named_steps['tfidf'], f)
        
    print(f"✅ Fallback model saved to {models_dir}")

if __name__ == "__main__":
    retrain_fallback_model()
