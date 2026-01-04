🩺 Multimodal Skin Disease Prediction System

Final Year Research Project – PP1 (Checklist 1)

📌 Project Overview

This project focuses on developing a Multimodal Skin Disease Prediction System that combines skin image analysis and voice-based symptom descriptions to improve diagnostic accuracy.

Traditional systems rely on a single modality (image or text), which can lead to incorrect predictions. Our approach integrates:

Image modality (skin lesion photos)

Voice modality (patient symptom descriptions → speech-to-text)

Multimodal fusion strategy

Knowledge-based interpretation

The system allows users to upload a skin image and record their symptoms, then produces:

A final disease prediction

Confidence score
Interpretable symptom-based explanation

This repository demonstrates real-world software engineering practices, including:
Proper Git version control
Branching and merging
Collaborative development
Reproducible experiments

🎯 Main Objectives

Build a CNN-based image classifier for skin diseases
Build a voice/text-based classifier using ASR + NLP
Design a fusion mechanism to combine both predictions
Provide explainable outputs using a knowledge base

Maintain industry-level Git version control
🧪 Models Used
📷 Image Model

Architecture: ResNet-18 (CNN)

Framework: PyTorch

Input: Skin lesion images

Output: Disease class probabilities

Saved Model:

models/image_best.pt

🎙️ Voice / Text Model

ASR: Speech-to-Text (Whisper / ASR pipeline)

Text Classifier: Transformer-based model

Input: Voice symptoms → transcript

Output: Disease probabilities

Saved Model:

models/asr_text_baseline/best_model/

🔀 Multimodal Fusion Strategy

Late Fusion approach

Combines image confidence and text confidence
Uses dynamic weighting (alpha)
Enhanced with knowledge-based symptom matching
Avoids hard overrides → safer predictions

📚 Knowledge-Based Interpretation (Optional but Used)

Disease ↔ Symptom mapping

Used to:

Validate predictions
Improve confidence estimation
Provide explainability

📁 Project Folder Structure
SkinDisease_Multimodal_Project/
│
├── data/
│   ├── splits/                 # Train/val/test CSVs
│   ├── knowledge_base/          # Disease–symptom mappings
│
├── models/
│   ├── image_best.pt            # Final image model
│   ├── asr_text_baseline/       # Final voice/text model
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_image_baseline.ipynb
│   ├── 03_audio_baseline.ipynb
│   ├── 03c_audio_asr_to_text.ipynb
│   ├── 03d_asr_text_semantic_baseline.ipynb
│   ├── 04_multimodal_fusion.ipynb
│   ├── 05_demo_inference_PERFECT_v3.ipynb
│
├── results/
│   ├── fusion_outputs/
│   ├── evaluation_reports/
│
├── README.md
└── requirements.txt

📓 Notebook Responsibilities (My Part)
Notebook	Purpose
01_data_exploration.ipynb	Dataset analysis & sanity checks
02_image_baseline.ipynb	Train CNN image model
03c_audio_asr_to_text.ipynb	Convert voice → text
03d_asr_text_semantic_baseline.ipynb	Train voice/text model
04_multimodal_fusion.ipynb	Fusion strategy & evaluation
05_demo_inference_PERFECT_v3.ipynb	Final demo & UI integration

⚙️ Dependencies

Core Libraries

Python 3.9+
PyTorch
TorchVision
Transformers (HuggingFace)
NumPy
Pandas
Scikit-learn
Matplotlib

ASR & Audio

Faster-Whisper / Whisper
FFmpeg
Librosa

Environment

Google Colab
Google Drive (model storage)

🔁 Version Control & Collaboration (Checklist 1 Requirement)

This repository includes:

✅ Full commit history
✅ Multiple commits over time
✅ Branch usage (feature development)
✅ Merges into main branch
✅ Clear progression of work

Evaluators:
Please review the commit history, branches, and merge records to verify collaboration and continuous development.


📊 Project Management (Checklist 2 – Planned)

MS Planner used for task tracking
Roles & responsibilities documented
Planner report will be exported and uploaded for Checklist 2

✅ PP1 Checklist Summary

 Git repository created
 README.md completed
 Architecture documented
 Dependencies listed
 Version control history visible
 Shareable repo link provided

👤 Author : Oshidee Prarthana Wijesinghe
Role: Multimodal Modeling & Fusion
Contributions:

Image model training
Voice/ASR integration
Fusion logic design
Explainability via KB
End-to-end demo pipeline
