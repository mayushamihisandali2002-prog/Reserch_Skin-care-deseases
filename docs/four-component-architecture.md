# Four-Component Ownership Plan

This document is the strict ownership map for the current repo.

Rule:
- If a file exists only to serve one user-facing capability, it belongs to that component.
- If a file supports more than one component, app bootstrapping, auth, config, database, or shared services, it stays in shared/core.

## Target Shape

```text
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
  services/
  inference/
  app.py
```

## 1. Conversational Diagnosis Assistant

Purpose:
- Symptom conversation
- Disease explanation
- Treatment guidance
- Follow-up questions
- Session-aware chat behavior

Frontend ownership:
- `frontend/lib/components/conversational_diagnosis_assistant/presentation/chat_screen.dart`

Backend ownership:
- `backend/components/conversational_diagnosis_assistant/distilbert_model.py`
- `backend/components/conversational_diagnosis_assistant/intent_classifier.py`
- `backend/components/conversational_diagnosis_assistant/knowledge_base.py`
- `backend/components/conversational_diagnosis_assistant/session_manager.py`
- `backend/components/conversational_diagnosis_assistant/__init__.py`

Backend route ownership:
- `backend/app.py` route: `/api/chat`

Model and data ownership:
- `backend/assets/models/distilbert/`
- `backend/assets/models/text_model.pkl`
- `backend/assets/models/vectorizer.pkl`
- `backend/assets/data/disease_symptom_edges_expanded.csv`
- `backend/assets/data/treatment_records_clean.csv`

Training, evaluation, and tests that belong here:
- `backend/train_distilbert.py`
- `backend/augment_symptom_data.py`
- `backend/comprehensive_symptom_miner.py`
- `backend/test_chat.py`
- `backend/test_intents.py`
- `backend/test_workflow.py`

Should not live here:
- App shell, auth, navigation, Supabase wiring
- Image upload and audio capture UI
- Skin-type routine logic
- Severity tracking persistence

## 2. Multimodal Image/Audio Diagnosis

Purpose:
- Image-only disease diagnosis
- Image + typed symptom fusion
- Image + audio symptom fusion
- Diagnosis result presentation

Frontend ownership:
- `frontend/lib/components/multimodal_image_audio_diagnosis/presentation/instruction_screen.dart`
- `frontend/lib/components/multimodal_image_audio_diagnosis/presentation/result_screen.dart`

Backend ownership:
- `backend/components/multimodal_image_audio_diagnosis/image_model.py`
- `backend/components/multimodal_image_audio_diagnosis/inference.py`
- `backend/components/multimodal_image_audio_diagnosis/__init__.py`

Backend route ownership:
- `backend/app.py` route: `/api/analyze`
- `backend/app.py` route: `/api/analyze-fused`
- `backend/app.py` audio transcription helpers used by fused analysis

Model and data ownership:
- `backend/assets/models/image_best_finetuned.pt`
- `backend/assets/data/research_dataset/`
- `backend/assets/data/combined_images/`

Training, evaluation, and tests that belong here:
- `backend/retrain_image_model.py`
- `backend/fetch_research_images.py`
- `backend/download_additional_images.py`
- `backend/download_ham10000.py`
- `backend/test_image_api.py`
- `backend/test_image_inference.py`
- `backend/test_image_model.py`
- `backend/test_image_refactored.py`
- `backend/verify_image_model.py`

Should not live here:
- Chat intent routing and session logic
- Skin-type recommendation policy
- Severity tracking history
- Auth or profile management

## 3. Skin-Type Based Skincare Recommendation

Purpose:
- Skin-type prediction
- Ingredient recommendations
- Ingredient avoidance
- Routine generation using questionnaire inputs

Frontend ownership:
- `frontend/lib/components/skin_type_skincare_recommendation/presentation/skin_care_screen.dart`

Backend ownership:
- `backend/components/skin_type_skincare_recommendation/skin_type_model.py`
- `backend/components/skin_type_skincare_recommendation/__init__.py`

Backend route ownership:
- `backend/app.py` route: `/api/analyze-skin-care`
- `backend/app.py` skin-type questionnaire and routine helper functions

Model and data ownership:
- `backend/assets/models/skin_type/`
- `backend/assets/data/skin_types/`
- `backend/assets/data/skin_types_hf/`

