"""
SkinAI Flask Backend
=====================
Endpoints:
  GET  /api/health          – health check
  GET  /api/status          – model availability
  POST /api/chat            – conversational AI diagnosis (text, session memory)
  POST /api/analyze         – image-only diagnosis (ResNet-18)
  POST /api/analyze-fused   – multimodal diagnosis (image + text, fusion)
  POST /api/analyze-skin-care  – skin-type analysis + routine guidance
  GET  /api/history         – progress history (mock)
  GET  /api/stats           – symptom stats (mock)
  POST /api/progress        – log new progress entry (mock)
"""

import datetime
import numpy as np
import os
import sys
import io
import logging
import tempfile
import shutil
import subprocess
import csv
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Force UTF-8 console output on Windows to prevent Unicode logging crashes
# (emoji/box characters in startup logs can fail under cp1252).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from flask import Flask, jsonify, request
from flask_cors import CORS

# Speech recognition for audio file transcription
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

# Pydub for audio format conversion (requires ffmpeg)
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# imageio-ffmpeg can provide a bundled ffmpeg binary if system ffmpeg is missing.
try:
    import imageio_ffmpeg
    IMAGEIO_FFMPEG_AVAILABLE = True
except ImportError:
    IMAGEIO_FFMPEG_AVAILABLE = False

# ── Configuration from environment ────────────────────────────────────────────
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

DEBUG = FLASK_DEBUG  # verbose logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from inference import get_inference_pipeline
from inference.config import (
    SEVERITY_METADATA_PATH,
    SEVERITY_MODEL_PATH,
    SKIN_TYPE_LABEL_MAP_PATH,
    SKIN_TYPE_MODEL_PATH,
    get_model_status,
)
from inference.skin_type_model import get_skin_type_model
from inference.severity_model import get_severity_model
from inference.knowledge_base import (
    SEVERITY_INFO, LIFESTYLE_ADVICE, CAUSE_INFO, 
    HEALING_INFO, WORSENING_INFO, DISEASE_KNOWLEDGE,
    SKIN_TYPE_INFO, DISEASE_ROUTINES, DISEASE_TRIGGERS
)

from services.supabase_service import SupabaseService

app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers="*",
    methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
)

# Selected ffmpeg binary path (if discovered by _configure_pydub_ffmpeg)
FFMPEG_BINARY_PATH = None

def _configure_pydub_ffmpeg() -> None:
    """
    Best-effort ffmpeg discovery for audio conversion.
    """
    global FFMPEG_BINARY_PATH

    candidates = []
    env_path = os.getenv("FFMPEG_BINARY")
    if env_path:
        candidates.append(Path(env_path))

    local_ffmpeg_dir = Path(__file__).parent / "ffmpeg"
    candidates.extend([
        local_ffmpeg_dir / "ffmpeg.exe",
        local_ffmpeg_dir / "bin" / "ffmpeg.exe",
        local_ffmpeg_dir / "ffmpeg",
        local_ffmpeg_dir / "bin" / "ffmpeg",
    ])

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        candidates.append(Path(system_ffmpeg))

    if IMAGEIO_FFMPEG_AVAILABLE:
        try:
            bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            if bundled_ffmpeg:
                candidates.append(Path(bundled_ffmpeg))
        except Exception as exc:
            logger.debug(f"imageio-ffmpeg lookup failed: {exc}")

    try:
        # Recursive search for any ffmpeg.exe in the local ffmpeg directory
        for found in local_ffmpeg_dir.rglob("ffmpeg.exe"):
            if found.is_file():
                candidates.append(found)
                # Don't break yet, we might find a better one if needed, 
                # but for now we'll take the first real file we find.
                break
    except Exception as exc:
        logger.debug(f"Local ffmpeg rglob failed: {exc}")

    selected = next((p for p in candidates if p and p.exists()), None)
    FFMPEG_BINARY_PATH = str(selected) if selected else None

    if selected:
        if PYDUB_AVAILABLE:
            AudioSegment.converter = str(selected)
            ffprobe_candidate = selected.with_name(
                "ffprobe.exe" if selected.suffix.lower() == ".exe" else "ffprobe"
            )
            if ffprobe_candidate.exists():
                AudioSegment.ffprobe = str(ffprobe_candidate)
        logger.info(f"Configured ffmpeg binary: {selected}")
    else:
        logger.warning(
            "ffmpeg binary not found. Non-WAV audio transcription may fail. "
            "Install ffmpeg or set FFMPEG_BINARY."
        )


def _transcribe_uploaded_audio(audio_file) -> tuple[str, str, str | None]:
    """
    Returns: (transcript, transcription_status, transcription_error)
    """
    if not audio_file:
        return "", "not_requested", None

    if not SPEECH_RECOGNITION_AVAILABLE:
        return "", "speech_recognition_unavailable", (
            "SpeechRecognition is not available on the backend."
        )

    tmp_original_path = None
    wav_path = None
    created_paths = set()

    try:
        original_filename = audio_file.filename or "audio.wav"
        file_ext = os.path.splitext(original_filename)[1].lower() or ".wav"

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_original:
            audio_file.save(tmp_original.name)
            tmp_original_path = tmp_original.name
            created_paths.add(tmp_original_path)

        wav_path = tmp_original_path
        if file_ext not in [".wav", ".wave"]:
            if not FFMPEG_BINARY_PATH and not PYDUB_AVAILABLE:
                return "", "unsupported_format", (
                    f"Unsupported audio format '{file_ext}'. Upload a WAV file or enable ffmpeg conversion."
                )

            try:
                logger.info(f"Converting {file_ext} audio to WAV")
                wav_path = tmp_original_path.rsplit(".", 1)[0] + ".wav"
                if FFMPEG_BINARY_PATH:
                    # Use ffmpeg directly so conversion works even when ffprobe is unavailable.
                    cmd = [
                        FFMPEG_BINARY_PATH,
                        "-y",
                        "-i",
                        tmp_original_path,
                        "-ac",
                        "1",
                        "-ar",
                        "16000",
                        wav_path,
                    ]
                    proc = subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    if proc.returncode != 0:
                        err_text = (proc.stderr or "").strip()
                        raise RuntimeError(err_text or "ffmpeg conversion failed")
                else:
                    audio = AudioSegment.from_file(tmp_original_path)
                    audio.export(wav_path, format="wav")
                created_paths.add(wav_path)
            except Exception as conv_err:
                return "", "conversion_failed", (
                    f"Failed to convert {file_ext} audio: {conv_err}"
                )

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)

        transcript = recognizer.recognize_google(audio_data, language="en-US").strip()
        if transcript:
            return transcript, "transcribed", None
        return "", "empty_transcript", "No words were detected in the audio."

    except sr.UnknownValueError:
        return "", "not_understood", (
            "Could not understand the voice note. Please speak clearly or try another recording."
        )
    except sr.RequestError as exc:
        return "", "service_error", f"Speech recognition service error: {exc}"
    except Exception as exc:
        return "", "transcription_error", f"Audio transcription failed: {exc}"
    finally:
        for path in created_paths:
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except Exception as cleanup_exc:
                logger.debug(f"Temp file cleanup warning ({path}): {cleanup_exc}")


_configure_pydub_ffmpeg()

# ── Boot inference pipeline ───────────────────────────────────────────────────
try:
    inference_pipeline = get_inference_pipeline()
    print("✅ Inference pipeline ready")
except Exception as exc:
    print(f"❌ Failed to load inference pipeline: {exc}")
    inference_pipeline = None

try:
    skin_type_model = get_skin_type_model(
        model_path=SKIN_TYPE_MODEL_PATH,
        label_map_path=SKIN_TYPE_LABEL_MAP_PATH,
    )
    if skin_type_model.loaded:
        print("Skin-type ConvNeXt model ready")
    else:
        print(f"Skin-type model failed to load: {skin_type_model.load_error}")
except Exception as exc:
    print(f"Failed to initialize skin-type model: {exc}")
    skin_type_model = None

try:
    severity_model = get_severity_model(
        model_path=SEVERITY_MODEL_PATH,
        metadata_path=SEVERITY_METADATA_PATH,
    )
    if severity_model.loaded:
        print("✅ Face skin severity model ready")
    else:
        print(f"Face severity model failed to load: {severity_model.load_error}")
except Exception as exc:
    print(f"Failed to initialize face severity model: {exc}")
    severity_model = None

SEVERITY_TRACK_DIR = Path(__file__).parent / "assets" / "data" / "severity_tracking"
SEVERITY_VISITS_CSV = SEVERITY_TRACK_DIR / "visits.csv"
SEVERITY_WEEKS_JSON = SEVERITY_TRACK_DIR / "_weeks.json"

# ── Mock data (history / stats) ───────────────────────────────────────────────
MOCK_HISTORY = [
    {"week": "Week 1", "date": "2025-11-01", "image_url": "assets/images/week1.png",
     "status": "Bad",      "score": 30,
     "metrics": {"redness": 90, "inflammation": 85, "scaling": 70, "texture": 60}},
    {"week": "Week 2", "date": "2025-11-08", "image_url": "assets/images/week2.png",
     "status": "Poor",     "score": 45,
     "metrics": {"redness": 80, "inflammation": 75, "scaling": 65, "texture": 65}},
    {"week": "Week 3", "date": "2025-11-15", "image_url": "assets/images/week3.png",
     "status": "Improving","score": 60,
     "metrics": {"redness": 60, "inflammation": 55, "scaling": 50, "texture": 70}},
    {"week": "Week 4", "date": "2025-11-22", "image_url": "assets/images/week4.png",
     "status": "Better",   "score": 75,
     "metrics": {"redness": 40, "inflammation": 35, "scaling": 30, "texture": 80}},
    {"week": "Week 5", "date": "2025-11-29", "image_url": "assets/images/week5.png",
     "status": "Good",     "score": 85,
     "metrics": {"redness": 20, "inflammation": 15, "scaling": 10, "texture": 90}},
    {"week": "Week 6", "date": "2025-12-06", "image_url": "assets/images/week6.png",
     "status": "Excellent","score": 95,
     "metrics": {"redness": 5,  "inflammation": 5,  "scaling": 0,  "texture": 95}},
]

