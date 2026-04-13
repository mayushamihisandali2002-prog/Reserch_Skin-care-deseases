import re

filepath = r"d:\Research\zip skin\Reserch_Skin-care-deseases\backend\retrain_fallback_model.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Update mapping in retrain fallback
rep = r'''    DISEASE_MAPPING = {
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
    }'''
content = re.sub(r'    DISEASE_MAPPING = \{.*?\}', rep, content, flags=re.DOTALL)

rep_sym = r'''    new_symptoms = {
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
    }'''
content = re.sub(r'    new_symptoms = \{.*?\}', rep_sym, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
