import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ENV_PATH = REPO_ROOT / "backend/.env"
if BACKEND_ENV_PATH.exists():
    load_dotenv(BACKEND_ENV_PATH, override=False)

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
PILOT_EMAIL = os.getenv("PILOT_EMAIL", "test@skincare.app").strip()
PILOT_PASSWORD = os.getenv("PILOT_PASSWORD", "Test123456").strip()


def _resolve_base_url() -> str:
    configured = os.getenv("PILOT_BASE_URL")
    if configured:
        return configured

    for candidate in ("http://localhost:5001", "http://localhost:5000"):
        try:
            response = requests.get(f"{candidate}/api/health", timeout=2)
            if response.status_code == 200:
                return candidate
        except Exception:
            continue

    return "http://localhost:5001"


BASE_URL = _resolve_base_url()


def _resolve_pilot_user_id() -> tuple[str, str]:
    configured_user_id = os.getenv("PILOT_USER_ID", "").strip()
    if UUID_PATTERN.match(configured_user_id):
        return configured_user_id, "using explicit PILOT_USER_ID"

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return "anonymous", "Supabase auth config is unavailable"

    if not PILOT_EMAIL or not PILOT_PASSWORD:
        return "anonymous", "pilot email/password are unavailable"

    try:
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            json={"email": PILOT_EMAIL, "password": PILOT_PASSWORD},
            timeout=20,
        )
        if response.status_code != 200:
            return (
                "anonymous",
                f"Supabase sign-in failed with status {response.status_code}",
            )

        payload = response.json()
        user_id = (payload.get("user") or {}).get("id", "").strip()
        if UUID_PATTERN.match(user_id):
            return user_id, f"authenticated as {PILOT_EMAIL}"
        return "anonymous", "Supabase sign-in succeeded but no valid user id was returned"
    except Exception as exc:
        return "anonymous", f"Supabase sign-in unavailable: {exc}"


PILOT_USER_ID, PILOT_USER_CONTEXT = _resolve_pilot_user_id()


def _sample_image_path() -> Path:
    candidates = [
        REPO_ROOT / "backend/assets/data/multimodal_image_audio_diagnosis/combined_images/Acne/07Acne081101.jpg",
        REPO_ROOT / "backend/assets/data/multimodal_image_audio_diagnosis/combined_images/Acne/07AcnePittedScars.jpg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No sample pilot image was found under backend/assets/data/")


def _image_file():
    return _sample_image_path().open("rb")


def _print_result(name: str, ok: bool, detail: str) -> bool:
    status = "[PASSED]" if ok else "[FAILED]"
    print(f"{name}: {status} - {detail}")
    return ok


def _has_real_pilot_user() -> bool:
    return bool(PILOT_USER_ID and UUID_PATTERN.match(PILOT_USER_ID))


def _print_skip(name: str, detail: str) -> None:
    print(f"{name}: [SKIPPED] - {detail}")


def test_health() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=30)
        payload = response.json()
        return _print_result(
            "Health",
            response.status_code == 200 and payload.get("ok") is True,
            json.dumps(payload),
        )
    except Exception as exc:
        return _print_result("Health", False, str(exc))


def test_status() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=60)
        payload = response.json()
        ok = response.status_code == 200 and payload.get("service") == "online"
        detail = json.dumps(
            {
                "inference_available": payload.get("inference_available"),
                "skin_type_inference_available": payload.get("skin_type_inference_available"),
                "severity_inference_available": payload.get("severity_inference_available"),
            }
        )
        return _print_result("Status", ok, detail)
    except Exception as exc:
        return _print_result("Status", False, str(exc))


def test_chat() -> bool:
    payload = {
        "message": "I have itchy red patches on my elbows",
        "session_id": "pilot-self-check",
        "user_id": PILOT_USER_ID,
    }
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        data = response.json()
        ok = response.status_code == 200 and "reply" in data
        return _print_result("Chat (C1)", ok, str(data.get("reply", ""))[:120])
    except Exception as exc:
        return _print_result("Chat (C1)", False, str(exc))


def test_multimodal() -> bool:
    try:
        with _image_file() as image_file:
            files = {"image": ("pilot-sample.jpg", image_file, "image/jpeg")}
            data = {"text": "Scaly plaque on knee", "user_id": PILOT_USER_ID}
            response = requests.post(
                f"{BASE_URL}/api/analyze-fused",
                files=files,
                data=data,
                timeout=120,
            )
        payload = response.json()
        ok = response.status_code == 200 and "status" in payload
        return _print_result("Multimodal (C2)", ok, json.dumps(sorted(payload.keys())[:8]))
    except Exception as exc:
        return _print_result("Multimodal (C2)", False, str(exc))


