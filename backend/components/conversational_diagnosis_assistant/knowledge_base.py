"""
SkinAI Condition Knowledge Base
===============================
Detailed medical guidance, lifestyle tips, and recovery timelines.
"""

# ── 1. Severity Info ──
SEVERITY_INFO = {
    "Eczema": {
        "level": "Mild to Moderate",
        "description": "Eczema is generally not dangerous but can significantly impact quality of life.",
        "warning_signs": ["Severe cracking or bleeding", "Signs of infection (pus, fever)", "Spreading rapidly", "Affecting sleep or daily activities"],
        "outlook": "Most cases are manageable with proper treatment. Flare-ups come and go, but symptoms can be controlled."
    },
    "Dermatitis": {
        "level": "Usually Mild",
        "description": "Contact dermatitis is typically not serious and resolves once the irritant is removed.",
        "warning_signs": ["Widespread rash covering large areas", "Difficulty breathing (allergic reaction)", "Blistering or oozing", "No improvement after 2 weeks"],
        "outlook": "Excellent prognosis. Identifying and avoiding triggers prevents recurrence."
    },
    "Psoriasis": {
        "level": "Chronic but Manageable",
        "description": "Psoriasis is a chronic autoimmune condition. While not life-threatening, it requires ongoing management.",
        "warning_signs": ["Joint pain or stiffness (psoriatic arthritis)", "Plaques covering >10% of body", "Pustular or erythrodermic flare-ups", "Severe nail changes"],
        "outlook": "Not curable but highly treatable. Many people achieve significant symptom control with modern treatments."
    },
    "Acne": {
        "level": "Mild to Moderate",
        "description": "Acne is very common and not dangerous, though severe cases can cause scarring.",
        "warning_signs": ["Deep, painful cysts or nodules", "Scarring occurring", "No response to over-the-counter treatments", "Significant emotional distress"],
        "outlook": "Most acne clears with treatment. Early intervention prevents scarring."
    },
    "Urticaria": {
        "level": "Usually Mild (Can Be Urgent)",
        "description": "Hives are typically harmless and temporary, but watch for signs of anaphylaxis.",
        "warning_signs": ["Difficulty breathing or swallowing", "Swelling of face, lips, or throat", "Dizziness or feeling faint", "Rapid heartbeat"],
        "outlook": "Acute hives usually resolve within 24-48 hours. Chronic cases may need investigation."
    },
    "Pigmentation / Dark Spots": {
        "level": "Primarily Cosmetic",
        "description": "Most pigmentation is harmless but can affect appearance and confidence.",
        "warning_signs": ["Rapidly changing borders (ABCDE rule)", "Developing a range of colors", "Itching or bleeding in a single spot", "Large size (>6mm)"],
        "outlook": "Excellent prognosis for basic spots. Deep pigmentation like melasma requires long-term sun protection."
    },
    "Ringworm": {
        "level": "Infectious but Mild",
        "description": "Fungal infection that is highly contagious but easily treated with antifungals.",
        "warning_signs": ["Spreading to scalp or nails", "Persistent itching causing skin breakdown", "Signs of secondary bacterial infection (pus)", "No improvement after 2 weeks of OTC treatment"],
        "outlook": "Usually resolves within 2-4 weeks of consistent antifungal application."
    },
    "Rosacea": {
        "level": "Chronic and Sensitive",
        "description": "Long-term skin condition causing redness and visible blood vessels, often triggered by heat or diet.",
        "warning_signs": ["Eye irritation or redness (Ocular Rosacea)", "Thickening of skin (especially on the nose)", "Severe, painful pustules", "Significant persistent flushing"],
        "outlook": "Manageable with lifestyle changes and topical treatments. Flash-ups are common but controllable."
    },
    "Shingles": {
        "level": "Moderate to Severe (Urgent)",
        "description": "Viral infection causing a painful, blistering rash. Requires prompt medical attention.",
        "warning_signs": ["Rash near the eye (danger to vision)", "Intense, debilitating pain", "Widespread blisters", "Fever or general malaise"],
        "outlook": "Antiviral treatment within 72 hours significantly reduces recovery time and prevents long-term nerve pain (PHN)."
    },
    "Vitiligo": {
        "level": "Autoimmune / Chronic",
        "description": "A condition in which the skin loses its pigment-producing cells, resulting in milky-white patches.",
        "warning_signs": ["Rapid spread of white patches", "Internal health issues (uveitis)", "Associated thyroid problems"],
        "outlook": "Progression varies; treatments can help restore pigment but don't cure the underlying cause."
    },
    "Impetigo": {
        "level": "Contagious Bacterial",
        "description": "A highly contagious bacterial skin infection common in children, characterized by honey-colored crusts.",
        "warning_signs": ["Spreading rapidly to others", "Deep sores that scar", "High fever", "Signs of kidney inflammation (rare)"],
        "outlook": "Responds very well to antibiotic treatment within 24-48 hours."
    },
    "Molluscum Contagiosum": {
        "level": "Localized Viral",
        "description": "A viral infection that causes small, painless, dome-shaped pearly bumps with a central dimple.",
        "warning_signs": ["Severe itching causing secondary infection", "Large size (>10mm)", "Signs of weakened immunity"],
        "outlook": "Usually resolves on its own without treatment, though it can take 6-12 months."
    },
    "Folliculitis": {
        "level": "Follicular Inflammation",
        "description": "Inflammation or infection of the hair follicles, appearing as small red bumps or white-headed pimples around hair.",
        "warning_signs": ["Boils or large painful lumps", "Spreading to deeper layers", "Recurrence after OTC treatment"],
        "outlook": "Usually clears with better hygiene or topical antibiotics."
    },
    "Scabies": {
        "level": "Parasitic (Urgent)",
        "description": "An infestation by tiny mites that burrow into the skin, causing intense nocturnal itching.",
        "warning_signs": ["Crusted scabies (severe form)", "Infection of entire household", "Sores from scratching that get infected"],
        "outlook": "Cured only with prescription scabicidal lotions; requires treatment of all household contacts."
    },
    "Warts": {
        "level": "Common Viral",
        "description": "Small, grainy skin growths caused by the human papillomavirus (HPV).",
        "warning_signs": ["Painful clusters (Mosaic warts)", "Warts that bleed or change shape", "Spreading to face or genitals"],
        "outlook": "Commonly treated with salicylic acid or freezing; often disappear spontaneously."
    },
    "Seborrheic Dermatitis": {
        "level": "Chronic / Inflammatory",
        "description": "A common skin condition that mainly affects the scalp, causing scaly, itchy, red patches and stubborn dandruff.",
        "warning_signs": ["Severe inflammation of eyelids (blepharitis)", "Secondary fungal overgrowth", "Hair loss (temporary)"],
        "outlook": "Manageable with medicated shampoos and creams; periodic flare-ups are common."
    },
    "Lichen Planus": {
        "level": "Inflammatory / Autoimmune",
        "description": "An inflammatory condition that can affect skin, hair, nails, and mucous membranes, marked by purple, itchy, flat-topped bumps.",
        "warning_signs": ["Painless white streaks in mouth", "Abnormal nail changes", "Rapid widespread rash"],
        "outlook": "Usually resolves within 18 months, but can be managed with anti-inflammatory topicals."
    },
    "Cellulitis": {
        "level": "Urgent Bacterial",
        "description": "A common, potentially serious bacterial skin infection that affects the deeper layers of the skin.",
        "warning_signs": ["Red area that expands rapidly", "Fever and chills", "Streaking (lymphangitis)", "Skin feels hot and very tender"],
        "outlook": "Requires prompt oral or IV antibiotics to prevent serious complications."
    },
    "Herpes Simplex": {
        "level": "Recurrent Viral",
        "description": "A viral infection caused by HSV-1 or HSV-2, resulting in small, fluid-filled blisters (cold sores).",
        "warning_signs": ["Infection near the eye", "Worsening with high fever", "Spreading to non-lip areas"],
        "outlook": "Manageable with antivirals; the virus remains dormant in nerves between outbreaks."
    },
    "Pityriasis Versicolor": {
        "level": "Superficial Fungal",
        "description": "A common fungal infection that causes small, discolored patches of skin.",
        "warning_signs": ["Itching that doesn't resolve with OTC antifungals", "Widespread involvement on the torso"],
        "outlook": "Treatable with antifungal creams or shampoos, though skin color may take months to return."
    },
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
    }
}

