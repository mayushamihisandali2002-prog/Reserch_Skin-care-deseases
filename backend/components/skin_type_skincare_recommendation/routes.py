import logging
from pathlib import Path

from flask import jsonify, request

from inference.config import (
    SKIN_TYPE_LABEL_MAP_PATH,
    SKIN_TYPE_MODEL_PATH,
)

from . import get_skin_type_model


logger = logging.getLogger(__name__)


def _sorted_probability_pairs(probabilities: dict[str, float]) -> list[tuple[str, float]]:
    pairs: list[tuple[str, float]] = []
    if not isinstance(probabilities, dict):
        return pairs

    for key, value in probabilities.items():
        try:
            pairs.append((str(key).strip(), float(value)))
        except Exception:
            continue
    pairs.sort(key=lambda item: item[1], reverse=True)
    return pairs


def _top_probability_gap(probabilities: dict[str, float]) -> float:
    pairs = _sorted_probability_pairs(probabilities)
    if len(pairs) < 2:
        return pairs[0][1] if pairs else 0.0
    return max(0.0, float(pairs[0][1]) - float(pairs[1][1]))


def _top_predictions(probabilities: dict[str, float], limit: int = 3) -> list[dict[str, float | str]]:
    pairs = _sorted_probability_pairs(probabilities)[:limit]
    return [
        {
            "label": label,
            "probability": round(float(probability), 4),
        }
        for label, probability in pairs
    ]


def _build_skin_type_review(
    *,
    confidence: float,
    top_gap: float,
    questionnaire_adjusted: bool,
    questionnaire_complete: bool,
) -> tuple[bool, list[str], list[str]]:
    reasons: list[str] = []
    steps: list[str] = []

    if confidence < 0.60:
        reasons.append("Low skin-type confidence")
    if top_gap < 0.10:
        reasons.append("Top skin-type probabilities are too close")
    if questionnaire_adjusted:
        reasons.append("Questionnaire answers changed the final skin-type assignment")

    if confidence < 0.60 or top_gap < 0.10:
        steps.append(
            "Retake a front-facing photo in even natural light without makeup, filters, or heavy shadows."
        )
    if not questionnaire_complete:
        steps.append(
            "Answer the wash-tightness and 2-3 hour shine questions to improve routine personalization."
        )
    steps.append("Use this output for cosmetic routine planning only, not disease diagnosis.")
    steps.append("If active rash, acne flare, or irritation is present, prioritize the diagnosis flow first.")

    return (len(reasons) > 0), reasons, list(dict.fromkeys(steps))[:4]


def _normalize_confidence_level(confidence: float, provided: str | None = None) -> str:
    """
    Normalize confidence band for consistent UI handling.
    """
    if provided:
        val = str(provided).strip().lower()
        if val in {"high", "moderate", "medium", "low"}:
            return "moderate" if val == "medium" else val

    if confidence >= 0.75:
        return "high"
    if confidence >= 0.50:
        return "moderate"
    return "low"


def _parse_tag_list(raw_value: str | None) -> list[str]:
    """
    Parse user-entered list values (comma/semicolon/newline separated).
    """
    if raw_value is None:
        return []

    text = str(raw_value).strip()
    if not text:
        return []

    tokens: list[str] = []
    separators_normalized = (
        text.replace(";", ",").replace("|", ",").replace("\n", ",").replace("\r", ",")
    )
    for token in separators_normalized.split(","):
        cleaned = token.strip().lower()
        if cleaned and cleaned not in tokens:
            tokens.append(cleaned)
    return tokens


def _parse_optional_bool_flag(raw_value: str | None) -> bool | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip().lower()
    if value in {"1", "true", "yes", "y"}:
        return True
    if value in {"0", "false", "no", "n"}:
        return False
    return None


def _normalize_choice(raw_value: str | None, allowed: set[str], default: str) -> str:
    if raw_value is None:
        return default
    value = str(raw_value).strip().lower()
    return value if value in allowed else default


def _to_display_terms(values: list[str], label_map: dict[str, str]) -> list[str]:
    result: list[str] = []
    for value in values:
        term = label_map.get(value, value.replace("_", " "))
        if term not in result:
            result.append(term)
    return result


def _normalize_probabilities(probabilities: dict) -> dict[str, float]:
    normalized: dict[str, float] = {}
    if not isinstance(probabilities, dict):
        return normalized
    for key, value in probabilities.items():
        label = str(key).strip().lower().replace(" ", "_")
        label = label.replace("-", "_")
        normalized[label] = float(value)
    return normalized


