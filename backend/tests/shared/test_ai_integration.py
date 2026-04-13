"""
End-to-End Test Script for AI Chat Integration
Tests the complete flow: message → inference pipeline → structured response
"""

import requests
import json
from typing import Dict, Any


class AIIntegrationTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_cases = [
            ("I have red itchy skin", "Possible eczema or dermatitis"),
            ("My skin is dry and flaky", "Possible psoriasis or dryness"),
            ("I have pimples and oily skin", "Possible acne"),
            ("I have hives and swelling", "Possible urticaria/allergic reaction"),
            ("What should I do for my skin?", "General skin care advice"),
        ]

    def test_status(self) -> bool:
        """Test that the server is running and models are loaded"""
        print("\n=== Testing Server Status ===")
        try:
            response = requests.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                data = response.json()
                print("✓ Server is running")
                print(f"  Service: {data.get('service', 'N/A')}")
                print(f"  Models available: {data.get('inference_available', False)}")
                
                models = data.get('models', {})
                for model_name, available in models.items():
                    status = "✓" if available else "✗"
                    print(f"    {status} {model_name}: {available}")
                return True
            else:
                print(f"✗ Server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("✗ Could not connect to server at", self.base_url)
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def test_chat_endpoint(self, message: str) -> Dict[str, Any] | None:
        """Test the /api/chat endpoint with a message"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": message},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  ✗ API returned {response.status_code}")
                return None
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate that response has all required fields"""
        required_fields = [
            'reply',
            'predicted_disease',
            'confidence',
            'confidence_level',
            'needs_more_info',
            'follow_up_questions',
            'treatments',
            'kg_available',
            'model_status'
        ]
        
        missing = [f for f in required_fields if f not in response]
        if missing:
            print(f"  ✗ Missing fields: {missing}")
            return False
        
        # Validate field types
        if not isinstance(response['reply'], str):
            print("  ✗ 'reply' should be string")
            return False
        if not isinstance(response['follow_up_questions'], list):
            print("  ✗ 'follow_up_questions' should be list")
            return False
        if not isinstance(response['treatments'], list):
            print("  ✗ 'treatments' should be list")
            return False
        if response['confidence_level'] not in ['high', 'medium', 'low']:
            print(f"  ✗ 'confidence_level' should be 'high', 'medium', or 'low', got '{response['confidence_level']}'")
            return False
        
        return True

    def run_tests(self):
        """Run all AI integration tests"""
        print("\n" + "="*60)
        print("  AI Chat Integration Test Suite")
        print("="*60)
        
        # Test 1: Server Status
        if not self.test_status():
            print("\n✗ Cannot continue - server not running")
            return False
        
        # Test 2: Chat Endpoint
        print("\n=== Testing Chat Endpoint ===")
        all_passed = True
        
        for message, description in self.test_cases:
            print(f"\nTest: {description}")
            print(f"  Message: '{message}'")
            
            response = self.test_chat_endpoint(message)
            if response is None:
                print("  ✗ Failed to get response")
                all_passed = False
                continue
            
            if not self.validate_response(response):
                print("  ✗ Response validation failed")
                all_passed = False
                continue
            
            print("  ✓ Response validated")
            print(f"    Disease: {response['predicted_disease']}")
            print(f"    Confidence: {response['confidence']:.2f} ({response['confidence_level']})")
            
            if response['follow_up_questions']:
                print(f"    Follow-up questions: {len(response['follow_up_questions'])}")
            
            if response['treatments']:
                print(f"    Treatments: {len(response['treatments'])}")
                for t in response['treatments'][:2]:
                    medicine = t.get('medicine', 'Unknown')
                    advice = t.get('advice', '')[:40]
                    print(f"      • {medicine}: {advice}...")
        
        # Summary
        print("\n" + "="*60)
        if all_passed:
            print("✓ All tests PASSED!")
            print("\nYou can now:")
            print("  1. Connect an Android device and run: flutter run")
            print("  2. Or enable Developer Mode and run: flutter run -d windows")
            print("  3. Or use Chrome web: flutter run -d chrome")
        else:
            print("✗ Some tests FAILED - check errors above")
        print("="*60)
        
        return all_passed


if __name__ == "__main__":
    tester = AIIntegrationTester()
    tester.run_tests()
