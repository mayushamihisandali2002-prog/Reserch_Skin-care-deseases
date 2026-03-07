"""
Fine-tune DistilBERT for Skin Disease Classification
=====================================================
Trains DistilBERT on symptom-disease data for 5-class classification.

Usage:
    python train_distilbert.py

Output:
    Saves fine-tuned model to assets/models/distilbert/
"""

import os
import random
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# ── Disease Category Mapping ─────────────────────────────────────────────────

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
}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}

# ── Data Generation ──────────────────────────────────────────────────────────

def load_symptom_data(csv_path: str) -> dict:
    """Load disease-symptom mappings from CSV."""
    df = pd.read_csv(csv_path)
    disease_symptoms = defaultdict(list)
    
    # Inject synthetic symptoms for Pigmentation since it might not be in the CSV
    pigmentation_symptoms = ["dark spots", "brown spots", "flat spots", "pigmentation", "sunspots", "freckles", "dark patches", "discoloration", "melanin spots", "sun damage", "darkened skin", "age spots"]
    for s in pigmentation_symptoms:
        disease_symptoms[5].append(s)
        
    ringworm_symptoms = ["ring-shaped rash", "circular rash", "round patch", "clear center", "ring on skin", "fungal ring", "scaly border"]
    for s in ringworm_symptoms:
        disease_symptoms[6].append(s)
        
    rosacea_symptoms = ["facial redness", "flushing", "visible blood vessels", "red face", "hot face", "broken capillaries", "redness on cheeks"]
    for s in rosacea_symptoms:
        disease_symptoms[7].append(s)
        
    shingles_symptoms = ["painful blisters", "band of rash", "stinging pain", "fluid-filled bumps", "shooting pain", "burning rash", "nerve pain"]
    for s in shingles_symptoms:
        disease_symptoms[8].append(s)

    vitiligo_symptoms = ["white patches", "loss of pigment", "depigmentation", "milky white skin", "pale spots"]
    for s in vitiligo_symptoms:
        disease_symptoms[9].append(s)

    impetigo_symptoms = ["honey-colored crust", "yellow crust", "blisters with pus", "weeping sores", "golden crust"]
    for s in impetigo_symptoms:
        disease_symptoms[10].append(s)

    molluscum_symptoms = ["pearly bumps", "dimpled papules", "umbilicated bumps", "painless smooth spots", "skin-colored bumps"]
    for s in molluscum_symptoms:
        disease_symptoms[11].append(s)

    folliculitis_symptoms = ["inflamed hair follicles", "pustules around hair", "shaving bumps", "itchy hair bulbs", "red bumps with hair"]
    for s in folliculitis_symptoms:
        disease_symptoms[12].append(s)

    scabies_symptoms = ["intense itching at night", "burrows in skin", "itchy web spaces", "tiny grey lines", "severe nocturnal itch"]
    for s in scabies_symptoms:
        disease_symptoms[13].append(s)

    warts_symptoms = ["rough papules", "verruca", "cauliflower-like growth", "fleshy bumps", "black dots in bump"]
    for s in warts_symptoms:
        disease_symptoms[14].append(s)

    seborrheic_symptoms = ["scalp flaking", "dandruff", "greasy scale", "flaky eyebrows", "yellowish oily flakes"]
    for s in seborrheic_symptoms:
        disease_symptoms[15].append(s)

    lichen_planus_symptoms = ["purple papules", "flat-topped bumps", "wickham striae", "polygon-shaped spots", "violaceous rash"]
    for s in lichen_planus_symptoms:
        disease_symptoms[16].append(s)

    cellulitis_symptoms = ["red hot skin", "spreading redness", "swollen tender skin", "fever with skin rash", "deep skin pain"]
    for s in cellulitis_symptoms:
        disease_symptoms[17].append(s)

    herpes_simplex_symptoms = ["cold sores", "lip blisters", "tingling before blisters", "grouped vesicles on lips", "fever blisters"]
    for s in herpes_simplex_symptoms:
        disease_symptoms[18].append(s)

    pityriasis_symptoms = ["discolored patches", "fine scales", "fawn-colored spots", "tinea versicolor", "patchy skin color"]
    for s in pityriasis_symptoms:
        disease_symptoms[19].append(s)
        
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

        
    for _, row in df.iterrows():
        disease = row['disease_name']
        symptom = row['symptom_name']
        if disease in DISEASE_MAPPING:
            label = DISEASE_MAPPING[disease]
            disease_symptoms[label].append(symptom)
    return disease_symptoms


