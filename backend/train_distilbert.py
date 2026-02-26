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
# Map detailed diseases to 5 main categories

DISEASE_MAPPING = {
    # Eczema (0)
    "Atopic dermatitis (Eczema)": 0,
    "Dyshidrotic eczema": 0,
    "Nummular eczema": 0,
    
    # Dermatitis (1)
    "Contact dermatitis (Irritant)": 1,
    "Contact dermatitis (Allergic)": 1,
    "Seborrheic dermatitis": 1,
    "Perioral dermatitis": 1,
    "Photodermatitis": 1,
    
    # Psoriasis (2)
    "Psoriasis vulgaris": 2,
    "Lichen planus": 2,  # Similar presentation
    
    # Acne (3)
    "Acne vulgaris": 3,
    "Acne rosacea": 3,
    "Rosacea": 3,
    "Folliculitis": 3,
    
    # Urticaria (4)
    "Urticaria (Hives)": 4,
    "Chronic urticaria": 4,
}

ID2LABEL = {0: "Eczema", 1: "Dermatitis", 2: "Psoriasis", 3: "Acne", 4: "Urticaria"}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}

# ── Data Generation ──────────────────────────────────────────────────────────

def load_symptom_data(csv_path: str) -> dict:
    """Load disease-symptom mappings from CSV."""
    df = pd.read_csv(csv_path)
    disease_symptoms = defaultdict(list)
    for _, row in df.iterrows():
        disease = row['disease_name']
        symptom = row['symptom_name']
        if disease in DISEASE_MAPPING:
            label = DISEASE_MAPPING[disease]
            disease_symptoms[label].append(symptom)
    return disease_symptoms


def generate_training_sentences(disease_symptoms: dict, samples_per_class: int = 200) -> tuple:
    """Generate training sentences from symptom combinations."""
    texts = []
    labels = []
    
    templates = [
        "I have {symptoms}",
        "My skin has {symptoms}",
        "I'm experiencing {symptoms}",
        "I noticed {symptoms} on my skin",
        "Symptoms include {symptoms}",
        "{symptoms}",
        "Suffering from {symptoms}",
        "I developed {symptoms}",
        "My condition shows {symptoms}",
        "I'm dealing with {symptoms}",
    ]
    
    for label_id, symptoms in disease_symptoms.items():
        unique_symptoms = list(set(symptoms))
        for _ in range(samples_per_class):
            # Pick 2-4 random symptoms
            n_symptoms = random.randint(2, min(4, len(unique_symptoms)))
            selected = random.sample(unique_symptoms, n_symptoms)
            
            # Create sentence
            if len(selected) == 1:
                symptom_text = selected[0]
            elif len(selected) == 2:
                symptom_text = f"{selected[0]} and {selected[1]}"
            else:
                symptom_text = ", ".join(selected[:-1]) + f", and {selected[-1]}"
            
            template = random.choice(templates)
            sentence = template.format(symptoms=symptom_text)
            
            texts.append(sentence)
            labels.append(label_id)
    
    return texts, labels


