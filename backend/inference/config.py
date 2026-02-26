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

# ── Legacy Paths (sklearn fallback) ───────────────────────────────────────────
TEXT_MODEL_PATH    = MODELS_DIR / "text_model.pkl"
VECTORIZER_PATH    = MODELS_DIR / "vectorizer.pkl"

# ── CSV Knowledge Base ────────────────────────────────────────────────────────
DISEASE_SYMPTOM_CSV   = DATA_DIR / "disease_symptom_edges_expanded.csv"
TREATMENT_RECORDS_CSV = DATA_DIR / "treatment_records_clean.csv"
KG_TFIDF_CACHE_PATH   = CACHE_DIR / "kg_tfidf_cache.joblib"

# ── Disease Labels (5 classes – matches DistilBERT + ResNet training) ─────────
DISEASE_LABELS: dict[int, str] = {
    0: "Eczema",
    1: "Dermatitis",
    2: "Psoriasis",
    3: "Acne",
    4: "Urticaria",
}

# ── Built-in Treatment Knowledge Base ─────────────────────────────────────────
# Used when CSV is unavailable or returns empty results.
DISEASE_TREATMENTS: dict[str, list[dict[str, str]]] = {
    "Eczema": [
        {
            "medicine": "Topical Corticosteroids (Hydrocortisone 1%)",
            "advice":   "Apply a thin layer to affected areas 1–2× daily for up to 2 weeks; do not use on face.",
        },
        {
            "medicine": "Emollients / Thick Moisturizer (Cetaphil, Eucerin)",
            "advice":   "Apply generously 2–3× daily, especially within 3 min of bathing to trap moisture.",
        },
        {
            "medicine": "Antihistamines (Cetirizine / Loratadine)",
            "advice":   "Take once daily at night for itch relief; non-drowsy options available.",
        },
        {
            "medicine": "Tacrolimus Ointment (Protopic 0.03%)",
            "advice":   "Non-steroidal alternative for sensitive areas (eyelids, face); use as directed by doctor.",
        },
    ],
    "Dermatitis": [
        {
            "medicine": "Hydrocortisone Cream 1%",
            "advice":   "Apply 2× daily for up to 7 days to reduce redness and itching.",
        },
        {
            "medicine": "Antihistamines (Diphenhydramine at night)",
            "advice":   "Relieves allergic/contact dermatitis; causes drowsiness — take before bed.",
        },
        {
            "medicine": "Cool Compresses",
            "advice":   "Apply cold damp cloth for 10–15 min several times a day to reduce swelling.",
        },
        {
            "medicine": "Identify & Avoid Triggers",
            "advice":   "Common triggers: nickel, latex, fragrance, soaps — keep a symptom diary.",
        },
    ],
    "Psoriasis": [
        {
            "medicine": "Vitamin D Analog Cream (Calcipotriol / Dovonex)",
            "advice":   "Apply to plaques once daily; effective for mild-to-moderate plaque psoriasis.",
        },
        {
            "medicine": "Coal Tar Shampoo / Cream",
            "advice":   "Use on scalp or body plaques to reduce scaling and itching; may stain clothing.",
        },
        {
            "medicine": "Topical Corticosteroids (Betamethasone)",
            "advice":   "Apply to plaques as prescribed; do not use on face or skin folds long-term.",
        },
        {
            "medicine": "Biologic Therapy (Adalimumab, Secukinumab)",
            "advice":   "For moderate-severe psoriasis; requires dermatologist referral and monitoring.",
        },
    ],
    "Acne": [
        {
            "medicine": "Benzoyl Peroxide 2.5%–5% Gel",
            "advice":   "Apply a thin layer once daily to clean, dry skin; kills acne-causing bacteria.",
        },
        {
            "medicine": "Salicylic Acid 2% Cleanser",
            "advice":   "Use daily to unclog pores and reduce blackheads; may cause mild dryness.",
        },
        {
            "medicine": "Topical Retinoid (Tretinoin 0.025%)",
            "advice":   "Apply at night; start 3× per week then daily — always use SPF 30+ in the morning.",
        },
        {
            "medicine": "Oral Doxycycline (for moderate-severe)",
            "advice":   "Take with food × 3 months; avoid sun exposure; do not take with dairy.",
        },
    ],
    "Urticaria": [
        {
            "medicine": "Non-sedating Antihistamines (Cetirizine / Loratadine 10 mg)",
            "advice":   "Take once daily — works within 1 hour; safe for long-term use.", 
        },
        {
            "medicine": "Sedating Antihistamines (Chlorphenamine 4 mg)",
            "advice":   "For severe nighttime itch — causes drowsiness, do not drive.",
        },
        {
            "medicine": "Short-course Oral Prednisolone",
            "advice":   "Reserved for severe acute attacks — max 5–7 days under doctor supervision.",
        },
        {
            "medicine": "Identify and Avoid Triggers",
            "advice":   "Common triggers: shellfish, nuts, NSAIDs, stress, heat — keep a trigger diary.",
        },
    ],
}

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
        "text_model_legacy":    TEXT_MODEL_PATH.exists(),
        "vectorizer_legacy":    VECTORIZER_PATH.exists(),
        "disease_symptom_csv":  DISEASE_SYMPTOM_CSV.exists(),
        "treatment_records_csv": TREATMENT_RECORDS_CSV.exists(),
    }