def _infer_skin_type_from_questions(
    predicted_skin_type: str,
    confidence: float,
    tight_after_wash: bool | None,
    shiny_after_2_3h: bool | None,
) -> str:
    predicted = str(predicted_skin_type or "").strip().lower().replace(" ", "_")
    if predicted not in SKIN_TYPES:
        predicted = "combination"

    if tight_after_wash is None or shiny_after_2_3h is None:
        return predicted
        
    # If the image model is highly confident, trust the model over the self-reporting
    if confidence >= 0.85:
        return predicted

    if tight_after_wash and not shiny_after_2_3h:
        return "dry"
    if shiny_after_2_3h and not tight_after_wash:
        return "oily"
        
    # If answers are contradicting or negative for both, trust the visual prediction
    return predicted


def _build_structured_skin_care_output(
    skin_type: str,
    goals_input: list[str],
    allergies_input: list[str],
    routine_level: str,
    budget: str,
) -> dict:
    key = str(skin_type or "").strip().lower().replace(" ", "_")
    if key not in SKIN_TYPES:
        key = "combination"

    base_safe_ingredients = {
        "oily": [
            "Niacinamide",
            "Salicylic Acid (BHA)",
            "Oil-free lightweight moisturizer",
            "Gel sunscreen SPF 30+",
        ],
        "dry": [
            "Hyaluronic Acid",
            "Ceramides",
            "Glycerin",
            "Cream moisturizer",
            "Sunscreen SPF 30+",
        ],
        "combination": [
            "Niacinamide",
            "Hyaluronic Acid",
            "Lightweight moisturizer",
            "Sunscreen SPF 30+",
        ],
    }

    goal_safe_additions = {
        "acne_pimples": ["Benzoyl Peroxide (low strength)"],
        "oil_control": ["Zinc PCA"],
        "dryness": ["Panthenol"],
        "redness_irritation": ["Azelaic Acid"],
        "dark_spots": ["Vitamin C (low strength)"],
        "texture_pores": ["PHA exfoliant (gentle)"],
        "wrinkles_anti_aging": ["Retinoid (low strength)"],
    }

    allergy_to_avoid_label = {
        "fragrance": "Fragrance",
        "alcohol_denat": "Alcohol Denat.",
        "essential_oils": "Essential Oils",
        "niacinamide": "Niacinamide",
        "salicylic_acid_bha": "Salicylic Acid (BHA)",
        "aha": "Glycolic/Lactic Acid (AHA)",
        "retinoids": "Retinoids",
        "benzoyl_peroxide": "Benzoyl Peroxide",
        "sunscreen_filters": "Chemical Sunscreen Filters",
    }

    allergy_conflict_tokens = {
        "fragrance": ["fragrance", "perfume", "essential oil"],
        "alcohol_denat": ["alcohol"],
        "essential_oils": ["essential oil"],
        "niacinamide": ["niacinamide"],
        "salicylic_acid_bha": ["salicylic"],
        "aha": ["glycolic", "lactic", "aha", "exfoliant"],
        "retinoids": ["retinoid", "retinol"],
        "benzoyl_peroxide": ["benzoyl peroxide"],
        "sunscreen_filters": ["chemical sunscreen filter"],
    }

    safe_ingredients = list(base_safe_ingredients.get(key, base_safe_ingredients["combination"]))
    for goal in goals_input:
        for ingredient in goal_safe_additions.get(goal, []):
            if ingredient not in safe_ingredients:
                safe_ingredients.append(ingredient)

    avoid_ingredients: list[str] = []
    conflict_tokens: list[str] = []
    for allergy in allergies_input:
        label = allergy_to_avoid_label.get(allergy)
        if label and label not in avoid_ingredients:
            avoid_ingredients.append(label)
        conflict_tokens.extend(allergy_conflict_tokens.get(allergy, []))

    if key == "oily" and "Heavy Oils" not in avoid_ingredients:
        avoid_ingredients.append("Heavy Oils")
    if key == "dry" and "Harsh Foaming Cleansers" not in avoid_ingredients:
        avoid_ingredients.append("Harsh Foaming Cleansers")

    filtered_safe: list[str] = []
    for ingredient in safe_ingredients:
        lowered = ingredient.lower()
        if any(token in lowered for token in conflict_tokens):
            continue
        if ingredient not in filtered_safe:
            filtered_safe.append(ingredient)
    safe_ingredients = filtered_safe or ["Fragrance-free gentle moisturizer"]

    am_steps = ["Gentle cleanser", "Light moisturizer", "Sunscreen SPF 30+"]
    pm_steps = ["Gentle cleanser", "Treatment", "Moisturizer"]

    if key == "oily":
        am_steps[0] = "Oil-control cleanser"
        pm_steps[0] = "Oil-control cleanser"
    if key == "dry":
        am_steps[1] = "Ceramide moisturizer"
        pm_steps[2] = "Barrier-repair moisturizer"

    if routine_level == "full":
        am_steps.insert(1, "Targeted serum")
        pm_steps.insert(1, "Targeted serum")

    if "acne_pimples" in goals_input:
        pm_steps[2 if routine_level == "full" else 1] = "Acne treatment (if tolerated)"
    if "dark_spots" in goals_input:
        am_steps[1 if routine_level == "simple" else 2] = "Brightening serum"
    if "redness_irritation" in goals_input and "Calming serum" not in pm_steps:
        pm_steps.append("Calming serum")

    note = "Cosmetic guidance only; not a medical diagnosis."
    if budget == "low":
        note += " Choose budget-friendly fragrance-free basics."
    elif budget == "flexible":
        note += " You can consider premium formulations if tolerated."

    visible_concerns = _to_display_terms(goals_input, GOAL_LABELS)
    recommendations = [
        f"Safe ingredients to prioritize: {', '.join(safe_ingredients)}.",
        f"Avoid ingredients: {', '.join(avoid_ingredients) if avoid_ingredients else 'none specific'}.",
    ]

    return {
        "safe_ingredients": safe_ingredients,
        "avoid_ingredients": avoid_ingredients,
        "routine": {"AM": am_steps, "PM": pm_steps},
        "visible_concerns": visible_concerns,
        "recommendations": recommendations,
        "disclaimer": note,
        "note": note,
    }