MOCK_STATS = {
    "labels": ["Redness", "Itch", "Dryness", "Scaling"],
    "values": [20, 40, 25, 15],
}


# ── Health / status ───────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return jsonify({
        "ok":        True,
        "service":   "skinai-backend",
        "timestamp": datetime.datetime.now().isoformat(),
    })


@app.get("/api/status")
def status():
    return jsonify({
        "service":              "online",
        "models":               get_model_status(),
        "inference_available":  inference_pipeline is not None,
        "skin_type_inference_available": (
            skin_type_model is not None and skin_type_model.loaded
        ),
        "severity_inference_available": (
            severity_model is not None and severity_model.loaded
        ),
        "python_executable":    sys.executable,
        "skin_type_model_error": (
            None
            if skin_type_model is None or skin_type_model.loaded
            else skin_type_model.load_error
        ),
        "severity_model_error": (
            None
            if severity_model is None or severity_model.loaded
            else severity_model.load_error
        ),
        "timestamp":            datetime.datetime.now().isoformat(),
    })


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


def _build_next_steps(
    confidence_level: str,
    symptom_match_score: float | None = None,
    has_transcript: bool = False,
) -> list[str]:
    """
    Provide concise actionable next steps based on signal quality.
    """
    steps = [
        "Track symptoms daily and monitor spread, pain, or discharge.",
        "Follow the routine consistently for 7-14 days unless irritation worsens.",
    ]

    if confidence_level == "low":
        steps.insert(0, "Retake a clearer close-up photo in natural light and re-run analysis.")
    elif confidence_level == "moderate":
        steps.insert(0, "Cross-check diagnosis with symptom progression over the next few days.")
    else:
        steps.insert(0, "Current pattern is consistent with the predicted condition.")

    if symptom_match_score is not None and symptom_match_score < 0.35:
        steps.append("Add a clearer symptom description or voice note for stronger multimodal matching.")

    if not has_transcript:
        steps.append("Optional: include a short symptom note to improve contextual accuracy.")

    steps.append("Seek dermatology care urgently for fever, spreading redness, severe pain, or infection signs.")
    return steps


def _skin_type_profile(skin_type_raw: str) -> dict:
    key = str(skin_type_raw or "").strip().lower().replace(" ", "_")
    return SKIN_TYPE_INFO.get(key, SKIN_TYPE_INFO["unknown"])


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
        text.replace(";", ",")
        .replace("|", ",")
        .replace("\n", ",")
        .replace("\r", ",")
    )
    for token in separators_normalized.split(","):
        cleaned = token.strip().lower()
        if cleaned and cleaned not in tokens:
            tokens.append(cleaned)
    return tokens


def _parse_bool_flag(raw_value: str | None) -> bool:
    if raw_value is None:
        return False
    value = str(raw_value).strip().lower()
    return value in {"1", "true", "yes", "y", "sensitive", "high"}


def _normalize_tags(raw_tags: list[str], synonyms: dict[str, str]) -> list[str]:
    normalized: list[str] = []
    for tag in raw_tags:
        canonical = synonyms.get(tag)
        if canonical is None:
            for key, mapped in synonyms.items():
                if key in tag:
                    canonical = mapped
                    break
        if canonical is None:
            canonical = tag.replace(" ", "_")
        if canonical not in normalized:
            normalized.append(canonical)
    return normalized


def _pretty_label(tag: str) -> str:
    return tag.replace("_", " ").title()


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


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _parse_track_flag(raw_value: str | None) -> bool:
    if raw_value is None:
        return False
    value = str(raw_value).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _append_severity_visit(
    user_id: str,
    severity_level: str,
    severity_score: float,
    confidence: float,
) -> None:
    SEVERITY_TRACK_DIR.mkdir(parents=True, exist_ok=True)

    file_exists = SEVERITY_VISITS_CSV.exists()
    timestamp = datetime.datetime.now().isoformat()

    with open(SEVERITY_VISITS_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "user_id",
                "severity_level",
                "severity_score",
                "confidence",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": timestamp,
                "user_id": user_id,
                "severity_level": severity_level,
                "severity_score": f"{severity_score:.4f}",
                "confidence": f"{confidence:.6f}",
            }
        )


def _build_severity_tracking_summary(user_id: str) -> dict:
    if not SEVERITY_VISITS_CSV.exists():
        return {
            "visits_count": 0,
            "improvement_percent": 0.0,
            "weekly_trend": [],
            "latest_visit": None,
            "files": {
                "visits_csv": str(SEVERITY_VISITS_CSV),
                "weeks_json": str(SEVERITY_WEEKS_JSON),
            },
        }

    rows: list[dict] = []
    with open(SEVERITY_VISITS_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("user_id") or "anonymous") == user_id:
                rows.append(row)

    if not rows:
        return {
            "visits_count": 0,
            "improvement_percent": 0.0,
            "weekly_trend": [],
            "latest_visit": None,
            "files": {
                "visits_csv": str(SEVERITY_VISITS_CSV),
                "weeks_json": str(SEVERITY_WEEKS_JSON),
            },
        }

    rows.sort(key=lambda item: item.get("timestamp", ""))

    first_score = _safe_float(rows[0].get("severity_score"), 0.0)
    latest_score = _safe_float(rows[-1].get("severity_score"), 0.0)

    if first_score > 0:
        # Positive improvement means severity score reduced over time.
        improvement_percent = ((first_score - latest_score) / first_score) * 100.0
    else:
        improvement_percent = 0.0

    week_scores: dict[str, list[float]] = {}
    for row in rows:
        ts = row.get("timestamp", "")
        score = _safe_float(row.get("severity_score"), 0.0)
        try:
            dt = datetime.datetime.fromisoformat(ts)
            iso = dt.isocalendar()
            week_key = f"{iso.year}-W{iso.week:02d}"
        except Exception:
            week_key = "unknown-week"
        week_scores.setdefault(week_key, []).append(score)

    weekly_trend = []
    for week_key in sorted(week_scores.keys()):
        scores = week_scores[week_key]
        avg_score = float(sum(scores) / max(1, len(scores)))
        weekly_trend.append({"week": week_key, "avg_severity_score": round(avg_score, 2)})

    payload = {
        "updated_at": datetime.datetime.now().isoformat(),
        "user_id": user_id,
        "weekly_trend": weekly_trend,
    }
    SEVERITY_TRACK_DIR.mkdir(parents=True, exist_ok=True)
    with open(SEVERITY_WEEKS_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    latest = rows[-1]
    return {
        "visits_count": len(rows),
        "improvement_percent": round(float(improvement_percent), 2),
        "weekly_trend": weekly_trend,
        "latest_visit": {
            "timestamp": latest.get("timestamp"),
            "severity_level": latest.get("severity_level"),
            "severity_score": round(_safe_float(latest.get("severity_score"), 0.0), 2),
            "confidence": round(_safe_float(latest.get("confidence"), 0.0), 4),
        },
        "files": {
            "visits_csv": str(SEVERITY_VISITS_CSV),
            "weeks_json": str(SEVERITY_WEEKS_JSON),
        },
    }


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
    tight_after_wash: bool | None,
    shiny_after_2_3h: bool | None,
) -> str:
    predicted = str(predicted_skin_type or "").strip().lower().replace(" ", "_")
    if predicted not in SKIN_TYPES:
        predicted = "combination"

    if tight_after_wash is None or shiny_after_2_3h is None:
        return predicted
    if tight_after_wash and not shiny_after_2_3h:
        return "dry"
    if shiny_after_2_3h and not tight_after_wash:
        return "oily"
    return "combination"


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


