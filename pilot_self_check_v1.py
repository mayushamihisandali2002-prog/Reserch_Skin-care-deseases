import json
import os
from pathlib import Path

import requests


BASE_URL = os.getenv("PILOT_BASE_URL", "http://localhost:5000")
PILOT_USER_ID = os.getenv("PILOT_USER_ID", "anonymous")


def _sample_image_path() -> Path:
    candidates = [
        Path("backend/assets/data/multimodal_image_audio_diagnosis/combined_images/Acne/07Acne081101.jpg"),
        Path("backend/assets/data/multimodal_image_audio_diagnosis/combined_images/Acne/07AcnePittedScars.jpg"),
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


def test_progress_and_history() -> bool:
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

    checks = [
        test_health,
        test_status,
        test_chat,
        test_multimodal,
        test_skincare,
        test_severity,
        test_progress_and_history,
    ]
    results = [check() for check in checks]

    print("\n=== FINAL RESULTS ===")
    if all(results):
        print("SYSTEM IS READY FOR A CONTROLLED INTERNAL PILOT.")
    else:
        print("SYSTEM STILL HAS BLOCKERS. REVIEW THE FAILED CHECKS ABOVE.")