# ── 2. Lifestyle Advice ──
LIFESTYLE_ADVICE = {
    "Eczema": {
        "do": ["Moisturize immediately after bathing", "Use fragrance-free products", "Wear soft, breathable fabrics (cotton)", "Keep nails short to reduce scratching damage", "Use a humidifier in dry weather"],
        "avoid": ["Hot showers (use lukewarm water)", "Harsh soaps and detergents", "Wool and synthetic fabrics", "Known triggers (dust, certain foods)", "Scratching when itchy"],
        "home_remedies": ["Oatmeal baths can soothe itching", "Coconut oil as a natural moisturizer", "Cool compresses for flare-ups", "Wet wrap therapy for severe patches"]
    },
    "Dermatitis": {
        "do": ["Identify and remove the irritant/allergen", "Keep the area clean and dry", "Apply cool compresses", "Use hypoallergenic products", "Wear protective gloves when cleaning"],
        "avoid": ["Contact with known irritants", "Scratching or rubbing the area", "Tight clothing on affected areas", "Overheating", "Strong fragrances"],
        "home_remedies": ["Aloe vera gel for soothing", "Cold compresses to reduce itching", "Gentle cleansing with mild soap", "Petroleum jelly as a barrier"]
    },
    "Psoriasis": {
        "do": ["Take daily baths (brief, lukewarm)", "Moisturize heavily after bathing", "Get moderate sun exposure", "Manage stress levels", "Maintain a healthy weight"],
        "avoid": ["Alcohol consumption", "Smoking", "Skin injuries (cuts, scrapes)", "Stress", "Certain medications (consult doctor)"],
        "home_remedies": ["Dead Sea salt baths", "Tea tree oil (diluted)", "Aloe vera for scaling", "Fish oil supplements (consult doctor)"]
    },
    "Acne": {
        "do": ["Wash face twice daily gently", "Use non-comedogenic products", "Change pillowcases frequently", "Stay hydrated", "Maintain consistent sleep schedule"],
        "avoid": ["Touching your face", "Popping or picking pimples", "Heavy makeup", "Over-washing (irritates skin)", "Greasy hair products near face"],
        "home_remedies": ["Tea tree oil (spot treatment)", "Honey masks (antibacterial)", "Green tea extract", "Ice cubes for inflammation"]
    },
    "Urticaria": {
        "do": ["Keep a symptom diary", "Wear loose, comfortable clothing", "Stay cool", "Take antihistamines as needed", "Apply calamine lotion"],
        "avoid": ["Known triggers (foods, medications)", "Extreme temperatures", "Tight clothing", "Stress and anxiety", "Alcohol"],
        "home_remedies": ["Cool compresses", "Oatmeal baths", "Aloe vera gel", "Baking soda paste for itching"]
    },
    "Pigmentation / Dark Spots": {
        "do": ["Apply broad-spectrum SPF 50+ every 2 hours outdoors", "Wear wide-brimmed hats and sunglasses", "Use brightening serums with Vitamin C or Niacinamide", "Stay consistent with treatment routines"],
        "avoid": ["Direct midday sun exposure (10 AM - 4 PM)", "Picking at acne (prevents post-inflammatory spots)", "Tanning beds", "Harsh physical scrubs", "Unprotected sun exposure"],
        "home_remedies": ["Aloe vera for soothing inflammation", "Niacinamide for evening skin tone", "Consistent hydration", "Gentle chemical exfoliation (AHAs)"]
    },
    "Ringworm": {
        "do": ["Apply antifungal cream 2cm beyond the visible border", "Wash hands thoroughly after touching the area", "Keep the area clean and dry", "Wash towels and bedding frequently in hot water"],
        "avoid": ["Sharing personal items like towels or hairbrushes", "Scratching the rash (prevents spreading)", "Tight-fitting clothing that traps moisture", "Touching pets that may have bald patches"],
        "home_remedies": ["Tea tree oil (diluted)", "Apple cider vinegar compresses", "Keeping the area exposed to air"]
    },
    "Rosacea": {
        "do": ["Use very gentle, soap-free cleansers", "Apply broad-spectrum sunscreen daily (physical blockers like Zinc preferred)", "Keep a trigger diary (spicy food, alcohol, heat)", "Cool the skin with lukewarm water"],
        "avoid": ["Spicy foods and hot beverages", "Alcohol (especially red wine)", "Harsh exfoliants and astringents", "Overheating and heavy exercise in heat"],
        "home_remedies": ["Green tea compresses to reduce redness", "Aloe vera gel", "Chamomile tea soaks"]
    },
    "Shingles": {
        "do": ["Seek medical attention within 72 hours for antivirals", "Keep the rash covered with a non-stick bandage", "Wear loose-fitting cotton clothing", "Rest and manage stress"],
        "avoid": ["Contact with pregnant women or unvaccinated people", "Scratching or popping blisters", "Applying heavy ointments without advice", "Tight bandages"],
        "home_remedies": ["Cool baths with colloidal oatmeal", "Calamine lotion for itching", "Cool, damp compresses"]
    },
    "Vitiligo": {
        "do": ["Wear high SPF daily to protect depigmented areas", "Use camouflage makeup or skin dyes", "Incorporate Vitamin D into diet", "Monitor for thyroid or other autoimmune signs"],
        "avoid": ["Sunburn (extremely high risk in white patches)", "Skin injury (Koebner phenomenon)", "Tattoos in active patches"],
        "home_remedies": ["Ginkgo biloba extract", "Managing stress", "Sun protection"]
    },
    "Impetigo": {
        "do": ["Wash lesions with mild soap and water", "Cover sores with gauze", "Wash hands immediately after touching infected skin", "Keep towels and utensils separate"],
        "avoid": ["Scratching the honey crusts", "Contact sports", "Sharing personal items", "Going to school until 24-48h of antibiotics"],
        "home_remedies": ["Warm water soaks to remove crusts", "Tea tree oil (diluted)"]
    },
    "Molluscum Contagiosum": {
        "do": ["Cover bumps with a bandage when in contact with others", "Wash hands frequently", "Dry the bumps with a separate towel"],
        "avoid": ["Shaving over the bumps", "Scratching or picking at the lesions", "Sharing gym equipment or towels"],
        "home_remedies": ["Tea tree oil", "Apple cider vinegar soaks", "Iodine solutions"]
    },
    "Folliculitis": {
        "do": ["Use a fresh razor every time you shave", "Wash regularly with antibacterial soap", "Apply warm compresses to drain pustules", "Wear loose clothing"],
        "avoid": ["Sharing razors", "Tight synthetic clothing", "Using oily skincare that clogs follicles", "Hot tubs with poor hygiene"],
        "home_remedies": ["Warm salt water compresses", "Aloe vera", "Avoiding shaving for several days"]
    },
    "Scabies": {
        "do": ["See a doctor for prescription Permethrin", "Treat all household members simultaneously", "Wash all clothes and linens in 60°C (140°F) water", "Vacuum carpets and upholstery"],
        "avoid": ["Close physical contact until 24h after treatment", "Sharing towels/bedding", "Delaying treatment for family members"],
        "home_remedies": ["Tea tree oil for itch relief", "Neem oil", "Clove oil"]
    },
    "Warts": {
        "do": ["Apply 17% salicylic acid daily", "Cover the wart with duct tape to irritate it", "Keep the area clean and dry", "Wash hands after treating the wart"],
        "avoid": ["Picking at the wart", "Walking barefoot in public pools/showers", "Sharing nail clippers used on warts"],
        "home_remedies": ["Duct tape occlusion", "Apple cider vinegar soaks", "Garlic extracts"]
    },
    "Seborrheic Dermatitis": {
        "do": ["Use anti-dandruff shampoos containing Ketoconazole", "Wash the skin gently with mild soap", "Apply mineral oil to soften scales", "Rinse well after shampooing"],
        "avoid": ["Heavy hair stylers or oils", "Harsh soaps on face", "Scratching the scalp"],
        "home_remedies": ["Apple cider vinegar rinses", "Tea tree oil shampoo", "Coconut oil for scaling"]
    },
    "Lichen Planus": {
        "do": ["Follow a balanced diet to reduce inflammation", "Apply cool compresses to itchy areas", "Maintain good oral hygiene if mouth is affected", "Use soap-free cleansers"],
        "avoid": ["Spicy or acidic foods if mouth is involved", "Skin trauma or injury", "Harsh chemical peels"],
        "home_remedies": ["Oatmeal baths", "Turmeric paste", "Aloe vera gel"]
    },
    "Cellulitis": {
        "do": ["Take the full course of prescribed antibiotics", "Elevate the affected limb to reduce swelling", "Keep the wound clean and covered", "Monitor the red area for spreading"],
        "avoid": ["Ignoring spread of redness", "Applying ointments without medical advice", "Walking on an infected foot", "Scratching the area"],
        "home_remedies": ["Elevation of the limb", "Cold compresses for pain relief", "Rest"]
    },
    "Herpes Simplex": {
        "do": ["Apply antiviral cream at the first sign of tingling", "Keep the area clean and dry", "Wash hands after touching the sore", "Use a separate lip balm/towel"],
        "avoid": ["Kissing others during an outbreak", "Sharing cups or utensils", "Picking at the blisters", "Touching your eyes"],
        "home_remedies": ["Lemon balm cream", "L-lysine supplements", "Cool compresses"]
    },
    "Pityriasis Versicolor": {
        "do": ["Use antifungal shampoos as body wash (Selsen Blue)", "Keep the skin cool and dry", "Wear breathable cotton clothing", "Wait 10 mins before rinsing antifungal wash"],
        "avoid": ["Heavy oily body lotions", "Excessive heat and sweating", "Synthetic clothing"],
        "home_remedies": ["Coconut oil", "Apple cider vinegar", "Garlic oil"]
    }
}

