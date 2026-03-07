"""
Configuration for SkinAI Inference Pipeline
=============================================
Central place for all paths, disease labels, treatment KB, and tunable params.
"""

from pathlib import Path

# ── Directory layout ───────────────────────────────────────────────────────────
BACKEND_DIR  = Path(__file__).parent.parent          # …/backend
PROJECT_DIR  = BACKEND_DIR.parent                    # …/Reserch_Skin-care-deseases

# Legacy CSV assets (knowledge-base / treatments)
ASSETS_DIR   = BACKEND_DIR  / "assets"
DATA_DIR     = ASSETS_DIR   / "data"
CACHE_DIR    = ASSETS_DIR   / "cache"
MODELS_DIR   = ASSETS_DIR   / "models"               # legacy sklearn models

# ── ★ REAL Model Paths ────────────────────────────────────────────────────────
#
#   1) DistilBERT fine-tuned text model
#      Folder: assets/models/distilbert/
#      Contains: model.safetensors, tokenizer.json, config.json, vocab.txt …
#
DISTILBERT_MODEL_DIR = MODELS_DIR / "distilbert"

#   2) ResNet-18 fine-tuned image model
#      File  : image_best_finetuned.pt (moved to assets/models/)
#
IMAGE_MODEL_PATH = MODELS_DIR / "image_best_finetuned.pt"

#   3) ConvNeXt skin-type model + label map
#
SKIN_TYPE_MODEL_PATH = MODELS_DIR / "skin_type" / "skin_type_convnext_cleaned_best.pt"
SKIN_TYPE_LABEL_MAP_PATH = MODELS_DIR / "skin_type" / "label_map_skin_type.json"

#   4) Face skin severity model + metadata
#
SEVERITY_MODEL_PATH = MODELS_DIR / "severity" / "severity_model.joblib"
SEVERITY_METADATA_PATH = MODELS_DIR / "severity" / "metadata.json"

# ── Legacy Paths (sklearn fallback) ───────────────────────────────────────────
TEXT_MODEL_PATH    = MODELS_DIR / "text_model.pkl"
VECTORIZER_PATH    = MODELS_DIR / "vectorizer.pkl"

# ── CSV Knowledge Base ────────────────────────────────────────────────────────
DISEASE_SYMPTOM_CSV   = DATA_DIR / "disease_symptom_edges_expanded.csv"
TREATMENT_RECORDS_CSV = DATA_DIR / "treatment_records_clean.csv"
KG_TFIDF_CACHE_PATH   = CACHE_DIR / "kg_tfidf_cache.joblib"

# ── Disease Labels (30 classes – Comprehensive Research Scope) ─────────────
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

# ── Disease Knowledge Base ────────────────────────────────────────────────────
from .knowledge_base import DISEASE_EXPLANATIONS, EXPECTED_SYMPTOMS, DISEASE_TREATMENTS


# ── Inference Parameters ───────────────────────────────────────────────────────
# Weighted fusion: final_prob = α × image_prob + (1-α) × text_prob
FUSION_ALPHA        = 0.60   # Image model weight (image is 'stronger' evidence)
CONFIDENCE_THRESHOLD = 0.30  # Minimum confidence to assert a disease
TOP_K_TREATMENTS    = 4      # Max treatments returned per disease

# ── Debug mode ────────────────────────────────────────────────────────────────
DEBUG = True


# ── Utility ───────────────────────────────────────────────────────────────────

def get_model_status() -> dict:
    """Return availability of each model/data file."""
    return {
        "distilbert_model":     DISTILBERT_MODEL_DIR.exists(),
        "image_model":          IMAGE_MODEL_PATH.exists(),
        "skin_type_model":      SKIN_TYPE_MODEL_PATH.exists(),
        "skin_type_label_map":  SKIN_TYPE_LABEL_MAP_PATH.exists(),
        "severity_model":       SEVERITY_MODEL_PATH.exists(),
        "severity_metadata":    SEVERITY_METADATA_PATH.exists(),
        "text_model_legacy":    TEXT_MODEL_PATH.exists(),
        "vectorizer_legacy":    VECTORIZER_PATH.exists(),
        "disease_symptom_csv":  DISEASE_SYMPTOM_CSV.exists(),
        "treatment_records_csv": TREATMENT_RECORDS_CSV.exists(),
    }
