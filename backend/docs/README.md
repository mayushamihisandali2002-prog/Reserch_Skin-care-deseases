# Skin Care Assistant

AI-assisted skin-health project organized around four main product components:

1. Conversational diagnosis assistant
2. Multimodal image/audio diagnosis
3. Skin-type based skincare recommendation
4. Severity assessment and tracking

## Project Structure

```text
Reserch_Skin-care-deseases/
  frontend/
    lib/
      components/
        conversational_diagnosis_assistant/
        multimodal_image_audio_diagnosis/
        skin_type_skincare_recommendation/
        severity_assessment_tracking/
      config/
      core/
        auth/
        navigation/
        overview/
      services/
      utils/
      main.dart
    logs/
    scripts/
    tools/
  backend/
    components/
      conversational_diagnosis_assistant/
      multimodal_image_audio_diagnosis/
      skin_type_skincare_recommendation/
      severity_assessment_tracking/
    assets/
      root_assets_legacy/
      data/
        conversational_diagnosis_assistant/
        multimodal_image_audio_diagnosis/
        skin_type_skincare_recommendation/
        severity_assessment_tracking/
      models/
        conversational_diagnosis_assistant/
        multimodal_image_audio_diagnosis/
        skin_type_skincare_recommendation/
        severity_assessment_tracking/
    inference/
      config.py
      label_space.py
    logs/
    reports/
    scripts/
    services/
    tests/
      shared/
    tools/
      admin/
      debug/
      legacy/
      pilot/
      validation/
    docs/
      README.md
      PILOT_READINESS.md
      PROJECT_SETUP_SUMMARY.md
      CHAT_WORKFLOW_GUIDE.md
      SETUP_COMPLETE.md
      four-component-architecture.md
    database/
    app.py
```

## Runtime Ownership

- `frontend/lib/components/*` contains the four feature UIs.
- `frontend/lib/core/*` contains auth, app shell, and overview/navigation.
- `backend/components/*` contains the four feature backends.
- `backend/inference/*` is shared configuration and label-space support only.
- `backend/tools/*`, `backend/tests/*`, `backend/logs/*`, and `backend/reports/*` hold shared support files that do not belong to one feature.
- `backend/docs/*` holds shared project documentation.
- `backend/tools/pilot/pilot_self_check_v1.py` is the pilot verification script.
- `backend/app.py` remains the Flask bootstrap and route registration entry point.

The repo is organized in two layers:

1. `frontend/` contains the Flutter application.
2. `backend/` contains the Flask API, model inference, persistence, and evaluation code.

Inside both runtimes, implementation is grouped by the same four major product components so frontend and backend stay aligned.

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Flutter App

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

## Validation Commands

```bash
cd backend
python tools/validation/evaluate_models.py --image-max-per-class 3 --fused-max-per-class 1 --output reports/validation_report_quick.json
```

```bash
cd backend
python -c "from components.multimodal_image_audio_diagnosis import get_inference_pipeline; print(bool(get_inference_pipeline()))"
```

## Current Readiness Snapshot

- Conversational diagnosis assistant: ready for internal testing
- Multimodal fused diagnosis: ready for internal testing
- Skin-type recommendation: ready for internal testing on unlabeled operational checks
- Severity assessment and tracking: ready for internal testing on unlabeled operational checks
- Image-only diagnosis: improved, but still not ready by the current benchmark threshold

## Disclaimer

This project provides AI-assisted guidance only and is not a substitute for diagnosis by a qualified dermatologist.
