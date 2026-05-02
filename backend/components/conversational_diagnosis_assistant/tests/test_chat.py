from __future__ import annotations

import requests


def main() -> None:
    try:
        response = requests.post(
            "http://localhost:5001/api/chat",
            headers={"Content-Type": "application/json"},
            json={"message": "Hi", "session_id": "test"},
        )
        print("Status:", response.status_code)
        print("Response:", response.text)
    except Exception as exc:
        print("Error:", exc)


if __name__ == "__main__":
    main()