def test_skincare() -> bool:
    try:
        with _image_file() as image_file:
            files = {"image": ("pilot-sample.jpg", image_file, "image/jpeg")}
            data = {
                "goals": "acne,oil_control",
                "allergies": "fragrance",
                "routine_level": "simple",
                "budget": "medium",
            }
            response = requests.post(
                f"{BASE_URL}/api/analyze-skin-care",
                files=files,
                data=data,
                timeout=120,
            )
        payload = response.json()
        ok = response.status_code == 200 and "skin_type" in payload
        return _print_result("Skincare (C3)", ok, str(payload.get("skin_type", "")))
    except Exception as exc:
        return _print_result("Skincare (C3)", False, str(exc))


def test_severity() -> bool:
    try:
        with _image_file() as image_file:
            files = {"image": ("pilot-sample.jpg", image_file, "image/jpeg")}
            data = {"track": "true", "user_id": PILOT_USER_ID}
            response = requests.post(
                f"{BASE_URL}/api/analyze-severity",
                files=files,
                data=data,
                timeout=120,
            )
        payload = response.json()
        ok = response.status_code == 200 and "severity_level" in payload
        return _print_result("Severity Analyze (C4)", ok, str(payload.get("severity_level", "")))
    except Exception as exc:
        return _print_result("Severity Analyze (C4)", False, str(exc))


def test_journey_tracking() -> bool:
    if not _has_real_pilot_user():
        _print_skip(
            "Journeys (Supabase)",
            "Authenticated pilot user is required to validate tracking journeys.",
        )
        return True

    try:
        title = f"Pilot Journey {PILOT_USER_ID[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/journey/start",
            json={
                "user_id": PILOT_USER_ID,
                "title": title,
                "body_part": "Face",
                "frequency": "weekly",
            },
            timeout=60,
        )
        create_payload = create_response.json()
        journey = create_payload.get("journey") or {}
        journey_id = journey.get("id")

        list_response = requests.get(
            f"{BASE_URL}/api/journey/list",
            params={"user_id": PILOT_USER_ID},
            timeout=60,
        )
        list_payload = list_response.json()
        journeys = list_payload.get("journeys") or []

        ok = (
            create_response.status_code == 200
            and list_response.status_code == 200
            and isinstance(journeys, list)
            and any(item.get("id") == journey_id for item in journeys)
        )
        detail = json.dumps(
            {
                "created_journey_id": journey_id,
                "journey_count": len(journeys),
            }
        )
        return _print_result("Journeys (Supabase)", ok, detail)
    except Exception as exc:
        return _print_result("Journeys (Supabase)", False, str(exc))


def test_progress_and_history() -> bool:
    if not _has_real_pilot_user():
        _print_skip(
            "Progress/History (C4)",
            "Set PILOT_USER_ID to a real authenticated UUID to validate persisted tracking.",
        )
        return True

    try:
        with _image_file() as image_file:
            files = {"image": ("pilot-sample.jpg", image_file, "image/jpeg")}
            data = {"user_id": PILOT_USER_ID}
            progress = requests.post(
                f"{BASE_URL}/api/progress",
                files=files,
                data=data,
                timeout=120,
            )
        progress_payload = progress.json()
        history = requests.get(f"{BASE_URL}/api/history?user_id={PILOT_USER_ID}", timeout=30)
        stats = requests.get(f"{BASE_URL}/api/stats?user_id={PILOT_USER_ID}", timeout=30)
        ok = (
            progress.status_code == 200
            and history.status_code == 200
            and stats.status_code == 200
            and isinstance(history.json(), list)
            and isinstance(stats.json(), dict)
        )
        detail = json.dumps(
            {
                "progress_status": progress_payload.get("status"),
                "history_count": len(history.json()) if isinstance(history.json(), list) else None,
                "stats_labels": stats.json().get("labels") if isinstance(stats.json(), dict) else None,
            }
        )
        return _print_result("Progress/History (C4)", ok, detail)
    except Exception as exc:
        return _print_result("Progress/History (C4)", False, str(exc))


if __name__ == "__main__":
    print("=== STARTING PILOT SELF-CHECK ===")
    print(f"Base URL: {BASE_URL}")
    print(f"User ID: {PILOT_USER_ID}")
    print(f"Pilot auth: {PILOT_USER_CONTEXT}")
    if not _has_real_pilot_user():
        print(
            "Note: persistence checks require PILOT_USER_ID to be set to a real authenticated UUID. "
            "Running stateless checks only."
        )

    checks = [
        test_health,
        test_status,
        test_chat,
        test_multimodal,
        test_skincare,
        test_severity,
        test_journey_tracking,
        test_progress_and_history,
    ]
    results = [check() for check in checks]

    print("\n=== FINAL RESULTS ===")
    if all(results):
        if _has_real_pilot_user():
            print("SYSTEM IS READY FOR A CONTROLLED INTERNAL PILOT.")
        else:
            print(
                "CORE SYSTEM CHECKS PASSED. "
                "Set PILOT_USER_ID to validate authenticated persistence before the live pilot."
            )
    else:
        print("SYSTEM STILL HAS BLOCKERS. REVIEW THE FAILED CHECKS ABOVE.")