ALLERGY_LABELS = {
    "fragrance": "fragrance",
    "alcohol_denat": "alcohol denat.",
    "essential_oils": "essential oils",
    "niacinamide": "niacinamide",
    "salicylic_acid_bha": "salicylic acid (BHA)",
    "aha": "glycolic/lactic acid (AHA)",
    "retinoids": "retinoids",
    "benzoyl_peroxide": "benzoyl peroxide",
    "sunscreen_filters": "sunscreen filters",
}

GOAL_LABELS = {
    "acne_pimples": "acne / pimples",
    "oil_control": "oil control",
    "dryness": "dryness",
    "redness_irritation": "redness/irritation",
    "dark_spots": "dark spots",
    "texture_pores": "texture / pores",
    "wrinkles_anti_aging": "wrinkles / anti-aging",
}

ROUTINE_LEVELS = {"simple", "full"}
BUDGET_LEVELS = {"low", "medium", "flexible"}
SKIN_TYPES = {"oily", "dry", "combination"}


def register_routes(app) -> None:
    """
    Skin-type based skincare recommendation routes.
    """

    @app.route("/api/analyze-skin-care", methods=["POST", "OPTIONS"])
    def analyze_skin_care():
        if request.method == "OPTIONS":
            return "", 204

        model = get_skin_type_model(
            model_path=SKIN_TYPE_MODEL_PATH,
            label_map_path=SKIN_TYPE_LABEL_MAP_PATH,
        )
        if model is None or not model.loaded:
            try:
                model = get_skin_type_model(
                    model_path=SKIN_TYPE_MODEL_PATH,
                    label_map_path=SKIN_TYPE_LABEL_MAP_PATH,
                    force_reload=True,
                )
            except Exception:
                model = None

        if model is None or not model.loaded:
            return jsonify(
                {
                    "error": "Skin-type model unavailable",
                    "detail": None if model is None else model.load_error,
                }
            ), 503

        image_file = request.files.get("image") or request.files.get("file")
        if not image_file:
            return jsonify({"error": "No image provided"}), 400

        filename = (image_file.filename or "").strip()
        suffix = Path(filename).suffix.lower()
        allowed_suffixes = {".jpg", ".jpeg", ".png"}
        if suffix and suffix not in allowed_suffixes:
            return jsonify(
                {
                    "error": "Unsupported image format",
                    "detail": "Allowed formats: .jpg, .jpeg, .png",
                }
            ), 400

        try:
            prediction = model.predict_from_bytes(image_file.read())
        except Exception as exc:
            msg = str(exc)
            if "cannot identify image file" in msg.lower():
                return jsonify({"error": "Invalid image file format", "detail": msg}), 400
            logger.exception("Skin-type prediction failed")
            return jsonify({"error": f"Skin-type prediction failed: {exc}"}), 500

        allergies_input = [
            item for item in _parse_tag_list(request.form.get("allergies"))
            if item in ALLERGY_LABELS
        ]
        goals_input = [
            item for item in _parse_tag_list(request.form.get("goals")) if item in GOAL_LABELS
        ][:3]
        routine_level = _normalize_choice(
            request.form.get("routine_level"), ROUTINE_LEVELS, "simple"
        )
        budget = _normalize_choice(request.form.get("budget"), BUDGET_LEVELS, "medium")
        tight_after_wash = _parse_optional_bool_flag(request.form.get("tight_after_wash"))
        shiny_after_2_3h = _parse_optional_bool_flag(request.form.get("shiny_after_2_3h"))

        predicted_skin_type = (
            str(prediction.get("skin_type_raw", ""))
            .strip()
            .lower()
            .replace(" ", "_")
        )
        
        confidence = float(prediction.get("confidence", 0.0))

        final_skin_type = _infer_skin_type_from_questions(
            predicted_skin_type=predicted_skin_type,
            confidence=confidence,
            tight_after_wash=tight_after_wash,
            shiny_after_2_3h=shiny_after_2_3h,
        )
        questionnaire_adjusted = final_skin_type != predicted_skin_type
        questionnaire_complete = (
            tight_after_wash is not None and shiny_after_2_3h is not None
        )

        if questionnaire_adjusted:
            confidence = max(0.40, confidence * 0.80)
        confidence_level = _normalize_confidence_level(confidence)

        structured = _build_structured_skin_care_output(
            skin_type=final_skin_type,
            goals_input=goals_input,
            allergies_input=allergies_input,
            routine_level=routine_level,
            budget=budget,
        )
        probabilities = _normalize_probabilities(prediction.get("probabilities", {}))
        top_gap = _top_probability_gap(probabilities)
        top_predictions = _top_predictions(probabilities)
        requires_review, review_reasons, next_steps = _build_skin_type_review(
            confidence=confidence,
            top_gap=top_gap,
            questionnaire_adjusted=questionnaire_adjusted,
            questionnaire_complete=questionnaire_complete,
        )
        note = structured["note"]
        limitations = [
            "No labeled skin-type benchmark is stored locally for this model, so only operational reliability checks are available.",
            "This output is for cosmetic skincare guidance only and is not a medical diagnosis.",
            "Lighting, camera quality, filters, and active inflammation can distort skin-type classification.",
        ]

        return jsonify(
            {
                "skin_type": final_skin_type,
                "model_skin_type": predicted_skin_type,
                "questionnaire_adjusted": questionnaire_adjusted,
                "skin_type_confidence": confidence,
                "probabilities": probabilities,
                "top_predictions": top_predictions,
                "top_probability_gap": round(float(top_gap), 4),
                "user_inputs": {
                    "allergies": _to_display_terms(allergies_input, ALLERGY_LABELS),
                    "goals": _to_display_terms(goals_input, GOAL_LABELS),
                    "routine_level": routine_level,
                    "budget": budget,
                    "tight_after_wash": tight_after_wash,
                    "shiny_after_2_3h": shiny_after_2_3h,
                },
                "recommendations": {
                    "safe_ingredients": structured["safe_ingredients"],
                    "avoid_ingredients": structured["avoid_ingredients"],
                    "routine": structured["routine"],
                },
                "note": note,
                "recommended_ingredients": structured["safe_ingredients"],
                "avoid_ingredients": structured["avoid_ingredients"],
                "routine": structured["routine"],
                "disclaimer": structured["disclaimer"],
                "confidence": confidence,
                "confidence_percent": f"{confidence * 100:.1f}%",
                "confidence_level": confidence_level,
                "validation_status": "operational_only_unlabeled",
                "analysis_scope": "cosmetic_routine_guidance_only",
                "requires_review": requires_review,
                "review_reasons": review_reasons,
                "next_steps": next_steps,
                "limitations": limitations,
                "visible_concerns": structured["visible_concerns"],
                "recommendations_list": structured["recommendations"],
                "model_used": prediction.get("model_name", "convnext_tiny"),
            }
        )
