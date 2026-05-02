from __future__ import annotations

import requests


def main() -> None:
    try:
        response = requests.options(
            "http://localhost:5001/api/analyze-fused",
            headers={
                "Origin": "http://localhost:54471",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        print("OPTIONS Status:", response.status_code)
        print("OPTIONS Headers:", response.headers)
    except Exception as exc:
        print("Error:", exc)


if __name__ == "__main__":
    main()