# ── 3. Causes and Triggers ──
CAUSE_INFO = {
    "Eczema": {
        "main_causes": ["Genetic factors (family history)", "Immune system dysfunction", "Skin barrier defects"],
        "triggers": ["Dry skin", "Irritants (soaps, detergents)", "Allergens", "Stress", "Temperature", "Foods"],
        "is_contagious": False,
        "description": "Eczema is a chronic inflammatory skin condition causing dry, itchy skin."
    },
    "Dermatitis": {
        "main_causes": ["Direct contact with irritants or allergens", "Sensitivity to chemicals"],
        "triggers": ["Soaps", "Metals (nickel)", "Plants", "Cosmetics", "Latex", "Fabrics"],
        "is_contagious": False,
        "description": "Dermatitis is skin inflammation often from contact with irritants."
    },
    "Psoriasis": {
        "main_causes": ["Autoimmune disorder", "Genetic predisposition"],
        "triggers": ["Stress", "Skin injuries", "Infections", "Medications", "Cold weather", "Smoking"],
        "is_contagious": False,
        "description": "Psoriasis is an autoimmune condition causing thick, scaly skin patches."
    },
    "Acne": {
        "main_causes": ["Excess oil production", "Clogged hair follicles", "Bacteria", "Hormonal changes"],
        "triggers": ["Hormones", "Medications", "Diet", "Stress", "Oily cosmetics"],
        "is_contagious": False,
        "description": "Acne occurs when hair follicles become clogged with oil and skin cells."
    },
    "Urticaria": {
        "main_causes": ["Allergic reactions", "Histamine release", "Unknown (idiopathic)"],
        "triggers": ["Foods", "Medications", "Insect stings", "Physical stimuli", "Infections", "Stress"],
        "is_contagious": False,
        "description": "Urticaria (hives) are itchy welts caused by histamine release."
    },
    "Pigmentation / Dark Spots": {
        "main_causes": ["Excess melanin production", "Sun damage (UV radiation)", "Hormonal shifts (Melasma)", "Post-inflammatory (Acne/Injury)"],
        "triggers": ["Sunlight", "Hormonal changes", "Heat", "Skin injury or inflammation", "Aging"],
        "is_contagious": False,
        "description": "Hyperpigmentation involves dark patches caused by localized melanin buildup."
    },
    "Ringworm": {
        "main_causes": ["Fungal infection (Dermatophytes)", "Contact with infected humans or animals"],
        "triggers": ["Moisture and warmth", "Skin-to-skin contact", "Contaminated surfaces"],
        "is_contagious": True,
        "description": "A common fungal infection that forms a ring-like rash."
    },
    "Rosacea": {
        "main_causes": ["Genetic factors", "Inappropriate immune response", "Demodex mites", "Vascular hyper-reactivity"],
        "triggers": ["Spicy foods", "Alcohol", "Sunlight", "Heat", "Stress", "Hot drinks"],
        "is_contagious": False,
        "description": "A chronic inflammatory condition causing facial redness and flushing."
    },
    "Shingles": {
        "main_causes": ["Reactivation of the Varicella-Zoster virus (Chickenpox virus)"],
        "triggers": ["Weakened immune system", "Stress", "Aging", "Illness"],
        "is_contagious": True,
        "description": "A viral infection resulting from the reactivation of the chickenpox virus."
    },
    "Vitiligo": {
        "main_causes": ["Autoimmune attack on melanocytes", "Genetic predisposition"],
        "triggers": ["Sunburn", "Emotional stress", "Skin trauma"],
        "is_contagious": False,
        "description": "A condition causing loss of pigment in patches of skin."
    },
    "Impetigo": {
        "main_causes": ["Staphylococcus aureus or Streptococcus pyogenes bacteria"],
        "triggers": ["Close contact", "Minor skin injury", "Warm/humid weather"],
        "is_contagious": True,
        "description": "A common and highly contagious bacterial skin infection."
    },
    "Molluscum Contagiosum": {
        "main_causes": ["Molluscum contagiosum virus (Poxvirus)"],
        "triggers": ["Direct skin-to-skin contact", "Contaminated objects", "Weakened immune system"],
        "is_contagious": True,
        "description": "A viral skin infection causing small, firm bumps."
    },
    "Folliculitis": {
        "main_causes": ["Bacterial or fungal infection of hair follicles", "Friction from clothing"],
        "triggers": ["Shaving", "Sweating", "Hot tubs", "Tight clothes"],
        "is_contagious": False,
        "description": "Inflammation or infection of one or more hair follicles."
    },
    "Scabies": {
        "main_causes": ["Sarcoptes scabiei mites burrowing into skin"],
        "triggers": ["Prolonged skin-to-skin contact", "Infested bedding"],
        "is_contagious": True,
        "description": "An itchy skin condition caused by burrowing mites."
    },
    "Warts": {
        "main_causes": ["Human Papillomavirus (HPV) infection"],
        "triggers": ["Direct contact", "Moist environments", "Small skin breaks"],
        "is_contagious": True,
        "description": "Small, rough skin growths caused by a virus."
    },
    "Seborrheic Dermatitis": {
        "main_causes": ["Malassezia yeast overgrowth", "Inflammatory response"],
        "triggers": ["Stress", "Cold/dry weather", "Oily skin"],
        "is_contagious": False,
        "description": "A chronic skin condition causing scaly patches and dandruff."
    },
    "Lichen Planus": {
        "main_causes": ["Immune system reaction", "Hepatitis C linkage (sometimes)"],
        "triggers": ["Skin injury", "Certain medications", "Oral infections"],
        "is_contagious": False,
        "description": "An inflammatory condition of skin and mucous membranes."
    },
    "Cellulitis": {
        "main_causes": ["Bacteria entering through skin breaks"],
        "triggers": ["Cuts", "Insect bites", "Skin conditions like eczema"],
        "is_contagious": False,
        "description": "A serious bacterial infection of the deep skin layers."
    },
    "Herpes Simplex": {
        "main_causes": ["Herpes Simplex Virus (HSV-1 or HSV-2)"],
        "triggers": ["Sunlight", "Stress", "Illness/Fever", "Menstruation"],
        "is_contagious": True,
        "description": "A viral infection causing recurring blisters near the mouth."
    },
    "Pityriasis Versicolor": {
        "main_causes": ["Overgrowth of Malassezia yeast on the skin"],
        "triggers": ["Hot/humid weather", "Oily skin", "Sweating"],
        "is_contagious": False,
        "description": "A common fungal infection causing discolored patches."
    }
}

# ── 4. Healing Info ──
HEALING_INFO = {
    "Eczema": {
        "timeline": "2-4 weeks with proper treatment",
        "signs_improving": ["Less itching", "Reduced redness", "Skin becoming smoother", "Smaller affected areas"],
        "factors": "Consistency with moisturizing and avoiding triggers is essential.",
        "can_cure": False
    },
    "Dermatitis": {
        "timeline": "1-3 weeks after removing irritant",
        "signs_improving": ["Itching subsides", "Redness fades", "Skin texture normalizes"],
        "factors": "Completely avoiding the trigger is the most important factor.",
        "can_cure": True
    },
    "Psoriasis": {
        "timeline": "4-8 weeks for improvement",
        "signs_improving": ["Scales thinning", "Patches shrinking", "Less silvery appearance"],
        "factors": "Ongoing management is needed as it is a chronic condition.",
        "can_cure": False
    },
    "Acne": {
        "timeline": "4-8 weeks to see results",
        "signs_improving": ["Fewer new breakouts", "Existing pimples healing", "Less inflammation"],
        "factors": "Patience is key; treatments take time to work deep in the pores.",
        "can_cure": True
    },
    "Urticaria": {
        "timeline": "24-48 hours for acute episodes",
        "signs_improving": ["Hives fading", "Less itching", "No new welts appearing"],
        "factors": "Avoid the suspected trigger and take antihistamines as directed.",
        "can_cure": True
    },
    "Pigmentation / Dark Spots": {
        "timeline": "3-6 months for visible fading",
        "signs_improving": ["Edge blurring", "Lighter color", "Reduced patch size"],
        "factors": "Strict sun protection is the #1 factor in treatment success.",
        "can_cure": True
    },
    "Ringworm": {
        "timeline": "2-4 weeks",
        "signs_improving": ["Rash shrinking", "Less scaling", "Redness fading", "Clear center remains but itch stops"],
        "factors": "Consistency with antifungal cream and hygiene.",
        "can_cure": True
    },
    "Rosacea": {
        "timeline": "Ongoing management",
        "signs_improving": ["Less frequent flushing", "Reduced redness", "Fewer pustules"],
        "factors": "Trigger avoidance and gentle skincare are critical.",
        "can_cure": False
    },
    "Shingles": {
        "timeline": "3-5 weeks",
        "signs_improving": ["Blisters crusting over", "Pain level decreasing", "No new lesions"],
        "factors": "Early antiviral treatment is the most important factor.",
        "can_cure": True
    },
    "Vitiligo": {
        "timeline": "6-12 months for response",
        "signs_improving": ["Small spots of pigment returning (repigmentation)", "Halting of patch expansion"],
        "factors": "Patience and consistency with UV or topical therapy.",
        "can_cure": False
    },
    "Impetigo": {
        "timeline": "7-10 days",
        "signs_improving": ["Sores drying up", "Crusts falling off", "No new blisters"],
        "factors": "Full course of antibiotics (oral or topical).",
        "can_cure": True
    },
    "Molluscum Contagiosum": {
        "timeline": "6-18 months",
        "signs_improving": ["Bumps becoming red/inflamed before disappearing", "Shrinking bumps"],
        "factors": "Immune system recognition of the virus.",
        "can_cure": True
    },
    "Folliculitis": {
        "timeline": "1-2 weeks",
        "signs_improving": ["Bumps flattening", "Reduced redness/itching", "No new pustules"],
        "factors": "Improved shaving habits and avoiding friction.",
        "can_cure": True
    },
    "Scabies": {
        "timeline": "2-4 weeks",
        "signs_improving": ["Night itching stops", "Old lesions healing", "No new burrows"],
        "factors": "Treating entire household and washing all linens.",
        "can_cure": True
    },
    "Warts": {
        "timeline": "Weeks to months",
        "signs_improving": ["Wart shrinking", "Disappearance of black dots", "Softening of texture"],
        "factors": "Consistent application of salicylic acid or freezing.",
        "can_cure": True
    },
    "Seborrheic Dermatitis": {
        "timeline": "1-2 weeks for control",
        "signs_improving": ["Reduced flaking", "Less redness on scalp/face", "Itch relief"],
        "factors": "Regular use of medicated shampoos.",
        "can_cure": False
    },
    "Lichen Planus": {
        "timeline": "6-18 months",
        "signs_improving": ["Bumps flattening into brown patches", "Reduced itching"],
        "factors": "Stress management and topical anti-inflammatories.",
        "can_cure": True
    },
    "Cellulitis": {
        "timeline": "7-14 days",
        "signs_improving": ["Redness shrinking in size", "Area feels less hot/painful", "Fever subsiding"],
        "factors": "Completing the full antibiotic course.",
        "can_cure": True
    },
    "Herpes Simplex": {
        "timeline": "7-10 days",
        "signs_improving": ["Scabs forming", "Pain/tingling stops", "Sores drying out"],
        "factors": "Early antiviral use (oral or topical).",
        "can_cure": False
    },
    "Pityriasis Versicolor": {
        "timeline": "2-4 weeks (patches take longer)",
        "signs_improving": ["Scaling stops", "Patches no longer itchy", "Fungus cleared"],
        "factors": "Skin color takes 1-3 months to return to normal after fungus is gone.",
        "can_cure": True
    }
}

