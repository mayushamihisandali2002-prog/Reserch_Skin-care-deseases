import requests
import json
import time

BASE_URL = "http://localhost:5001"

SCENARIOS = [
    {
        "name": "Scenario A: Ringworm (Infectious Path)",
        "messages": [
            "Hi, I have a red ring on my arm.",
            "It's on my inner forearm, near the wrist.",
            "It's itchy and has scaly edges, but the center is clear.",
            "I've had it for about a week. What could this be?",
            "Is this condition contagious to others?",
            "How can I treat it at home?",
            "What medicines are typical for this?",
            "Does Clotrimazole work for this kind of rash?",
            "What are the active ingredients in Clotrimazole?",
            "Are there any common side effects for this medicine?"
        ]
    },
    {
        "name": "Scenario B: Acne (Maintenance Path)",
        "messages": [
            "I'm having a lot of breakouts on my face lately.",
            "They are appearing mostly on my forehead and jawline.",
            "My skin feels very oily and I see red bumps and blackheads.",
            "I've had this for 2 months. Can you tell me more about Acne Vulgaris?",
            "What causes these kinds of breakouts?",
            "What are the common triggers I should avoid?",
            "What is the best over-the-counter medicine for acne?",
            "How does Benzoyl Peroxide work?",
            "What are the ingredients usually found in Benzoyl Peroxide gels?",
            "Can I apply it along with a normal moisturizer?"
        ]
    },
    {
        "name": "Scenario C: Melanoma (High-Risk Screening)",
        "messages": [
            "I'm worried about a mole on my back that looks different.",
            "It's right between my shoulder blades.",
            "It has irregular borders, multiple colors, and it has grown recently.",
            "Is this a sign of something serious like cancer?",
            "What exactly is Melanoma?",
            "How do doctors usually diagnose this condition?",
            "Are there any topical creams or medicines for it?",
            "What ingredients are in clinical skin cancer treatments?",
            "Can I just use an antifungal cream on it to see if it goes away?",
            "What are the ABCDE warning signs I should look for?"
        ]
    }
]

def run_real_world_test():
    print("="*80)
    print(" SKINAI REAL-WORLD USER SIMULATION TEST (30 INPUTS) ")
    print("="*80)
    
    overall_start = time.time()
    
    for scenario in SCENARIOS:
        print(f"\n>>> STARTING {scenario['name']}")
        print("-" * 40)
        session_id = f"real_world_{int(time.time())}_{scenario['name'][9:10]}"
        
        for i, msg in enumerate(scenario['messages']):
            print(f"[{i+1}/10] User: {msg}")
            
            try:
                payload = {
                    "message": msg,
                    "session_id": session_id,
                    "user_id": "anonymous"
                }
                
                resp = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=45)
                
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get('reply', '')
                    # Wrap reply for readability
                    clean_reply = reply.replace('\n', ' ')[:120] + "..."
                    print(f"      AI: {clean_reply}")
                else:
                    print(f"      [ERROR] Status {resp.status_code}")
                
            except Exception as e:
                print(f"      [ERROR] Request failed: {e}")
            
            # Small delay to simulate reading time
            time.sleep(1)
        
        print(f">>> COMPLETED {scenario['name']}")
        print("=" * 40)

    total_duration = time.time() - overall_start
    print(f"\nTOTAL TEST DURATION: {total_duration:.2f} seconds")
    print("="*80)

if __name__ == "__main__":
    run_real_world_test()
