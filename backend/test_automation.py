
import requests
import os

# Test the fully automated smart scan
def test_smart_scan():
    url = "http://localhost:5001/api/smart-scan"
    
    # Path to a test image (e.g., from existing project assets)
    image_path = "assets/test_face.jpg"
    if not os.path.exists(image_path):
        # Create a mock file if it doesn't exist for test purposes
        print("Test image not found, skipping image analysis part of test.")
        files = None
    else:
        files = {'image': open(image_path, 'rb')}
    
    data = {
        'text': 'I have red itchy patches near my nose',
        'user_id': 'test_user_automation'
    }
    
    print(f"--- Sending FULLY AUTOMATED request to {url} ---")
    try:
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            res = response.json()
            print("\n[SUCCESS] Automated Report Received:")
            print(f"Summary: {res.get('summary')}")
            print(f"Diagnosis: {res['diagnosis']['disease']} ({res['diagnosis']['confidence_level']})")
            
            if res.get('severity'):
                print(f"Severity: {res['severity']['level']} (Score: {res['severity']['score']})")
                
            if res.get('skin_profile'):
                print(f"Skin Profile: {res['skin_profile']['type']} skin")
            
            print("\nAutomation complete. User received full analysis in one call.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed (is the server running?): {e}")

if __name__ == "__main__":
    test_smart_scan()