def generate_training_sentences(disease_symptoms: dict, samples_per_class: int = 1000) -> tuple:
    """Generate diverse training sentences from symptom combinations and synonyms."""
    texts = []
    labels = []
    
    # Synonym expansions for common symptoms
    synonyms = {
        "itching": ["itchy", "pruritus", "scratchy", "burning itch", "irritating itch"],
        "dry skin": ["dryness", "xerosis", "flaky skin", "cracked skin", "parched skin"],
        "red patches": ["redness", "erythema", "inflamed spots", "red rash", "irritated patches"],
        "pimples": ["breakouts", "pustules", "zits", "bumps", "papules", "spots"],
        "oily skin": ["greasy skin", "sebum", "shiny skin", "excess oil", "slick skin"],
        "silvery scale": ["silver scales", "white plaques", "scaly buildup", "silvery buildup"],
        "scaling": ["flaking", "peeling", "shedding skin", "dandruff-like flakes", "crusty"],
        "raised wheals": ["hives", "welts", "swollen bumps", "urticarial wheals", "itchy bumps"],
        "burning": ["stinging", "tingling", "hot sensation", "fiery", "irritated"],
        "dark spots": ["brown spots", "flat brown spots", "dark patches", "sunspots", "freckles", "hyperpigmentation"],
        "ring-shaped rash": ["circular rash", "round patch", "clear center", "ring spot", "scaly ring"],
        "facial redness": ["flushing", "red nose", "red cheeks", "blushing", "rosy face"],
        "painful blisters": ["stinging bumps", "burning rash", "painful spots", "nerve rash", "strip of blisters", "fiery bumps", "stabbing pain"],
        "white patches": ["loss of pigment", "depigmented spots", "milky patches", "pale skin areas", "colorless skin", "vitiligo spots"],
        "honey-colored crust": ["golden yellow crusts", "weeping honey sores", "yellowish scabs", "blisters with honey crust", "sticky yellow fluid"],
        "pearly bumps": ["dimpled bumps", "small dome-shaped marks", "painless smooth bumps", "molluscum spots", "shiny pearly spots"],
        "scalp flaking": ["severe dandruff", "flaky scalp", "yellowish greasy flakes", "seborrheic scaling", "oily dandruff"],
        "red hot skin": ["spreading red area", "tender hot skin", "swollen painful rash", "feverish skin", "inflamed swelling"],
        "cold sores": ["lip blisters", "tingling lips", "herpes blisters", "fever blisters", "grouped lip vesicles"],
        "burrows in skin": ["tiny grey lines", "skin tunnels", "mite tracks", "itchy burrows", "winding lines"],
        "rough papules": ["warty growth", "cauliflower bump", "hard fleshy growth", "verruca", "grainy bump"],
    }
    
    templates = [
        "I have {symptoms}", "My skin has {symptoms}", "I'm experiencing {symptoms}",
        "I noticed {symptoms} on my skin", "Symptoms include {symptoms}", "{symptoms}",
        "Suffering from {symptoms}", "I developed {symptoms}", "My condition shows {symptoms}",
        "I'm dealing with {symptoms}", "There are {symptoms} on my body",
        "It feels like {symptoms}", "Dealing with severe {symptoms}",
        "Chronic {symptoms} for a few days", "Suddenly noticed {symptoms}",
        "Help! I have {symptoms}", "Condition update: {symptoms}",
        "How do I treat {symptoms}?", "My skin is reacting with {symptoms}",
        "The area is showing {symptoms}", "Persistent {symptoms}",
    ]
    
    for label_id, symptoms in disease_symptoms.items():
        unique_symptoms = list(set(symptoms))
        
        # Base class name as a symptom
        class_name = ID2LABEL[label_id].lower()
        
        for i in range(samples_per_class):
            # Pick 1-4 random symptoms
            n_symptoms = random.randint(1, min(4, len(unique_symptoms)))
            selected = random.sample(unique_symptoms, n_symptoms)
            
            # Augment with synonyms
            augmented = []
            for s in selected:
                if s in synonyms and random.random() > 0.4:
                    augmented.append(random.choice(synonyms[s]))
                else:
                    augmented.append(s)
            
            # Randomly add class name to some sentences
            if i < samples_per_class // 5 and random.random() > 0.5:
                augmented.append(class_name)
                
            random.shuffle(augmented)
            
            # Create sentence
            if not augmented:
                continue
                
            if len(augmented) == 1:
                symptom_text = augmented[0]
            elif len(augmented) == 2:
                symptom_text = f"{augmented[0]} and {augmented[1]}"
            else:
                symptom_text = ", ".join(augmented[:-1]) + f", and {augmented[-1]}"
            
            template = random.choice(templates)
            sentence = template.format(symptoms=symptom_text)
            
            # Random lowercase/casing
            if random.random() > 0.8:
                sentence = sentence.lower()
            
            texts.append(sentence)
            labels.append(label_id)
    
    return texts, labels