# ── 5. Worsening Info ──
WORSENING_INFO = {
    "Eczema": {
        "warning_signs": ["Spreading to new areas rapidly", "Skin cracking or bleeding", "Yellow crusting", "Fever"],
        "when_urgent": "If you see signs of infection (oozing, yellow crust, fever), see a doctor.",
        "spreading": "Not contagious. Scratching can spread it on your own body.",
        "prevention": "Keep skin moisturized and avoid scratching."
    },
    "Dermatitis": {
        "warning_signs": ["Blistering or weeping", "Signs of infection", "Severe swelling", "Difficulty breathing"],
        "when_urgent": "Seek immediate care for breathing trouble or widespread blistering.",
        "spreading": "Spreads only with continued trigger contact. Not contagious.",
        "prevention": "Strict avoidance of your specific irritants/allergens."
    },
    "Psoriasis": {
        "warning_signs": ["Rapid spread", "Pustules forming", "Joint pain/stiffness", "Entire body turning red"],
        "when_urgent": "Full body redness (erythrodermic psoriasis) is a medical emergency.",
        "spreading": "Can spread to new body areas but is not contagious.",
        "prevention": "Manage stress and avoid skin injuries."
    },
    "Acne": {
        "warning_signs": ["Deep, painful cysts", "Scarring developing", "Significant emotional distress"],
        "when_urgent": "Consult a dermatologist if you develop cystic acne or notice scarring.",
        "spreading": "Not contagious. Worsening is usually due to hormonal/oil factors.",
        "prevention": "Maintain a gentle daily routine and do not pop pimples."
    },
    "Urticaria": {
        "warning_signs": ["Swelling of lips/tongue/throat", "Difficulty breathing", "Dizziness/fainting"],
        "when_urgent": "**EMERGENCY:** For throat swelling or trouble breathing, call emergency services.",
        "spreading": "Hives move around the body but are not contagious.",
        "prevention": "Avoid known triggers and carry antihistamines."
    },
    "Pigmentation / Dark Spots": {
        "warning_signs": ["Irregular borders", "Rapid darkening", "Bleeding", "Height changes"],
        "when_urgent": "If a dark spot grows fast or has irregular edges, see a dermatologist to rule out melanoma.",
        "spreading": "May develop more spots with sun exposure. Not contagious.",
        "prevention": "Wear SPF 50+ daily, even on cloudy days."
    },
    "Ringworm": {
        "warning_signs": ["Rash spreading to new areas", "Severe pain or swelling", "Pus or weeping"],
        "when_urgent": "See a doctor if it spreads to the scalp or doesn't improve with OTC creams.",
        "spreading": "Highly contagious through touch or sharing items.",
        "prevention": "Avoid sharing towels, keep skin dry, and treat infected pets."
    },
    "Rosacea": {
        "warning_signs": ["Eye pain or gritiness", "Bulbous nose growth", "Painful inflammatory bumps"],
        "when_urgent": "If eyes feel affected (burning, dry, red), see an ophthalmologist or dermatologist.",
        "spreading": "Does not spread to others. Can worsen locally on face.",
        "prevention": "Strict trigger avoidance and sun protection."
    },
    "Shingles": {
        "warning_signs": ["Rash near eye or nose tip", "Fever", "Intolerable pain"],
        "when_urgent": "**URGENT:** See a doctor immediately (within 72h) for antiviral meds.",
        "spreading": "Contagious to those without chickenpox immunity. Avoid high-risk groups.",
        "prevention": "Vaccination is available for older adults or high-risk individuals."
    },
    "Vitiligo": {
        "warning_signs": ["Sunburned white patches", "Associated eye pain"],
        "when_urgent": "Not urgent, but see a dermatologist for diagnosis and treatment planning.",
        "spreading": "May spread over time. Not contagious.",
        "prevention": "Strict sun protection; managing stress."
    },
    "Impetigo": {
        "warning_signs": ["Sores not healing after 1 week", "Fever", "Difficulty swallowing"],
        "when_urgent": "See a doctor for prescription antibiotics to prevent spread and complications.",
        "spreading": "Highly contagious through skin-to-skin contact or shared items.",
        "prevention": "Good hygiene, treating small cuts, avoiding contact with infected people."
    },
    "Molluscum Contagiosum": {
        "warning_signs": ["Extremely many bumps (>50)", "Bumps near eyes", "Severe inflammation"],
        "when_urgent": "See a doctor if it spreads rapidly or causes significant distress.",
        "spreading": "Highly contagious through touch, especially in pools/gyms.",
        "prevention": "Don't share towels, cover existing bumps with bandages."
    },
    "Folliculitis": {
        "warning_signs": ["Painful boils forming", "High fever", "Recurrent infections"],
        "when_urgent": "If a large painful lump (funiculitis) forms, see a doctor for drainage.",
        "spreading": "Can spread if not kept clean, but usually remains localized.",
        "prevention": "Use sharp razors, clean shaving area, wear loose clothes."
    },
    "Scabies": {
        "warning_signs": ["Widespread crusting on skin", "Secondary bacterial infection"],
        "when_urgent": "**URGENT TREATMENT REQUIRED:** Requires prescription scabicide for household.",
        "spreading": "Extremely contagious through close contact or bedding.",
        "prevention": "Avoid physical contact with infested persons; wash all fabrics."
    },
    "Warts": {
        "warning_signs": ["Bleeding growths", "Pain when walking (plantar warts)", "Facial involvement"],
        "when_urgent": "Usually not urgent, but see a podiatrist for painful foot warts.",
        "spreading": "Contagious; can spread if picked or through wet floors.",
        "prevention": "Use flip-flops in public showers; don't pick at warts."
    },
    "Seborrheic Dermatitis": {
        "warning_signs": ["Internal eye irritation", "Swollen eyelids", "Severe itching"],
        "when_urgent": "Consult a dermatologist if OTC shampoos fail to control it.",
        "spreading": "Does not spread to others. Chronic condition.",
        "prevention": "Stress management and regular medicated hair care."
    },
    "Lichen Planus": {
        "warning_signs": ["Mouth sores that bleed", "Severe hair loss", "Genital involvement"],
        "when_urgent": "See a doctor if mouth or genitals are affected as this can be more severe.",
        "spreading": "Not contagious. Can spread to various body parts over time.",
        "prevention": "Avoid skin trauma and manage stress."
    },
    "Cellulitis": {
        "warning_signs": ["Red 'streaks' moving up limb", "High fever / Chills", "Confusion"],
        "when_urgent": "**URGENT MEDICAL ATTENTION:** Requires antibiotics to prevent sepsis.",
        "spreading": "Spreads rapidly through deep skin tissue. Not contagious.",
        "prevention": "Treat minor cuts promptly; manage underlying skin conditions."
    },
    "Herpes Simplex": {
        "warning_signs": ["Blisters near eye", "Recurring very frequently", "Widespread sores"],
        "when_urgent": "See a doctor if it affects the eyes or lasts more than 10 days.",
        "spreading": "Highly contagious through direct contact (kissing, sharing stuff).",
        "prevention": "Identify triggers (stress, sun); use antivirals early."
    },
    "Pityriasis Versicolor": {
        "warning_signs": ["Large area involvement", "Resistance to treatments"],
        "when_urgent": "Not urgent, but see a doctor if patches are widespread on the body.",
        "spreading": "Not contagious. Yeast is already on everyone's skin.",
        "prevention": "Keep skin dry and use antifungal washes in hot weather."
    }
}

