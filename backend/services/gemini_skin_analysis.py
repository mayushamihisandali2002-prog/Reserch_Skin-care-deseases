from __future__ import annotations

import io
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, UnidentifiedImageError


CONDITIONS = [
    "acne",
    "rosacea",
    "eczema",
    "fungal infection",
    "allergic reaction",
    "uncertain",
]

SEVERITY_LEVELS = ["mild", "moderate", "severe"]

JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "most_likely_condition": {
            "type": "string",
            "enum": CONDITIONS,
            "description": "Most likely possible condition, or uncertain.",
        },
        "confidence": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Realistic educational confidence score from 0 to 100.",
        },
        "possible_conditions": {
            "type": "array",
            "items": {"type": "string", "enum": CONDITIONS},
            "description": "Ranked possible conditions from the allowed list.",
        },
        "visual_features": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Visible skin features observed in the image.",
        },
        "symptom_match": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Evidence in the image or symptoms matching the condition.",
        },
        "recommendation": {
            "type": "string",
            "description": "Short, helpful educational next step.",
        },
        "reasoning": {
            "type": "string",
            "description": "Concise reasoning for the assistance result.",
        },
        "severity": {
            "type": "string",
            "enum": SEVERITY_LEVELS,
            "description": "Likely clinical severity.",
        },
        "warning": {
            "type": "string",
            "description": "Mandatory non-medical warning.",
        },
    },
    "required": [
        "most_likely_condition",
        "confidence",
        "possible_conditions",
        "visual_features",
        "symptom_match",
        "recommendation",
        "reasoning",
        "severity",
        "warning",
    ],
}


class GeminiSkinAnalysisError(Exception):
    """Raised when Gemini skin analysis cannot complete."""


def load_environment() -> None:
    # Get the absolute path to the backend directory
    backend_dir = Path(__file__).resolve().parents[1]
    env_path = backend_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    else:
        # Fallback to current directory
        load_dotenv(".env", override=True)


def gemini_enabled() -> bool:
    enabled = os.getenv("GEMINI_SKIN_ANALYSIS_ENABLED", "true").strip().lower()
    return enabled not in {"0", "false", "no", "off"}


def get_api_key() -> str:
    load_environment()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    if not api_key:
        raise GeminiSkinAnalysisError("GEMINI_API_KEY is missing from .env file.")
    
    # Debug log (masked for safety)
    print(f"[Gemini] Active Key: {api_key[:10]}...{api_key[-4:]}")
    
    if api_key.lower() in {
        "your_api_key_here",
        "your_gemini_api_key_here",
        "your_real_api_key_here",
    }:
        raise GeminiSkinAnalysisError("GEMINI_API_KEY is still a placeholder.")
    return api_key


def build_prompt(symptoms: str) -> str:
    symptom_text = symptoms.strip() or "No symptom text provided."
    return f"""
Analyze this skin image and symptom text for a student educational project.

You MUST return a JSON object with the following fields:
1. most_likely_condition: (condition name or "uncertain")
2. confidence: (integer 0-100, overall)
3. image_accuracy: (integer 0-100, how clearly the image shows the condition)
4. text_accuracy: (integer 0-100, how well the text matches the image findings)
5. mismatch_detected: (boolean, true if text and image are unrelated or contradictory)
6. relevance_score: (number 0.0 to 1.0, based on how relevant the symptom text is)
7. possible_conditions: (list)
8. visual_features: (list)
9. symptom_match: (list)
10. recommendation: (Instructions for the patient. MUST include: "See a dermatologist, do not ignore.")
11. reasoning: (explanation of the image+text alignment)
12. severity: (mild, moderate, or severe)
13. warning: "This is not a medical diagnosis"

Special Rules:
    - If mismatch_detected is true, the recommendation must focus on the contradiction.
    - Always include the "See a dermatologist" instruction.
    - NEVER use the words "AI", "Gemini", or "Large Language Model". Use "System" instead.
    - Example: Instead of "AI analysis", use "System analysis".

User symptoms:
{symptom_text}
""".strip()


def parse_json_response(response_text: str) -> dict[str, Any]:
    text = response_text.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    if text.startswith("```"):
        text = text.removeprefix("```").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse Gemini JSON: {response_text}")
        raise GeminiSkinAnalysisError(f"Gemini returned invalid JSON format.") from exc

