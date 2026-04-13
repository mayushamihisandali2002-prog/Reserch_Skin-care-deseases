"""
Configuration for SkinAI inference paths, labels, and tunable parameters.
"""

from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

ASSETS_DIR = BACKEND_DIR / "assets"
DATA_DIR = ASSETS_DIR / "data"
CACHE_DIR = ASSETS_DIR / "cache"
MODELS_DIR = ASSETS_DIR / "models"

# Category-owned asset roots
CONVERSATIONAL_DATA_DIR = DATA_DIR / "conversational_diagnosis_assistant"
MULTIMODAL_DATA_DIR = DATA_DIR / "multimodal_image_audio_diagnosis"
SKIN_TYPE_DATA_DIR = DATA_DIR / "skin_type_skincare_recommendation"
SEVERITY_DATA_DIR = DATA_DIR / "severity_assessment_tracking"

CONVERSATIONAL_MODELS_DIR = MODELS_DIR / "conversational_diagnosis_assistant"
MULTIMODAL_MODELS_DIR = MODELS_DIR / "multimodal_image_audio_diagnosis"
SKIN_TYPE_MODELS_DIR = MODELS_DIR / "skin_type_skincare_recommendation" / "skin_type"
SEVERITY_MODELS_DIR = MODELS_DIR / "severity_assessment_tracking" / "severity"

# Main model paths
DISTILBERT_MODEL_DIR = CONVERSATIONAL_MODELS_DIR / "distilbert"
IMAGE_MODEL_PATH = MULTIMODAL_MODELS_DIR / "image_best_finetuned.pt"
SKIN_TYPE_MODEL_PATH = SKIN_TYPE_MODELS_DIR / "skin_type_convnext_cleaned_best.pt"
SKIN_TYPE_LABEL_MAP_PATH = SKIN_TYPE_MODELS_DIR / "label_map_skin_type.json"
SEVERITY_MODEL_PATH = SEVERITY_MODELS_DIR / "severity_model.joblib"
SEVERITY_METADATA_PATH = SEVERITY_MODELS_DIR / "metadata.json"

# Legacy conversational fallback model paths
TEXT_MODEL_PATH = CONVERSATIONAL_MODELS_DIR / "text_model.pkl"
VECTORIZER_PATH = CONVERSATIONAL_MODELS_DIR / "vectorizer.pkl"

# Category-owned data paths
DISEASE_SYMPTOM_CSV = CONVERSATIONAL_DATA_DIR / "disease_symptom_edges_expanded.csv"
TREATMENT_RECORDS_CSV = CONVERSATIONAL_DATA_DIR / "treatment_records_clean.csv"
RESEARCH_DATASET_DIR = MULTIMODAL_DATA_DIR / "research_dataset"
COMBINED_IMAGES_DIR = MULTIMODAL_DATA_DIR / "combined_images"
SKIN_TYPE_DATASET_DIR = SKIN_TYPE_DATA_DIR / "skin_types"
SKIN_TYPE_HF_DATA_DIR = SKIN_TYPE_DATA_DIR / "skin_types_hf"
SEVERITY_TRACK_DIR = SEVERITY_DATA_DIR / "severity_tracking"
KG_TFIDF_CACHE_PATH = CACHE_DIR / "kg_tfidf_cache.joblib"

# Disease Labels (30 classes)
DISEASE_LABELS: dict[int, str] = {
    0: "Eczema",
    1: "Dermatitis",
    2: "Psoriasis",
    3: "Acne",
    4: "Urticaria",
    5: "Pigmentation / Dark Spots",
    6: "Ringworm",
    7: "Rosacea",
    8: "Shingles",
    9: "Vitiligo",
    10: "Impetigo",
    11: "Molluscum Contagiosum",
    12: "Folliculitis",
    13: "Scabies",
    14: "Warts",
    15: "Seborrheic Dermatitis",
    16: "Lichen Planus",
    17: "Cellulitis",
    18: "Herpes Simplex",
    19: "Pityriasis Versicolor",
    20: "Melanoma",
    21: "Basal Cell Carcinoma",
    22: "Actinic Keratosis",
    23: "Seborrheic Keratosis",
    24: "Dermatofibroma",
    25: "Cherry Angioma",
    26: "Melanocytic Nevi",
    27: "Hidradenitis Suppurativa",
    28: "Alopecia Areata",
    29: "Melasma",
}

from components.conversational_diagnosis_assistant.knowledge_base import (
    DISEASE_EXPLANATIONS,
    EXPECTED_SYMPTOMS,
    DISEASE_TREATMENTS,
)


FUSION_ALPHA = 0.60
CONFIDENCE_THRESHOLD = 0.30
TOP_K_TREATMENTS = 4
DEBUG = True


def get_model_status() -> dict:
    """Return availability of each model/data file."""
    return {
        "distilbert_model": DISTILBERT_MODEL_DIR.exists(),
        "image_model": IMAGE_MODEL_PATH.exists(),
        "skin_type_model": SKIN_TYPE_MODEL_PATH.exists(),
        "skin_type_label_map": SKIN_TYPE_LABEL_MAP_PATH.exists(),
        "severity_model": SEVERITY_MODEL_PATH.exists(),
        "severity_metadata": SEVERITY_METADATA_PATH.exists(),
        "text_model_legacy": TEXT_MODEL_PATH.exists(),
        "vectorizer_legacy": VECTORIZER_PATH.exists(),
        "disease_symptom_csv": DISEASE_SYMPTOM_CSV.exists(),
        "treatment_records_csv": TREATMENT_RECORDS_CSV.exists(),
        "research_dataset": RESEARCH_DATASET_DIR.exists(),
        "combined_images_dataset": COMBINED_IMAGES_DIR.exists(),
        "skin_type_dataset": SKIN_TYPE_DATASET_DIR.exists(),
        "skin_type_hf_dataset": SKIN_TYPE_HF_DATA_DIR.exists(),
        "severity_tracking_data": SEVERITY_TRACK_DIR.exists(),
    }
