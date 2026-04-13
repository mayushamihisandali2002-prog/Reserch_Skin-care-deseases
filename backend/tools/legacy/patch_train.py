import re

def patch_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for pat, rep in replacements:
        content = re.sub(pat, rep, content, flags=re.DOTALL)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

distilbert_replacements = [
    (r'# ── Disease Category Mapping.*?\nID2LABEL = \{.*?\n\}', 
    r'''# ── Disease Category Mapping ─────────────────────────────────────────────────

DISEASE_MAPPING = {
    "Atopic dermatitis (Eczema)": 0, "Dyshidrotic eczema": 0, "Nummular eczema": 0,
    "Contact dermatitis (Irritant)": 1, "Contact dermatitis (Allergic)": 1, "Perioral dermatitis": 1, "Photodermatitis": 1,
    "Psoriasis vulgaris": 2, "Lichen planus": 16,
    "Acne vulgaris": 3, "Acne rosacea": 3, "Rosacea": 7, "Folliculitis": 12,
    "Urticaria (Hives)": 4, "Chronic urticaria": 4,
    "Freckles (Ephelides)": 5, "Solar Lentigines (Sunspots)": 5, "Post-inflammatory hyperpigmentation": 5,
    "Tinea corporis (Ringworm)": 6, "Tinea pedis (Athlete's foot)": 6, "Tinea cruris (Jock itch)": 6, "Tinea capitis (Scalp ringworm)": 6,
    "Herpes zoster (Shingles)": 8, "Vitiligo": 9, "Impetigo": 10, "Molluscum contagiosum": 11,
    "Scabies": 13, "Warts (Verruca vulgaris)": 14, "Warts": 14, "Seborrheic dermatitis": 15,
    "Cellulitis": 17, "Herpes simplex (Cold sores)": 18, "Cold sores": 18, "Pityriasis versicolor": 19,
    "Melanoma": 20, "Basal Cell Carcinoma": 21, "Actinic Keratosis": 22, "Seborrheic Keratosis": 23,
    "Dermatofibroma": 24, "Cherry Angioma": 25, "Melanocytic Nevi": 26, "Hidradenitis Suppurativa": 27,
    "Alopecia Areata": 28, "Melasma": 29
}

ID2LABEL = {
    0: "Eczema", 1: "Dermatitis", 2: "Psoriasis", 3: "Acne", 4: "Urticaria", 
    5: "Pigmentation / Dark Spots", 6: "Ringworm", 7: "Rosacea", 8: "Shingles",
    9: "Vitiligo", 10: "Impetigo", 11: "Molluscum Contagiosum", 12: "Folliculitis",
    13: "Scabies", 14: "Warts", 15: "Seborrheic Dermatitis", 16: "Lichen Planus",
    17: "Cellulitis", 18: "Herpes Simplex", 19: "Pityriasis Versicolor",
    20: "Melanoma", 21: "Basal Cell Carcinoma", 22: "Actinic Keratosis",
    23: "Seborrheic Keratosis", 24: "Dermatofibroma", 25: "Cherry Angioma",
    26: "Melanocytic Nevi", 27: "Hidradenitis Suppurativa", 28: "Alopecia Areata",
    29: "Melasma"
}'''),
    (r'num_labels=20', r'num_labels=30'),
    (r'disease_symptoms\[19\]\.append\(s\)', r'''disease_symptoms[19].append(s)
        
    symptoms_20 = ["assymetrical mole", "border irregularity", "changing mole color", "bleeding mole", "growing spot"]
    for s in symptoms_20: disease_symptoms[20].append(s)
    
    symptoms_21 = ["pearly bump", "pink growth", "sore that bleeds easily", "translucent skin bump"]
    for s in symptoms_21: disease_symptoms[21].append(s)
    
    symptoms_22 = ["rough scaly patch", "sandpaper skin texture", "pink precancer spot", "sun damaged spot"]
    for s in symptoms_22: disease_symptoms[22].append(s)
    
    symptoms_23 = ["waxy brown bump", "pasted on growth", "crusty black spot", "raised age spot"]
    for s in symptoms_23: disease_symptoms[23].append(s)
    
    symptoms_24 = ["hard brown lump", "dimple when pinched", "firm bump on leg"]
    for s in symptoms_24: disease_symptoms[24].append(s)
    
    symptoms_25 = ["bright red bump", "cherry red small spot", "red mole"]
    for s in symptoms_25: disease_symptoms[25].append(s)
    
    symptoms_26 = ["normal brown mole", "round even spot", "stable skin spot"]
    for s in symptoms_26: disease_symptoms[26].append(s)
    
    symptoms_27 = ["painful boils armpit", "groin abscess", "recurrent cysts groin", "tunneling sores"]
    for s in symptoms_27: disease_symptoms[27].append(s)
    
    symptoms_28 = ["patchy hair loss", "sudden bald spot", "round hairless area"]
    for s in symptoms_28: disease_symptoms[28].append(s)
    
    symptoms_29 = ["facial hyperpigmentation", "brown mask pregnant", "dark patches cheeks"]
    for s in symptoms_29: disease_symptoms[29].append(s)
''')
]

fallback_replacements = distilbert_replacements


patch_file(r"d:\Research\zip skin\Reserch_Skin-care-deseases\backend\train_distilbert.py", distilbert_replacements)
try:
    patch_file(r"d:\Research\zip skin\Reserch_Skin-care-deseases\backend\retrain_fallback_model.py", distilbert_replacements)
except:
    pass