def analyze_skin_image_bytes(
    image_bytes: bytes,
    symptoms: str,
    model: str | None = None,
) -> dict[str, Any]:
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key, transport='rest')

        model_name = model or os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        gemini_model = genai.GenerativeModel(model_name=model_name)
        
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        prompt = build_prompt(symptoms)
        
        response = gemini_model.generate_content(
            [prompt, img],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            )
        )
        
        if not response or not response.text:
            raise GeminiSkinAnalysisError("Gemini returned an empty response.")
            
        result = parse_json_response(response.text)
        
        # Ensure default values and match UI requirements
        defaults = {
            "most_likely_condition": "uncertain",
            "confidence": 0,
            "image_accuracy": 0,
            "text_accuracy": 0,
            "mismatch_detected": False,
            "possible_conditions": [],
            "visual_features": [],
            "symptom_match": [],
            "recommendation": "Please consult a dermatologist for a professional evaluation. Do not ignore your symptoms.",
            "reasoning": "Awaiting more context.",
            "severity": "mild",
            "warning": "This is not a medical diagnosis"
        }
        for key, val in defaults.items():
            if key not in result:
                result[key] = val
                
        return result
        
    except Exception as exc:
        import traceback
        error_msg = str(exc)
        logger.error("Gemini Analysis Error: %s\n%s", error_msg, traceback.format_exc())
        raise GeminiSkinAnalysisError(f"Analysis failed: {error_msg}")


def _display_condition(condition: Any) -> str:
    text = str(condition or "uncertain").replace("_", " ").strip()
    if not text:
        text = "uncertain"
    return text.title()


def _confidence_level(confidence: float) -> str:
    if confidence >= 0.75:
        return "High"
    if confidence >= 0.50:
        return "Medium"
    return "Low"


import logging
logger = logging.getLogger(__name__)


def _severity_score(severity: str) -> float:
    return {"mild": 0.33, "moderate": 0.66, "severe": 0.9}.get(
        severity.lower(),
        0.0,
    )


def build_frontend_report(
    gemini_result: dict[str, Any],
    transcript: str,
    transcription_status: str = "frontend_text",
    transcription_error: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    condition = _display_condition(gemini_result.get("most_likely_condition"))
    confidence_percent = max(0, min(100, int(gemini_result.get("confidence", 0))))
    confidence = confidence_percent / 100.0
    severity = str(gemini_result.get("severity", "mild")).lower()
    possible_conditions = [
        _display_condition(item) for item in gemini_result.get("possible_conditions", [])
    ]
    warning = gemini_result.get("warning") or "This is not a medical diagnosis"
    recommendation = str(gemini_result.get("recommendation", "")).strip()
    reasoning = str(gemini_result.get("reasoning", "")).strip()

    diagnosis = {
        "disease": condition,
        "display_disease": condition,
        "final_diagnosis": condition,
        "diagnostic_status": "uncertain"
        if condition.lower() == "uncertain"
        else "possible_condition",
        "confidence": confidence,
        "confidence_percent": f"{confidence_percent:.1f}%",
        "confidence_level": _confidence_level(confidence),
        "model_used": "gemini",
        "fallback_used": False,
        "medical_disclaimer": "This is not a medical diagnosis",
        "decision_mode": "gemini_multimodal",
        "transcript": transcript,
        "transcription_status": transcription_status,
        "transcription_error": transcription_error,
        "disease_explanation": reasoning,
        "image_accuracy": max(0, min(100, int(gemini_result.get("image_accuracy", 0)))),
        "text_accuracy": max(0, min(100, int(gemini_result.get("text_accuracy", 0)))),
        "mismatch_detected": bool(gemini_result.get("mismatch_detected", False)),
        "visual_features": gemini_result.get("visual_features", []),
        "symptom_match": gemini_result.get("symptom_match", []),
        "matched_symptoms": gemini_result.get("symptom_match", []),
        "possible_conditions": possible_conditions,
        "next_steps": [recommendation] if recommendation else [],
        "recommendations": [recommendation] if recommendation else [],
        "warnings": [warning],
        "requires_dermatologist_review": confidence < 0.70
        or condition.lower() == "uncertain"
        or severity == "severe",
        "review_reasons": [],
    }

    if diagnosis["requires_dermatologist_review"]:
        diagnosis["review_reasons"] = [
            "AI result is only a possible condition and should be reviewed if symptoms persist or worsen."
        ]

    return {
        "status": "success",
        "automation_level": "gemini_multimodal",
        "ai_enhanced": True,
        "summary": reasoning,
        "diagnosis": diagnosis,
        "ai_assistance_result": {
            "disease": condition,
            "confidence": confidence,
            "reasoning": reasoning,
            "warning": warning,
            "is_urgent": severity == "severe",
        },
        "severity": {
            "level": severity,
            "severity_label": severity.title(),
            "score": _severity_score(severity),
            "source": "gemini",
        },
        "quality_check": {"passed": True, "notes": []},
        "raw_gemini_result": gemini_result,
    }
