import requests

try:
    resp = requests.options(
        "http://localhost:5001/api/analyze-fused",
        headers={
            "Origin": "http://localhost:54471",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    print("OPTIONS Status:", resp.status_code)
    print("OPTIONS Headers:", resp.headers)
except Exception as e:
    print("Error:", e)
