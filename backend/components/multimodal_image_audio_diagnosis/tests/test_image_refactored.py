from __future__ import annotations

import os

import requests


def run_analyze_refactored_smoke() -> None:
    url = "http://localhost:5001/api/analyze"
    image_path = "assets/test_face.jpg"
    files = None

    if os.path.exists(image_path):
        files = {"image": open(image_path, "rb")}
    else:
        print("Note: assets/test_face.jpg missing, sending empty request to test error handling")

    print(f"--- Sending request to {url} ---")
    try:
        response = requests.post(url, files=files)
        print(f"Status: {response.status_code}")
        payload = response.json()
        print(payload)
    except Exception as exc:
        print(f"Error: {exc}")
    finally:
        if files is not None:
            files["image"].close()


if __name__ == "__main__":
    run_analyze_refactored_smoke()