def add_synthetic_data(texts: list, labels: list) -> tuple:
    """Add high-quality synthetic data for edge cases."""
    
    synthetic_data = [
        # Eczema (0)
        ("I have very dry and itchy skin on my arms and legs", 0),
        ("Red patches that are extremely itchy and dry", 0),
        ("Itching gets worse at night, my skin is cracked and dry", 0),
        ("Dry flaky skin with intense itching", 0),
        ("My hands are dry, cracked and very itchy", 0),
        ("Itchy red rash that comes and goes", 0),
        ("Severe pruritus and xerosis, cracks in skin", 0),
        
        # Dermatitis (1)
        ("Skin reacted to new soap, red and burning", 1),
        ("Rash appeared after touching plants", 1),
        ("Irritation where my watch strap was", 1),
        ("Burning and redness where I applied the cream", 1),
        ("Scalp is flaking with yellow greasy scales", 1),
        ("Contact irritation from metal jewelry", 1),
        
        # Psoriasis (2)
        ("Thick silvery scales on my elbows and knees", 2),
        ("Raised red patches covered with white scales", 2),
        ("Plaque-like lesions that are scaly and thick", 2),
        ("Silvery white scaling on my scalp", 2),
        ("Scale buildup that cracks and bleeds easily", 2),
        
        # Acne (3)
        ("Pimples and blackheads all over my face", 3),
        ("Oily skin with lots of breakouts", 3),
        ("Acne on my chin and forehead with whiteheads", 3),
        ("Painful cystic bumps on my cheeks", 3),
        ("My face is constantly shiny and breaking out", 3),
        
        # Urticaria (4)
        ("Sudden welts appeared all over my body", 4),
        ("Itchy hives after eating shellfish", 4),
        ("Raised red bumps that appeared quickly and itch immensely", 4),
        ("Allergic hives spreading across my skin", 4),
        ("Angioedema swelling and itchy wheals", 4),
        
        # Pigmentation / Dark Spots (5)
        ("Small brown spots on my nose and cheeks", 5),
        ("Flat non painful darkened spots from sun exposure", 5),
        ("I noticed many small brown spots appearing on my face", 5),
        ("Dark hyperpigmentation after my severe acne healed", 5),
        ("Sunspots and freckles on my shoulders and face", 5),
        ("My skin has flat brown patches that get darker in the sun", 5),
        ("Age spots and melasma on my forehead", 5),
        ("Not painful flat brown marks appearing", 5),

        # Ringworm (6)
        ("I have a circular red rash with a clear center on my arm", 6),
        ("Itchy ring-shaped patch on my leg that's scaly at the edges", 6),
        ("A round scaly spot that looks like a ring", 6),
        ("Fungal infection on my body in a perfect circle", 6),

        # Rosacea (7)
        ("My face is always red and i flush easily when drinking coffee", 7),
        ("Persistent redness on my cheeks and nose with visible vessels", 7),
        ("Burning and flushing of the face, looks like a blush", 7),
        ("Facial redness that doesn't go away", 7),

        # Shingles (8)
        ("Painful strip of blisters on one side of my waist", 8),
        ("Intense burning pain followed by a band of red bumps", 8),
        ("Stabbing pain and clusters of fluid-filled blisters", 8),
        ("A painful rash that wraps around my torso", 8),

        # Vitiligo (9)
        ("I have milky white patches appearing on my hands and face", 9),
        ("Loss of pigment making my skin look patchy with white spots", 9),

        # Impetigo (10)
        ("Honey-colored crust on sores around my nose and mouth", 10),
        ("Golden yellow scabs that look like they are weeping", 10),

        # Molluscum (11)
        ("Small pearly bumps with a little dimple in the middle", 11),
        ("Cluster of painless skin-colored dome-shaped bumps", 11),

        # Folliculitis (12)
        ("Inflamed hair follicles after shaving my legs", 12),
        ("Red itchy bumps localized around my hair follicles", 12),

        # Scabies (13)
        ("Intense itching that's much worse at night between my fingers", 13),
        ("Tiny burrow lines on my wrists and extreme nocturnal itch", 13),

        # Warts (14)
        ("Rough fleshy bumps on my fingers that look like cauliflower", 14),
        ("Hard grainy growths with tiny black dots on my feet", 14),

        # Seborrheic Dermatitis (15)
        ("Greasy yellow scale and dandruff on my scalp and eyebrows", 15),
        ("Flaky itchy patches behind my ears and on my forehead", 15),

        # Lichen Planus (16)
        ("Flat-topped purple bumps that itch extremely on my wrists", 16),
        ("Violaceous polygon-shaped spots appearing on my forearms", 16),

        # Cellulitis (17)
        ("A red area of skin that feels hot, swollen, and very tender", 17),
        ("Spreading redness and swelling along with a light fever", 17),

        # Herpes Simplex (18)
        ("Tingling sensation followed by grouped blisters on my lip", 18),
        ("Cold sores forming near the edge of my mouth", 18),

        # Pityriasis Versicolor (19)
        ("Patchy skin discoloration with fine scales on my chest", 19),
        ("Light-colored spots that don't tan in the sun on my back", 19),
    ]
    
    for text, label in synthetic_data:
        texts.append(text)
        labels.append(label)
    
    # Add negative/non-medical samples (filtered by intent anyway)
    # but good to have some robustness
    negative_samples = [
        "hello how are you", "what is the time", "i love skin care",
        "who are you", "tell me a joke", "i like pizza"
    ]
    # We map these to None or just skip, but if we want a robust 
    # classifier we should have a 6th class. However, we'll rely on the 
    # intent classifier to filter these out before they reach here.
    
    return texts, labels


