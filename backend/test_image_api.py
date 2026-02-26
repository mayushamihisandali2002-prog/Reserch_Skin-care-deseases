"""Test image analysis API endpoint"""
import requests
from PIL import Image
import io

# Create a test image
print("Creating test image...")
img = Image.new('RGB', (224, 224), color=(200, 100, 100))  # Reddish color
buf = io.BytesIO()
img.save(buf, format='JPEG')
image_bytes = buf.getvalue()
print(f"Image size: {len(image_bytes)} bytes")

# Send POST request
print("\nTesting /api/analyze endpoint...")
url = "http://127.0.0.1:5000/api/analyze"

files = {'image': ('test.jpg', image_bytes, 'image/jpeg')}

try:
    response = requests.post(url, files=files, timeout=30)
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Prediction: {result.get('prediction', result.get('disease', 'N/A'))}")
    print(f"Confidence: {result.get('confidence', 0):.1%}")
    print(f"Model used: {result.get('model_used', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")