# ── 6. Comprehensive Overview ──
DISEASE_KNOWLEDGE = {
    "Eczema": {
        "overview": "Eczema (atopic dermatitis) is a chronic inflammatory condition affecting 10-20% of people.",
        "symptoms": "Dry, itchy patches that can be red, cracked, or oozing. Common on elbows, knees, and face.",
        "causes": "Combination of genetics, immune dysfunction, and environmental triggers.",
        "treatments": "Moisturizers, topical steroids, antihistamines, and trigger avoidance.",
        "tips": "Moisturize regularly, use fragrance-free products, and avoid hot showers."
    },
    "Dermatitis": {
        "overview": "Dermatitis is skin inflammation often caused by contact with irritants or allergens.",
        "symptoms": "Red, itchy, swollen skin that may blister, ooze, or peel.",
        "causes": "Contact with soaps, chemicals, nickel, or plants. Seborrheic type relates to oil.",
        "treatments": "Avoiding triggers, topical steroids, and soothing moisturizers.",
        "tips": "Identify triggers, patch test new products, and wear protective gloves."
    },
    "Psoriasis": {
        "overview": "Psoriasis is a chronic autoimmune condition causing rapid skin cell turnover.",
        "symptoms": "Thick, red patches covered with silvery scales. Can be itchy or painful.",
        "causes": "Overactive immune system and genetic factors. Triggered by stress or injury.",
        "treatments": "Topical steroids, vitamin D analogs, phototherapy, and systemic meds.",
        "tips": "Keep skin moisturized, manage stress, and get moderate sun exposure."
    },
    "Acne": {
        "overview": "Acne is a condition where hair follicles become clogged with oil and dead skin cells.",
        "symptoms": "Pimples, blackheads, whiteheads, and painful cysts on face, chest, or back.",
        "causes": "Excess oil, clogged pores, bacteria (C. acnes), and hormonal fluctuations.",
        "treatments": "Benzoyl peroxide, salicylic acid, retinoids, and antibiotics.",
        "tips": "Wash gently twice daily, don't pick pimples, and use non-comedogenic products."
    },
    "Urticaria": {
        "overview": "Urticaria (hives) are itchy, raised welts that often appear suddenly.",
        "symptoms": "Red or skin-colored welts that blanch when pressed and move around the body.",
        "causes": "Allergic reactions, infections, stress, or temperature changes.",
        "treatments": "Antihistamines are first-line; avoid triggers; steroids for severe cases.",
        "tips": "Identify and avoid triggers, keep cool, and wear loose clothing."
    },
    "Pigmentation / Dark Spots": {
        "overview": "Hyperpigmentation refers to patches of skin that become darker than the surrounding skin.",
        "symptoms": "Flat, darkened patches or spots ranging from light brown to black.",
        "causes": "Sun damage, inflammation, hormonal changes, or medications.",
        "treatments": "Topical brighteners, sun protection, chemical peels, and laser therapy.",
        "tips": "SPF is non-negotiable, avoid picking skin, and be patient with results."
    },
    "Ringworm": {
        "overview": "Ringworm (Tinea) is a common fungal infection that spreads in a circular pattern.",
        "symptoms": "Itchy, red, circular rash with a clearer center and scaly edges.",
        "causes": "Fungal dermatophytes spreading via contact.",
        "treatments": "Topical antifungal creams (Clotrimazole, Terbinafine).",
        "tips": "Keep the area dry, wash hands often, and don't share personal items."
    },
    "Rosacea": {
        "overview": "Rosacea is a chronic skin condition causing facial redness and often small, red, pus-filled bumps.",
        "symptoms": "Facial flushing, visible blood vessels, red bumps, and eye irritation.",
        "causes": "Genetic and environmental factors; triggers include spicy food and sun.",
        "treatments": "Topical Metronidazole, Azelaic Acid, and oral antibiotics for severe cases.",
        "tips": "Identify triggers, use mineral sunscreen, and avoid harsh products."
    },
    "Shingles": {
        "overview": "Shingles is a viral infection that causes a painful, blistering rash in a specific area.",
        "symptoms": "Pain, burning, numbness, and a red rash that turns into fluid-filled blisters.",
        "causes": "Varicella-zoster virus (the same virus that causes chickenpox).",
        "treatments": "Antiviral medications (Acyclovir), pain relievers, and calamine lotion.",
        "tips": "See a doctor early, keep the rash clean, and avoid contact with vulnerable people."
    },
    "Vitiligo": {
        "overview": "Vitiligo is an autoimmune condition where the skin loses its natural color in patches.",
        "symptoms": "Milky-white patches of skin, often appearing on hands, face, and around body openings.",
        "causes": "Autoimmune destruction of pigment cells (melanocytes).",
        "treatments": "Corticosteroid creams, light therapy (UVB), and skin grafting.",
        "tips": "Use high SPF sunscreen, manage stress, and use cosmetic camouflage if desired."
    },
    "Impetigo": {
        "overview": "Impetigo is a highly contagious bacterial skin infection common in children.",
        "symptoms": "Red sores that quickly rupture, ooze, and form a honey-colored crust.",
        "causes": "Staphylococcus or Streptococcus bacteria entering through skin breaks.",
        "treatments": "Topical Mupirocin cream or oral antibiotics.",
        "tips": "Don't share towels, wash hands frequently, and keep sores covered."
    },
    "Molluscum Contagiosum": {
        "overview": "A viral infection producing small, painless, pearly bumps on the skin.",
        "symptoms": "Small, smooth, dome-shaped bumps with a central dimple; usually skin-colored.",
        "causes": "Molluscum contagiosum virus (Poxvirus).",
        "treatments": "Cryotherapy, curettage, or topical treatments. Often left to heal naturally.",
        "tips": "Avoid scratching, don't share personal items, and cover bumps with bandages."
    },
    "Folliculitis": {
        "overview": "Folliculitis is the inflammation or infection of hair follicles.",
        "symptoms": "Red bumps or white-headed pimples around hair follicles; itching and tenderness.",
        "causes": "Bacterial (Staph) or fungal infection, or irritation from shaving/tight clothes.",
        "treatments": "Antibacterial or antifungal washes, topical antibiotics, and avoiding shaving.",
        "tips": "Use clean razors, wear loose clothing, and avoid hot tubs with poor maintenance."
    },
    "Scabies": {
        "overview": "Scabies is an itchy skin condition caused by burrowing mites.",
        "symptoms": "Intense itching, especially at night, and thin, wavy burrow lines.",
        "causes": "Infestation by the Sarcoptes scabiei mite.",
        "treatments": "Prescription scabicide lotions like Permethrin or oral Ivermectin.",
        "tips": "Treat all household members, wash all clothes in hot water, and be patient with the itch."
    },
    "Warts": {
        "overview": "Warts are common, benign skin growths caused by a viral infection of the skin layer.",
        "symptoms": "Small, rough, grainy growths; often has tiny black dots (clotted blood vessels).",
        "causes": "Infection with Human Papillomavirus (HPV).",
        "treatments": "Salicylic acid, freezing (cryotherapy), or chemical cauterization.",
        "tips": "Don't pick at warts, wear flip-flops in public showers, and keep feet dry."
    },
    "Seborrheic Dermatitis": {
        "overview": "A chronic form of eczema that primarily affects the scalp and oily areas of the face.",
        "symptoms": "Scaly red patches, stubborn dandruff, and yellow/greasy skin scale.",
        "causes": "Overgrowth of Malassezia yeast and an inflammatory skin response.",
        "treatments": "Medicated shampoos (Ketoconazole), topical steroids, and antifungal creams.",
        "tips": "Wash hair regularly, use a mild face cleanser, and manage stress levels."
    },
    "Lichen Planus": {
        "overview": "Lichen planus is an inflammatory condition that causes itchy, purple, flat-topped bumps.",
        "symptoms": "Purple, shiny, flat papules with white streaks (Wickham striae).",
        "causes": "Immune system trigger, sometimes linked to viral infections like Hepatitis C.",
        "treatments": "Corticosteroid creams, antihistamines, and phototherapy.",
        "tips": "Avoid skin injury, use gentle skincare, and see a dentist if mouth is involved."
    },
    "Cellulitis": {
        "overview": "Cellulitis is a potentially serious bacterial infection of the deep skin and underlying tissues.",
        "symptoms": "Expanding red area that feels hot, swollen, and very tender to touch.",
        "causes": "Bacteria (Staph/Strep) entering through a cut, bite, or skin break.",
        "treatments": "Prescription oral or intravenous (IV) antibiotics.",
        "tips": "Treat minor wounds quickly, elevate the infected limb, and seek help if fever occurs."
    },
    "Herpes Simplex": {
        "overview": "A viral infection causing recurring small, painful blisters around the lips (cold sores).",
        "symptoms": "Tingling, burning sensation followed by a cluster of small blisters.",
        "causes": "Herpes Simplex Virus (HSV-1).",
        "treatments": "Antiviral creams (Zovirax) or oral medications (Valacyclovir).",
        "tips": "Apply cream at the first sign of tingling, don't kiss during outbreaks, and use sunblock."
    },
    "Pityriasis Versicolor": {
        "overview": "A common fungal infection that causes small, discolored patches on the skin.",
        "symptoms": "Light or dark patches that don't tan; fine scaling and occasional itching.",
        "causes": "Overgrowth of a common yeast (Malassezia) on the skin's surface.",
        "treatments": "Antifungal shampoos used as body wash (Ketoconazole, Selenium Sulfide).",
        "tips": "In hot weather, keep skin dry and use antifungal washes once a week."
    }
}

# ── 7. Global Keyword Extraction ──
SYMPTOM_KEYWORDS = [
    "itching", "itchy", "itch", "redness", "red", "dry", "dryness",
    "scaling", "scaly", "flaky", "burning", "pain", "painful",
    "swelling", "swollen", "bumps", "pimples", "blisters", "rash",
    "patches", "spots", "cracked", "peeling", "oozing", "crusty",
    "inflammation", "irritation", "sore", "tender", "thickened",
    "discoloration", "whiteheads", "blackheads", "oily", "greasy"
]

SYMPTOM_MAP = {
    "itchy": "itching", "itch": "itching",
    "red": "redness", "scaly": "scaling", "flaky": "scaling",
    "dry": "dryness", "swollen": "swelling",
    "painful": "pain", "sore": "pain",
}

# ── 8. Derived Mappings ──
DISEASE_EXPLANATIONS = {d: info["overview"] for d, info in DISEASE_KNOWLEDGE.items()}
EXPECTED_SYMPTOMS = {
    "Eczema": ["itching", "dryness", "redness", "scaling", "cracked", "inflammation"],
    "Dermatitis": ["redness", "itching", "swelling", "blisters", "rash", "irritation"],
    "Psoriasis": ["scaling", "redness", "itching", "dryness", "patches", "thickened"],
    "Acne": ["pimples", "blackheads", "whiteheads", "oily", "inflammation", "bumps"],
    "Urticaria": ["swelling", "redness", "itching", "bumps", "rash", "welts"],
    "Pigmentation / Dark Spots": ["spots", "darkened", "patches", "brown", "discoloration", "sunspot"],
    "Ringworm": ["ring", "circular", "scaly", "itching", "round", "fungal"],
    "Rosacea": ["redness", "flushing", "veins", "bumps", "burning", "sensitive"],
    "Shingles": ["pain", "blisters", "burning", "band", "localized", "stinging"],
    "Vitiligo": ["white", "pigment", "patches", "pale", "milky", "color"],
    "Impetigo": ["honey", "crust", "scabs", "golden", "sores", "yellow"],
    "Molluscum Contagiosum": ["bumps", "pearly", "dimple", "pearly", "smooth", "dome"],
    "Folliculitis": ["hair", "follicle", "shaving", "bumps", "pustules", "red"],
    "Scabies": ["itch", "night", "burrows", "fingers", "mites", "severe"],
    "Warts": ["verruca", "growth", "grainy", "rough", "cauliflower", "dots"],
    "Seborrheic Dermatitis": ["dandruff", "scalp", "flaking", "scale", "greasy", "yellow"],
    "Lichen Planus": ["purple", "shiny", "flat", "bumps", "mouth", "shiny"],
    "Cellulitis": ["hot", "swollen", "tender", "redness", "pain", "leg"],
    "Herpes Simplex": ["cold", "sore", "lip", "blisters", "tingling", "mouth"],
    "Pityriasis Versicolor": ["spots", "tinea", "patches", "chest", "discolored", "light"],
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
,
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
,
}

