
import requests
import os
import json

BASE_URL = "http://localhost:5001/api"

def test_onboarding_and_tracking():
    print("--- Testing Personalization & Tracking Journey ---")
    
    # 1. Update Profile (Onboarding)
    profile_data = {
        "user_id": "test_personalization_user",
        "full_name": "John Doe",
        "skin_type": "Oily",
        "allergies": "Fragrance, Alcohol",
        "tracking_preference": "weekly"
    }
    
    print("\n1. Updating User Profile...")
    resp = requests.post(f"{BASE_URL}/profile", json=profile_data)
    if resp.status_code == 200:
        print("[SUCCESS] Profile updated.")
    else:
        print(f"[FAIL] {resp.status_code}: {resp.text}")

    # 2. Start a Tracking Journey
    journey_data = {
        "user_id": "test_personalization_user",
        "title": "Face Acne Recovery",
        "body_part": "Face",
        "frequency": "weekly"
    }
    
    print("\n2. Starting Tracking Journey...")
    resp = requests.post(f"{BASE_URL}/journey/start", json=journey_data)
    journey_id = None
    if resp.status_code == 200:
        res = resp.json()
        journey_id = res.get("id")
        print(f"[SUCCESS] Journey started with ID: {journey_id}")
    else:
        print(f"[FAIL] {resp.status_code}: {resp.text}")

    # 3. Simulate a Scan within the journey (Correct part: Face)
    # Since we don't have a real image on the runner filesystem, we can't easily test face detection here
    # but we can check if the API accepts the journey_id correctly.
    
    # 4. List Journeys
    print("\n4. Listing Journeys...")
    resp = requests.get(f"{BASE_URL}/journey/list", params={"user_id": "test_personalization_user"})
    if resp.status_code == 200:
        journeys = resp.json()
        print(f"[SUCCESS] Found {len(journeys)} active journeys.")
    else:
        print(f"[FAIL] {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    test_onboarding_and_tracking()
