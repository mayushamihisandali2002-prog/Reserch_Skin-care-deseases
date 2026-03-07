
import requests
import os

def test_analyze_refactored():
    url = "http://localhost:5001/api/analyze"
    # Even if image is missing, the endpoint should handle it or error gracefully
    image_path = "assets/test_face.jpg"
    files = None
    if os.path.exists(image_path):
        files = {'image': open(image_path, 'rb')}
    else:
        print("Note: assets/test_face.jpg missing, sending empty request to test error handling")
        
    print(f"--- Sending request to REFACTORED {url} ---")
    try:
        response = requests.post(url, files=files)
        print(f"Status: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_analyze_refactored()
