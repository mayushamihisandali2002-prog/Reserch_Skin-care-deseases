import os
from datasets import load_dataset
from PIL import Image
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
RESEARCH_DATASET_DIR = (
    BACKEND_DIR
    / "assets"
    / "data"
    / "multimodal_image_audio_diagnosis"
    / "research_dataset"
)

# Mapping our 30 classes to DermNet's 23 categories
# (Note: DermNet labels are 0-22)
DERMNET_MAP = {
    0: 5,   # Eczema -> Eczema Photos
    1: 2,   # Dermatitis -> Atopic Dermatitis Photos
    2: 15,  # Psoriasis -> Psoriasis pictures Lichen Planus and related diseases
    3: 0,   # Acne -> Acne and Rosacea Photos
    4: 20,  # Urticaria -> Urticaria Hives
    5: 10,  # Pigmentation -> Light Diseases and Disorders of Pigmentation
    6: 19,  # Ringworm -> Tinea Ringworm and other Fungal Infections
    7: 0,   # Rosacea -> Acne and Rosacea Photos
    8: 9,   # Shingles -> Herpes Simplex and other Viral Infections
    9: 10,  # Vitiligo -> Light Diseases and Disorders of Pigmentation
    10: 4,  # Impetigo -> Cellulitis Impetigo and other Bacterial Infections
    11: 9,  # Molluscum -> Herpes Simplex and other Viral Infections
    12: 4,  # Folliculitis -> Cellulitis Impetigo and other Bacterial Infections
    13: 16, # Scabies -> Scabies Lyme Disease and other Infestations and Bites
    14: 9,  # Warts -> Herpes Simplex and other Viral Infections
    15: 5,  # Seborrheic Dermatitis -> Eczema Photos (Close approximation)
    16: 15, # Lichen Planus -> Psoriasis pictures Lichen Planus and related diseases
    17: 4,  # Cellulitis -> Cellulitis Impetigo and other Bacterial Infections
    18: 9,  # Herpes Simplex -> Herpes Simplex and other Viral Infections
    19: 19, # Pityriasis Versicolor -> Tinea Ringworm and other Fungal Infections
    20: 12, # Melanoma -> Melanoma Skin Cancer Nevi and Moles
    21: 1,  # Basal Cell Carcinoma -> Actinic Keratosis Basal Cell Carcinoma and other Malignant Lesions
    22: 1,  # Actinic Keratosis -> Actinic Keratosis Basal Cell Carcinoma and other Malignant Lesions
    23: 17, # Seborrheic Keratosis -> Seborrheic Keratosis and other Benign Tumors
    24: 17, # Dermatofibroma -> Seborrheic Keratosis and other Benign Tumors
    25: 22, # Cherry Angioma -> Vascular Tumors
    26: 12, # Melanocytic Nevi -> Melanoma Skin Cancer Nevi and Moles
    27: 0,  # Hidradenitis Suppurativa -> Acne and Rosacea Photos
    28: 8,  # Alopecia Areata -> Hair Loss Photos Alopecia and other Hair Diseases
    29: 10, # Melasma -> Light Diseases and Disorders of Pigmentation
}

DISEASE_LABELS = {
    0: "Eczema", 1: "Dermatitis", 2: "Psoriasis", 3: "Acne", 4: "Urticaria", 
    5: "Pigmentation / Dark Spots", 6: "Ringworm", 7: "Rosacea", 8: "Shingles",
    9: "Vitiligo", 10: "Impetigo", 11: "Molluscum Contagiosum", 12: "Folliculitis",
    13: "Scabies", 14: "Warts", 15: "Seborrheic Dermatitis", 16: "Lichen Planus",
    17: "Cellulitis", 18: "Herpes Simplex", 19: "Pityriasis Versicolor",
    20: "Melanoma", 21: "Basal Cell Carcinoma", 22: "Actinic Keratosis",
    23: "Seborrheic Keratosis", 24: "Dermatofibroma", 25: "Cherry Angioma",
    26: "Melanocytic Nevi", 27: "Hidradenitis Suppurativa", 28: "Alopecia Areata",
    29: "Melasma"
}

def download_research_images(limit_per_class=200):
    print(f"[Data] Starting research dataset collection from DermNet for {len(DISEASE_LABELS)} classes...")
    base_dir = RESEARCH_DATASET_DIR
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Check existing counts to resume
    counts = {i: 0 for i in DISEASE_LABELS.keys()}
    for our_id, disease in DISEASE_LABELS.items():
        disease_name = disease.replace(" ", "_").replace("/", "_")
        save_dir = base_dir / disease_name
        if save_dir.exists():
            counts[our_id] = len(list(save_dir.glob("*.jpg")))
    
    if all(c >= limit_per_class for c in counts.values()):
         print("[Data] All classes already reached target limit!")
         return

    # Load dataset streaming to save disk initially
    ds = load_dataset("exper1ment/dermnet", split="train", streaming=True)
    
    print("[Data] Iterating and saving images...")
    iters = 0
    for item in ds:
        iters += 1
        dermnet_label = item['label']
        if iters % 1000 == 0:
            print(f"Processed {iters} raw images...")
            
        found_any = False
        
        # Check which of our classes this DermNet label could belong to
        for our_id, target_dermnet_id in DERMNET_MAP.items():
            if dermnet_label == target_dermnet_id:
                if counts[our_id] < limit_per_class:
                    disease_name = DISEASE_LABELS[our_id].replace(" ", "_").replace("/", "_")
                    save_dir = base_dir / disease_name
                    save_dir.mkdir(exist_ok=True)
                    
                    img = item['image']
                    if not isinstance(img, Image.Image):
                        break
                        
                    try:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        # Use unique filenames to avoid overwriting existing ones during resume
                        import uuid
                        img_path = save_dir / f"{disease_name}_{uuid.uuid4().hex[:8]}.jpg"
                        img.save(img_path)
                        counts[our_id] += 1
                        found_any = True
                    except Exception as e:
                        print(f"Failed to save image: {e}")
                        pass
        
        # Check if we are done with all classes
        if all(c >= limit_per_class for c in counts.values()):
            print("[Data] All classes reached target limit!")
            break

    print("[Data] Final Collection Summary:")
    for our_id, count in counts.items():
        print(f"   {DISEASE_LABELS[our_id]}: {count} images")

if __name__ == "__main__":
    # 200 images per class for high-accuracy training (targeting 80%+).
    # The function resumes automatically if interrupted.
    download_research_images(limit_per_class=200)