def _build_skin_care_assistant(
    skin_type_raw: str,
    confidence: float,
    concerns_input: list[str],
    allergies_input: list[str],
    goals_input: list[str],
    sensitive_skin: bool,
) -> dict:
    concern_synonyms = {
        "acne": "acne",
        "pimples": "acne",
        "breakout": "acne",
        "breakouts": "acne",
        "redness": "redness",
        "dark spots": "dark_spots",
        "pigmentation": "dark_spots",
        "spots": "dark_spots",
        "dry": "dryness",
        "dryness": "dryness",
        "flaky": "dryness",
        "oiliness": "oiliness",
        "oily": "oiliness",
        "large pores": "large_pores",
        "pores": "large_pores",
        "dullness": "dullness",
        "sensitive": "sensitivity",
        "sensitivity": "sensitivity",
        "texture": "uneven_texture",
        "uneven texture": "uneven_texture",
        "fine lines": "fine_lines",
    }

    goal_synonyms = {
        "glow": "glow",
        "brighten": "brightening",
        "brightening": "brightening",
        "hydration": "hydration",
        "hydrate": "hydration",
        "oil control": "oil_control",
        "reduce oil": "oil_control",
        "reduce acne": "acne_control",
        "acne control": "acne_control",
        "clear acne": "acne_control",
        "reduce redness": "reduce_redness",
        "calm redness": "reduce_redness",
        "anti aging": "anti_aging",
        "anti-aging": "anti_aging",
        "fine lines": "anti_aging",
        "dark spots": "spot_fading",
        "fade spots": "spot_fading",
        "barrier repair": "barrier_repair",
        "repair barrier": "barrier_repair",
    }

    skin_type_defaults = {
        "oily": ["oiliness", "large_pores"],
        "dry": ["dryness", "dullness"],
        "combination": ["oiliness", "dryness", "uneven_texture"],
    }
    default_goals = {
        "oily": ["oil_control", "acne_control"],
        "dry": ["hydration", "barrier_repair"],
        "combination": ["oil_control", "hydration", "glow"],
    }

    key = str(skin_type_raw or "").strip().lower().replace(" ", "_")
    concerns = _normalize_tags(concerns_input, concern_synonyms)
    goals = _normalize_tags(goals_input, goal_synonyms)
    inferred_concerns = skin_type_defaults.get(key, [])
    for concern in inferred_concerns:
        if concern not in concerns:
            concerns.append(concern)
    if not goals:
        goals = default_goals.get(key, ["hydration", "glow"])

    ingredient_rules = {
        "fragrance": ["fragrance", "parfum", "perfume", "essential oil"],
        "salicylic_acid": ["salicylic", "bha"],
        "retinoids": ["retinol", "retinoid", "tretinoin", "adapalene"],
        "benzoyl_peroxide": ["benzoyl peroxide"],
        "niacinamide": ["niacinamide"],
        "vitamin_c": ["vitamin c", "ascorbic"],
        "nuts": ["nut", "almond", "argan"],
        "sulfates": ["sulfate", "sls", "sles"],
        "alcohol_denat": ["alcohol", "ethanol", "alcohol denat"],
    }

    avoid_ingredients: list[str] = []
    for allergy in allergies_input:
        for ingredient_key, cues in ingredient_rules.items():
            if any(cue in allergy for cue in cues):
                label = _pretty_label(ingredient_key)
                if label not in avoid_ingredients:
                    avoid_ingredients.append(label)

    if sensitive_skin:
        for sensitive_avoid in ["Fragrance", "Alcohol Denat", "High-Strength Exfoliants"]:
            if sensitive_avoid not in avoid_ingredients:
                avoid_ingredients.append(sensitive_avoid)

    profile = _skin_type_profile(key)
    routine = {
        "morning": profile["routine"]["morning"],
        "night": profile["routine"]["night"],
        "weekly": "Exfoliate gently 1-2 times per week only if skin is stable.",
    }

    if "acne" in concerns or "acne_control" in goals:
        routine["night"] += " Add acne treatment (salicylic acid or retinoid) on alternate nights if tolerated."
    if "dark_spots" in concerns or "spot_fading" in goals:
        routine["morning"] += " Add antioxidant/brightening step (e.g., vitamin C or azelaic acid) if tolerated."
    if "dryness" in concerns or "hydration" in goals:
        routine["night"] += " Seal hydration with a ceramide-rich moisturizer."
    if sensitive_skin or "sensitivity" in concerns:
        routine["weekly"] = "Skip harsh exfoliation; prioritize barrier-repair products and patch testing."

    product_categories = [
        {"category": "Cleanser", "purpose": "Gentle cleansing without over-stripping"},
        {"category": "Moisturizer", "purpose": "Support barrier and hydration balance"},
        {"category": "Sunscreen SPF 30+", "purpose": "Daily UV protection and spot prevention"},
    ]
    if "acne" in concerns:
        product_categories.append({"category": "Acne Treatment", "purpose": "Control breakouts and reduce inflammation"})
    if "dark_spots" in concerns:
        product_categories.append({"category": "Brightening Serum", "purpose": "Fade uneven tone and post-acne marks"})
    if "fine_lines" in concerns or "anti_aging" in goals:
        product_categories.append({"category": "Night Active", "purpose": "Support collagen and texture refinement"})

    recommendations = []
    for item in product_categories[:6]:
        recommendations.append(
            f"{item['category']}: {item['purpose']}."
        )
    if avoid_ingredients:
        recommendations.append(
            "Avoid products containing: " + ", ".join(avoid_ingredients) + "."
        )

    glow_up_plan = []
    goal_actions = {
        "glow": "Focus on consistent SPF use and hydration for 4-6 weeks.",
        "brightening": "Use one brightening active (vitamin C or azelaic acid) daily if tolerated.",
        "hydration": "Use humectant + ceramide moisturizer morning and night.",
        "oil_control": "Use lightweight non-comedogenic products and control over-cleansing.",
        "acne_control": "Introduce acne active slowly and avoid picking lesions.",
        "reduce_redness": "Use fragrance-free calming products and avoid high-heat exposure.",
        "anti_aging": "Use sunscreen daily and start low-frequency retinoid if tolerated.",
        "spot_fading": "Prioritize sunscreen and brightening actives consistently.",
        "barrier_repair": "Minimize actives temporarily and rebuild with soothing moisturizers.",
    }
    for goal in goals:
        action = goal_actions.get(goal)
        if action and action not in glow_up_plan:
            glow_up_plan.append(action)
    if not glow_up_plan:
        glow_up_plan.append("Stay consistent with a simple routine for at least 4 weeks before changing products.")

    cautions = []
    if sensitive_skin:
        cautions.append("Use one new product at a time with 48-hour patch testing.")
    if confidence < 0.50:
        cautions.append("Model confidence is low. Retake a clear frontal image in natural light.")
    if avoid_ingredients:
        cautions.append("Cross-check product ingredient lists before use.")

    return {
        "visible_concerns": [_pretty_label(item) for item in concerns],
        "goals": [_pretty_label(item) for item in goals],
        "routine": routine,
        "product_categories": product_categories,
        "recommendations": recommendations,
        "glow_up_plan": glow_up_plan,
        "safety_screening": {
            "allergies_reported": allergies_input,
            "sensitivity_reported": sensitive_skin,
            "avoid_ingredients": avoid_ingredients,
            "cautions": cautions,
        },
        "follow_up_questions": [
            "Any active ingredients currently in your routine?",
            "Do you want a low-budget or premium routine?",
        ],
    }


# ── Image analysis (ResNet-18) ────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def analyze():
    """
    Image-only skin disease diagnosis via the automated smart_predict pipeline.
    """
    if request.method == "OPTIONS":
        return "", 204

    pipe = get_inference_pipeline()
    if pipe is None:
        return jsonify({"error": "Inference pipeline unavailable"}), 503

    image_file = request.files.get("image") or request.files.get("file")
    journey_id = request.form.get("journey_id")
    user_id = request.form.get("user_id", "anonymous")
    
    if not image_file:
        return jsonify({"error": "No image provided"}), 400

    image_bytes = image_file.read()
    
    # Journey context lookup
    target_part = "Skin"
    if journey_id:
        try:
            db_part = SupabaseService.get_journey_part(journey_id)
            if db_part: target_part = db_part
        except Exception:
            pass

    # Fully automated prediction
    report = pipe.smart_predict(
        text="", 
        image_bytes=image_bytes, 
        journey_id=journey_id,
        target_body_part=target_part
    )

    # Automated Logging
    if user_id != "anonymous":
        try:
            SupabaseService.save_skin_analysis(
                user_id=user_id,
                image_url="uploaded_via_analyze",
                predicted_disease=report["diagnosis"]["disease"],
                confidence=report["diagnosis"]["confidence"],
                confidence_level=report["diagnosis"]["confidence_level"],
                journey_id=journey_id,
                body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
                model_used="automated_analyze"
            )
        except Exception as e:
            logger.warning(f"Auto-log failed: {e}")

    return jsonify(report)


# ── Speech-to-Text Helper ─────────────────────────────────────────────────────

def transcribe_audio(audio_file) -> str:
    """
    Speech-to-text is now handled on the frontend.
    This function is kept for backwards compatibility but returns empty string.
    """
    logger.info("Audio transcription handled on frontend - backend receives text directly")
    return ""


@app.route("/api/analyze-fused", methods=["POST", "OPTIONS"])
def analyze_fused():
    """
    Multimodal diagnosis: image (ResNet-18) + text (DistilBERT) → fused result.
    Accepts multipart/form-data: 'image' file + 'text' field (transcribed speech from frontend).
    Optionally accepts 'audio' file for server-side transcription.
    """
    if request.method == "OPTIONS":
        return "", 204

    pipe = get_inference_pipeline()
    if pipe is None:
        return jsonify({"error": "Inference pipeline unavailable"}), 503

    image_file = request.files.get("image") or request.files.get("file")
    text = request.form.get("text", "").strip()
    audio_file = request.files.get("audio")
    journey_id = request.form.get("journey_id")
    user_id = request.form.get("user_id", "anonymous")

    if not image_file:
        return jsonify({"error": "No image provided"}), 400

    image_bytes = image_file.read()
    
    transcript = text
    if audio_file and not text:
        transcript, _, _ = _transcribe_uploaded_audio(audio_file)

    # Journey target lookup
    target_part = "Skin"
    if journey_id:
        try:
            db_part = SupabaseService.get_journey_part(journey_id)
            if db_part: target_part = db_part
        except Exception:
            pass

    report = pipe.smart_predict(
        text=transcript, 
        image_bytes=image_bytes, 
        journey_id=journey_id,
        target_body_part=target_part
    )

    # Automated Logging
    if user_id != "anonymous" and report.get("diagnosis"):
        try:
            diag = report["diagnosis"]
            SupabaseService.save_skin_analysis(
                user_id=user_id,
                image_url="uploaded_via_fused_analyze",
                predicted_disease=diag.get("disease", "Unknown"),
                confidence=diag.get("confidence", 0.0),
                confidence_level=diag.get("confidence_level", "low"),
                journey_id=journey_id,
                body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
                model_used="automated_fused"
            )
        except Exception as e:
            logger.warning(f"Auto-log failed: {e}")

    return jsonify(report)


