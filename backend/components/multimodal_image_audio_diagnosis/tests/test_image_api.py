from __future__ import annotations

import io

import requests
from PIL import Image


def main() -> None:
    print("Creating test image...")
    image = Image.new("RGB", (224, 224), color=(200, 100, 100))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()
    print(f"Image size: {len(image_bytes)} bytes")

    print("\nTesting /api/analyze safety block...")
    files = {"image": ("test.jpg", image_bytes, "image/jpeg")}

    try:
        response = requests.post(
            "http://127.0.0.1:5001/api/analyze",
            files=files,
            timeout=30,
        )
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response status: {result.get('status', 'N/A')}")
        print(f"Error: {result.get('error', 'N/A')}")
        print(f"Message: {result.get('message', 'N/A')}")
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