def add_synthetic_data(texts: list, labels: list) -> tuple:
    """Add additional synthetic training data."""
    
    synthetic_data = [
        # Eczema (0)
        ("I have very dry and itchy skin on my arms and legs", 0),
        ("Red patches that are extremely itchy and dry", 0),
        ("Itching gets worse at night, my skin is cracked and dry", 0),
        ("Dry flaky skin with intense itching", 0),
        ("My hands are dry, cracked and very itchy", 0),
        ("Itchy red rash that comes and goes, worse in winter", 0),
        ("Eczema flare up with dry patches on elbows", 0),
        ("Severe itching with dry scaly patches", 0),
        ("Inflamed itchy dry skin on my body", 0),
        ("Red irritated patches that itch constantly", 0),
        
        # Dermatitis (1)
        ("My skin reacted badly to a new soap, red and burning", 1),
        ("Rash appeared after touching plants in garden", 1),
        ("Irritation and redness where my watch strap was", 1),
        ("Allergic reaction on skin with blisters forming", 1),
        ("Chemical burn from cleaning products on my hands", 1),
        ("Contact rash from metal jewelry", 1),
        ("My scalp is flaky with greasy yellow scales", 1),
        ("Dandruff and itchy scalp with redness", 1),
        ("Skin irritation from cosmetics", 1),
        ("Burning sensation and redness after sun exposure", 1),
        
        # Psoriasis (2)
        ("Thick silvery scales on my elbows and knees", 2),
        ("Raised red patches covered with white scales", 2),
        ("Plaque-like lesions that are scaly and thick", 2),
        ("Silvery white scaling on my scalp", 2),
        ("Thick patches of skin with silver scales", 2),
        ("Psoriasis plaques on elbows getting worse", 2),
        ("Nail pitting and thick scaly skin", 2),
        ("Scaly patches that crack and sometimes bleed", 2),
        ("Red raised areas with silvery buildup", 2),
        ("Chronic scaling skin condition on my knees", 2),
        
        # Acne (3)
        ("Pimples and blackheads all over my face", 3),
        ("Oily skin with lots of breakouts", 3),
        ("Acne on my chin and forehead with whiteheads", 3),
        ("Deep painful cystic acne on my cheeks", 3),
        ("Constant breakouts with oily skin", 3),
        ("Blocked pores and pimples", 3),
        ("Red bumps and pustules on my face", 3),
        ("Teenage acne that won't go away", 3),
        ("Inflamed hair follicles on my back", 3),
        ("Facial acne with sebum and blackheads", 3),
        
        # Urticaria (4)
        ("Sudden welts appeared all over my body", 4),
        ("Itchy hives after eating shellfish", 4),
        ("Raised red bumps that appeared quickly and itch", 4),
        ("Allergic hives spreading across my skin", 4),
        ("Swollen itchy welts on my arms", 4),
        ("Hives outbreak with intense itching", 4),
        ("Wheals appearing and disappearing randomly", 4),
        ("Angioedema with swollen lips and hives", 4),
        ("Chronic hives that come daily", 4),
        ("Itchy raised welts all over after allergic reaction", 4),
    ]
    
    for text, label in synthetic_data:
        texts.append(text)
        labels.append(label)
    
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
    from datasets import Dataset
    
    print(f"\n[Training] Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
    
    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.15, random_state=42, stratify=labels
    )
    
    print(f"[Training] Train samples: {len(train_texts)}")
    print(f"[Training] Val samples: {len(val_texts)}")
    
    # Create datasets
    train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels})
    val_dataset = Dataset.from_dict({"text": val_texts, "label": val_labels})
    
    # Load tokenizer and model
    print("[Training] Loading DistilBERT base model...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased",
        num_labels=5,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    
    # Tokenize
    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=128)
    
    print("[Training] Tokenizing data...")
    train_dataset = train_dataset.map(tokenize_fn, batched=True)
    val_dataset = val_dataset.map(tokenize_fn, batched=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./training_output",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=epochs,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        logging_dir="./logs",
        logging_steps=50,
        report_to="none",  # Disable wandb
    )
    
    # Metrics
    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        accuracy = (predictions == labels).mean()
        return {"accuracy": accuracy}
    
    # Train
    print(f"[Training] Starting training for {epochs} epochs...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )
    
    trainer.train()
    
    # Evaluate
    print("\n[Training] Final evaluation...")
    results = trainer.evaluate()
    print(f"[Training] Validation accuracy: {results['eval_accuracy']:.2%}")
    
    # Save
    print(f"\n[Training] Saving model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
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
    accuracy = train_model(texts, labels, output_dir, epochs=5)
    
    # Test
    test_model(output_dir)
    
    print("\n" + "=" * 60)
    print(f"✅ TRAINING COMPLETE - Model saved to {output_dir}")
    print(f"   Validation accuracy: {accuracy:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    main()
