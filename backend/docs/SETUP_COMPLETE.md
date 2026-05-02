# AI Skin Care Assistant - Setup Complete

Status at a glance
- Backend: default development port is `http://localhost:5001`
- Frontend: Flutter web/desktop/mobile runs from `frontend/`
- Auth: Supabase-backed login, register, and onboarding are wired
- Rendering: light mode only

Current architecture
```text
Reserch_Skin-care-deseases/
  frontend/lib/
    components/
      conversational_diagnosis_assistant/
      multimodal_image_audio_diagnosis/
      skin_type_skincare_recommendation/
      severity_assessment_tracking/
    core/
    services/
    config/
    utils/
    main.dart
  backend/
    app.py
    components/
      conversational_diagnosis_assistant/
      multimodal_image_audio_diagnosis/
      skin_type_skincare_recommendation/
      severity_assessment_tracking/
    assets/
    inference/
    services/
    database/
```

Readiness snapshot
- Conversational diagnosis: ready for internal testing
- Multimodal fused diagnosis: ready for internal testing
- Skin-type recommendation: operational, unlabeled validation still pending
- Severity assessment and tracking: operational, unlabeled validation still pending
- Image-only diagnosis: disabled for safety; use the fused path instead

Run commands
- Backend: `cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python app.py`
- Frontend: `cd frontend && flutter pub get && flutter run -d chrome`
- Quick model check: `cd backend && python tools/validation/evaluate_models.py --image-max-per-class 3 --fused-max-per-class 1 --output reports/validation_report_quick.json`

APIs
- `GET /api/health` - health check
- `GET /api/status` - model availability, readiness summary, and pending issues
- `POST /api/chat` - conversational diagnosis assistant
- `POST /api/analyze` - safety-blocked image-only compatibility endpoint
- `POST /api/analyze-fused` - multimodal image plus symptom diagnosis
- `POST /api/analyze-skin-care` - skin-type analysis and routine guidance
- `POST /api/analyze-severity` - severity score and review signals
- `POST /api/smart-scan` - automated fused flow with logging
- Profile and journey helpers: `/api/profile`, `/api/journey/start`, `/api/journey/list`

What changed recently
- Frontend imports are aligned to `core/` and `components/`.
- Backend runtime ownership is aligned to `backend/components/*`.
- Severity tracking persists to Supabase when available, with CSV fallback for offline or setup-failure cases.
- The image-only route is now safety-blocked instead of exposing low-trust standalone results.

Remaining gaps
- Skin-type and severity components still need labeled benchmark datasets for formal accuracy claims.
- Backend routes are still registered centrally from `backend/app.py`, even though the route logic now lives per component.
- The standalone image classifier is still below the project production bar; fused diagnosis remains the recommended path.
