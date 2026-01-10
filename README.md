🧠 Multimodal, Explainable & Fair AI Framework for Skin Disease Diagnosis, Severity Tracking, and Personalized Treatment Support

Final Year Research Project – PP1 (Checklist 1)
Sri Lanka Institute of Information Technology (SLIIT)

📌 Project Overview

This research presents a comprehensive AI-driven framework for skin disease analysis, combining diagnosis, severity assessment, fairness-aware modeling, and personalized treatment support.

Unlike traditional dermatology AI systems that focus only on single-image disease classification, this framework integrates:

Multimodal skin disease prediction (Image + Voice/Text)

Explainable face skin severity assessment & progress tracking

Personalized treatment recommendation & follow-up monitoring

Cross-cultural fairness & domain adaptation to reduce skin-tone bias

The system is designed as a decision-support tool, prioritizing:

Explainability

Safety

Fairness

Real-world usability

⚠️ This system does not replace medical professionals.

🧩 Integrated Research Components
1️⃣ Multimodal Skin Disease Prediction System

(Image + Voice-Based Diagnosis)

Objective: Improve diagnostic accuracy by combining multiple modalities.

Key Features

Skin lesion image analysis using CNNs

Voice-based symptom input (Speech-to-Text)

Late fusion strategy with dynamic confidence weighting

Knowledge-based symptom validation

Explainable disease predictions

Models & Tools

Image Model: ResNet-18 (PyTorch)

ASR: Whisper / Faster-Whisper

Text Model: Transformer-based NLP

Fusion: Confidence-based late fusion

Outputs

Final disease prediction

Confidence score

Symptom-based explanation

2️⃣ 🧴 Face Skin Severity & Progress Tracking System

(Explainable & Non-CNN Approach)

Author: Laksopan
Role: Skin Severity Modeling & Progress Tracking

📌 Overview

This component focuses on quantifying face skin severity and tracking progression over time using single skin images.

Unlike disease classifiers, this system:

Quantifies severity (mild / moderate / severe)

Tracks condition changes over time

Ensures same facial region consistency

Provides interpretable, feature-based outputs

Due to the lack of public sequential datasets, a hybrid classical ML approach is used.

🎯 Objectives

Extract dermatologically meaningful handcrafted features

Generate severity labels via rule-based scoring

Train & compare classical ML models

Track severity progression (Improving / Stable / Worsening)

Maintain explainability & reproducibility

🧠 Architecture (Conceptual)
User Image
   ↓
Preprocessing (CLAHE)
   ↓
Handcrafted Feature Extraction
   ↓
Rule-Based Severity Scoring
   ↓
RF / SVM-RBF Classifier
   ↓
Progress Tracking Logic

🧪 Models Used

Handcrafted Feature Extractor

Rule-Based Severity Labeling

Random Forest (Baseline)

SVM-RBF (Improved Model)

Rule-Based Progress Tracking

📁 Folder Structure
Face_Skin_Severity_System/
├── 01_raw_datasets/
├── 02_preprocessing/
├── 03_feature_store/
├── 04_models/
├── 05_tracking/
├── 06_results/
├── 07_notebooks/
└── README.md

🧑‍💻 Contributions – Laksopan

Designed feature-based severity framework

Implemented rule-based severity labeling

Trained & compared RF and SVM-RBF models

Developed progression tracking logic

Built explainable, non-CNN pipeline

Integrated demo & evaluation workflow

3️⃣ Personalized Skin Treatment Support & Monitoring System

Author: Mihisandali W.K.M
Registration No: IT22246400

📌 Overview

This system extends beyond diagnosis to provide:

Safe OTC/self-care treatment recommendations

Knowledge-graph-based explanations

Red-flag detection

Notification-based follow-ups (Day 1 / 3 / 7)

🧠 Core Functionality

A single integrated function:

Predicts disease from symptom text

Normalizes disease names

Recommends safe treatments

Explains decisions using a medical knowledge graph

Produces structured, explainable output

🧪 Models Used

TF-IDF Vectorizer

Logistic Regression

SGDClassifier

Calibrated Linear SVM (Selected Model)

🛡️ Ethical Design

Uses synthetic data

Provides decision support, not diagnosis

Advises professional care when red flags are detected

4️⃣ 🧬 Cross-Cultural Skin Disease Classification via Domain Adaptation

Author: Devindi K. T. P

📌 Overview

This component addresses skin-tone bias in dermatology AI systems.

💡 Key Contributions

Unsupervised Domain Adaptation (UDA)

Adversarial domain-invariant feature learning

Subtype-aware fairness (oily vs dry skin within darker tones)

Fair performance across demographics

🧠 Architecture
Skin Image
   ↓
CNN Feature Extractor
   ↓
Domain-Invariant Feature Space
   ↓
Disease Classifier + Domain Discriminator

🌍 Impact

Reduces healthcare disparities

Improves diagnostic reliability

Supports culturally aware AI

Highly relevant to Sri Lankan populations

⚙️ Technologies & Dependencies

Languages & Frameworks

Python 3.9+
PyTorch
Scikit-learn
HuggingFace Transformers
Vision & Audio
OpenCV
Whisper / Faster-Whisper
Librosa
Explainability
Knowledge Graphs (NetworkX)
Grad-CAM

Feature Importance

Environment

Google Colab
Google Drive
Git & GitHub

🔁 Version Control & Collaboration (PP1 – Checklist 1)

This project demonstrates industry-level Git practices:

✅ Git repository created
✅ Regular commits over time
✅ Feature branches used
✅ Merges into main branch
✅ Modular notebook workflow
✅ Reproducible experiments

Evaluators are encouraged to review commit history, branches, and merge records.

📊 PP1 Checklist Summary

✅ Problem definition completed
✅ System architecture documented
✅ Models clearly described
✅ Dependencies listed
✅ Notebooks organized
✅ Version control history visible
✅ Repository ready for evaluation

👥 Authors & Roles

Name	                        Role
Oshidee Prarthana Wijesinghe	Multimodal Disease Prediction & Fusion
Laksopan	                    Face Skin Severity Modeling & Progress Tracking
Mihisandali W.K.M            	Personalized Treatment Support System
Devindi K. T. P	              Fairness & Domain Adaptation

⚠️ Disclaimer
This system is developed strictly for academic and research purposes and is not a substitute for professional medical diagnosis or treatment.