@app.route("/api/analyze-skin-care", methods=["POST", "OPTIONS"])
def analyze_skin_care():
    global skin_type_model

    if request.method == "OPTIONS":
        return "", 204

    if skin_type_model is None or not skin_type_model.loaded:
        try:
            skin_type_model = get_skin_type_model(
                model_path=SKIN_TYPE_MODEL_PATH,
                label_map_path=SKIN_TYPE_LABEL_MAP_PATH,
                force_reload=True,
            )
        except Exception:
            skin_type_model = None

    if skin_type_model is None or not skin_type_model.loaded:
        return jsonify({
            "error": "Skin-type model unavailable",
            "detail": (
                None if skin_type_model is None else skin_type_model.load_error
            ),
        }), 503

    image_file = request.files.get("image") or request.files.get("file")
    if not image_file:
        return jsonify({"error": "No image provided"}), 400

    try:
        prediction = skin_type_model.predict_from_bytes(image_file.read())
    except Exception as exc:
        logger.exception("Skin-type prediction failed")
        return jsonify({"error": f"Skin-type prediction failed: {exc}"}), 500

    allergies_input = [
        item for item in _parse_tag_list(request.form.get("allergies"))
        if item in ALLERGY_LABELS
    ]
    goals_input = [
        item for item in _parse_tag_list(request.form.get("goals"))
        if item in GOAL_LABELS
    ][:3]
    routine_level = _normalize_choice(
        request.form.get("routine_level"), ROUTINE_LEVELS, "simple"
    )
    budget = _normalize_choice(request.form.get("budget"), BUDGET_LEVELS, "medium")
    tight_after_wash = _parse_optional_bool_flag(
        request.form.get("tight_after_wash")
    )
    shiny_after_2_3h = _parse_optional_bool_flag(
        request.form.get("shiny_after_2_3h")
    )

    predicted_skin_type = str(prediction.get("skin_type_raw", "")).strip().lower().replace(" ", "_")
    final_skin_type = _infer_skin_type_from_questions(
        predicted_skin_type=predicted_skin_type,
        tight_after_wash=tight_after_wash,
        shiny_after_2_3h=shiny_after_2_3h,
    )

    confidence = float(prediction.get("confidence", 0.0))
    if final_skin_type != predicted_skin_type:
        confidence = max(0.50, confidence * 0.90)
    confidence_level = _normalize_confidence_level(confidence)

    structured = _build_structured_skin_care_output(
        skin_type=final_skin_type,
        goals_input=goals_input,
        allergies_input=allergies_input,
        routine_level=routine_level,
        budget=budget,
    )
    probabilities = _normalize_probabilities(prediction.get("probabilities", {}))
    note = structured["note"]

    return jsonify({
        # Required final schema
        "skin_type": final_skin_type,
        "skin_type_confidence": confidence,
        "probabilities": probabilities,
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

        # Additional aliases for demo/reporting convenience
        "recommended_ingredients": structured["safe_ingredients"],
        "avoid_ingredients": structured["avoid_ingredients"],
        "routine": structured["routine"],
        "disclaimer": structured["disclaimer"],

        # Compatibility metadata
        "confidence": confidence,
        "confidence_percent": f"{confidence * 100:.1f}%",
        "confidence_level": confidence_level,
        "visible_concerns": structured["visible_concerns"],
        "recommendations_list": structured["recommendations"],
        "model_used": prediction.get("model_name", "convnext_tiny"),
    })


@app.route("/api/analyze-severity", methods=["POST", "OPTIONS"])
def analyze_severity():
    global severity_model

    if request.method == "OPTIONS":
        return "", 204

    if severity_model is None or not severity_model.loaded:
        try:
            severity_model = get_severity_model(
                model_path=SEVERITY_MODEL_PATH,
                metadata_path=SEVERITY_METADATA_PATH,
                force_reload=True,
            )
        except Exception:
            severity_model = None

    if severity_model is None or not severity_model.loaded:
        return jsonify({
            "error": "Severity model unavailable",
            "detail": None if severity_model is None else severity_model.load_error,
        }), 503

    image_file = request.files.get("image") or request.files.get("file")
    if not image_file:
        return jsonify({"error": "No image provided"}), 400

    filename = (image_file.filename or "").strip()
    suffix = Path(filename).suffix.lower()
    allowed_suffixes = {".jpg", ".jpeg", ".png"}
    if suffix and suffix not in allowed_suffixes:
        return jsonify({
            "error": "Unsupported image format",
            "detail": "Allowed formats: .jpg, .jpeg, .png",
        }), 400

    try:
        prediction = severity_model.predict_from_bytes(image_file.read())
    except Exception as exc:
        logger.exception("Severity prediction failed")
        return jsonify({"error": f"Severity prediction failed: {exc}"}), 500

    severity_level = str(prediction.get("severity_level", "Moderate"))
    severity_score = _safe_float(prediction.get("severity_score"), 0.0)
    confidence = _safe_float(prediction.get("confidence"), 0.0)

    tracking_enabled = _parse_track_flag(
        request.form.get("track") or request.args.get("track")
    )
    user_id = (
        request.form.get("user_id") or request.args.get("user_id") or "anonymous"
    ).strip() or "anonymous"

    tracking = None
    if tracking_enabled:
        try:
            _append_severity_visit(
                user_id=user_id,
                severity_level=severity_level,
                severity_score=severity_score,
                confidence=confidence,
            )
            tracking = _build_severity_tracking_summary(user_id)
        except Exception as exc:
            logger.exception("Severity tracking update failed")
            tracking = {
                "error": f"Failed to update tracking data: {exc}",
                "files": {
                    "visits_csv": str(SEVERITY_VISITS_CSV),
                    "weeks_json": str(SEVERITY_WEEKS_JSON),
                },
            }

    return jsonify({
        # Primary output
        "severity_level": severity_level,
        "severity_score": round(severity_score, 2),

        # Model diagnostics
        "confidence": confidence,
        "probabilities": prediction.get("probabilities", {}),
        "score_based_level": prediction.get("score_based_level"),
        "thresholds": prediction.get("thresholds", {}),
        "feature_vector": prediction.get("feature_vector", {}),
        "normalized_features": prediction.get("normalized_features", {}),
        "preprocessing": prediction.get("preprocessing", {}),

        # Compatibility aliases
        "severity_class": severity_level,
        "score": round(severity_score, 2),

        # Optional progress tracking
        "tracking_enabled": tracking_enabled,
        "tracking": tracking,
        "tracking_files": {
            "visits_csv": str(SEVERITY_VISITS_CSV),
            "weeks_json": str(SEVERITY_WEEKS_JSON),
        },
        "timestamp": datetime.datetime.now().isoformat(),
    })


@app.route("/api/smart-scan", methods=["POST", "OPTIONS"])
def smart_scan():
    """
    FULLY AUTOMATED MULTI-MODAL SCAN.
    Coordinates all AI models to provide a comprehensive skin health report in one call.
    Includes consistency checks for progress tracking journeys.
    """
    if request.method == "OPTIONS":
        return "", 204

    try:
        image_file = request.files.get("image") or request.files.get("file")
        text_input = request.form.get("text", "").strip() or request.form.get("message", "").strip()
        user_id = request.form.get("user_id", "anonymous")
        journey_id = request.form.get("journey_id")

        if not image_file and not text_input:
            return jsonify({"error": "Automation requires at least an image or a symptom description."}), 400

        image_bytes = None
        if image_file:
            image_bytes = image_file.read()

        # ── Journey Context Lookup ──
        target_part = "Skin"
        if journey_id:
            try:
                # Real journey lookup
                db_target_part = SupabaseService.get_journey_part(journey_id)
                if db_target_part:
                    target_part = db_target_part
            except Exception:
                logger.warning(f"Could not fetch target part for journey {journey_id}")

        pipe = get_inference_pipeline()
        report = pipe.smart_predict(
            text=text_input, 
            image_bytes=image_bytes, 
            journey_id=journey_id,
            target_body_part=target_part
        )

        # ── Automated Logging ──
        if user_id and user_id != "anonymous":
            try:
                # In a real production app, we would upload to Supabase Storage first and get a URL
                # For this integrated automation, we log the result data with the journey context
                SupabaseService.save_skin_analysis(
                    user_id=user_id,
                    image_url="uploaded_via_smart_scan", # URL would be from storage upload
                    predicted_disease=report["diagnosis"]["disease"],
                    confidence=report["diagnosis"]["confidence"],
                    confidence_level=report["diagnosis"]["confidence_level"],
                    treatments=report["diagnosis"].get("treatments"),
                    journey_id=journey_id,
                    body_part_detected=report.get("anatomical_check", {}).get("detected_part"),
                    model_used="smart_scan_fused"
                )
            except Exception as e:
                logger.warning(f"Failed to auto-log analysis: {e}")

        return jsonify(report)
    except Exception as e:
        logger.exception("Smart scan failed")
        return jsonify({"status": "error", "message": f"Automated analysis failed: {str(e)}"}), 500

# ── New Journey & Profile Endpoints ──

@app.route("/api/profile", methods=["POST"])
def update_profile():
    """Update user personal details for automation."""
    try:
        data = request.json
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400
            
        profile = SupabaseService.update_user_profile(user_id, data)
        return jsonify({
            "status": "success", 
            "message": "Profile updated successfully",
            "profile": profile
        })
    except Exception as e:
        logger.exception("Profile update failed")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/journey/start", methods=["POST"])
