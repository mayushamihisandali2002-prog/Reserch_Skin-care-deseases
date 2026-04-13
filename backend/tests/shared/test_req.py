import requests
import io

img_bytes = b"\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB\x00\x43\x00" + b"\x00" * 100
audio_bytes = b"fake mp3 audio bytes"

try:
    resp = requests.post(
        "http://localhost:5001/api/analyze-fused",
        files={
            "image": ("image.jpg", img_bytes, "application/octet-stream"),
            "audio": ("patient_symptoms.mp3", audio_bytes, "application/octet-stream")
        },
        data={"text": "", "journey_id": "test"}
    )
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Error:", e)
