# 🧴 Face Skin Severity & Progress Tracking System

**Final Year Research Project – PP1 (Checklist 1)**

---

## 📌 Project Overview

This project focuses on developing an **Explainable Face Skin Severity Assessment and Progress Tracking System** using **single skin images**.

Unlike traditional skin analysis systems that only classify diseases, this system is designed to:

* Quantify **skin severity levels** (mild, moderate, severe)
* Track **skin condition changes over time**
* Ensure **same facial region consistency** during tracking
* Provide **interpretable, feature-based outputs**

Due to the absence of publicly available **sequential skin image datasets**, this project adopts a **hybrid classical machine learning approach** that is robust, explainable, and suitable for real-world user uploads.

The system allows users to:

* Upload a face skin image
* Receive a severity assessment
* Upload follow-up images (daily/weekly)
* Track progression as **Improving / Stable / Worsening**

This repository demonstrates strong software engineering and research practices, including:

* Modular notebook-based workflow
* Reproducible experiments
* Classical ML model comparison
* Clean folder organization
* Version-controlled development

---

## 🎯 Main Objectives

* Extract **dermatologically meaningful features** from face skin images
* Generate **severity labels** where public datasets lack annotations
* Train and compare **classical ML models** for severity prediction
* Ensure **region-consistent tracking** (same face, same cheek)
* Track severity progression over time
* Provide **explainable outputs** suitable for medical interpretation
* Maintain industry-level Git version control

---

## 🧠 System Architecture

### 🔹 High-Level Architecture Diagram (Conceptual)

```
┌──────────────────────────┐
│        User Input        │
│   (Face Skin Image)     │
└─────────────┬──────────┘
              │
┌─────────────▼─────────────┐
│ Image Preprocessing       │
│ Resize + Normalize (CLAHE)│
└─────────────┬─────────────┘
              │
┌─────────────▼─────────────┐
│ Handcrafted Feature       │
│ Extraction Module         │
│ (Color, Texture, Edges)   │
└─────────────┬─────────────┘
              │
┌─────────────▼─────────────┐
│ Rule-Based Severity       │
│ Scoring & Labeling        │
└─────────────┬─────────────┘
              │
┌─────────────▼─────────────┐
│ ML Severity Classifier    │
│ (RF / SVM-RBF)            │
└─────────────┬─────────────┘
              │
┌─────────────▼─────────────┐
│ Progress Tracking Logic   │
│ (Improving / Stable /     │
│  Worsening)               │
└──────────────────────────┘
```

---

## 🧪 Models Used

### 🧩 Model 1: Handcrafted Feature Extraction (Non-ML)

* **Type:** Deterministic image analysis
* **Purpose:** Convert images into numeric dermatological indicators
* **Features extracted:**

  * redness_index
  * saturation_mean
  * brightness_mean
  * edge_density
  * texture_entropy
  * spotness
* **Why used:** Interpretability, low data requirement, medical relevance

---

### 🧠 Model 2: Rule-Based Severity Scoring Model

* **Type:** Mathematical / rule-based
* **Purpose:** Generate severity labels where datasets lack annotations
* **Output:**

  * Severity score (continuous)
  * Severity level (mild / moderate / severe)
* **Justification:** Public skin datasets do not provide severity annotations

---

### 🌲 Model 3: Random Forest Severity Classifier (Baseline)

* **Model Name:** HLF-RF Skin Severity Model
* **Algorithm:** Random Forest
* **Input:** Handcrafted features
* **Output:** Severity class
* **Role:** Baseline model with high interpretability
* **Strength:** Feature importance analysis

Saved Model:

```
04_models/severity_model_rf.joblib
```

---

### 📐 Model 4: SVM-RBF Severity Classifier (Improved Model)

* **Model Name:** SVM-RBF Severity Classifier
* **Algorithm:** Support Vector Machine (RBF kernel)
* **Input:** Same handcrafted features
* **Output:** Severity class + probabilities
* **Role:** Accuracy comparison and improvement over baseline
* **Strength:** Strong non-linear separation on small datasets

Saved Model:

```
04_models/severity_model_svm_rbf.joblib
```

---

### 📈 Model 5: Progression / Tracking Model

* **Type:** Rule-based temporal logic
* **Purpose:** Track severity changes across visits
* **Output:**

  * IMPROVING
  * STABLE
  * WORSENING
* **Why not time-series ML:** No public sequential datasets available

---

## 📁 Project Folder Structure

```
Face_Skin_Severity_System/
│
├── 01_raw_datasets/            # Original skin image datasets
├── 02_preprocessing/
│   ├── resized/
│   └── normalized/
├── 03_feature_store/
│   └── features.csv            # Extracted handcrafted features
├── 04_models/
│   ├── severity_model_rf.joblib
│   ├── severity_model_svm_rbf.joblib
│   └── metadata_*.json
├── 05_tracking/                # User tracking data (daily/weekly)
├── 06_results/
│   └── evaluation/             # Graphs & reports
├── 07_notebooks/
│   ├── 01_preprocessing.ipynb
│   ├── 02_feature_extraction.ipynb
│   ├── 03_severity_model.ipynb
│   ├── 03b_severity_training_SVM_RBF.ipynb
│   └── 05_tracking_demo.ipynb
├── README.md
└── requirements.txt
```

---

## 📓 Notebook Responsibilities (My Part)

| Notebook                            | Purpose                         |
| ----------------------------------- | ------------------------------- |
| 01_preprocessing.ipynb              | Image resizing & normalization  |
| 02_feature_extraction.ipynb         | Handcrafted feature extraction  |
| 03_severity_model.ipynb             | Baseline Random Forest training |
| 03b_severity_training_SVM_RBF.ipynb | Improved SVM model training     |
| 05_tracking_demo.ipynb              | Severity tracking & demo        |

---

## ⚙️ Dependencies

### Core Libraries

* Python 3.9+
* NumPy
* Pandas
* Scikit-learn
* OpenCV
* Matplotlib

### Environment

* Google Colab
* Google Drive (dataset & model storage)

---

## 🔁 Version Control & Collaboration (Checklist 1 Requirement)

This repository includes:

✅ Git repository created
✅ Regular commits over time
✅ Notebook-based modular development
✅ Clear workflow progression
✅ Reproducible experiments
✅ Clean folder organization

Evaluators are encouraged to review commit history to verify continuous development.

---

## 🔗 Repository Access (PP1 Submission)

* Git repository link provided
* Read access enabled
* Repository link uploaded to:

  * **OneDrive → Checklist 1 folder**

---

## 📊 PP1 Checklist Summary

✅ Problem definition completed
✅ System architecture documented
✅ Models clearly described
✅ Notebooks organized
✅ Graphical evaluation included
✅ Repository ready for evaluation

---

## 👤 Author (My Contribution)

**Role:** Skin Severity Modeling & Tracking

**Contributions:**

* Designed feature-based skin severity framework
* Implemented rule-based severity labeling
* Trained and compared RF & SVM models
* Designed progression tracking logic
* Developed explainable, non-CNN pipeline
* Integrated demo & evaluation workflow

