from __future__ import annotations

import requests


BASE_URL = "http://localhost:5001/api"


def run_onboarding_and_tracking_smoke() -> None:
    print("--- Testing Personalization & Tracking Journey ---")

    profile_data = {
        "user_id": "test_personalization_user",
        "full_name": "John Doe",
        "skin_type": "Oily",
        "allergies": "Fragrance, Alcohol",
        "tracking_preference": "weekly",
    }

    print("\n1. Updating User Profile...")
    resp = requests.post(f"{BASE_URL}/profile", json=profile_data)
    if resp.status_code == 200:
        print("[SUCCESS] Profile updated.")
    else:
        print(f"[FAIL] {resp.status_code}: {resp.text}")

    journey_data = {
        "user_id": "test_personalization_user",
        "title": "Face Acne Recovery",
        "body_part": "Face",
        "frequency": "weekly",
    }

    print("\n2. Starting Tracking Journey...")
    resp = requests.post(f"{BASE_URL}/journey/start", json=journey_data)
    if resp.status_code == 200:
        journey = resp.json()
        print(f"[SUCCESS] Journey started with ID: {journey.get('id')}")
    else:
        print(f"[FAIL] {resp.status_code}: {resp.text}")

    print("\n3. Listing Journeys...")
    resp = requests.get(
        f"{BASE_URL}/journey/list",
        params={"user_id": "test_personalization_user"},
    )
    if resp.status_code == 200:
        journeys = resp.json()
        print(f"[SUCCESS] Found {len(journeys)} active journeys.")
    else:
        print(f"[FAIL] {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    run_onboarding_and_tracking_smoke()
