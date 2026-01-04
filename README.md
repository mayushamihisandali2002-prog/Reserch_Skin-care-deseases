# Reserch_Skin-care-deseases
 Personalized Treatment Support & Monitoring System

**Student Name:** Mihisandali W.K.M  
**Registration No:** IT22246400  

## 1. Project Overview
This project focuses on providing **personalized treatment support and monitoring** for skin-related conditions.
Unlike traditional systems that stop at diagnosis, this system continues to support users through safe self-care recommendations and scheduled follow-up monitoring.

The system uses **rule-augmented NLP**, **machine learning**, and a **knowledge graph** to deliver explainable, safe, and personalized skin care guidance.

## 2. Problem Statement
Many skin-care AI solutions provide only one-time diagnosis or advice.
There is a lack of:
- Follow-up monitoring
- Treatment adherence support
- Safety escalation mechanisms

This project addresses these gaps by introducing a **notification-based monitoring system (Day 1 / Day 3 / Day 7)**.

---

## 3. Key Features
- Text-based skin symptom analysis
- Safe OTC and self-care recommendations
- Notification-based follow-ups (Day 1 / 3 / 7)
- Red-flag detection using rule-augmented NLP
- Explainable recommendations using a Knowledge Graph
- Personalized treatment pathways
- Multilingual support (Sinhala / English – planned)
- Lifetime patient record storage (planned)

- ## 4. System Architecture
### High-Level Architecture

User Input (Text/Image)
→ Preprocessing
→ TF-IDF Feature Extraction
→ Disease Classification (ML Models)
→ Red-Flag Detection (Rules)
→ Knowledge Graph Explanation
→ Treatment Recommendation
→ Follow-up Monitoring (Day 1 / 3 / 7)

---

## 5. Technologies Used

### Programming & Environment
- Python
- Google Colab
- Git & GitHub

### Data Processing
- Pandas
- NumPy
### NLP & Machine Learning
- TF-IDF Vectorizer
- Logistic Regression
- SGDClassifier (log_loss)
- Calibrated Linear SVM

### Explainability
- NetworkX (Knowledge Graph)

### Model Evaluation
- Accuracy
- Precision / Recall / F1-score
- Confusion Matrix
- Macro-F1

---

## 6. Model Comparison
Three models were trained and compared using the same TF-IDF features:

| Model | Strengths | Limitations |
|-----|----------|------------|
| Logistic Regression | Simple, interpretable | Lower confidence |
| SGDClassifier | Fast, scalable | Poor calibration |
| Calibrated Linear SVM | Best accuracy & confidence | Slightly slower |

**Selected Model:** Calibrated Linear SVM  
**Reason:** Best macro-F1 score and reliable confidence estimation.

---

## 7. Project Structure
data/
├── raw/
├── processed/
└── synthetic/

models/notebooks/
README.md

## 8. Version Control
This repository maintains:
- Full commit history
- Feature branches
- Merges between development stages

This reflects real-world industry version control practices.

---

## 9. Ethical Considerations
- Uses synthetic data to protect privacy
- Provides decision support, not diagnosis
- Advises professional consultation when red flags are detected

---

## 10. Future Enhancements
- Image-based skin analysis
- Transformer-based NLP models (SBERT, BERT)
- Cloud deployment
- Mobile notifications
- Advanced patient record management


Personalies treatment suggesion function

      It takes a user’s skin symptom description as input, predicts the most likely skin disease, recommends suitable treatments based on historical clinical data, and explains the result using a medical knowledge graph.

This function integrates multiple AI components into a single workflow, providing structured, explainable, and safety-aware skin care guidance.

            Purpose of the Function
The function is the core function of the SkinAI system.
It integrates disease prediction, treatment recommendation, and knowledge graph explanation into a single end-to-end workflow.

This function is responsible for converting raw user symptom input into a structured, explainable medical guidance output.

       
         Why This Function Is Needed
Instead of calling multiple independent components manually (classifier, treatment engine, knowledge graph), this function:
Centralizes the logic in one place
Ensures correct execution order
Makes the system easier to deploy as a chatbot or API
Improves maintainability and readability

                 Input Parameters

The function typically accepts:
   symptom_text (string)
User’s description of skin symptoms in natural language
    severity (optional, string)
Severity level such as mild, moderate, or severe
     skin_type / patient profile info (optional)
Used to personalize recommendations
      preferences (optional)
Such as allergy list or OTC-only preference

Step-by-Step Function Workflow
1️⃣ Disease Prediction

The input text is vectorized using the trained TF-IDF vectorizer

The classifier predicts:

Most likely disease

Top-K alternative diseases

Confidence scores

  Why:
Symptom text is unstructured; prediction converts it into a medical category.

2️⃣ Disease Name Normalization

The predicted disease name is normalized

Mapped to synthetic/knowledge-base disease names

Why:
Different datasets may use different naming conventions (e.g.,
“Ringworm (Tinea Corporis)” vs “Tinea corporis”).

3️⃣ Treatment Recommendation

Uses historical synthetic clinical data

Recommends treatments that previously led to improvement

Filters treatments based on:

Severity

Allergy restrictions

OTC preference

Why:
Ensures recommendations are data-driven and safety-aware.

4️⃣ Knowledge Graph Explanation

Retrieves:

Disease description

Associated symptoms

Related diseases

Explains why the disease was predicted

Why:
Improves transparency and trust using Explainable AI (XAI).

5️⃣ Output Formatting

Combines all results into a structured dictionary or formatted output:

Predicted disease

Confidence level

Alternative diseases

Treatment suggestions

Knowledge graph explanation

Why:
Makes output suitable for chatbot UI, API response, or report generation.

                 Output of the Function
  The function returns a structured result containing:
  Predicted disease
  Confidence score
  Top-K alternative diseases
  Recommended treatments
  Explanation based on medical knowledge graph

          Key Design Advantages
Modular integration of multiple AI components
Explainable predictions (not black-box output)
Safe medical guidance (non-diagnostic)
Easy to extend with new models or datasets
