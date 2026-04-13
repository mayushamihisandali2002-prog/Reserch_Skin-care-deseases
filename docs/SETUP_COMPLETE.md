# AI Skin Care Assistant — Setup Complete

Status at a glance
- Backend: running and serving APIs on http://localhost:5000
- Frontend: Flutter web/desktop/mobile builds run from `frontend/`
- Auth: Supabase-backed login/register/onboarding wired
- Rendering: light mode only

Current architecture
```
Reserch_Skin-care-deseases/
  frontend/lib/
    components/
      conversational_diagnosis_assistant/
      multimodal_image_audio_diagnosis/
      skin_type_skincare_recommendation/
      severity_assessment_tracking/
    core/        # auth, navigation, overview
    services/    # API + Supabase clients
    config/
    utils/
    main.dart
  backend/
    app.py       # Flask bootstrap + route registration
    components/
      conversational_diagnosis_assistant/
      multimodal_image_audio_diagnosis/
      skin_type_skincare_recommendation/
      severity_assessment_tracking/
    assets/      # models + data
    inference/   # shared config + label space only
    services/    # Supabase service
    database/    # tracking_schema.sql
```

Readiness snapshot
- Conversational diagnosis: ready for internal testing
- Multimodal fused diagnosis: ready for internal testing
- Skin-type recommendation: operational (unlabeled validation pending)
- Severity assessment/tracking: operational (unlabeled validation pending)
- Image-only diagnosis: improved/calibrated but still not ready for production

Run commands
- Backend: `cd backend && python -m venv .venv && .venv\\Scripts\\activate && pip install -r requirements.txt && python app.py`
- Frontend: `cd frontend && flutter pub get && flutter run -d chrome`
- Quick model check: `cd backend && python tools/validation/evaluate_models.py --image-max-per-class 3 --fused-max-per-class 1 --output reports/validation_report_quick.json`

APIs (served from backend/app.py)
- `GET  /api/health` — health check
- `GET  /api/status` — model availability
- `POST /api/chat` — conversational diagnosis assistant
- `POST /api/analyze` — image-only diagnosis (provisional)
- `POST /api/analyze-fused` — multimodal (image+text) diagnosis
- `POST /api/analyze-skin-care` — skin-type analysis + routine guidance
- `POST /api/analyze-severity` — severity score/class
- `POST /api/smart-scan` — automated fused flow with logging
- Profile/journey helpers: `/api/profile`, `/api/journey/start`, `/api/journey/list`

What changed recently
- Frontend now imports from `core` + `components`; legacy screen-layer layout removed.
- Backend bootstrap now imports models from `backend/components/*`; legacy `backend/inference/*` feature modules removed.
- Image-only pipeline now calibrated with runtime operating point metadata; provisional flag surfaces to UI.

Remaining gaps
- Flutter analyzer timed out in this environment; a clean analyze pass is still pending.
- Backend routes are still centralized in `backend/app.py`; splitting into per-component route modules is the next structural step.
- Image-only classifier still below the project’s production bar; fused flow is the recommended path for dermatologist testing.
