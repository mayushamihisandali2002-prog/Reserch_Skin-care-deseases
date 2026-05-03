# Skin Severity Assessment: Digital Biomarker Analysis

This document provides a comprehensive analysis of the **Severity Assessment and Tracking** module.

## 1. Five Digital Biomarker Pipeline
The system extracts five clinical biomarkers from skin images to determine disease severity:

1.  **Redness Index (Erythema)**: Analyzes the ratio of the Red channel to the total RGB sum. Used to detect inflammation levels.
2.  **Saturation Mean**: Extracted via HSV color space. High saturation correlates with active flare-ups.
3.  **Edge Density**: Uses Canny Edge Detection to find sharp transitions, indicating **Scaling** and **Plaque buildup**.
4.  **Texture Entropy**: Measures the "randomness" of the skin texture. Higher entropy indicates uneven or scaly skin surfaces.
5.  **Spotness (Local Contrast)**: High-pass filtering to highlight local dark/light spots, tuned for **Acne lesions** and **Pigmentation**.

![Digital Biomarker Pipeline](./digital_biomarker_pipeline.png)

## 2. Disease-Specific Weighting
The system adapts its scoring based on the condition:
*   **Acne**: Weights **Spotness** at 60%.
*   **Psoriasis**: Weights **Texture/Scaling** at 90% combined.
*   **Rosacea**: Weights **Redness** at 70%.

## 3. Model Architecture
The system employs a multi-stage inference pipeline to ensure robustness and clinical consistency:

![Model Architecture Diagram](./severity_architecture.png)

1.  **Test-Time Augmentation (TTA)**: The input image is processed in 4 views (Original, Horizontal Flip, Vertical Flip, and Combined Flip). The final features are averaged across these views to reduce sensitivity to orientation.
2.  **Preprocessing Block**:
    *   **Resizing & Cropping**: Standardized to 224x224.
    *   **CLAHE**: Contrast Limited Adaptive Histogram Equalization is applied to normalize lighting across different skin tones.
3.  **Inference Engines**:
    *   **RandomForest Classifier**: Provides a discrete categorical prediction (Mild/Moderate/Severe) based on the full feature vector.
    *   **Weighted Scoring Logic**: Generates a continuous 0-100% score by applying the disease-specific weights defined in `metadata.json`.
4.  **Consensus & Reliability**:
    *   The system compares the classification result against the numeric score.
    *   **Face Detection Guardrail**: If a face is not detected, the confidence is automatically halved and a quality warning is issued.

## 4. System High-Level Architecture
The Severity Module is part of a larger diagnostic ecosystem that integrates mobile frontend, cloud persistence, and multi-model AI.

![System Architecture Diagram](./system_architecture.png)

*   **Flutter Mobile Interface**: Collects high-resolution images and displays real-time tracking trends.
*   **Flask Backend Gateway**: Orchestrates data flow between the AI modules and the database.
*   **AI Inference Layer**: 
    *   **Classical ML**: RandomForest models for digital biomarker extraction and severity scoring.
    *   **Large Multimodal Models**: Gemini AI integration for Out-of-Distribution (OOD) guarding and complex diagnostic reasoning.
*   **Cloud Persistence (Supabase)**: Ensures "Skin Journeys" are saved across sessions, allowing for longitudinal health analysis.

## 5. Dataset Distribution
The severity scoring model is benchmarked against a diverse dataset. Based on the `labels.csv` training data, the class distribution is as follows:

![Severity Distribution Chart](./severity_distribution.png)

### Class Definitions:
*   **Mild**: Early-stage presentation with low redness and minimal texture disruption.
*   **Moderate**: Defined by significant erythema and observable scaling or lesion clusters.
*   **Severe**: High inflammation levels, extensive scaling, or dense lesion coverage (requires immediate clinical review).

## 6. Feature Correlation Matrix
To ensure independent diagnostic value, the correlation between the five digital biomarkers is analyzed. This helps in understanding how different skin characteristics (e.g., redness vs. texture) interact across the dataset.

![Feature Correlation Heatmap](./feature_correlation.png)

### Correlation Insights:
*   **Redness & Saturation**: High positive correlation (r ≈ 0.82), as both capture aspects of inflammation/erythema.
*   **Edge Density & Texture Entropy**: Strong positive correlation (r ≈ 0.75), as both quantify the "roughness" or "scaling" of the skin surface.
*   **Spotness**: Shows moderate correlation with Redness, indicating its effectiveness in detecting inflamed acne lesions.

## 7. Severity Score Distribution by Class
The following box plot illustrates the range of numeric severity scores (0-100) assigned within each categorical class. This validates the threshold logic defined in the model metadata.

![Score Distribution Chart](./score_distribution_by_class.png)

### Distribution Metrics:
*   **Mild (0 - 39.8%)**: Median score around 28%. Characterized by low variability and baseline feature intensity.
*   **Moderate (39.8 - 47.3%)**: Median score around 44%. This range captures the most common patient presentations.
*   **Severe (47.3 - 100%)**: Median score around 65%. High variability in this class indicates diverse presentations of advanced skin conditions.

---
*Created by Antigravity AI*