DISEASE_ROUTINES = {
    "Eczema": {
        "morning": "Gentle cleanser, thick moisturizer, SPF 30+ sunscreen",
        "night": "Lukewarm bath, pat dry, apply emollient, topical steroid if prescribed",
        "treatment": "Apply hydrocortisone cream or prescribed ointment to affected areas",
    },
    "Dermatitis": {
        "morning": "Fragrance-free cleanser, barrier cream, sunscreen",
        "night": "Gentle cleanse, cool compress if inflamed, apply prescribed cream",
        "treatment": "Identify and avoid triggers, use antihistamines for itch relief",
    },
    "Psoriasis": {
        "morning": "Gentle soap, moisturize immediately, vitamin D cream if prescribed",
        "night": "Coal tar or salicylic acid treatment, heavy moisturizer",
        "treatment": "Apply topical steroids or vitamin D analogs as directed",
    },
    "Acne": {
        "morning": "Salicylic acid cleanser, oil-free moisturizer, non-comedogenic SPF",
        "night": "Double cleanse, benzoyl peroxide or retinoid treatment",
        "treatment": "Apply benzoyl peroxide or prescribed retinoid to affected areas",
    },
    "Urticaria": {
        "morning": "Cool shower, fragrance-free products, antihistamine if needed",
        "night": "Avoid hot water, loose clothing, calamine lotion for itch",
        "treatment": "Take antihistamines, apply cool compresses, avoid known triggers",
    },
    "Pigmentation / Dark Spots": {
        "morning": "Vitamin C serum, Niacinamide, SPF 50+ Sunscreen",
        "night": "Gentle cleanser, Retinol or Azelaic Acid, barrier-repair moisturizer",
        "treatment": "Apply spot treatments or all-over brighteners as part of a consistent routine",
    },
    "Ringworm": {
        "morning": "Clean with mild soap, dry thoroughly, apply antifungal cream",
        "night": "Clean, dry, and reapply antifungal cream; wash bedding",
        "treatment": "Use Terbinafine or Clotrimazole cream twice daily for 2-4 weeks",
    },
    "Rosacea": {
        "morning": "Gentle soap-free cleanser, Azelaic Acid, Mineral SPF 30+",
        "night": "Double cleanse (gentle), Metronidazole gel, lightweight moisturizer",
        "treatment": "Avoid known triggers and use anti-inflammatory topicals",
    },
    "Shingles": {
        "morning": "Clean gently, apply cool compress, apply calamine or non-stick dressing",
        "night": "Loose clothing, pain management, keep the area protected",
        "treatment": "Oral antivirals as prescribed by your doctor immediately",
    },
    "Vitiligo": {
        "morning": "Broad-spectrum SPF 50+, apply topical steroid/calcineurin inhibitor",
        "night": "Gentle cleansing, apply prescribed treatment, psychological support",
        "treatment": "Narrow-band UVB or prescribed topical therapies",
    },
    "Impetigo": {
        "morning": "Gentle wash with soap, remove crusts, apply Mupirocin cream",
        "night": "Wash area, apply Mupirocin and cover with non-stick gauze",
        "treatment": "Topical or oral antibiotics for 7-10 days",
    },
    "Molluscum Contagiosum": {
        "morning": "Keep bumps clean and covered if going into social settings",
        "night": "Wash gently, apply over-the-counter drying agents if recommended",
        "treatment": "Self-resolution or cryotherapy/curettage by doctor",
    },
    "Folliculitis": {
        "morning": "Wash with benzoyl peroxide or antibacterial soap, dry with clean towel",
        "night": "Warm compress to soothe inflammation, apply topical antibiotic",
        "treatment": "Avoid shaving area until inflammation subsides",
    },
    "Scabies": {
        "morning": "Wash off scabicide cream if applied night before, change all linens",
        "night": "Apply Permethrin 5% cream from neck down to feet; leave overnight",
        "treatment": "Prescription scabicides; treat all household members at once",
    },
    "Warts": {
        "morning": "Remove duct tape or bandage, file down dead skin with emery board",
        "night": "Apply 17% salicylic acid, allow to dry, cover with tape/bandage",
        "treatment": "Daily salicylic acid application or professional freezing",
    },
    "Seborrheic Dermatitis": {
        "morning": "Wash with Ketoconazole shampoo, gentle face cleanser",
        "night": "Apply hydrocortisone or antifungal cream to red patches if needed",
        "treatment": "Anti-dandruff shampoo and topical anti-inflammatories",
    },
    "Lichen Planus": {
        "morning": "Cool compress, non-irritating clothing, topical steroid",
        "night": "Moisturize, apply prescribed ointments, manage itch",
        "treatment": "Prescribed corticosteroids and monitoring by dermatologist",
    },
    "Cellulitis": {
        "morning": "Clean wound, apply new bandage, elevate limb, take antibiotic",
        "night": "Elevate limb above heart level, take next dose of antibiotic",
        "treatment": "Full course of oral/IV antibiotics as primary therapy",
    },
    "Herpes Simplex": {
        "morning": "Apply Penciclovir or Acyclovir cream, use lip balm with SPF",
        "night": "Clean area, reapply antiviral cream, keep hydrated",
        "treatment": "Early treatment with topical or oral antivirals",
    },
    "Pityriasis Versicolor": {
        "morning": "Clean skin, apply antifungal lotion or shampoo (let sit 10m)",
        "night": "Keep skin dry, use loose-fitting clothing",
        "treatment": "Antifungal body washes and topical antifungal creams",
    }
}

DISEASE_TRIGGERS = {
    "Eczema": ["Dry skin", "Irritants", "Allergens", "Stress", "Weather", "Foods"],
    "Dermatitis": ["Soaps", "Nickel", "Plants", "Cosmetics", "Latex", "Chemicals"],
    "Psoriasis": ["Stress", "Skin injury", "Infection", "Medication", "Cold weather"],
    "Acne": ["Hormones", "Oily products", "Medications", "Pore-clogging diet", "Stress"],
    "Urticaria": ["Foods", "Medications", "Insect stings", "Heat/Cold", "Stress"],
    "Pigmentation / Dark Spots": ["UV Exposure", "Hormonal changes", "Heat", "Skin injury/Post-Acne", "Visible Light"],
    "Ringworm": ["Dampness", "Skin contact", "Personal hygiene", "Contaminated surfaces"],
    "Rosacea": ["Spicy foods", "Sunlight", "Alcohol", "Extreme temperatures", "Stress"],
    "Shingles": ["Immune stress", "Age", "Illness", "Fatigue"],
    "Vitiligo": ["Sunburn", "Emotional Stress", "Skin trauma"],
    "Impetigo": ["Close contact", "Minor cuts", "Humidity"],
    "Molluscum Contagiosum": ["Physical contact", "Swimming pools", "Sharing towels"],
    "Folliculitis": ["Shaving", "Sweating", "Hot tubs", "Tight clothes"],
    "Scabies": ["Close touch", "Shared bedding", "Overcrowding"],
    "Warts": ["HP Virus", "Wet floors", "Barefoot walking"],
    "Seborrheic Dermatitis": ["Winter weather", "Stress", "Oily skin"],
    "Lichen Planus": ["Medications", "Skin injury", "Infections"],
    "Cellulitis": ["Diabetes", "Poor circulation", "Broken skin"],
    "Herpes Simplex": ["Intense Sun", "Stress", "Fatigue", "Cold weather"],
    "Pityriasis Versicolor": ["Heat", "Humidity", "Oily skin", "Sweating"],
}

# ── 9. Skin Type Info ──
SKIN_TYPE_INFO = {
    "oily": {
        "display": "Oily",
        "recommendations": [
            "Use a gentle gel or foaming cleanser twice daily.",
            "Choose oil-free, non-comedogenic moisturizer.",
            "Use broad-spectrum SPF 30+ every morning.",
            "Use salicylic acid 2-3 times per week if tolerated.",
        ],
        "routine": {
            "morning": "Foaming cleanser, lightweight moisturizer, SPF 30+.",
            "night": "Cleanser, oil-control serum (optional), light moisturizer.",
        },
    },
    "dry": {
        "display": "Dry",
        "recommendations": [
            "Use a creamy, fragrance-free cleanser.",
            "Apply rich moisturizer on damp skin after cleansing.",
            "Use sunscreen SPF 30+ daily.",
            "Avoid over-exfoliation and very hot water.",
        ],
        "routine": {
            "morning": "Gentle cleanser, hydrating moisturizer, SPF 30+.",
            "night": "Cleanser, barrier-repair moisturizer, optional occlusive layer.",
        },
    },
    "combination": {
        "display": "Combination",
        "recommendations": [
            "Use a gentle low-foam cleanser twice daily.",
            "Apply lightweight moisturizer overall, extra on dry areas.",
            "Use broad-spectrum SPF 30+ daily.",
            "Target oily zones with mild exfoliation 1-2 times per week.",
        ],
        "routine": {
            "morning": "Gentle cleanser, balanced moisturizer, SPF 30+.",
            "night": "Cleanser, light moisturizer, spot treatment on oily areas if needed.",
        },
    },
    "unknown": {
        "display": "Unknown",
        "recommendations": [
            "Use a gentle cleanser and fragrance-free moisturizer.",
            "Use broad-spectrum SPF 30+ daily.",
            "Avoid introducing multiple new products at once.",
        ],
        "routine": {
            "morning": "Gentle cleanser, moisturizer, SPF 30+.",
        },
    },
}

