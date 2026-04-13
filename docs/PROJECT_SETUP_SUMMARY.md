# Skin Care Assistant - Project Setup Summary

## Current Structure

The project is organized around four main product components:

1. Conversational diagnosis assistant
2. Multimodal image/audio diagnosis
3. Skin-type based skincare recommendation
4. Severity assessment and tracking

## Repository Layout

```text
Reserch_Skin-care-deseases/
  frontend/
    docs/
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
      data/
      models/
    database/
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
      validation/
    app.py
```

## Frontend Ownership

- `frontend/lib/components/` contains the four feature-specific UI areas.
- `frontend/lib/core/auth/` contains login, register, and onboarding flow.
- `frontend/lib/core/navigation/` contains the main shell and tab container.
- `frontend/lib/core/overview/` contains the dashboard and cross-feature summary UI.
- `frontend/lib/main.dart` is the light-mode app bootstrap.

## Backend Ownership

- `backend/components/` contains the four feature-specific model and service modules.
- `backend/inference/` is now shared support only for config and label-space utilities.
- `backend/tools/`, `backend/tests/`, `backend/logs/`, and `backend/reports/` now hold shared support files that do not belong to a single component.
- `backend/app.py` is the Flask bootstrap and active API entry point.
- `backend/database/tracking_schema.sql` remains the tracking schema source for the severity journey flow.

## Setup Status

- Top-level runtime split: `frontend/` + `backend/`
- Flutter app structure: aligned to the 4-category layout
- Backend module structure: aligned to the 4-category layout
- Legacy single-folder screen layer: removed
- Legacy `backend/inference/*.py` feature-module imports: removed from active backend boot path
- Supabase-backed auth/profile flow: active
- Light mode: forced

## Current Readiness Snapshot

- Conversational diagnosis assistant: ready for internal testing
- Multimodal fused diagnosis: ready for internal testing
- Skin-type recommendation: operational, but still needs labeled validation for stronger claims
- Severity assessment and tracking: operational, but still needs labeled validation for stronger claims
- Image-only diagnosis: improved and calibrated, but not yet ready by the current benchmark threshold

## Run Commands

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Flutter

```bash
cd frontend
flutter pub get
flutter run -d chrome
```

### Quick Backend Validation

```bash
cd backend
python -m py_compile app.py tools/validation/evaluate_models.py
python tools/validation/evaluate_models.py --image-max-per-class 3 --fused-max-per-class 1 --output reports/validation_report_quick.json
```

## Important Note

This project is structured for dermatologist-assisted evaluation, not autonomous medical diagnosis. Final clinical use still requires stronger model validation, especially for the standalone image-only classifier.