def start_journey():
    """Log the beginning of a skin journey (e.g., 'Forehead Acne Tracking')"""
    try:
        data = request.json
        user_id = data.get("user_id")
        title = data.get("title")
        body_part = data.get("body_part", "Face")
        frequency = data.get("frequency", "weekly")
        
        if not user_id or not title:
            return jsonify({"status": "error", "message": "user_id and title are required"}), 400
            
        journey = SupabaseService.create_journey(user_id, title, body_part, frequency)
        return jsonify({
            "status": "success", 
            "message": "Tracking journey started", 
            "journey": journey
        })
    except Exception as e:
        logger.exception("Journey start failed")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/journey/list", methods=["GET"])
def list_journeys():
    """List all progress tracking journeys for a user."""
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "user_id is required"}), 400
            
        journeys = SupabaseService.get_user_journeys(user_id)
        return jsonify({
            "status": "success", 
            "journeys": journeys
        })
    except Exception as e:
        logger.exception("Listing journeys failed")
        return jsonify({"status": "error", "message": str(e)}), 500


# ── Vague Message Detection ───────────────────────────────────────────────────

def is_message_vague(message: str) -> tuple:
    """
    Detect if a symptom message is too vague for confident prediction.
    
    Returns: (is_vague: bool, missing_info: list[str], follow_up_questions: list[str])
    """
    message_lower = message.lower()
    words = message_lower.split()
    word_count = len(words)
    
    # Key symptom indicators
    has_location = any(loc in message_lower for loc in [
        'face', 'arm', 'leg', 'hand', 'foot', 'back', 'chest', 'scalp', 
        'neck', 'elbow', 'knee', 'finger', 'toe', 'body', 'forehead',
        'cheek', 'nose', 'chin', 'shoulder', 'stomach', 'belly', 'skin'
    ])
    
    has_appearance = any(app in message_lower for app in [
        'red', 'white', 'scaly', 'dry', 'flaky', 'oily', 'bumpy', 'pimple',
        'blister', 'patch', 'rash', 'spot', 'lesion', 'sore', 'swollen',
        'inflamed', 'cracked', 'peeling', 'oozing', 'crusty', 'dark'
    ])
    
    has_sensation = any(sens in message_lower for sens in [
        'itch', 'itchy', 'itching', 'pain', 'painful', 'burning', 'sting',
        'tender', 'sore', 'tingling', 'numb', 'hurt', 'discomfort'
    ])
    
    has_duration = any(dur in message_lower for dur in [
        'day', 'week', 'month', 'year', 'hour', 'recently', 'suddenly',
        'chronic', 'long time', 'few days', 'started', 'began', 'since'
    ])
    
    # Calculate completeness score
    info_present = [has_location, has_appearance, has_sensation, has_duration]
    completeness_score = sum(info_present) / 4.0
    
    # Build missing info list
    missing_info = []
    follow_up_questions = []
    
    if not has_location:
        missing_info.append("location")
        follow_up_questions.append("Where is it located?")
    
    if not has_appearance:
        missing_info.append("appearance")
        follow_up_questions.append("What does it look like?")
    
    if not has_sensation:
        missing_info.append("sensation")
        follow_up_questions.append("How does it feel?")
    
    if not has_duration:
        missing_info.append("duration")
        follow_up_questions.append("How long have you had it?")
    
    # Message is vague if: too short OR missing 2+ key details
    is_vague = (word_count < 4) or (completeness_score < 0.5)
    
    return is_vague, missing_info, follow_up_questions


