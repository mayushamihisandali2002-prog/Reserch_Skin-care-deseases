import requests
import json
import uuid
import time

BASE_URL = "http://localhost:5001/api/chat"

# A collection of diverse inputs to stress test the chatbot
test_inputs = [
    # Initial greetings
    "Hello", "Hi there", "Hey, can you help me?",
    
    # Simple symptom reports
    "I have itchy skin", "My face is red", "I have bumps on my arm",
    
    # Detailed clinical scenarios
    "I have red itchy bumps on my neck after wearing a new scarf yesterday",
    "There are small white blisters on my hands that sting when I touch them",
    "I have a scaly patch on my elbow that has been there for 2 weeks",
    "My acne is flaring up and it's very painful and deep",
    
    # General dermatology questions
    "What is the best SPF for oily skin?",
    "How do I know if a mole is dangerous?",
    "Is it okay to use retinol every night?",
    "What causes dry skin in winter?",
    
    # Follow-ups (using the same session)
    "Should I use hydrocortisone on it?",
    "What about calamine lotion?",
    "How long will it take to heal?",
    
    # Edge cases
    "asdfghjkl", # Gibberish
    "I'm feeling fine today", # No concern
    "Thank you so much!", # Politeness
    "Goodbye",
    
    # More scenarios to reach 50+
    "Itchy scalp and dandruff", "Small red dots on legs after shaving",
    "Sunburn on shoulders", "Dark spots on forehead", "Peeling skin on nose",
    "Bumps on back of arms (chicken skin)", "Yellowish crust on baby's head",
    "Swollen eyelid", "Red ring-shaped rash on chest", "Ingrown hair on chin",
    "Fungal infection on toes", "White patches on back", "Oily forehead and dry cheeks",
    "Is vitamin C good for skin?", "Best treatment for dark circles?",
    "What is hyaluronic acid?", "Can stress cause rashes?",
    "I have a painful boil on my leg", "Small clear bumps on fingers",
    "Redness around my mouth", "Does chocolate cause acne?",
    "My skin is very sensitive to everything", "What are the early signs of melanoma?",
    "How to treat a cold sore?", "Dry cracked heels", "Itchy bug bite or rash?",
    "Small skin tag on neck", "Wart on finger", "Heat rash under armpits"
]

def run_stress_test():
    session_id = str(uuid.uuid4())
    print(f"STARTING STRESS TEST with Session ID: {session_id}")
    print("-" * 50)
    
    success_count = 0
    fail_count = 0
    leaks_found = 0
    
    for i, user_input in enumerate(test_inputs):
        print(f"[{i+1}/{len(test_inputs)}] Testing: '{user_input}'")
        
        try:
            start_time = time.time()
            response = requests.post(BASE_URL, json={
                "message": user_input,
                "session_id": session_id,
                "user_id": "stress_test_user"
            }, timeout=120)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                title = data.get("chat_title", "N/A")
                
                # Check for "Internal Leaks"
                leaks = ["ML Scan Data", "Symptom State", "confidence", "predicted_disease", "structured_data"]
                found_leaks = [l for l in leaks if l in reply]
                
                if found_leaks:
                    print(f"   WARNING: LEAK DETECTED: {found_leaks}")
                    leaks_found += 1
                
                print(f"   SUCCESS ({duration:.1f}s) | Title: {title}")
                success_count += 1
            else:
                print(f"   FAILED (Status: {response.status_code})")
                fail_count += 1
                
        except Exception as e:
            print(f"   ERROR: {str(e)}")
            fail_count += 1
            
        # Small sleep to avoid rate limiting
        time.sleep(0.5)

    print("-" * 50)
    print(f"SUMMARY:")
    print(f"   Total Inputs: {len(test_inputs)}")
    print(f"   Successes: {success_count}")
    print(f"   Failures: {fail_count}")
    print(f"   Leaks Found: {leaks_found}")
    print("-" * 50)

if __name__ == "__main__":
    run_stress_test()
