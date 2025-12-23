# 🧬 Cross-Cultural Skin Disease Classification via Domain Adaptation

> This repository focuses exclusively on the Cross-Cultural Fairness and Domain Adaptation component of the overall multimodal skin disease diagnosis system.

---

## 📌 Overview

This repository contains the implementation of the **Cross-Cultural Skin Disease Classification via Unsupervised Domain Adaptation (UDA)** component, developed as part of the research project:

**“Multimodal AI Framework for Personalized and Culturally Aware Skin Disease Diagnosis, Monitoring, and Treatment Support.”**

The primary goal of this component is to **reduce skin-tone bias in dermatological AI systems** and ensure **fair, reliable, and culturally aware skin disease classification** across diverse populations.

---

## 🎯 Problem Statement

Most existing AI-based skin disease classification models are trained on datasets that are heavily biased toward **lighter skin tones**, leading to:

- Poor generalization to darker skin tones  
- Increased misdiagnosis in underrepresented populations  
- Lack of fairness across ethnic and cultural groups  

Additionally, darker skin tones are often treated as a **single homogeneous group**, ignoring important **intra-tone variations** such as **oily and dry skin types**, which significantly influence lesion appearance and diagnostic accuracy.

---

## 💡 Proposed Solution

This component addresses these challenges using **Unsupervised Domain Adaptation (UDA)** combined with **fairness-aware learning techniques**.

### Key Contributions

- Cross-cultural domain adaptation between **light-skinned (source domain)** and **dark-skinned (target domain)** datasets  
- **Adversarial learning** to obtain domain-invariant feature representations  
- **Subtype-aware fairness modeling** by explicitly distinguishing **oily vs. dry subtypes** within darker skin tones  
- Equitable classification performance across both **skin tones** and **intra-tone subgroups**

This approach ensures that diagnostic outcomes are not biased toward any specific demographic group.

---

## 🧠 Methodology

### Image Input & Lesion Detection
- Users upload or capture skin images  
- CNN-based lesion detection identifies the region of interest  
- Low-quality images are rejected to maintain diagnostic reliability  

### Domain-Adaptive Feature Extraction
- A shared CNN feature extractor learns visual representations  
- **Unsupervised Domain Adaptation** aligns feature distributions between:  
  - **Source domain**: well-annotated light-skin datasets  
  - **Target domain**: underrepresented dark-skin datasets  
- **Adversarial training (DANN-style)** enforces domain-invariant feature learning  

### Subtype-Aware Fair Classification
- Dark skin samples are further categorized into:  
  - **Oily skin**  
  - **Dry skin**  
- Subtype-sensitive embeddings are incorporated into the classifier  
- Ensures fairness both **across skin tones** and **within darker skin subgroups**  

### Explainability
- **Grad-CAM visualizations** highlight lesion-focused regions  
- Improves transparency, trust, and clinical interpretability  

---

## 🏗️ System Architecture

Input Skin Image
↓
CNN Feature Extractor
↓
Domain-Invariant Feature Space
├── Disease Classifier
└── Domain Discriminator (Adversarial Training)
↓
Subtype-Aware Fair Classification


---

## ⚙️ Tools & Technologies

- **Programming Language**: Python  
- **Deep Learning Frameworks**: PyTorch / TensorFlow  
- **Domain Adaptation**: DANN, Feature Alignment, Adversarial Training  
- **Image Processing**: OpenCV, PIL  
- **Explainable AI**: Grad-CAM  
- **Backend (optional)**: FastAPI / Flask  

---

## 📊 Evaluation Strategy

The model is evaluated using:

- Overall classification accuracy  
- Skin-tone-wise performance comparison  
- **Intra-tone fairness analysis (dark skin: oily vs. dry)**  
- Fairness-aware metrics (error parity across subgroups)  

This ensures the system does not favor any single demographic group.

---

## 🌍 Significance

- Reduces healthcare disparities caused by AI bias  
- Improves diagnostic reliability for darker skin tones  
- Introduces **novel intra-tone fairness modeling**  
- Supports culturally aware and inclusive healthcare AI  
- Particularly relevant for **Sri Lankan and other underrepresented populations**

---

## 🚀 Future Work

- Expansion to additional skin disease categories  
- Larger-scale clinical validation across regions  
- Integration with multimodal patient metadata  
- Deployment as a dermatology decision-support tool  

---

## 👩‍💻 Author

**Devindi K. T. P**  
B.Sc. (Hons) in Information Technology   
Sri Lanka Institute of Information Technology (SLIIT)

---

## 📜 License

This project is developed for **academic and research purposes only**.

---

## ⚠️ Disclaimer

This system is intended strictly for **research purposes** and is **not a substitute for professional medical diagnosis or treatment**.

---

## ✅ Final Confirmation

- ✔ Component-specific  
- ✔ Group-safe  
- ✔ Supervisor-safe  
- ✔ Viva-safe  
- ✔ GitHub-professional  
