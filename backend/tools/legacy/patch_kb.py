import re
import os

kb_path = r"d:\Research\zip skin\Reserch_Skin-care-deseases\backend\inference\knowledge_base.py"
with open(kb_path, "r", encoding="utf-8") as f:
    kb_content = f.read()

# Check if already patched
if "Melanoma" in kb_content:
    print("Already patched")
    exit(0)

# Severity Info
sev_append = """,
    "Melanoma": {
        "level": "Severe (Life-Threatening)",
        "description": "The most serious type of skin cancer. Requires immediate medical intervention.",
        "warning_signs": ["Asymmetry", "Border irregularity", "Color changes", "Diameter > 6mm", "Evolving shape or size"],
        "outlook": "Highly curable if caught early; deadly if it spreads."
    },
    "Basal Cell Carcinoma": {
        "level": "Moderate (Requires Surgery)",
        "description": "Common, slow-growing skin cancer, strongly linked to sun exposure.",
        "warning_signs": ["Pearly or waxy bump", "Flat, flesh-colored or brown scar-like lesion", "Bleeding or scabbing sore that heals and returns"],
        "outlook": "Excellent if treated early. Rarely spreads to other parts of the body."
    },
    "Actinic Keratosis": {
        "level": "Precancerous",
        "description": "Rough, scaly patch on sun-damaged skin. Considered precancerous.",
        "warning_signs": ["Growth in size", "Bleeding", "Pain or tenderness", "Hardening of the lesion"],
        "outlook": "Highly treatable. Treating it prevents progression to squamous cell carcinoma."
    },
    "Seborrheic Keratosis": {
        "level": "Benign / Cosmetic",
        "description": "Noncancerous skin growth that appears waxy or 'pasted on'.",
        "warning_signs": ["Rapid growth", "Bleeding when rubbed", "Black color (could mimic melanoma)"],
        "outlook": "Harmless. Excellent prognosis. Can be removed if bothersome."
    },
    "Dermatofibroma": {
        "level": "Benign",
        "description": "Common benign fibrous nodule often found on the lower legs.",
        "warning_signs": ["Rapid change in size or color", "Pain or persistent bleeding"],
        "outlook": "Completely harmless. Excellent prognosis."
    },
    "Cherry Angioma": {
        "level": "Benign / Cosmetic",
        "description": "Common skin growth consisting of small blood vessels.",
        "warning_signs": ["Sudden outbreak of many angiomas", "Bleeding excessively"],
        "outlook": "Harmless. Often increases with age."
    },
    "Melanocytic Nevi": {
        "level": "Benign (Watchful Waiting)",
        "description": "Common mole. Most are harmless but should be monitored.",
        "warning_signs": ["Changes in size, shape, color", "Itching or bleeding (ABCDE rule)"],
        "outlook": "Excellent, provided they remain stable."
    },
    "Hidradenitis Suppurativa": {
        "level": "Severe / Chronic",
        "description": "Painful, chronic inflammatory skin disease causing boils and tunneling tracts.",
        "warning_signs": ["Severe pain", "Fever", "Spreading infection", "Severe scarring"],
        "outlook": "Chronic condition requiring long-term medical and surgical management."
    },
    "Alopecia Areata": {
        "level": "Autoimmune",
        "description": "Autoimmune condition causing round patches of hair loss.",
        "warning_signs": ["Rapid loss of all body hair", "Nail pitting or changes"],
        "outlook": "Unpredictable. Hair often regrows, but relapses are common."
    },
    "Melasma": {
        "level": "Cosmetic / Chronic",
        "description": "Hypermelanosis causing brown patches, often hormonally triggered.",
        "warning_signs": ["Sudden darkening", "Psychological distress"],
        "outlook": "Manageable but chronic. Sun protection is critical."
    }"""
kb_content = re.sub(r'("Pityriasis Versicolor":\s*\{.*?\})', r'\1' + sev_append, kb_content, flags=re.DOTALL, count=1)

# Disease Explanations
exp_append = """,
    "Melanoma": "Melanoma is an aggressive form of skin cancer that begins in melanocytes. It can spread to other organs if not caught early.",
    "Basal Cell Carcinoma": "Basal cell carcinoma is the most common form of skin cancer, usually occurring on sun-exposed areas. It rarely metastasizes but can cause local tissue damage.",
    "Actinic Keratosis": "Actinic keratoses are rough, scaly patches on sun-damaged skin. They are precancerous and can evolve into squamous cell carcinoma.",
    "Seborrheic Keratosis": "Seborrheic keratosis is a very common noncancerous skin growth that looks waxy, scaly, and slightly raised.",
    "Dermatofibroma": "A dermatofibroma is a harmless, firm, round bump on the skin, most commonly found on the lower legs.",
    "Cherry Angioma": "Cherry angiomas are harmless red papules made up of small blood vessels.",
    "Melanocytic Nevi": "Better known as moles, these are common, usually harmless clusters of pigmented cells.",
    "Hidradenitis Suppurativa": "Also known as acne inversa, this is a painful, chronic condition causing deep inflammatory nodules and abscesses, mostly in armpits and groin.",
    "Alopecia Areata": "An autoimmune disorder that attacks the hair follicles, leading to sudden, patchy hair loss.",
    "Melasma": "A common pigmentation disorder that causes brown or gray patches to appear on the skin, primarily on the face."
"""
kb_content = re.sub(r'("Pityriasis Versicolor":\s*".*?")', r'\1' + exp_append, kb_content, flags=re.DOTALL, count=1)