# ── 10. Recommended Treatments ──
DISEASE_TREATMENTS = {
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
    "Pigmentation / Dark Spots": [
        {
            "medicine": "Broad Spectrum SPF 50+ Sunscreen",
            "advice":   "Essential to prevent darkening; reapply every 2 hours.",
        },
        {
            "medicine": "Vitamin C Serum (10-20%)",
            "advice":   "Apply in the morning before moisturizer to brighten and protect against free radicals.",
        },
        {
            "medicine": "Azelaic Acid 10-15%",
            "advice":   "Inhibits excess melanin; safe for most skin types and can be used twice daily.",
        },
        {
            "medicine": "Hydroquinone (Doctor supervised)",
            "advice":   "Short-term treatment (3 months) for stubborn spots; requires medical supervision.",
        },
    ],
    "Ringworm": [
        {
            "medicine": "Terbinafine (Lamisil) 1% Cream",
            "advice":   "Apply to the rash and 2cm surrounding it twice daily for at least 1 week after clear.",
        },
        {
            "medicine": "Clotrimazole (Lotrimin) Cream",
            "advice":   "Effective OTC choice; apply twice daily for 2-4 weeks.",
        },
        {
            "medicine": "Keep Area Dry",
            "advice":   "Fungi thrive in moisture; use a dedicated towel and dry thoroughly.",
        },
    ],
    "Rosacea": [
        {
            "medicine": "Metronidazole (MetroGel) 0.75%",
            "advice":   "Standard topical antibiotic; apply twice daily to reduce redness and bumps.",
        },
        {
            "medicine": "Azelaic Acid (Finacea) 15%",
            "advice":   "Reduces inflammation and redness; apply twice daily after cleansing.",
        },
        {
            "medicine": "Mineral Sunscreen (Zinc/Titanium)",
            "advice":   "Chemical sunscreens may sting; mineral versions are better tolerated by rosacea skin.",
        },
    ],
    "Shingles": [
        {
            "medicine": "Acyclovir / Valacyclovir (Oral Antivirals)",
            "advice":   "**MUST START WITHIN 72H:** Reduces duration and severity significantly.",
        },
        {
            "medicine": "Pain Management (Gabapentin / Lidocaine)",
            "advice":   "Prescribed for the intense nerve pain associated with shingles.",
        },
        {
            "medicine": "Calamine Lotion",
            "advice":   "Apply to blisters to dry them out and soothe the intense itching.",
        },
    ],
    "Vitiligo": [
        {
            "medicine": "Topical Corticosteroids (Momentasone)",
            "advice":   "Helps stop progression and may induce repigmentation in early cases.",
        },
        {
            "medicine": "Topical Calcineurin Inhibitors (Tacrolimus)",
            "advice":   "Used for sensitive areas (face, joints) as a non-steroidal alternative.",
        },
        {
            "medicine": "Narrow-band UVB Light Therapy",
            "advice":   "Controlled UV exposure to stimulate pigment-producing cells.",
        },
    ],
    "Impetigo": [
        {
            "medicine": "Mupirocin (Bactroban) 2% Ointment",
            "advice":   "Apply 3× daily for 10 days; essential to cover the area to prevent spread.",
        },
        {
            "medicine": "Oral Antibiotics (Cephalexin)",
            "advice":   "Prescribed if multiple locations are involved or if it's spreading fast.",
        },
        {
            "medicine": "Antibacterial Wash (Chlorhexidine)",
            "advice":   "Gentle cleansing of the area to remove infective crusts.",
        },
    ],
    "Molluscum Contagiosum": [
        {
            "medicine": "Cryotherapy (Liquid Nitrogen)",
            "advice":   "Bumps are frozen by a doctor to destroy the viral tissue.",
        },
        {
            "medicine": "Cantharidin ('Beetle Juice')",
            "advice":   "Applied by professional to create a blister and clear the bump.",
        },
        {
            "medicine": "Tretinoin (Retin-A) 0.025%",
            "advice":   "Can be used to irritate the bumps and prompt the immune system to react.",
        },
    ],
    "Folliculitis": [
        {
            "medicine": "Ketoconazole or Benzoyl Peroxide Cleanser",
            "advice":   "Wash the area twice daily to kill bacteria or fungi in hair follicles.",
        },
        {
            "medicine": "Topical Clindamycin Solution",
            "advice":   "Applied to the individual red bumps to clear bacterial infection.",
        },
        {
            "medicine": "Mupirocin Ointment for Nose",
            "advice":   "Often Staph bacteria colonizes the nose; apply to nostrils if recurrent.",
        },
    ],
    "Scabies": [
        {
            "medicine": "Permethrin 5% Cream (Elimite)",
            "advice":   "Apply from neck to toes, leave for 8-14 hours, then wash. Repeat in 1 week.",
        },
        {
            "medicine": "Crotamiton (Eurax) 10% Cream",
            "advice":   "Alternative for itching; apply twice daily for 2 days.",
        },
        {
            "medicine": "Oral Ivermectin",
            "advice":   "Prescribed for severe cases or when creams cannot be used easily.",
        },
    ],
    "Warts": [
        {
            "medicine": "Salicylic Acid (17-40%)",
            "advice":   "Apply daily after soaking and filing the wart; takes weeks of consistency.",
        },
        {
            "medicine": "Cryotherapy (Freezing)",
            "advice":   "Requires multiple hospital visits every 2-3 weeks until the wart is gone.",
        },
        {
            "medicine": "Imiquimod (Aldara) 5% Cream",
            "advice":   "Stimulates local immune system to attack the wart; used for stubborn cases.",
        },
    ],
    "Seborrheic Dermatitis": [
        {
            "medicine": "Ketoconazole (Nizoral) 2% Shampoo",
            "advice":   "Leave on scalp/face for 5 minutes before rinsing; use twice weekly.",
        },
        {
            "medicine": "Fluocinolone Acetonide Scalp Oil",
            "advice":   "For severe scaling; apply overnight and wash off in the morning.",
        },
        {
            "medicine": "Hydrocortisone 1% Cream (Brief use)",
            "advice":   "Reduces inflammation during a flare; do not use long-term on the face.",
        },
    ],
    "Lichen Planus": [
        {
            "medicine": "Topical Triamcinolone 0.1% Ointment",
            "advice":   "Apply twice daily to reduce itching and flatten purple bumps.",
        },
        {
            "medicine": "Antihistamines (Hydroxyzine)",
            "advice":   "Stronger relief for the intense itching characteristic of this condition.",
        },
        {
            "medicine": "Phototherapy (PUVA)",
            "advice":   "Light therapy combined with medication for widespread skin involvement.",
        },
    ],
    "Cellulitis": [
        {
            "medicine": "Dicloxacillin or Cephalexin (Oral Antibiotics)",
            "advice":   "Standard 7-14 day course; must be taken exactly as prescribed.",
        },
        {
            "medicine": "Elevation of Affected Area",
            "advice":   "Critical to reduce swelling and pain; keep leg/arm above the heart.",
        },
        {
            "medicine": "Wound Care / Gauze",
            "advice":   "If there is an entry wound, keep it clean and covered with sterile dressings.",
        },
    ],
    "Herpes Simplex": [
        {
            "medicine": "Valacyclovir (Valtrex) 2000mg",
            "advice":   "Taken at first sign of tingling; often stops the blister from forming.",
        },
        {
            "medicine": "Acyclovir 5% Ointment",
            "advice":   "Apply to sores 5× daily for 4 days to speed up healing and reduce pain.",
        },
        {
            "medicine": "Docosanol (Abreva) 10%",
            "advice":   "Effective over-the-counter antiviral cream; use 5× daily.",
        },
    ],
    "Pityriasis Versicolor": [
        {
            "medicine": "Ketoconazole (Nizoral) Shampoo",
            "advice":   "Apply to skin as a body wash, leave for 5-10 mins, then rinse.",
        },
        {
            "medicine": "Terbinafine or Clotrimazole Cream",
            "advice":   "Applied twice daily to affected patches for 2 weeks.",
        },
        {
            "medicine": "Oral Fluconazole (Single Dose)",
            "advice":   "Prescribed by doctors for widespread or recurrent infections.",
        },
    ],
}

SKIN_CONDITIONS = {
    "Common Skin Symptoms": [
        "red", "redness", "rash", "itch", "itching", "itchy", "scratch",
        "scratching", "pain", "painful", "dry", "dryness", "patch",
        "patches", "scaly", "scale", "scales", "flaky", "cracked",
        "swelling", "swollen", "burning", "stinging", "bumps", "blister",
        "blisters", "hives", "welts", "spots", "sore", "sores", "oozing",
        "pus", "bleeding"
    ],
    "Eczema": [
        "itching", "dryness", "dry patches", "redness", "red rash",
        "cracked skin", "flaky skin", "scaly patches", "inflammation",
        "sensitive skin", "oozing"
    ],
    "Dermatitis": [
        "red rash", "itching", "swelling", "blisters", "burning",
        "irritation", "inflamed skin", "contact rash", "skin allergy",
        "tender rash"
    ],
    "Psoriasis": [
        "thick scales", "silvery scales", "red patches", "itching",
        "cracked skin", "bleeding skin", "plaque", "dry thick skin",
        "scaling", "thickened patches"
    ],
    "Acne": [
        "pimples", "whiteheads", "blackheads", "cystic acne", "nodules",
        "breakouts", "oily skin", "clogged pores", "pus", "inflamed acne",
        "acne bumps"
    ],
    "Urticaria": [
        "hives", "welts", "itching", "swelling", "raised bumps",
        "red bumps", "rash", "allergic rash", "skin welts", "burning"
    ],
    "Pigmentation / Dark Spots": [
        "dark spots", "uneven skin tone", "pigmentation", "hyperpigmentation",
        "sun spots", "brown patches", "dark patches", "discoloration",
        "darkened skin", "post acne marks"
    ],
    "Ringworm": [
        "ring-shaped rash", "circular rash", "round rash", "itching",
        "red patches", "scaly edges", "spreading rash", "fungal rash",
        "ring rash", "flaky border"
    ],
    "Rosacea": [
        "redness", "flushing", "burning", "stinging", "sensitive skin",
        "visible blood vessels", "facial redness", "cheek redness",
        "irritation", "warm skin", "red face"
    ],
    "Shingles": [
        "painful blisters", "burning pain", "one-sided rash", "band rash",
        "tingling", "stinging", "localized pain", "fluid blisters",
        "nerve pain", "sensitive skin"
    ],
    "Vitiligo": [
        "white patches", "loss of pigment", "depigmentation", "pale patches",
        "milky white skin", "skin color loss", "patchy color", "white spots",
        "uneven pigment", "lighter skin"
    ],
    "Impetigo": [
        "honey crust", "golden crust", "yellow crust", "oozing sores",
        "skin sores", "blisters", "scabs", "crusted rash", "red sores",
        "weeping rash"
    ],
    "Molluscum Contagiosum": [
        "pearly bumps", "dome bumps", "central dimple", "smooth bumps",
        "small bumps", "flesh-colored bumps", "raised papules", "painless bumps",
        "umbilicated bumps", "clustered bumps"
    ],
    "Folliculitis": [
        "hair follicle bumps", "red bumps", "pustules", "itching",
        "tender bumps", "shaving bumps", "inflamed follicles", "pus bumps",
        "hair bumps", "follicle pain"
    ],
    "Scabies": [
        "intense itching", "night itching", "burrows", "finger web itching",
        "mite rash", "small bumps", "scratch marks", "severe itch",
        "wrist rash", "household itching"
    ],
    "Warts": [
        "wart", "warts", "rough growth", "grainy bump", "cauliflower growth",
        "black dots", "hard bump", "skin growth", "verruca", "raised rough bump"
    ],
    "Seborrheic Dermatitis": [
        "dandruff", "greasy scales", "yellow scales", "scalp flakes",
        "flaking", "itchy scalp", "red scalp", "oily patches",
        "facial flaking", "seborrheic rash"
    ],
    "Lichen Planus": [
        "purple bumps", "shiny bumps", "flat-topped bumps", "itchy bumps",
        "mouth streaks", "white mouth lines", "wrist bumps", "ankle bumps",
        "violaceous rash", "skin lesions"
    ],
    "Cellulitis": [
        "hot skin", "swollen skin", "tender skin", "redness", "pain",
        "spreading redness", "warm swelling", "fever", "skin infection",
        "leg swelling"
    ],
    "Herpes Simplex": [
        "cold sore", "lip blisters", "fluid blisters", "tingling",
        "burning", "mouth sores", "painful blisters", "recurrent blisters",
        "crusted blisters", "clustered blisters"
    ],
    "Pityriasis Versicolor": [
        "light patches", "dark patches", "discolored patches", "chest spots",
        "back spots", "fine scaling", "tinea versicolor", "patchy spots",
        "itching", "uneven color"
    ],
    "Melanoma": [
        "asymmetrical mole", "irregular border", "multiple colors",
        "changing mole", "evolving lesion", "bleeding mole", "itching mole",
        "dark mole", "large mole", "new mole"
    ],
    "Basal Cell Carcinoma": [
        "pearly bump", "shiny bump", "bleeding sore", "non-healing sore",
        "pink lesion", "translucent bump", "visible blood vessels",
        "scabbing sore", "waxy bump", "rolled edge"
    ],
    "Actinic Keratosis": [
        "rough patch", "scaly patch", "sandpaper texture", "sun damaged skin",
        "pink patch", "crusty patch", "tender patch", "dry rough spot",
        "precancerous spot", "sun-exposed rash"
    ],
    "Seborrheic Keratosis": [
        "waxy growth", "pasted-on growth", "brown growth", "black growth",
        "crusty surface", "stuck-on bump", "rough plaque", "raised growth",
        "itchy growth", "wart-like growth"
    ],
    "Dermatofibroma": [
        "firm bump", "hard bump", "brown nodule", "pink nodule",
        "dimple sign", "leg bump", "small nodule", "tender nodule",
        "scar-like bump", "stable bump"
    ],
    "Cherry Angioma": [
        "red bump", "bright red bump", "cherry red spot", "red papule",
        "small red dot", "bleeding red bump", "blood vessel spot",
        "round red bump", "ruby spot", "vascular bump"
    ],
    "Melanocytic Nevi": [
        "mole", "brown mole", "round spot", "even color", "stable mole",
        "symmetrical spot", "distinct border", "skin-colored mole",
        "flat mole", "raised mole"
    ],
    "Hidradenitis Suppurativa": [
        "painful boils", "armpit lumps", "groin abscess", "draining tracts",
        "blackheads in pairs", "recurrent boils", "skin tunnels",
        "underarm bumps", "painful nodules", "pus drainage"
    ],
    "Alopecia Areata": [
        "round bald patches", "sudden hair loss", "patchy hair loss",
        "bald spots", "exclamation mark hairs", "nail pitting",
        "smooth bald patch", "hair shedding", "scalp patch", "beard hair loss"
    ],
    "Melasma": [
        "brown facial patches", "symmetrical discoloration", "forehead patches",
        "cheek hyperpigmentation", "worse after sun", "dark facial patches",
        "melasma", "mask-like pigmentation", "brown patches", "uneven pigment"
    ],
}