# ── Training ─────────────────────────────────────────────────────────────────

def train_model(texts: list, labels: list, output_dir: str, epochs: int = 5):
    """Fine-tune DistilBERT on the training data."""
    
    import torch
    from transformers import (
        DistilBertTokenizerFast,
        DistilBertForSequenceClassification,
        TrainingArguments,
        Trainer,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import precision_recall_fscore_support, accuracy_score
    from datasets import Dataset
    
    print(f"\n[Training] Using Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.15, random_state=42, stratify=labels
    )
    
    print(f"[Training] Train samples: {len(train_texts)} | Val samples: {len(val_texts)}")
    
    # Create datasets
    train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels})
    val_dataset = Dataset.from_dict({"text": val_texts, "label": val_labels})
    
    # Load tokenizer and model
    print("[Training] Loading DistilBERT base checkpoint...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=30,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    
    # Enable mixed precision if on CUDA
    use_fp16 = torch.cuda.is_available()
    
    # Tokenize
    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)
    
    print("[Training] Tokenizing data...")
    train_dataset = train_dataset.map(tokenize_fn, batched=True)
    val_dataset = val_dataset.map(tokenize_fn, batched=True)
    
    # Metrics
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=1)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average="weighted"
        )
        acc = accuracy_score(labels, predictions)
        return {
            "accuracy": acc,
            "f1": f1,
            "precision": precision,
            "recall": recall
        }
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./training_output",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=3e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir="./logs",
        logging_steps=50,
        fp16=use_fp16,
        report_to="none",
    )
    
    # Train
    print(f"[Training] Starting fine-tuning for {epochs} epochs...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )
    
    trainer.train()
    
    # Evaluate
    print("\n[Training] Final evaluation on validation set...")
    results = trainer.evaluate()
    print(f"   Accuracy  : {results['eval_accuracy']:.2%}")
    print(f"   F1 Score  : {results['eval_f1']:.2%}")
    print(f"   Precision : {results['eval_precision']:.2%}")
    print(f"   Recall    : {results['eval_recall']:.2%}")
    
    # Save
    print(f"\n[Training] Saving perfect model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    return results['eval_f1']
    
    # Cleanup
    import shutil
    if os.path.exists("./training_output"):
        shutil.rmtree("./training_output")
    if os.path.exists("./logs"):
        shutil.rmtree("./logs")
    
    return results['eval_accuracy']


def test_model(model_dir: str):
    """Test the trained model."""
    
    import torch
    import torch.nn.functional as F
    from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
    
    print("\n" + "=" * 60)
    print("TESTING TRAINED MODEL")
    print("=" * 60)
    
    tokenizer = DistilBertTokenizerFast.from_pretrained(model_dir)
    model = DistilBertForSequenceClassification.from_pretrained(model_dir)
    model.eval()
    
    test_cases = [
        ("I have dry itchy patches on my arms", "Eczema"),
        ("My skin reacted to a new soap with redness", "Dermatitis"),
        ("Thick silvery scales on my elbows", "Psoriasis"),
        ("Pimples and oily skin on my face", "Acne"),
        ("Sudden hives appeared after eating", "Urticaria"),
        ("Red itchy inflamed skin that's very dry", "Eczema"),
        ("Flaky dandruff on my scalp", "Dermatitis"),
        ("Raised red plaques with white scales", "Psoriasis"),
        ("Blackheads and whiteheads breakout", "Acne"),
        ("Itchy welts all over my body", "Urticaria"),
    ]
    
    correct = 0
    for text, expected in test_cases:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits, dim=-1)[0].numpy()
        
        pred_id = int(np.argmax(probs))
        pred_label = ID2LABEL[pred_id]
        confidence = probs[pred_id]
        
        is_correct = pred_label == expected
        correct += int(is_correct)
        symbol = "✅" if is_correct else "❌"
        
        print(f"{symbol} '{text[:45]}...'")
        print(f"   Predicted: {pred_label} ({confidence:.1%}) | Expected: {expected}")
    
    print(f"\nTest accuracy: {correct}/{len(test_cases)} ({correct/len(test_cases):.0%})")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("DISTILBERT FINE-TUNING FOR SKIN DISEASE CLASSIFICATION")
    print("=" * 60)
    
    # Paths
    data_path = "assets/data/disease_symptom_edges_expanded.csv"
    output_dir = "assets/models/distilbert"
    
    # Load data
    print("\n[Data] Loading symptom data...")
    disease_symptoms = load_symptom_data(data_path)
    
    for label_id, symptoms in disease_symptoms.items():
        print(f"   {ID2LABEL[label_id]}: {len(set(symptoms))} unique symptoms")
    
    # Generate training data
    print("\n[Data] Generating training sentences...")
    texts, labels = generate_training_sentences(disease_symptoms, samples_per_class=150)
    
    # Add synthetic data
    texts, labels = add_synthetic_data(texts, labels)
    
    # Shuffle
    combined = list(zip(texts, labels))
    random.shuffle(combined)
    texts, labels = zip(*combined)
    texts, labels = list(texts), list(labels)
    
    print(f"[Data] Total training samples: {len(texts)}")
    
    # Class distribution
    from collections import Counter
    dist = Counter(labels)
    print("[Data] Class distribution:")
    for label_id in sorted(dist.keys()):
        print(f"   {ID2LABEL[label_id]}: {dist[label_id]} samples")
    
    # Train
    # Set epochs higher for a better "perfect" model, 3 is sufficient for fine-tuning.
    f1_score = train_model(texts, labels, output_dir, epochs=2)
    
    # Test
    test_model(output_dir)
    
    print("\n" + "=" * 60)
    print(f"✅ TRAINING COMPLETE - Model saved to {output_dir}")
    print(f"   Validation F1 Score: {f1_score:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    main()
