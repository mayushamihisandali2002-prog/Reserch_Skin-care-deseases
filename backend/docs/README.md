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
      config/
      core/
      services/
      utils/
      main.dart
    docs/
    scripts/
    tools/
  backend/
    app.py
    components/
    assets/
      data/
      models/
    database/
    docs/
    inference/
    reports/
    scripts/
    services/
    tests/
    tools/
```

## Runtime Ownership

- `frontend/lib/components/*` contains the four feature UIs.
- `frontend/lib/core/*` contains auth, navigation, onboarding, and overview.
- `backend/components/*` contains the four feature backends.
- `backend/inference/*` is shared configuration and label-space support only.
- `backend/tools/*`, `backend/tests/*`, `backend/logs/*`, and `backend/reports/*` contain shared support files.
- `backend/docs/*` contains shared project documentation.
- `backend/app.py` is the Flask bootstrap and route registration entry point.

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

## Current Readiness Snapshot

- Conversational diagnosis assistant: ready for internal testing
- Multimodal fused diagnosis: ready for internal testing
- Skin-type recommendation: ready for internal testing on unlabeled operational checks
- Severity assessment and tracking: ready for internal testing on unlabeled operational checks
- Image-only diagnosis: disabled for safety; use the fused multimodal path

## Disclaimer

This project provides AI-assisted guidance only and is not a substitute for diagnosis by a qualified dermatologist.
