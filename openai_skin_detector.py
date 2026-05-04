from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from PIL import Image, UnidentifiedImageError


CONDITIONS = [
    "acne",
    "rosacea",
    "eczema",
    "fungal infection",
    "allergic rash",
    "uncertain",
]

JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "most_likely": {
            "type": "string",
            "enum": CONDITIONS,
            "description": "The most likely condition from the allowed list, or uncertain.",
        },
        "confidence": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Educational confidence score from 0 to 100.",
        },
        "possible_conditions": {
            "type": "array",
            "items": {"type": "string", "enum": CONDITIONS},
            "description": "Ranked possible conditions from the allowed list.",
        },
        "visual_clues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Visible features noticed in the image.",
        },
        "reasoning": {
            "type": "string",
            "description": "Brief non-diagnostic reasoning based on visual clues and symptoms.",
        },
        "recommendation": {
            "type": "string",
            "description": "General next step or care recommendation.",
        },
        "warning": {
            "type": "string",
            "description": "Safety warning and when to seek medical help.",
        },
    },
    "required": [
        "most_likely",
        "confidence",
        "possible_conditions",
        "visual_clues",
        "reasoning",
        "recommendation",
        "warning",
    ],
    "additionalProperties": False,
}


def load_environment() -> None:
    """Load OPENAI_API_KEY from .env files if present."""
    script_dir = Path(__file__).resolve().parent
    load_dotenv(script_dir / ".env")
    load_dotenv(script_dir / "backend" / ".env", override=False)


def validate_image(image_path: Path) -> str:
    """Validate the local image and return its MIME type."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Path is not a file: {image_path}")
    if image_path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Image is larger than the 50 MB OpenAI request limit.")

    try:
        with Image.open(image_path) as image:
            if getattr(image, "is_animated", False):
                raise ValueError("Animated GIFs are not supported. Use a still image.")
            image.verify()
            image_format = (image.format or "").upper()
    except UnidentifiedImageError as exc:
        raise ValueError("File is not a supported image.") from exc

    mime_by_format = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
        "GIF": "image/gif",
    }
    mime_type = mime_by_format.get(image_format) or mimetypes.guess_type(
        image_path.name
    )[0]

    supported = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if mime_type not in supported:
        raise ValueError(
            "Unsupported image type. Use JPG, JPEG, PNG, WEBP, or non-animated GIF."
        )

    return mime_type


def image_to_data_url(image_path: Path, mime_type: str) -> str:
    image_bytes = image_path.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is missing. Add it to your environment or a .env file."
        )

    placeholder_values = {
        "your_api_key_here",
        "your_real_api_key_here",
        "your_openai_api_key_here",
    }
    if api_key.lower() in placeholder_values:
        raise EnvironmentError(
            "OPENAI_API_KEY is still a placeholder. Replace it with your real key "
            "from https://platform.openai.com/api-keys."
        )

    return api_key


def build_prompt(symptoms: str) -> str:
    symptom_text = symptoms.strip() or "No symptom context provided."
    return f"""
Analyze this skin image for a student project.

Rules:
- Do NOT give a medical diagnosis.
- Return structured JSON only.
- Compare only these possibilities: acne, rosacea, eczema, fungal infection, allergic rash.
- If the image or symptoms are not enough, set most_likely to "uncertain".
- If unsure, use a lower confidence score.
- Include confidence score from 0 to 100.
- Do not recommend prescription medication.
- Recommend professional medical care for severe, spreading, painful, infected, or persistent symptoms.

Symptom context from user:
{symptom_text}
""".strip()


def analyze_skin_image(
    image_path: Path,
    symptoms: str,
    model: str,
    detail: str,
) -> dict[str, Any]:
    api_key = get_openai_api_key()

    mime_type = validate_image(image_path)
    image_url = image_to_data_url(image_path, mime_type)
    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a careful educational skin-image triage assistant. "
                    "You are not a doctor. You must avoid diagnosis language and "
                    "must produce only valid JSON matching the requested schema."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": build_prompt(symptoms)},
                    {
                        "type": "input_image",
                        "image_url": image_url,
                        "detail": detail,
                    },
                ],
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "skin_condition_analysis",
                "strict": True,
                "schema": JSON_SCHEMA,
            }
        },
        max_output_tokens=700,
    )

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"OpenAI returned invalid JSON: {response.output_text}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a local skin image with OpenAI Vision and print JSON."
    )
    parser.add_argument("image", help="Path to a local image file.")
    parser.add_argument(
        "--symptoms",
        default="",
        help="Optional symptom context, such as itch, pain, location, and duration.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        help="OpenAI vision-capable model to use.",
    )
    parser.add_argument(
        "--detail",
        choices=["low", "high", "auto"],
        default="high",
        help="Image detail level. Use low for cheaper/faster requests.",
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
            detail=args.detail,
        )
    except (EnvironmentError, FileNotFoundError, ValueError, OpenAIError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