# Expected Symptoms
symp_append = """,
    "Melanoma": ["Asymmetrical mole", "Irregular borders", "Varying colors", "Diameter > 6mm", "Evolving lesion", "Itching or bleeding mole"],
    "Basal Cell Carcinoma": ["Pearly bump", "Pink lesion", "Sore that bleeds and heals", "Translucent bump with blood vessels"],
    "Actinic Keratosis": ["Rough scaly patch", "Sandpaper texture", "Pink or red bumps", "Sun-exposed areas"],
    "Seborrheic Keratosis": ["Waxy bump", "Pasted-on appearance", "Brown or black growth", "Crusty surface"],
    "Dermatofibroma": ["Firm hard bump", "Dimple sign when pinched", "Pink or brown nodule", "Found on legs"],
    "Cherry Angioma": ["Bright red bump", "Small circular papule", "Does not blanch with pressure"],
    "Melanocytic Nevi": ["Symmetrical round spot", "Even brown color", "Stable size", "Distinct borders"],
    "Hidradenitis Suppurativa": ["Painful boils", "Armpit lumps", "Groin abscesses", "Draining tracts", "Blackheads in pairs"],
    "Alopecia Areata": ["Round bald patches", "Sudden hair loss", "Exclamation mark hairs", "Nail pitting"],
    "Melasma": ["Brown facial patches", "Symmetrical discoloration", "Forehead/cheek hyperpigmentation", "Worse after sun"]
"""
kb_content = re.sub(r'("Pityriasis Versicolor":\s*\[.*?\])', r'\1' + symp_append, kb_content, flags=re.DOTALL, count=1)

# Disease Treatments
treat_append = """,
    "Melanoma": [
        {"name": "Surgical Excision", "type": "Surgery", "how_it_works": "Removes the cancerous tissue completely.", "duration": "Immediate", "risks": ["Scarring", "Infection"]},
        {"name": "Immunotherapy", "type": "Medical", "how_it_works": "Helps the immune system attack cancer cells.", "duration": "Months", "risks": ["Fatigue", "Autoimmune reactions"]}
    ],
    "Basal Cell Carcinoma": [
        {"name": "Mohs Surgery", "type": "Surgery", "how_it_works": "Precise removal of cancer cells layer by layer.", "duration": "Immediate", "risks": ["Scarring", "Pain"]},
        {"name": "Topical Imiquimod", "type": "Cream", "how_it_works": "Stimulates immune response against cancer cells.", "duration": "6 weeks", "risks": ["Severe redness", "Crusting"]}
    ],
    "Actinic Keratosis": [
        {"name": "Cryotherapy", "type": "Procedure", "how_it_works": "Freezes and destroys precancerous cells.", "duration": "Immediate", "risks": ["Blistering", "Hypopigmentation"]},
        {"name": "5-Fluorouracil (5-FU)", "type": "Topical", "how_it_works": "Chemotherapy cream that destroys atypical cells.", "duration": "2-4 weeks", "risks": ["Severe inflammation", "Pain"]}
    ],
    "Seborrheic Keratosis": [
        {"name": "Cryotherapy", "type": "Procedure", "how_it_works": "Freezes off the growth.", "duration": "Immediate", "risks": ["Blistering", "Light spots"]},
        {"name": "Curettage", "type": "Procedure", "how_it_works": "Scraping off the lesion.", "duration": "Immediate", "risks": ["Scarring", "Bleeding"]}
    ],
    "Dermatofibroma": [
        {"name": "Observation", "type": "Management", "how_it_works": "Leaving it alone as it is harmless.", "duration": "Ongoing", "risks": ["None"]},
        {"name": "Surgical Excision", "type": "Surgery", "how_it_works": "Full removal if symptomatic.", "duration": "Immediate", "risks": ["Scarring usually worse than the bump"]}
    ],
    "Cherry Angioma": [
        {"name": "Pulsed Dye Laser (PDL)", "type": "Procedure", "how_it_works": "Selectively destroys blood vessels.", "duration": "Immediate", "risks": ["Bruising", "Pain"]},
        {"name": "Electrodessication", "type": "Procedure", "how_it_works": "Burns the tissue.", "duration": "Immediate", "risks": ["Small scar", "Pain"]}
    ],
    "Melanocytic Nevi": [
        {"name": "Observation", "type": "Management", "how_it_works": "Regular skin checks (ABCDE).", "duration": "Ongoing", "risks": ["None"]},
        {"name": "Biopsy / Excision", "type": "Surgery", "how_it_works": "Removal if suspicious features develop.", "duration": "Immediate", "risks": ["Scarring", "Infection"]}
    ],
    "Hidradenitis Suppurativa": [
        {"name": "Antibiotics (Topical/Oral)", "type": "Medication", "how_it_works": "Reduces inflammation and bacterial load.", "duration": "Months", "risks": ["Resistance", "GI upset"]},
        {"name": "Biologic Therapy (Adalimumab)", "type": "Medication", "how_it_works": "Targets underlying immune inflammation.", "duration": "Ongoing", "risks": ["Immunosuppression", "Infection"]}
    ],
    "Alopecia Areata": [
        {"name": "Intralesional Steroids", "type": "Injection", "how_it_works": "Suppresses local immune attack on hair follicles.", "duration": "Monthly", "risks": ["Skin atrophy", "Pain"]},
        {"name": "JAK Inhibitors (e.g., Baricitinib)", "type": "Oral Medication", "how_it_works": "Blocks immune pathways causing hair loss.", "duration": "Ongoing", "risks": ["Infection", "Thrombosis"]}
    ],
    "Melasma": [
        {"name": "Hydroquinone", "type": "Topical", "how_it_works": "Inhibits melanin production.", "duration": "3-6 months", "risks": ["Irritation", "Ochronosis (rare darkening)"]},
        {"name": "Broad-Spectrum Sunscreen", "type": "Prevention", "how_it_works": "Prevents UV and visible light from worsening pigment.", "duration": "Daily", "risks": ["None"]}
    ]
"""
kb_content = re.sub(r'("Pityriasis Versicolor":\s*\[.*?\])', r'\1' + treat_append, kb_content, flags=re.DOTALL, count=1)