Training, evaluation, and tests that belong here:
- `backend/download_skin_type_data.py`
- `backend/retrain_skin_type_model.py`
- `backend/verify_skin_type_model.py`
- `backend/test_skin_type_api.py`

Should not live here:
- Disease chat knowledge base
- Disease image classifier
- Severity scoring and progress history

## 4. Severity Assessment And Tracking

Purpose:
- Severity class prediction
- Severity score calculation
- Progress tracking
- Healing analysis and journey setup

Frontend ownership:
- `frontend/lib/components/severity_assessment_tracking/presentation/severity_screen.dart`
- `frontend/lib/components/severity_assessment_tracking/presentation/progress_screen.dart`
- `frontend/lib/components/severity_assessment_tracking/presentation/healing_analysis_screen.dart`
- `frontend/lib/components/severity_assessment_tracking/presentation/journey_setup_screen.dart`
- `frontend/lib/components/severity_assessment_tracking/presentation/analyze_screen.dart`

Backend ownership:
- `backend/components/severity_assessment_tracking/severity_model.py`
- `backend/components/severity_assessment_tracking/__init__.py`

Backend route ownership:
- `backend/app.py` route: `/api/analyze-severity`
- `backend/app.py` severity tracking helpers

Model and data ownership:
- `backend/assets/models/severity/`
- `backend/assets/data/severity_tracking/`
- `backend/database/tracking_schema.sql`

Training, evaluation, and tests that belong here:
- `backend/test_severity_api.py`
- `backend/test_tracking_journeys.py`

Should not live here:
- Disease chat model
- Multimodal fusion logic
- Skin-type questionnaire and routine generation

## Shared And Core

These files must stay outside the 4 component folders because they serve multiple parts of the app.

Frontend shared/core:
- `frontend/lib/main.dart`
- `frontend/lib/core/auth/presentation/`
- `frontend/lib/core/navigation/home_container.dart`
- `frontend/lib/core/overview/presentation/dashboard_screen.dart`
- `frontend/lib/services/api_service.dart`
- `frontend/lib/services/supabase_service.dart`
- `frontend/lib/config/app_config.dart`
- `frontend/lib/config/supabase_config.dart`
- `frontend/lib/utils/`

Backend shared/core:
- `backend/app.py`
- `backend/inference/config.py`
- `backend/services/supabase_service.py`
- `backend/database/schema.sql`
- `backend/ffmpeg/`

Cross-component validation and maintenance:
- `backend/tools/validation/evaluate_models.py`
- `backend/reports/validation_report.json`
- `backend/reports/validation_report_quick.json`
- `backend/tests/shared/test_models.py`
- `backend/tests/shared/test_ai_integration.py`
- `backend/tests/shared/test_automation.py`
- `backend/tests/shared/test_req.py`
- `backend/tests/shared/test_options.py`
- `backend/tools/debug/inspect_skincap.py`
- `backend/tools/debug/debug_path.py`
- `backend/tools/admin/create_test_user.py`
- `backend/tools/legacy/patch_fallback.py`
- `backend/tools/legacy/patch_kb.py`
- `backend/tools/legacy/patch_train.py`
- `backend/components/conversational_diagnosis_assistant/tools/legacy/add_hyperpigmentation_treatments_root_legacy.py`
- `frontend/tools/apply_theme.py`

## Practical Restructure Rule

If you physically keep restructuring the repo, use this rule:

- Put UI screens in the matching `frontend/lib/components/<component>/presentation/` folder.
- Put model code and component logic in the matching `backend/components/<component>/` folder.
- Put per-component training scripts and tests under the matching `backend/components/<component>/tools/` and `backend/components/<component>/tests/` folders.
- Keep shared validation, admin scripts, logs, and reports in `backend/tools/`, `backend/tests/shared/`, `backend/logs/`, and `backend/reports/`.
- Keep app bootstrap, auth, config, services, database, and shared assets outside the 4 components.

## Backend Status

Route ownership is now split by component:

- `backend/components/conversational_diagnosis_assistant/routes.py`
- `backend/components/multimodal_image_audio_diagnosis/routes.py`
- `backend/components/skin_type_skincare_recommendation/routes.py`
- `backend/components/severity_assessment_tracking/routes.py`

`backend/app.py` is now the shared bootstrap (CORS/logging) plus route registration and shared `/api/health` + `/api/status`.