# ── Chat endpoint (DistilBERT + session memory + intent routing) ──────────────

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    """
    Production-grade conversational AI chat endpoint.
    Implements xAI-like behavior: intent routing, session memory, DistilBERT prediction.

    Request body (JSON):
    {
        "session_id": "optional-uuid",
        "message"   : "I have itchy red patches on my arms"
    }

    Response (JSON):
    {
        "session_id"           : str,
        "reply"                : str,
        "predicted_disease"    : str | null,
        "confidence"           : float,
        "confidence_level"     : "high"|"medium"|"low"|"none",
        "needs_more_info"      : bool,
        "follow_up_questions"  : list[str],
        "recommended_treatments": list[{medicine, advice}],
        "model_status"         : str,
    }
    """
    if request.method == "OPTIONS":
        return "", 204

    try:
        from inference.intent_classifier import get_intent_classifier
        from inference.session_manager import get_session_manager

        if request.is_json:
            data = request.get_json(force=True, silent=True) or {}
            user_message = data.get("message", "").strip()
            session_id = data.get("session_id")
            image_bytes = None
        else:
            # Automation: allow form-data for message + image
            user_message = request.form.get("message", "").strip()
            session_id = request.form.get("session_id")
            image_file = request.files.get("image") or request.files.get("file")
            image_bytes = image_file.read() if image_file else None

        # ── Empty message guard ───────────────────────────────────────────────
        if not user_message:
            return jsonify({
                "session_id":           session_id,
                "reply":                "Please describe your symptoms so I can help diagnose your condition.",
                "predicted_disease":    None,
                "confidence":           0.0,
                "confidence_level":     "none",
                "needs_more_info":      True,
                "follow_up_questions":  [],
                "recommended_treatments": [],
                "model_status":         "online",
            }), 400

        # ── Input validation (detect gibberish/non-meaningful text) ───────────
        def is_valid_input(text: str) -> tuple[bool, str]:
            """
            Validate user input - detect gibberish, random characters, etc.
            Returns (is_valid, reason)
            """
            import re
            
            text_lower = text.lower().strip()
            
            # Check for minimum meaningful content
            if len(text) < 2:
                return False, "too_short"
            
            # Common greetings and valid short phrases (allow these)
            VALID_SHORT = {'hi', 'hello', 'hey', 'help', 'bye', 'thanks', 'ok', 'yes', 'no', 'thank you', 'goodbye'}
            if text_lower in VALID_SHORT:
                return True, "greeting"
            
            # Check if mostly alphabetic or common punctuation
            alpha_chars = sum(1 for c in text if c.isalpha() or c in ' .,!?')
            if len(text) > 3 and alpha_chars / len(text) < 0.5:
                return False, "gibberish"
            
            # Detect random character sequences (no vowels, too many consonants)
            vowels = set('aeiouAEIOU')
            consonants = sum(1 for c in text if c.isalpha() and c not in vowels)
            vowel_count = sum(1 for c in text if c in vowels)
            
            # If text is longer than 4 chars and has no vowels = likely gibberish
            if len(text) > 4 and vowel_count == 0:
                return False, "gibberish"
            
            # If consonant to vowel ratio is too high (>5:1) = likely gibberish
            if vowel_count > 0 and consonants / vowel_count > 6:
                return False, "gibberish"
            
            # Check for repeating characters (like "aaaaaaa")
            if re.search(r'(.)\1{4,}', text):
                return False, "gibberish"
            
            # Check for random uppercase mixed with lowercase (like "fgDFDTYAFscYHAG")
            if len(text) > 5:
                upper_count = sum(1 for c in text if c.isupper())
                lower_count = sum(1 for c in text if c.islower())
                if upper_count > 2 and lower_count > 2 and 0.3 < upper_count / len(text) < 0.7:
                    # Random mix of upper/lower - likely gibberish
                    if not any(word in text.lower() for word in ['i', 'my', 'is', 'have', 'the', 'skin', 'red', 'itchy']):
                        return False, "gibberish"
            
            return True, "valid"
        
        is_valid, validation_reason = is_valid_input(user_message)
        
        if not is_valid:
            return jsonify({
                "session_id":           session_id,
                "reply":                "I didn't quite understand that. Could you please describe your skin symptoms in more detail? For example: location, appearance (red, scaly, bumpy), and any sensations (itchy, painful).",
                "predicted_disease":    None,
                "confidence":           0.0,
                "confidence_level":     "none",
                "needs_more_info":      True,
                "follow_up_questions":  ["What skin symptoms are you experiencing?"],
                "recommended_treatments": [],
                "model_status":         "online",
            })

        # ── Intent classification ─────────────────────────────────────────────
        try:
            intent_clf = get_intent_classifier()
            intent, intent_conf = intent_clf.predict(user_message)
        except Exception as exc:
            if DEBUG:
                print(f"Intent classifier error: {exc}")
            intent, intent_conf = "symptom_description", 0.5

        # ── Session management ────────────────────────────────────────────────
        session_mgr = get_session_manager()
        session = session_mgr.get_session(session_id) if session_id else None
        if not session:
            session_id = session_mgr.create_session(session_id)
            session = session_mgr.get_session(session_id)

        # Log user message
        session.add_message("user", user_message)

        # ── Smart intent override rules ───────────────────────────────────────
        # Rule 1: Short follow-up with existing high-confidence prediction
        #         → treat as clarification, not re-prediction
        if (
            session.last_predicted_disease is not None
            and len(user_message.split()) <= 8
            and intent == "symptom_description"
            and session.last_confidence >= 0.60
        ):
            intent = "clarify_existing"

        # Rule 2: Treatment-related keywords + existing prediction
        #         → switch to ask_treatment (but NOT if already a specific intent)
        TREATMENT_KEYWORDS = [
            "treatment", "apply", "use the", "dosage", "dose", "how should i apply",
            "medicine", "ointment", "cream", "frequency", "how many times",
            "per day", "how often", "for how long", "times a day",
            "remedy", "cure", "fix it", "emollient", "lotion", "medication",
        ]
        
        # Exclude these phrases from treatment detection
        EXCLUDE_TREATMENT = ['what can you do', 'how can you help', 'what do you do']
        
        # Only override to treatment if intent is not already specific
        NON_OVERRIDE_INTENTS = ['ask_severity', 'ask_advice', 'ask_causes', 'ask_about_disease', 'other']
        
        lowered = user_message.lower()
        is_excluded = any(ex in lowered for ex in EXCLUDE_TREATMENT)
        
        if session.last_predicted_disease and intent not in NON_OVERRIDE_INTENTS and not is_excluded:
            if any(k in lowered for k in TREATMENT_KEYWORDS):
                intent = "ask_treatment"
        
        # Rule 3: Severity-related keywords → ask_severity
        SEVERITY_KEYWORDS = [
            'serious', 'dangerous', 'worried', 'severe', 'bad', 'worse',
            'emergency', 'urgent', 'hospital', 'harm', 'safe', 'normal'
        ]
        if session.last_predicted_disease:
            lowered = user_message.lower()
            if any(k in lowered for k in SEVERITY_KEYWORDS) and intent == 'symptom_description':
                intent = "ask_severity"
        
        # Rule 4: Advice-related keywords → ask_advice
        ADVICE_KEYWORDS = [
            'else can i', 'what else', 'tips', 'advice', 'lifestyle',
            'home remedy', 'home remedies', 'prevent', 'avoid', 'help my skin',
            'daily', 'routine', 'foods', 'diet'
        ]
        if session.last_predicted_disease:
            lowered = user_message.lower()
            if any(k in lowered for k in ADVICE_KEYWORDS) and intent not in NON_OVERRIDE_INTENTS:
                intent = "ask_advice"
        
        # Rule 5: Cause-related keywords → ask_causes
        CAUSE_KEYWORDS = [
            'cause', 'causes', 'why do i', 'how did i get', 'trigger',
            'contagious', 'spread', 'genetic', 'hereditary', 'started'
        ]
        if session.last_predicted_disease:
            lowered = user_message.lower()
            if any(k in lowered for k in CAUSE_KEYWORDS) and intent not in NON_OVERRIDE_INTENTS:
                intent = "ask_causes"

        # ── Automated Image Analysis (if present) ─────────────────────────────
        automated_result = None
        if image_bytes:
            try:
                automated_result = inference_pipeline.smart_predict(user_message, image_bytes)
                # Sync intent if we have an image
                if automated_result["diagnosis"]["confidence"] > 0.4:
                    intent = "symptom_description"
            except Exception as e:
                logger.error(f"Chat automated scan failed: {e}")

        # ── Build response skeleton ───────────────────────────────────────────
        response: dict = {
            "session_id":            session_id,
            "predicted_disease":     None,
            "confidence":            0.0,
            "confidence_level":      "none",
            "needs_more_info":       False,
            "follow_up_questions":   [],
            "recommended_treatments": [],
            "reply":                 "",
            "model_status":          "online",
            "automated_scan":        automated_result,
        }

        # ── Intent routing ────────────────────────────────────────────────────

        if intent == "symptom_description":
            # ──────────────────────────────────────────────────────────────────
            # Run prediction (either automated or text-only)
            if automated_result:
                # Use results from smart scan
                diag_res = automated_result["diagnosis"]
                disease = diag_res["disease"]
                confidence = diag_res["confidence"]
                probs = np.array(list(diag_res.get("top3_predictions", {}).values())) # simplistic mapping
            else:
                disease, confidence, probs = inference_pipeline._text_probs(user_message)
            
            # ──────────────────────────────────────────────────────────────────
            # Vagueness check (skip if image is present - automation)
            if automated_result:
                is_vague = False
                missing_info = []
                vague_followup = []
            else:
                is_vague, missing_info, vague_followup = is_message_vague(user_message)
            
            if is_vague and len(missing_info) >= 3 and not automated_result:
                # Very vague message — need more info before prediction
                response.update({
                    "predicted_disease":     None,
                    "confidence":            0.0,
                    "confidence_level":      "none",
                    "needs_more_info":       True,
                    "follow_up_questions":   [],
                    "recommended_treatments": [],
                    "reply": (
                        "I'd like to help! Could you tell me a bit more about what you're experiencing?\n\n"
                        "For example, what does it look like, how does it feel, and where is it on your body?"
                    ),
                    "model_status":          "online",
                })
            elif inference_pipeline:
                # Run DistilBERT disease prediction
                try:
                    result     = inference_pipeline.predict_disease(user_message)
                    disease    = result.get("disease")
                    confidence = result.get("confidence", 0.0)
                    treatments = result.get("treatments", [])
                    followup   = result.get("followup_questions", [])
                    model_used = result.get("model_used", "unknown")

                    # Boost follow-up with specific missing info
                    if is_vague and vague_followup:
                        followup = vague_followup[:2] + followup[:1]

                    # Update session memory
                    session_mgr.update_session(
                        session_id,
                        last_predicted_disease=disease,
                        last_confidence=confidence,
                    )

                    # Confidence tier
                    if confidence >= 0.70:
                        confidence_level = "high"
                        certainty_text   = "Based on your symptoms, I believe this is"
                    elif confidence >= 0.45:
                        confidence_level = "medium"
                        certainty_text   = "Based on your description, this appears to be"
                    else:
                        confidence_level = "low"
                        certainty_text   = "Your symptoms suggest this might be"

                    # Compose reply - conversational style like ChatGPT
                    # Don't dump treatments immediately, let user ask
                    if confidence >= 0.70:
                        reply = (
                            f"\n\n{certainty_text} **{disease}**.\n\n"
                            f"This is a common skin condition that's typically manageable with proper care.\n\n"
                            f"Would you like to know about treatments, causes, or tips for managing it?"
                        )
                        needs_more_info = False
                        # Clear treatments from initial response - user should ask
                        treatments = []
                    elif confidence >= 0.45:
                        reply = (
                            f"\n\n{certainty_text} **{disease}**.\n\n"
                            f"Could you tell me a bit more to help me give you better guidance? "
                            f"How long have you had it and how does it feel?"
                        )
                        needs_more_info = True
                        treatments = []
                    else:
                        # Low confidence - but still show the prediction!
                        # Only ask for more info if the message was actually vague
                        if is_vague and missing_info:
                            # Message is actually vague - ask for more details
                            reply = (
                                f"\n\nBased on what you've shared, this could be **{disease}**.\n\n"
                                f"Could you tell me more about what it looks like and how it feels? "
                                f"That will help me give you better guidance."
                            )
                            followup = []
                            needs_more_info = True
                            treatments = []
                        else:
                            # Message has details, but model confidence is low
                            reply = (
                                f"\n\n{certainty_text} **{disease}**.\n\n"
                                f"This condition can sometimes overlap with other skin conditions, "
                                f"so I'd recommend consulting a dermatologist for a definitive diagnosis.\n\n"
                                f"Would you like to know about treatments, causes, or tips for managing it?"
                            )
                            followup = []
                            needs_more_info = False
                            treatments = []

                    response.update({
                        "predicted_disease":      disease,
                        "confidence":             float(confidence),
                        "confidence_level":       confidence_level,
                        "recommended_treatments": treatments,
                        "follow_up_questions":    followup if needs_more_info else [],
                        "needs_more_info":        needs_more_info,
                        "reply":                  reply,
                        "model_status":           model_used,
                    })

                except Exception as exc:
                    if DEBUG:
                        import traceback; traceback.print_exc()
                    response["reply"] = f"Prediction error: {str(exc)[:100]}"
            else:
                response["reply"] = "The AI service is temporarily unavailable. Please try again later."

        elif intent == "clarify_existing":
            # ──────────────────────────────────────────────────────────────────
            # User added detail to an already-predicted disease
            # ──────────────────────────────────────────────────────────────────
            disease    = session.last_predicted_disease
            treatments = []
            if inference_pipeline and disease:
                treatments = inference_pipeline._get_treatments(disease)

            response.update({
                "predicted_disease":      disease,
                "confidence":             session.last_confidence,
                "confidence_level":       "high" if session.last_confidence >= 0.70 else "medium",
                "recommended_treatments": treatments,
                "needs_more_info":        False,
                "follow_up_questions":    [],
                "reply": (
                    f"Thanks for the additional details. Based on everything you've shared, "
                    f"I still believe this is **{disease}**.\n\n"
                    f"Is there anything specific you'd like to know?\n"
                    f"• Treatment options\n"
                    f"• Causes and triggers\n"
                    f"• Lifestyle advice\n\n"
                    f"If you notice new symptoms like blistering, rapid spreading, or fever, "
                    f"please consult a dermatologist immediately."
                ),
            })

        elif intent == "ask_treatment":
            # ──────────────────────────────────────────────────────────────────
            # "What is the treatment?" — use session memory, don't re-predict
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease

            if disease and inference_pipeline:
                treatments = inference_pipeline._get_treatments(disease)

                usage_guidance = (
                    "Apply a thin layer to affected areas 2–3 times daily. "
                    "Best applied within a few minutes after washing when skin is still slightly damp."
                )

                meds_text = "\n".join(
                    [f"  • **{t['medicine']}** — {t['advice']}" for t in treatments[:4]]
                ) or "No specific treatments in my database."

                response.update({
                    "predicted_disease":      disease,
                    "confidence":             session.last_confidence,
                    "confidence_level":       "high" if session.last_confidence >= 0.70 else "medium",
                    "recommended_treatments": treatments,
                    "reply": (
                        f"\n\nHere are the recommended treatments for **{disease}**:\n\n"
                        f"{meds_text}\n\n"
                        f"💡 **Application tip:** {usage_guidance}\n\n"
                        f"For best results, be consistent with your treatment routine. "
                        f"If you don't see improvement within 2 weeks, please see a dermatologist.\n\n"
                        f"Would you like to know about causes or lifestyle tips?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I'd be happy to suggest treatments, but I need to understand your symptoms first.\n\n"
                        "Could you describe what you're experiencing? For example:\n"
                        "• What does it look like? (red, scaly, bumpy)\n"
                        "• How does it feel? (itchy, painful)\n"
                        "• Where is it located?"
                    ),
                    "follow_up_questions": ["What symptoms are you experiencing?"],
                    "needs_more_info":     True,
                })

        elif intent == "ask_severity":
            # ──────────────────────────────────────────────────────────────────
            # "Is this serious?" — provide condition-specific severity info
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            if disease and disease in SEVERITY_INFO:
                info = SEVERITY_INFO[disease]
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "confidence_level": "high" if session.last_confidence >= 0.70 else "medium",
                    "reply": (
                        f"\n\n**About {disease} Severity:**\n\n"
                        f"📊 **Typical Severity:** {info['level']}\n\n"
                        f"{info['description']}\n\n"
                        f"🚨 **Seek medical attention if you notice:**\n"
                        + "\n".join([f"  • {sign}" for sign in info['warning_signs']]) +
                        f"\n\n✨ **Outlook:** {info['outlook']}\n\n"
                        f"Is there anything else you'd like to know about {disease}?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "⚠️ **Let's follow the proper workflow!**\n\n"
                        "I can't assess severity without knowing your condition first.\n\n"
                        "**Step 1:** Describe your symptoms (e.g., 'I have flaky, scaling patches')\n"
                        "**Step 2:** Then I can assess how serious your condition is\n\n"
                        "What skin symptoms are you experiencing?"
                    ),
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"]
                })

        elif intent == "ask_advice":
            # ──────────────────────────────────────────────────────────────────
            # "What else can I do?" — lifestyle and self-care advice
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            if disease and disease in LIFESTYLE_ADVICE:
                advice = LIFESTYLE_ADVICE[disease]
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "confidence_level": "high" if session.last_confidence >= 0.70 else "medium",
                    "reply": (
                        f"\n\n**Tips for Managing {disease}:**\n\n"
                        f"✅ **What helps:**\n"
                        + "\n".join([f"  • {tip}" for tip in advice['do'][:5]]) +
                        f"\n\n❌ **What to avoid:**\n"
                        + "\n".join([f"  • {tip}" for tip in advice['avoid'][:5]]) +
                        f"\n\n🏠 **Home remedies that may help:**\n"
                        + "\n".join([f"  • {tip}" for tip in advice['home_remedies'][:4]]) +
                        f"\n\nWould you like to know anything else about managing {disease}?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "⚠️ **Let's follow the proper workflow!**\n\n"
                        "I'd love to give you lifestyle advice, but first I need to identify your condition.\n\n"
                        "**Step 1:** Describe your symptoms (e.g., 'I have bumps and dry skin')\n"
                        "**Step 2:** Then I can provide personalized lifestyle tips\n\n"
                        "What skin symptoms are you experiencing?"
                    ),
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"]
                })

        elif intent == "ask_causes":
            # ──────────────────────────────────────────────────────────────────
            # "What causes this?" — explain causes and triggers
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            if disease and disease in CAUSE_INFO:
                info = CAUSE_INFO[disease]
                contagious_text = "❌ **Not contagious** — you cannot spread this to others." if not info['is_contagious'] else "⚠️ **May be contagious**"
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "confidence_level": "high" if session.last_confidence >= 0.70 else "medium",
                    "reply": (
                        f"\n\n**Understanding {disease}:**\n\n"
                        f"🔬 **Main causes:**\n"
                        + "\n".join([f"  • {cause}" for cause in info['main_causes']]) +
                        f"\n\n⚡ **Common triggers:**\n"
                        + "\n".join([f"  • {trigger}" for trigger in info['triggers'][:6]]) +
                        f"\n\n{contagious_text}\n\n"
                        f"Understanding your triggers can help you prevent flare-ups. "
                        f"Would you like tips on managing {disease}?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I can explain the causes once I know what condition you're dealing with. "
                        "Could you describe your symptoms first?"
                    ),
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"]
                })

        elif intent == "ask_healing":
            # ──────────────────────────────────────────────────────────────────
            # "Is this healing?" "How long to heal?" "Am I getting better?"
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            if disease and disease in HEALING_INFO:
                info = HEALING_INFO[disease]
                cure_text = "✅ This condition **can be cured** with proper treatment." if info['can_cure'] else "This is a **chronic condition** but very manageable with the right care."
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"Great question! Here's what to expect with **{disease}**:\n\n"
                        f"⏱️ **Typical healing time:** {info['timeline']}\n\n"
                        f"**Signs you're improving:**\n"
                        + "\n".join([f"  • {sign}" for sign in info['signs_improving']]) +
                        f"\n\n{cure_text}\n\n"
                        f"💡 {info['factors']}\n\n"
                        f"Is there anything specific about your recovery you'd like to know?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I'd love to tell you about healing expectations, but I need to know your condition first.\n\n"
                        "Could you describe your symptoms? For example:\n"
                        "• What does your skin look like?\n"
                        "• Is it itchy, painful, or burning?"
                    ),
                    "needs_more_info": True,
                })

        elif intent == "ask_worsening":
            # ──────────────────────────────────────────────────────────────────
            # "Is this getting worse?" "What if it spreads?" "Warning signs"
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            if disease and disease in WORSENING_INFO:
                info = WORSENING_INFO[disease]
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"I understand your concern about **{disease}** getting worse. Here's what to watch for:\n\n"
                        f"🚨 **Warning signs to watch:**\n"
                        + "\n".join([f"  • {sign}" for sign in info['warning_signs']]) +
                        f"\n\n⚠️ **When to see a doctor:** {info['when_urgent']}\n\n"
                        f"📍 **About spreading:** {info['spreading']}\n\n"
                        f"💡 **Prevention:** {info['prevention']}\n\n"
                        f"Are you noticing any of these warning signs?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I can definitely help you understand warning signs and what to watch for.\n\n"
                        "First, could you tell me what symptoms you're experiencing? "
                        "That way I can give you specific guidance on what changes might be concerning."
                    ),
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"]
                })

        elif intent == "general_question":
            # ──────────────────────────────────────────────────────────────────
            # General questions - ChatGPT-like informative responses
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            lowered = user_message.lower()
            
            if disease and disease in DISEASE_KNOWLEDGE:
                info = DISEASE_KNOWLEDGE[disease]
                # Context-aware informative response - actually provide information!
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"**{disease}** - {info['overview']}\n\n"
                        f"**Common symptoms:** {info['symptoms']}\n\n"
                        f"**What causes it:** {info['causes']}\n\n"
                        f"**Treatment options:** {info['treatments']}\n\n"
                        f"**Daily tips:** {info['tips']}\n\n"
                        f"Is there anything specific about {disease} you'd like me to explain further?"
                    ),
                })
            elif disease:
                # Fallback for diseases not in knowledge base
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"**{disease}** is a skin condition that can vary in severity and presentation.\n\n"
                        f"For the most accurate information about your specific case, I'd recommend consulting a dermatologist "
                        f"who can examine your skin directly.\n\n"
                        f"In the meantime, what specific aspect would you like to know about - symptoms, causes, or treatments?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I'm a skin care assistant that can help you understand various skin conditions.\n\n"
                        "I have detailed knowledge about **Eczema**, **Dermatitis**, **Psoriasis**, **Acne**, and **Urticaria** "
                        "including their symptoms, causes, treatments, and daily care tips.\n\n"
                        "Describe your symptoms and I'll help identify what might be causing them!"
                    ),
                })

        elif intent == "ask_about_disease":
            # ──────────────────────────────────────────────────────────────────
            # "What is eczema?" or "Tell me about psoriasis"
            # ──────────────────────────────────────────────────────────────────
            # Try to extract disease name from message
            lowered = user_message.lower()
            mentioned_disease = None
            for d_name in ["eczema", "dermatitis", "psoriasis", "acne", "urticaria"]:
                if d_name in lowered:
                    mentioned_disease = d_name.title()
                    break
            
            # Use session disease if no specific one mentioned
            target_disease = mentioned_disease or session.last_predicted_disease
            
            # Check if asking about causes
            if target_disease and any(w in lowered for w in ['cause', 'causes', 'why', 'trigger', 'contagious']):
                if target_disease in CAUSE_INFO:
                    info = CAUSE_INFO[target_disease]
                    contagious_text = "❌ **Not contagious** — you cannot spread this to others." if not info['is_contagious'] else "⚠️ **May be contagious**"
                    response.update({
                        "predicted_disease": target_disease,
                        "confidence": session.last_confidence if target_disease == session.last_predicted_disease else 0.0,
                        "reply": (
                            f"\n\n**About {target_disease}:**\n\n"
                            f"📖 {info['description']}\n\n"
                            f"🔬 **Primary Causes:**\n"
                            + "\n".join([f"  • {cause}" for cause in info['main_causes']]) +
                            f"\n\n⚡ **Common Triggers:**\n"
                            + "\n".join([f"  • {trigger}" for trigger in info['triggers'][:5]]) +
                            f"\n\n{contagious_text}"
                        ),
                    })
                else:
                    response.update({
                        "reply": (
                            "I can provide information about Eczema, Dermatitis, Psoriasis, Acne, or Urticaria. "
                            "Which condition would you like to know about?"
                        ),
                        "follow_up_questions": ["Which skin condition would you like to learn about?"],
                    })
            elif target_disease and target_disease in DISEASE_KNOWLEDGE:
                # General info about the disease
                info = DISEASE_KNOWLEDGE[target_disease]
                response.update({
                    "predicted_disease": target_disease,
                    "confidence": session.last_confidence if target_disease == session.last_predicted_disease else 0.0,
                    "reply": (
                        f"**{target_disease}** - {info['overview']}\n\n"
                        f"**What it looks like:** {info['symptoms']}\n\n"
                        f"**Causes:** {info['causes']}\n\n"
                        f"**Treatment:** {info['treatments']}\n\n"
                        f"Would you like more details about anything specific?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I can provide information about various skin conditions. "
                        "If you describe your symptoms, I can give you personalized guidance!"
                    ),
                    "follow_up_questions": ["What symptoms are you experiencing?"],
                    "needs_more_info": True,
                })

        else:  # "other" — greeting / off-topic / unknown
            lowered = user_message.lower().strip()
            words = lowered.split()
            disease = session.last_predicted_disease
            
            # Common greetings
            GREETINGS = {'hi', 'hello', 'hey', 'hola', 'good morning', 'good afternoon', 'good evening', 'morning', 'afternoon', 'evening'}
            is_greeting = lowered in GREETINGS or any(g in lowered for g in ['hello', 'good morning', 'good afternoon', 'good evening'])
            
            # Check for various conversational patterns
            if any(w in lowered for w in ['thank', 'thanks', 'thx', 'appreciate']):
                if disease:
                    response["reply"] = (
                        f"You're welcome! Happy I could help with your {disease}.\n\n"
                        f"Quick reminders:\n"
                        f"• Stay consistent with treatment\n"
                        f"• Watch for any changes\n"
                        f"• Consult a dermatologist if it persists\n\n"
                        f"Feel free to ask if anything else comes up!"
                    )
                else:
                    response["reply"] = "You're welcome! Let me know if you have any skin concerns I can help with."
                    
            elif any(w in lowered for w in ['bye', 'goodbye', 'see you', 'later', 'take care']):
                response["reply"] = (
                    "Take care! Remember to stick with your treatment routine. "
                    "Feel free to come back anytime you have questions!"
                )
                
            elif any(w in lowered for w in ['help', 'what can you do', 'how do you work', 'what are you', 'what is this']):
                response["reply"] = (
                    "I'm an AI assistant specializing in skin health.\n\n"
                    "I can help identify conditions, recommend treatments, explain causes, "
                    "and provide guidance on when to see a dermatologist.\n\n"
                    "What would you like to know?"
                )
                
            elif is_greeting:
                response["reply"] = (
                    "Hey! 👋 How can I help you today?\n\n"
                    "Feel free to describe any skin concerns you're experiencing, "
                    "or ask me anything about skin conditions."
                )
                
            elif any(w in lowered for w in ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'yea']):
                # Affirmative response - context aware
                if disease:
                    response["reply"] = (
                        f"Great! What would you like to know about {disease}?\n\n"
                        f"I can tell you about treatments, causes, healing time, warning signs, or daily care tips."
                    )
                else:
                    response["reply"] = "Sure! What would you like to know? You can describe your symptoms or ask me anything about skin conditions."
                    
            elif any(w in lowered for w in ['no', 'nope', 'nah', 'not really']):
                # Negative response
                if disease:
                    response["reply"] = (
                        f"No worries! Let me know if you have any other questions about {disease} or anything else skin-related."
                    )
                else:
                    response["reply"] = "No problem! I'm here whenever you need help with any skin concerns."
                    
            elif any(w in lowered for w in ['maybe', 'not sure', 'idk', 'i dont know', "don't know", 'confused']):
                # Uncertain response
                if disease:
                    response["reply"] = (
                        f"That's okay! Based on our conversation about {disease}, here are some things you might want to know:\n\n"
                        f"• How long will it take to heal?\n"
                        f"• What should I watch out for?\n"
                        f"• Any tips for daily care?\n\n"
                        f"Just pick one or ask something else!"
                    )
                else:
                    response["reply"] = (
                        "No worries, I can help you figure this out!\n\n"
                        "Try describing what you're experiencing:\n"
                        "• What does it look like?\n"
                        "• How does it feel?\n"
                        "• Where is it on your body?"
                    )
                    
            elif any(w in lowered for w in ['doctor', 'dermatologist', 'hospital', 'clinic', 'appointment']):
                # Questions about professional care
                if disease:
                    response["reply"] = (
                        f"Good thinking to consider professional help for {disease}!\n\n"
                        f"**When to see a dermatologist:**\n"
                        f"• If symptoms aren't improving after 2 weeks of treatment\n"
                        f"• If the condition is spreading or getting worse\n"
                        f"• If you notice signs of infection\n"
                        f"• If it's affecting your quality of life\n\n"
                        f"A dermatologist can prescribe stronger treatments and provide a proper diagnosis. Would you like tips on what to tell them?"
                    )
                else:
                    response["reply"] = (
                        "Seeing a dermatologist is always a good idea for persistent skin issues!\n\n"
                        "They can provide:\n"
                        "• Accurate diagnosis\n"
                        "• Prescription treatments\n"
                        "• Personalized care plans\n\n"
                        "In the meantime, would you like to describe your symptoms? I can give you some initial guidance."
                    )
                    
            elif any(w in lowered for w in ['worse', 'bad', 'spreading', 'getting bigger', 'more']):
                # Concerns about worsening
                if disease:
                    response["reply"] = (
                        f"I understand you're worried about {disease} getting worse. That's a valid concern.\n\n"
                        f"Would you like me to tell you:\n"
                        f"• Warning signs to watch for?\n"
                        f"• When you should see a doctor?\n"
                        f"• What might be causing it to flare up?"
                    )
                else:
                    response["reply"] = (
                        "I hear your concern about things getting worse. To help you better, could you describe what's happening?\n\n"
                        "Tell me:\n"
                        "• What does it look like now?\n"
                        "• How has it changed?\n"
                        "• Any other symptoms?"
                    )
                    
            elif any(w in lowered for w in ['better', 'improving', 'healing', 'working']):
                # Questions about improvement
                if disease:
                    response["reply"] = (
                        f"Great that you're thinking about progress! For {disease}:\n\n"
                        f"**Signs of improvement:**\n"
                        f"• Less itching/discomfort\n"
                        f"• Reduced redness or swelling\n"
                        f"• Affected area getting smaller\n\n"
                        f"Would you like to know typical healing timelines or what else you can do to speed recovery?"
                    )
                else:
                    response["reply"] = (
                        "I'd be happy to help you understand if things are improving!\n\n"
                        "Could you first describe what you're dealing with? Then I can tell you what improvement typically looks like for your specific situation."
                    )
                    
            else:
                # General fallback - be helpful and conversational
                if disease:
                    response["reply"] = (
                        f"I'm here to help with any questions about {disease} or skin care in general.\n\n"
                        f"Some things I can help with:\n"
                        f"• Is it healing properly?\n"
                        f"• What warning signs should I watch for?\n"
                        f"• How can I manage it day-to-day?\n"
                        f"• Should I see a doctor?\n\n"
                        f"What's on your mind?"
                    )
                else:
                    response["reply"] = (
                        "I'm your skin care assistant - I'm here to help!\n\n"
                        "I can answer questions about:\n"
                        "• Common skin conditions (eczema, psoriasis, acne, etc.)\n"
                        "• Treatments and medications\n"
                        "• Healing expectations\n"
                        "• When to see a doctor\n\n"
                        "What would you like to know? Or just describe your symptoms and I'll help identify what might be going on."
                    )
            response["follow_up_questions"] = []

        # ── Log reply and return ──────────────────────────────────────────────
        session.add_message("assistant", response.get("reply", ""))
        return jsonify(response)

    except Exception as exc:
        if DEBUG:
            import traceback; traceback.print_exc()
        return jsonify({
            "reply":                 f"An internal error occurred: {str(exc)[:100]}",
            "predicted_disease":     None,
            "confidence":            0.0,
            "confidence_level":      "none",
            "recommended_treatments": [],
            "follow_up_questions":   [],
            "needs_more_info":       True,
            "model_status":          "error",
        }), 500


# ── History / stats / progress (mock) ─────────────────────────────────────────

@app.route("/api/history", methods=["GET"])
def history():
    return jsonify(MOCK_HISTORY)


@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(MOCK_STATS)


@app.route("/api/progress", methods=["POST"])
def add_progress():
    new_entry = {
        "week":      f"Week {len(MOCK_HISTORY) + 1}",
        "date":      datetime.date.today().isoformat(),
        "image_url": "assets/images/placeholder.png",
        "status":    "Improving",
        "score":     85 + (len(MOCK_HISTORY) % 15),
        "metrics":   {"redness": 10, "inflammation": 10, "scaling": 5, "texture": 92},
    }
    MOCK_HISTORY.append(new_entry)
    return jsonify({
        "message":   "Progress logged successfully",
        "analysis":  "Inflammation has reduced by 15% compared to last week.",
        "new_entry": new_entry,
    })


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║               SKIN CARE ASSISTANT - API SERVER                   ║
╠══════════════════════════════════════════════════════════════════╣
║  Environment: {FLASK_ENV:<15}                                    ║
║  Debug Mode:  {str(FLASK_DEBUG):<15}                             ║
║  Server:      http://{HOST}:{PORT}                               ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=FLASK_DEBUG, port=PORT, host=HOST)
