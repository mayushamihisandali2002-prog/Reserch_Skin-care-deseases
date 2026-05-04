from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
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
            "description": "How the optional symptom text matches or does not match clues.",
        },
        "reasoning": {
            "type": "string",
            "description": "Brief non-diagnostic reasoning.",
        },
        "severity": {
            "type": "string",
            "enum": SEVERITY_LEVELS,
            "description": "Estimated visual severity level.",
        },
        "recommendation": {
            "type": "string",
            "description": "General safe next steps, not prescription treatment.",
        },
        "warning": {
            "type": "string",
            "description": "Must say: This is not a medical diagnosis",
        },
    },
    "required": [
        "most_likely_condition",
        "confidence",
        "possible_conditions",
        "visual_features",
        "symptom_match",
        "reasoning",
        "severity",
        "recommendation",
        "warning",
    ],
    "additionalProperties": False,
    "propertyOrdering": [
        "most_likely_condition",
        "confidence",
        "possible_conditions",
        "visual_features",
        "symptom_match",
        "reasoning",
        "severity",
        "recommendation",
        "warning",
    ],
}


def load_environment() -> None:
    """Load GEMINI_API_KEY from .env files if present."""
    script_dir = Path(__file__).resolve().parent
    load_dotenv(script_dir / ".env")
    load_dotenv(script_dir / "backend" / ".env", override=False)


def get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is missing. Add it to your environment or a .env file."
        )

    placeholder_values = {
        "your_api_key_here",
        "your_gemini_api_key_here",
        "your_real_api_key_here",
    }
    if api_key.lower() in placeholder_values:
        raise EnvironmentError(
            "GEMINI_API_KEY is still a placeholder. Replace it with your real "
            "Gemini key from https://aistudio.google.com/app/apikey."
        )

    return api_key


def image_to_png_bytes(image_path: Path) -> bytes:
    """Open a local image with Pillow and convert it to PNG bytes for Gemini."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Path is not a file: {image_path}")
    if image_path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("Image is larger than 20 MB. Use a smaller image.")

    try:
        with Image.open(image_path) as image:
            if getattr(image, "is_animated", False):
                raise ValueError("Animated images are not supported. Use a still image.")

            image.load()
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGB")

            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()
    except UnidentifiedImageError as exc:
        raise ValueError("File is not a supported image.") from exc


def build_prompt(symptoms: str) -> str:
    symptom_text = symptoms.strip() or "No symptom text provided."
    return f"""
Analyze this skin image for a student educational project.

Rules:
- Do NOT give a medical diagnosis.
- Only suggest possible conditions.
- Compare only these possibilities: acne, rosacea, eczema, fungal infection, allergic reaction.
- If the image or symptom text is not enough, set most_likely_condition to "uncertain".
- Confidence must be realistic and not overconfident.
- Use lower confidence for poor image quality, mixed signs, or missing symptom context.
- Do not recommend prescription medication.
- Return STRICT JSON only.
- The warning field must be exactly: This is not a medical diagnosis

Optional user symptoms:
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
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {response_text}") from exc

    missing = [key for key in JSON_SCHEMA["required"] if key not in result]
    if missing:
        raise ValueError(f"Gemini response is missing required fields: {missing}")

    return result


def analyze_skin_image(image_path: Path, symptoms: str, model: str) -> dict[str, Any]:
    api_key = get_gemini_api_key()
    image_bytes = image_to_png_bytes(image_path)

    client = genai.Client(api_key=api_key)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

    response = client.models.generate_content(
        model=model,
        contents=[image_part, build_prompt(symptoms)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=JSON_SCHEMA,
            temperature=0.2,
        ),
    )

    return parse_json_response(response.text or "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a local skin image with Google Gemini and print JSON."
    )
    parser.add_argument("image", help="Path to a local image file.")
    parser.add_argument(
        "--symptoms",
        default="",
        help="Optional symptoms, such as itch, pain, location, and duration.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        help="Gemini model to use.",
    )
    return parser.parse_args()


def main() -> int:
    load_environment()
    args = parse_args()

    try:
        result = analyze_skin_image(
            image_path=Path(args.image),
            symptoms=args.symptoms,
            model=args.model,
        )
    except (
        EnvironmentError,
        FileNotFoundError,
        ValueError,
        errors.APIError,
        errors.ClientError,
        errors.ServerError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
