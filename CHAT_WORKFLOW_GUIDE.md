# 🩺 AI Skin Care Chat Workflow Guide

## Overview

This document explains how the chat component works end-to-end using your two trained models:
- **`image_best_finetuned.pt`** - ResNet-18 image classifier
- **`best_model/best_model/`** - DistilBERT text classifier

---

## 📁 Model Functions Summary

### 1️⃣ DistilBERT Text Model (`best_model/best_model/`)

| **Property** | **Value** |
|-------------|-----------|
| **Architecture** | DistilBertForSequenceClassification |
| **Input** | User symptom text (e.g., "I have red itchy patches on my arms") |
| **Output** | 5-class probability vector + confidence score |
| **Classes** | Eczema, Dermatitis, Psoriasis, Acne, Urticaria |
| **Role** | Text-based symptom analysis |
| **Used by** | `/api/chat` endpoint |

**How it works:**
```python
# User message → tokenize → model → softmax → disease prediction
text = "I have itchy red patches"
disease, confidence, probs = distilbert_model.predict(text)
# Returns: ("Dermatitis", 0.45, [0.1, 0.45, 0.2, 0.15, 0.1])
```

---

### 2️⃣ ResNet-18 Image Model (`image_best_finetuned.pt`)

| **Property** | **Value** |
|-------------|-----------|
| **Architecture** | ResNet-18 (modified final fc layer) |
| **Input** | Skin image (224×224 RGB, normalized) |
| **Output** | 5-class probability vector + confidence score |
| **Classes** | Eczema, Dermatitis, Psoriasis, Acne, Urticaria |
| **Role** | Visual pattern recognition |
| **Used by** | `/api/analyze` and `/api/analyze-fused` endpoints |

**How it works:**
```python
# Image → preprocess → model → softmax → disease prediction
image_bytes = read_image_file("skin.jpg")
disease, confidence, probs = image_model.predict_from_bytes(image_bytes)
# Returns: ("Eczema", 0.85, [0.85, 0.05, 0.03, 0.04, 0.03])
```

---

### 3️⃣ Fusion Logic (No file - just code)

When both image and text are provided:

```
P_final = α × P_image + (1-α) × P_text
```

Where `α = 0.60` (image model gets 60% weight since visual evidence is stronger)

**Example:**
```python
image_probs = [0.85, 0.05, 0.03, 0.04, 0.03]  # Image: Eczema
text_probs  = [0.10, 0.12, 0.55, 0.08, 0.15]  # Text: Psoriasis

fused_probs = 0.6 * image_probs + 0.4 * text_probs
# = [0.55, 0.078, 0.238, 0.072, 0.078]
# Final prediction: Eczema (weighted towards image)
```

---

