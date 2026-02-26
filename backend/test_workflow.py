"""Test complete chat workflow - ChatGPT-like experience"""
import requests
import json

base = 'http://127.0.0.1:5000'
session_id = 'test-workflow-123'

print("=" * 60)
print("SKIN CARE ASSISTANT - WORKFLOW TEST")
print("=" * 60)

# Test 1: Vague message
print('\n=== Test 1: Vague message ===')
r = requests.post(f'{base}/api/chat', json={'message': 'I have a rash', 'session_id': session_id})
d = r.json()
print(f"✓ Needs more info: {d.get('needs_more_info')}")
print(f"✓ Follow-up questions: {len(d.get('follow_up_questions', []))}")

# Test 2: Detailed symptom
print('\n=== Test 2: Detailed symptom ===')
r = requests.post(f'{base}/api/chat', json={'message': 'Its on my arms, very itchy and red for 2 weeks', 'session_id': session_id})
d = r.json()
print(f"✓ Disease: {d.get('predicted_disease')}")
print(f"✓ Confidence: {d.get('confidence')*100:.1f}%")
print(f"✓ Treatments: {len(d.get('recommended_treatments', []))}")

# Test 3: Treatment question
print('\n=== Test 3: Treatment question ===')
r = requests.post(f'{base}/api/chat', json={'message': 'How should I apply the emollient?', 'session_id': session_id})
d = r.json()
print(f"✓ Maintains context (disease): {d.get('predicted_disease')}")
print(f"✓ Reply contains 'How to apply': {'apply' in d.get('reply', '').lower()}")

# Test 4: Severity question
print('\n=== Test 4: Severity question ===')
r = requests.post(f'{base}/api/chat', json={'message': 'Is this condition serious?', 'session_id': session_id})
d = r.json()
reply = d.get('reply', '')
print(f"✓ Severity Level mentioned: {'Severity Level' in reply}")
print(f"✓ Warning signs included: {'warning' in reply.lower() or 'attention' in reply.lower()}")

# Test 5: Lifestyle advice
print('\n=== Test 5: What else can I do? ===')
r = requests.post(f'{base}/api/chat', json={'message': 'What else can I do to help my skin?', 'session_id': session_id})
d = r.json()
reply = d.get('reply', '')
print(f"✓ Do/Avoid tips: {'Things to Do' in reply or 'avoid' in reply.lower()}")
print(f"✓ Home remedies: {'Home Remedies' in reply or 'remedy' in reply.lower()}")

# Test 6: Causes question
print('\n=== Test 6: What causes this? ===')
r = requests.post(f'{base}/api/chat', json={'message': 'What causes eczema?', 'session_id': session_id})
d = r.json()
reply = d.get('reply', '')
print(f"✓ Causes explained: {'Cause' in reply}")
print(f"✓ Triggers listed: {'Trigger' in reply}")
print(f"✓ Contagious info: {'contagious' in reply.lower()}")

# Test 7: Contagious question
print('\n=== Test 7: Is it contagious? ===')
r = requests.post(f'{base}/api/chat', json={'message': 'Is this contagious?', 'session_id': session_id})
d = r.json()
reply = d.get('reply', '')
print(f"✓ Answers about spreading: {'contagious' in reply.lower() or 'spread' in reply.lower()}")

# Test 8: New session - greeting
print('\n=== Test 8: New session greeting ===')
new_session = 'test-new-session'
r = requests.post(f'{base}/api/chat', json={'message': 'Hello!', 'session_id': new_session})
d = r.json()
reply = d.get('reply', '')
print(f"✓ Greeting response: {'Hello' in reply or 'AI' in reply}")
print(f"✓ Asks for symptoms: {'symptom' in reply.lower() or 'describe' in reply.lower()}")

# Test 9: Different disease - Psoriasis
print('\n=== Test 9: Psoriasis symptoms ===')
psoriasis_session = 'psoriasis-test'
r = requests.post(f'{base}/api/chat', json={'message': 'I have thick silvery scales on my elbows and knees, been there for months', 'session_id': psoriasis_session})
d = r.json()
print(f"✓ Disease: {d.get('predicted_disease')}")
print(f"✓ Confidence: {d.get('confidence')*100:.1f}%")

# Test 10: Quick follow-up
print('\n=== Test 10: Quick follow-up ===')
r = requests.post(f'{base}/api/chat', json={'message': 'Thanks, is there anything else I should know?', 'session_id': session_id})
d = r.json()
print(f"✓ Maintains disease context: {d.get('predicted_disease')}")
print(f"✓ Reply not empty: {len(d.get('reply', '')) > 20}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
