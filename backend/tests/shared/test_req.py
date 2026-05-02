from __future__ import annotations

import requests


def main() -> None:
    img_bytes = (
        b"\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB\x00\x43\x00"
        + b"\x00" * 100
    )
    audio_bytes = b"fake mp3 audio bytes"

    try:
        response = requests.post(
            "http://localhost:5001/api/analyze-fused",
            files={
                "image": ("image.jpg", img_bytes, "application/octet-stream"),
                "audio": ("patient_symptoms.mp3", audio_bytes, "application/octet-stream"),
            },
            data={"text": "", "journey_id": "test"},
        )
        print("Status:", response.status_code)
        print("Response:", response.text)
    except Exception as exc:
        print("Error:", exc)


if __name__ == "__main__":
    main()
