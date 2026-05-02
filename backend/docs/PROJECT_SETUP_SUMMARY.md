# Skin Care Assistant - Project Setup Summary

## Current Structure

The product is organized around four main components:

1. Conversational diagnosis assistant
2. Multimodal image/audio diagnosis
3. Skin-type based skincare recommendation
4. Severity assessment and tracking

## Repository Layout

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

## Ownership Summary

- `frontend/lib/components/` contains the four feature-specific UI areas.
- `frontend/lib/core/` contains auth, app shell, navigation, and overview.
- `backend/components/` contains the four feature-specific inference and route modules.
- `backend/inference/` is shared support only for config and label-space utilities.
- `backend/app.py` is the Flask bootstrap and API registration entry point.
- `backend/database/schema.sql` is the base database schema.
- `backend/database/tracking_schema.sql` is the tracking extension schema.

## Setup Status

- Top-level runtime split: `frontend/` plus `backend/`
- Shared project documentation: `backend/docs/`
- Pilot verification tooling: `backend/tools/pilot/`
- Flutter app structure: aligned to the 4-category layout
- Backend module structure: aligned to the 4-category layout
- Supabase-backed auth/profile flow: active
- Light mode: forced
- Severity tracking persistence: Supabase-first with CSV fallback

## Current Readiness Snapshot

- Conversational diagnosis assistant: ready for internal testing
- Multimodal fused diagnosis: ready for internal testing
- Skin-type recommendation: operational, but still needs labeled validation for stronger claims
- Severity assessment and tracking: operational, but still needs labeled validation for stronger claims
- Image-only diagnosis: disabled for safety; use the fused multimodal path

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

This project is structured for dermatologist-assisted evaluation, not autonomous medical diagnosis. Final clinical use still requires stronger model validation, especially for the disabled standalone image path and the unlabeled skin-type and severity components.