## 🔄 Complete Chat Workflow

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  User types: "I have red itchy skin for 2 weeks"                │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flutter sends to backend:                                       │
│  POST /api/chat                                                  │
│  {                                                               │
│    "session_id": "abc-123",                                      │
│    "message": "I have red itchy skin for 2 weeks"               │
│  }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: Intent Classification                                  │
│  ─────────────────────────                                       │
│  Checks if message is:                                           │
│  • symptom_description → run AI prediction                       │
│  • ask_treatment → use session memory                            │
│  • ask_about_disease → provide info                              │
│  • other → greeting/off-topic                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: Vague Message Check                                    │
│  ────────────────────────────                                    │
│  Checks for:                                                     │
│  ✓ Location (face, arm, leg...)                                 │
│  ✓ Appearance (red, scaly, bumpy...)                            │
│  ✓ Sensation (itchy, painful...)                                │
│  ✓ Duration (days, weeks...)                                    │
│                                                                  │
│  If too vague → ask follow-up questions                          │
│  If sufficient → proceed to AI prediction                        │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: DistilBERT Prediction                                  │
│  ──────────────────────────────                                  │
│  text → tokenize → model → softmax                               │
│  → disease + confidence                                          │
│                                                                  │
│  Confidence tiers:                                               │
│  • ≥70% → high (definitive answer)                              │
│  • 45-70% → medium (likely match)                               │
│  • <45% → low (need more info)                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend: Session Memory Update                                  │
│  ─────────────────────────────                                   │
│  Stores:                                                         │
│  • last_predicted_disease = "Dermatitis"                        │
│  • last_confidence = 0.65                                        │
│  • conversation_history = [...]                                  │
│                                                                  │
│  So follow-up "What is the treatment?" works                     │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend Returns JSON:                                           │
│  {                                                               │
│    "reply": "Based on your symptoms...",                        │
│    "predicted_disease": "Dermatitis",                           │
│    "confidence": 0.65,                                          │
│    "confidence_level": "medium",                                │
│    "needs_more_info": true,                                     │
│    "follow_up_questions": ["Where is it located?", ...],        │
│    "recommended_treatments": [                                   │
│      {"medicine": "emollient", "advice": "Apply 2x daily"}      │
│    ]                                                             │
│  }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Flutter Renders:                                                │
│  ─────────────────                                               │
│  ✓ Assistant text reply                                          │
│  ✓ Disease badge with confidence bar                             │
│  ✓ Expandable treatment panel                                    │
│  ✓ Follow-up question chips (tap to set input hint)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💬 Chat Intent Handling

### Intent: `symptom_description`
User provides symptoms → Run DistilBERT prediction

**Example:**
- Input: "I have itchy red patches on my face"
- Action: Predict disease, return treatments

### Intent: `ask_treatment`
User asks about treatment → Use session memory

**Example:**
- Input: "What is the treatment?"
- Action: Return treatments for last predicted disease (no re-prediction)

### Intent: `clarify_existing`
User provides more detail after prediction → Keep same diagnosis

**Example:**
- Previous: "Dermatitis" predicted
- Input: "It's also on my elbows"
- Action: Acknowledge, keep same diagnosis

### Intent: `ask_about_disease`
User asks general question about a disease

**Example:**
- Input: "What is eczema?"
- Action: Ask for their symptoms to personalize response

---

## 🔧 API Endpoints

| Endpoint | Method | Purpose | Model Used |
|----------|--------|---------|------------|
| `/api/chat` | POST | Conversational diagnosis | DistilBERT |
| `/api/analyze` | POST | Image-only diagnosis | ResNet-18 |
| `/api/analyze-fused` | POST | Image + text fusion | Both models |
| `/api/status` | GET | Check model availability | None |
| `/api/health` | GET | Server health check | None |

---

## ✅ Follow-Up Chip Behavior (Important!)

The follow-up chips are **correctly implemented**:

❌ **Wrong approach:** Chip sends the question as a message
✅ **Correct approach:** Chip sets input placeholder → user answers → answer is sent

**Example flow:**
1. User sees chip: "Where is it located?"
2. User taps chip → input hint changes to "Where is it located?"
3. User types: "On my face and neck"
4. That answer is sent to backend

---

## 🚀 Running the System

### Start Backend
```bash
cd backend
python app.py
```
Backend runs at: `http://127.0.0.1:5000`

### Run Flutter App
```bash
cd app
flutter run -d chrome  # or -d windows, -d android
```

---

## 📊 Disease Classes (5 total)

| ID | Disease | Common Symptoms |
|----|---------|-----------------|
| 0 | Eczema | Dry, itchy, inflamed patches |
| 1 | Dermatitis | Red, irritated, contact-triggered |
| 2 | Psoriasis | Scaly, thick, silvery patches |
| 3 | Acne | Pimples, blackheads, oily skin |
| 4 | Urticaria | Hives, swelling, allergic reaction |

---

## 🧠 Session Memory

Each session stores:
- `session_id` - Unique identifier
- `last_predicted_disease` - Most recent prediction
- `last_confidence` - Confidence of last prediction
- `conversation_history` - All messages in session
- `created_at` - Timestamp (sessions expire after 30 min)

This enables natural follow-up conversations without re-predicting.