def _normalize_keyword_text(text: str) -> str:
    chars = []
    for char in str(text or "").lower():
        chars.append(char if char.isalnum() else " ")
    return " ".join("".join(chars).split())


def _keyword_variants(normalized_keyword: str) -> set[str]:
    variants = {normalized_keyword}
    words = normalized_keyword.split()
    if not words:
        return variants

    last_word = words[-1]
    if last_word.endswith("ies") and len(last_word) > 4:
        variants.add(" ".join([*words[:-1], f"{last_word[:-3]}y"]))
    elif last_word.endswith(("ches", "shes", "xes", "zes", "ses")) and len(last_word) > 4:
        variants.add(" ".join([*words[:-1], last_word[:-2]]))
    elif last_word.endswith("s") and len(last_word) > 3:
        variants.add(" ".join([*words[:-1], last_word[:-1]]))
    elif len(last_word) > 2:
        variants.add(" ".join([*words[:-1], f"{last_word}s"]))
    return variants


def _expected_symptom_keyword_categories() -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {
        "Common Skin Symptoms": SKIN_CONDITIONS.get("Common Skin Symptoms", []),
    }
    for condition, symptoms in EXPECTED_SYMPTOMS.items():
        if not isinstance(symptoms, list):
            continue
        categories[condition] = [
            str(symptom)
            for symptom in symptoms
            if isinstance(symptom, str) and symptom.strip()
        ]
    return categories


def validate_skin_condition_keywords(text: str, minimum_keywords: int = 4) -> dict:
    normalized_text = f" {_normalize_keyword_text(text)} "
    matches: list[dict[str, str]] = []
    seen: set[str] = set()
    condition_hits: set[str] = set()

    for condition, keywords in _expected_symptom_keyword_categories().items():
        for keyword in keywords:
            normalized_keyword = _normalize_keyword_text(keyword)
            if not normalized_keyword:
                continue
            variants = _keyword_variants(normalized_keyword)
            matched_variant = next(
                (variant for variant in variants if f" {variant} " in normalized_text),
                None,
            )
            if matched_variant:
                condition_hits.add(condition)
                if not seen.intersection(variants):
                    seen.update(variants)
                    matches.append({"condition": condition, "keyword": keyword})

    return {
        "valid": len(matches) >= minimum_keywords,
        "validation_mode": "expected_symptoms_any_4_across_all_disease_categories",
        "mismatch_symptoms_allowed": True,
        "minimum_keywords": minimum_keywords,
        "keyword_count": len(matches),
        "matches": matches,
        "matched_keywords": [match["keyword"] for match in matches],
        "matched_conditions": sorted(condition_hits),
    }


def _normalize_condition_name(condition: str | None) -> str:
    raw = str(condition or "").replace("_", " ").strip()
    if not raw:
        return "Unknown"

    lowered = raw.lower()
    for known in DISEASE_KNOWLEDGE:
        if known.lower() == lowered:
            return known
    for known in DISEASE_KNOWLEDGE:
        if known.lower() in lowered or lowered in known.lower():
            return known
    return raw.title()


def _text_matches_condition(transcript: str, condition: str) -> tuple[bool, list[str]]:
    text = str(transcript or "").lower()
    expected = EXPECTED_SYMPTOMS.get(condition, [])
    if not isinstance(expected, list):
        return False, []

    normalized_terms = set()
    for word in text.replace("/", " ").replace(",", " ").replace(".", " ").split():
        cleaned = word.strip().lower()
        if cleaned:
            normalized_terms.add(cleaned)
            normalized_terms.add(SYMPTOM_MAP.get(cleaned, cleaned))

    matched: list[str] = []
    for symptom in expected:
        if not isinstance(symptom, str):
            continue
        token = symptom.lower().strip()
        if token and (token in text or token in normalized_terms) and token not in matched:
            matched.append(token)
    return len(matched) > 0, matched[:5]


def _condition_visual_phrase(condition: str) -> str:
    info = DISEASE_KNOWLEDGE.get(condition, {})
    symptoms = str(info.get("symptoms", "")).strip()
    if symptoms:
        phrase = symptoms[0].lower() + symptoms[1:]
        return phrase.rstrip(".")
    return f"visual features commonly associated with {condition.lower()}"


def build_system_summary(
    *,
    condition: str,
    transcript: str,
    image_correct: bool | None,
    text_correct: bool | None,
    mismatch_detected: bool,
    image_accuracy: float = 0.0,
    text_accuracy: float = 0.0,
) -> dict:
    """Build the visible System Summary from the Python knowledge base."""

    condition_name = _normalize_condition_name(condition)
    transcript_text = str(transcript or "").strip()
    if not transcript_text:
        transcript_text = "no symptom text"

    kb_text_match, matched_terms = _text_matches_condition(transcript_text, condition_name)
    if text_correct is None and kb_text_match:
        text_correct = True

    visual_phrase = _condition_visual_phrase(condition_name)
    matched_phrase = ", ".join(matched_terms)
    if matched_phrase:
        text_phrase = f"the text also mentions relevant terms ({matched_phrase})."
    else:
        text_phrase = "the submitted text does not contain clear expected skin symptoms for this condition."

    image_quality_problem = image_correct is False
    image_uncertain = image_correct is None
    text_uncertain = text_correct is None

    if image_correct is True and text_correct is True and not mismatch_detected:
        case_id = "image_and_text_matched"
        summary = (
            f"System analysis indicates the image and text are matched. "
            f"The image is consistent with {condition_name}: {visual_phrase}. "
            f"{text_phrase.capitalize()} The final result is taken from the diagnostic analysis."
        )
    elif image_correct is True and text_correct is False:
        case_id = "image_correct_text_incorrect"
        summary = (
            f"System analysis indicates a mismatch. The image appears to show {condition_name}, "
            f"with visual findings such as {visual_phrase}. However, the user text "
            f"({transcript_text!r}) is not clinically related to the visible skin problem. "
            f"The final result is taken from the diagnostic analysis."
        )
    elif image_quality_problem and text_correct is True:
        case_id = "image_incorrect_text_correct"
        summary = (
            f"System analysis indicates the text is clinically useful, but the image is not reliable. "
            f"The photo may be blurred, unclear, or not closely related to the described skin problem. "
            f"The text points toward {condition_name}; {text_phrase} The final result is taken from "
            f"the diagnostic analysis."
        )
    elif image_quality_problem and text_correct is False:
        case_id = "image_and_text_incorrect"
        summary = (
            f"System analysis cannot confirm a reliable match. The image is weak, blurred, or not clearly "
            f"related to a skin problem, and the text ({transcript_text!r}) does not describe useful skin "
            f"symptoms. Please upload a clearer skin image and describe symptoms such as itch, pain, scaling, "
            f"redness, duration, and body location."
        )
    elif image_uncertain and text_uncertain:
        case_id = "uncertain"
        summary = (
            f"System analysis could not confidently compare the image and text. The final result is still "
            f"taken from the diagnostic analysis, but a clearer image and more specific symptom text would "
            f"make the backend summary stronger."
        )
    else:
        case_id = "partial_match"
        summary = (
            f"System analysis found a partial image-text match for {condition_name}. "
            f"The image score is {image_accuracy:.0f}% and the text alignment score is {text_accuracy:.0f}%. "
            f"The final result is taken from the diagnostic analysis."
        )

    return {
        "case_id": case_id,
        "condition": condition_name,
        "matched_terms": matched_terms,
        "summary": summary,
        "source": "backend_python_knowledge_base",
    }


def treatment_suggestions_for_confidence(
    *,
    condition: str,
    confidence: float,
    threshold: float = 0.60,
) -> dict:
    """Return treatment suggestions only when backend confidence is high enough."""

    normalized_condition = _normalize_condition_name(condition)
    confidence_value = float(confidence or 0.0)
    if confidence_value > 1.0:
        confidence_value = confidence_value / 100.0

    include_treatments = confidence_value >= threshold
    treatments = DISEASE_TREATMENTS.get(normalized_condition, []) if include_treatments else []

    return {
        "include_treatments": include_treatments,
        "threshold": threshold,
        "confidence": confidence_value,
        "condition": normalized_condition,
        "treatments": treatments,
        "source": "backend_python_knowledge_base",
    }
