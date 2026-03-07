import requests

try:
    resp = requests.post(
        "http://localhost:5001/api/chat",
        headers={"Content-Type": "application/json"},
        json={"message": "Hi", "session_id": "test"}
    )
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Error:", e)
