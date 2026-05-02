# Supabase Setup Guide

This guide matches the current project structure and configuration flow.

## What this project expects

- Frontend credentials are injected at run time with `--dart-define`
- Backend credentials are loaded from `backend/.env`
- The database schema lives in:
  - `backend/database/schema.sql`
  - `backend/database/tracking_schema.sql`

## 1. Create the Supabase project

1. Create a project in the Supabase dashboard.
2. Open `Settings -> API`.
3. Copy:
   - Project URL
   - anon/public key
   - service role key

## 2. Apply the SQL schema

Run these files in the Supabase SQL editor in this order:

1. `backend/database/schema.sql`
2. `backend/database/tracking_schema.sql`

The second file is safe to run after the first one and adds tracking-specific tables and policies.

## 3. Configure the backend

1. Copy `backend/.env.example` to `backend/.env`.
2. Fill in these values:

```env
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_SECRET_KEY=YOUR_SERVICE_ROLE_KEY
SUPABASE_ANON_KEY=YOUR_ANON_OR_PUBLISHABLE_KEY
```

Notes:
- The backend accepts either `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_KEY`.
- Do not commit `backend/.env`.

## 4. Configure the frontend

Do not edit source files to insert keys.

Use one of these approaches instead:

### Option A: direct `flutter run`

```powershell
cd frontend
flutter pub get
flutter run -d chrome `
  --dart-define=SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co `
  --dart-define=SUPABASE_ANON_KEY=YOUR_ANON_OR_PUBLISHABLE_KEY
```

### Option B: helper script

If `backend/.env` is already filled, use:

```powershell
powershell -ExecutionPolicy Bypass -File frontend/scripts/run_flutter_with_env.ps1 -Device chrome
```

This reads `backend/.env` and forwards the values as `--dart-define`.

## 5. Optional Google Sign-In

If you are using Google authentication, also pass:

- `GOOGLE_WEB_CLIENT_ID`
- `GOOGLE_ANDROID_CLIENT_ID`
- `GOOGLE_IOS_CLIENT_ID`

See [AUTH_SETUP.md](/d:/Research/zip%20skin/Reserch_Skin-care-deseases/frontend/docs/AUTH_SETUP.md) for the current auth flow.

## 6. Verify the setup

Backend:

```powershell
cd backend
python app.py
```

Health check:

```powershell
python -c "import sys; sys.path.insert(0, 'backend'); from app import app; c = app.test_client(); print(c.get('/api/health').json)"
```

Frontend:

```powershell
cd frontend
flutter analyze
```

## 7. Benchmark validation status

The project is engineering-ready without benchmark data, but two validation datasets are still manual:

- `backend/assets/data/skin_type_skincare_recommendation/skin_types`
- `backend/assets/data/severity_assessment_tracking/severity_benchmark`

Check benchmark readiness with:

```powershell
python backend/tools/validation/benchmark_readiness.py
```

Run the full validation report with:

```powershell
python backend/tools/validation/evaluate_models.py --image-max-per-class 3 --fused-max-per-class 1 --output backend/reports/validation_report_quick.json
```

## Security rules

- Frontend: only anon/public credentials
- Backend: service role key only
- Never hardcode real project secrets in committed Dart or Python source
