from __future__ import annotations

from pathlib import Path

import requests


def run_smart_scan_smoke() -> None:
    url = "http://localhost:5001/api/smart-scan"
    backend_dir = Path(__file__).resolve().parents[2]
    image_path = backend_dir / "assets" / "test_face.jpg"

    if not image_path.exists():
        print("Test image not found, skipping image analysis part of test.")
        files = None
    else:
        files = {"image": open(image_path, "rb")}

    data = {
        "text": "I have red itchy patches near my nose",
        "user_id": "test_user_automation",
    }

    print(f"--- Sending automated request to {url} ---")
    try:
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            payload = response.json()
            print("\n[SUCCESS] Automated Report Received:")
            print(f"Summary: {payload.get('summary')}")
            print(
                f"Diagnosis: {payload['diagnosis']['disease']} "
                f"({payload['diagnosis']['confidence_level']})"
            )

            if payload.get("severity"):
                print(
                    f"Severity: {payload['severity']['level']} "
                    f"(Score: {payload['severity']['score']})"
                )

            if payload.get("skin_profile"):
                print(f"Skin Profile: {payload['skin_profile']['type']} skin")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as exc:
        print(f"Connection failed (is the server running?): {exc}")
    finally:
        if files is not None:
            files["image"].close()


if __name__ == "__main__":
    run_smart_scan_smoke()
