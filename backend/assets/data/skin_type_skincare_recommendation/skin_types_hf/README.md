## Skin-Type Reference Dataset

This folder is reserved for raw/reference skin-type data downloaded from external sources such as Hugging Face.

Current tooling:
- `backend/components/skin_type_skincare_recommendation/tools/download_skin_type_data.py`

Important:
- This folder is **not** the formal benchmark input for `backend/tools/validation/evaluate_models.py`.
- The helper script now requires you to pass a valid dataset ID explicitly.
- Reference datasets often contain labels such as `dry`, `normal`, and `oily`.
- The local benchmark used for project validation expects curated folders under `skin_types/` with:
  - `Dry/`
  - `Oily/`
  - `Combination/`

Use this folder for:
- reference data inspection
- future retraining experiments
- manual curation before moving selected images into the benchmark folders

Recommended workflow:
1. Review candidate source images here.
2. Copy `skin_types/curation_manifest.template.csv` to `skin_types/curation_manifest.csv`.
3. Fill in `source_path` and the reviewed `target_label`.
4. Run `python backend/tools/validation/import_skin_type_curation.py --manifest backend/assets/data/skin_type_skincare_recommendation/skin_types/curation_manifest.csv`.

Do not treat `skin_types_hf/` as proof of benchmark coverage.