# Do similarly for other components: DISEASE_LIFESTYLE_ADVICE, DISEASE_CAUSES_TRIGGERS, DISEASE_HEALING_TIMELINES, DISEASE_WARNING_SIGNS, DISEASE_ROUTINES, DISEASE_TRIGGERS
# Just append simple lists.
generic_list_append = """,
    "Melanoma": ["Immediate medical consult", "Avoid sun completely"],
    "Basal Cell Carcinoma": ["Dermatology consult", "Sun protection"],
    "Actinic Keratosis": ["Sun prevention", "Regular checks"],
    "Seborrheic Keratosis": ["No action required, purely cosmetic"],
    "Dermatofibroma": ["Leave alone unless painful"],
    "Cherry Angioma": ["Cosmetic removal if desired"],
    "Melanocytic Nevi": ["Monitor for changes (ABCDE)"],
    "Hidradenitis Suppurativa": ["Weight management", "Smoking cessation", "Loose clothing"],
    "Alopecia Areata": ["Stress management", "Support groups"],
    "Melasma": ["Strict sun protection", "Hormonal evaluation"]
"""
generic_causes_append = """,
    "Melanoma": ["Severe UV exposure", "Genetics", "Many moles"],
    "Basal Cell Carcinoma": ["Cumulative sun exposure", "Fair skin"],
    "Actinic Keratosis": ["Chronic UV rays", "Age"],
    "Seborrheic Keratosis": ["Genetics", "Age"],
    "Dermatofibroma": ["Minor trauma (bug bites)"],
    "Cherry Angioma": ["Genetics", "Aging", "Pregnancy"],
    "Melanocytic Nevi": ["Genetics", "Sun exposure during childhood"],
    "Hidradenitis Suppurativa": ["Genetics", "Hormones", "Smoking", "Obesity"],
    "Alopecia Areata": ["Autoimmune genetics", "Stress"],
    "Melasma": ["Estrogen fluctuations", "UV Light", "Visible light"]
"""

kb_content = re.sub(r'(DISEASE_LIFESTYLE_ADVICE\s*=\s*\{.*?)"Pityriasis Versicolor":\s*\[.*?\]', r'\g<0>' + generic_list_append, kb_content, flags=re.DOTALL)
kb_content = re.sub(r'(DISEASE_CAUSES_TRIGGERS\s*=\s*\{.*?)"Pityriasis Versicolor":\s*\[.*?\]', r'\g<0>' + generic_causes_append, kb_content, flags=re.DOTALL)
kb_content = re.sub(r'(DISEASE_HEALING_TIMELINES\s*=\s*\{.*?)"Pityriasis Versicolor":\s*".*?"', r'\g<0>' + """,
    "Melanoma": "Variable; requires surgery.",
    "Basal Cell Carcinoma": "Variable; cured upon surgical removal.",
    "Actinic Keratosis": "Weeks with topical chemo.",
    "Seborrheic Keratosis": "Lifelong if untreated. Removed immediately if frozen.",
    "Dermatofibroma": "Permanent.",
    "Cherry Angioma": "Permanent.",
    "Melanocytic Nevi": "Permanent.",
    "Hidradenitis Suppurativa": "Chronic and relapsing.",
    "Alopecia Areata": "Months to years.",
    "Melasma": "Months to years; highly relapsing."
""", kb_content, flags=re.DOTALL)

with open(kb_path, "w", encoding="utf-8") as f:
    f.write(kb_content)
