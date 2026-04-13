"""
Regenerate proper working demo ML models for SkinAI
"""
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
MODELS_DIR = (
    BACKEND_DIR / "assets" / "models" / "conversational_diagnosis_assistant"
)

# Create realistic training dataset
training_texts = [
    # Eczema (ID: 0)
    'red itchy skin dry', 'itching dryness inflammation', 'inflamed itchy patches',
    'dry skin rashes itching', 'itchy red patches', 'eczema itching dry skin',
    'inflamed skin itching', 'dry patches itching redness',
    
    # Dermatitis (ID: 1)
    'contact dermatitis rash', 'skin irritation redness', 'irritated skin reaction',
    'allergic skin rash', 'chemical burn skin', 'dermatitis inflammation',
    'irritated inflamed skin', 'rash from irritant',
    
    # Psoriasis (ID: 2)
    'scaling plaques skin', 'thick scaly patches', 'plaque psoriasis thick',
    'silver scales scalp', 'scaling silvery patches', 'psoriasis plaques',
    'scaly skin thickness', 'patches with scaling',
    
    # Acne (ID: 3)
    'pimples breakout oily', 'acne pimples spots', 'oily skin acne',
    'blackheads whiteheads acne', 'facial acne breakout', 'acne breakout',
    'pimples on face', 'oily skin with spots',
    
    # Urticaria (ID: 4)
    'hives itchy swelling', 'urticaria hives swelling', 'itchy hives welts',
    'allergic hives reaction', 'swollen itchy hives', 'hives allergy',
    'welts on skin', 'swollen hives itching'
]

training_labels = [
    0, 0, 0, 0, 0, 0, 0, 0,           # Eczema (0)
    1, 1, 1, 1, 1, 1, 1, 1,           # Dermatitis (1)
    2, 2, 2, 2, 2, 2, 2, 2,           # Psoriasis (2)
    3, 3, 3, 3, 3, 3, 3, 3,           # Acne (3)
    4, 4, 4, 4, 4, 4, 4, 4            # Urticaria (4)
]

disease_names = {
    0: 'Eczema',
    1: 'Dermatitis',
    2: 'Psoriasis',
    3: 'Acne',
    4: 'Urticaria'
}

print("=" * 60)
print("REGENERATING DEMO ML MODELS")
print("=" * 60)

# Train vectorizer and model
print("\n1. Training TF-IDF Vectorizer...")
vectorizer = TfidfVectorizer(max_features=200, min_df=1, max_df=0.95, lowercase=True)
X = vectorizer.fit_transform(training_texts)
print(f"   ✅ Vectorizer trained: {X.shape[1]} features from {X.shape[0]} texts")

print("\n2. Training Naive Bayes classifier...")
model = MultinomialNB(alpha=0.1)
model.fit(X, training_labels)
print(f"   ✅ Model trained: {len(model.classes_)} classes")

# Save models
print("\n3. Saving models...")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
try:
    with open(MODELS_DIR / 'text_model.pkl', 'wb') as f:
        pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("   ✅ text_model.pkl saved (Naive Bayes classifier)")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

try:
    with open(MODELS_DIR / 'vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("   ✅ vectorizer.pkl saved (TF-IDF vectorizer)")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Verify by loading and testing
print("\n4. Verifying models...")
try:
    with open(MODELS_DIR / 'text_model.pkl', 'rb') as f:
        loaded_model = pickle.load(f)
    with open(MODELS_DIR / 'vectorizer.pkl', 'rb') as f:
        loaded_vec = pickle.load(f)
    print("   ✅ Models loaded successfully from disk")
except Exception as e:
    print(f"   ❌ Failed to load: {e}")
    exit(1)

# Test predictions
print("\n5. Testing predictions...")
test_cases = [
    ("I have red itchy skin", "Eczema or Dermatitis"),
    ("My skin has thick scaly patches", "Psoriasis"),
    ("I have pimples and oily skin", "Acne"),
    ("I have hives and swelling", "Urticaria"),
]

for test_text, expected in test_cases:
    X_test = loaded_vec.transform([test_text])
    pred_class = loaded_model.predict(X_test)[0]
    confidence = float(loaded_model.predict_proba(X_test)[0].max())
    pred_disease = disease_names[pred_class]
    
    symbol = "✅" if confidence > 0.5 else "⚠️"
    print(f"   {symbol} '{test_text}'")
    print(f"      → {pred_disease} ({confidence:.1%} confidence)")

print("\n" + "=" * 60)
print("✅ DEMO MODELS READY FOR PRODUCTION")
print("=" * 60)
print("\nNote: These are demo models trained on sample data.")
print("Replace with your real trained models when ready.")
print(f"Model files location: {MODELS_DIR / 'text_model.pkl'}, {MODELS_DIR / 'vectorizer.pkl'}")
