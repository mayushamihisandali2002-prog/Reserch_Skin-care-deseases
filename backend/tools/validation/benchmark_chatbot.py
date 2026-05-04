import sys
import os
from pathlib import Path

# Setup path
BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

import json
from components.multimodal_image_audio_diagnosis import get_inference_pipeline
from components.conversational_diagnosis_assistant.routes import get_intent_classifier

def run_benchmark():
    print("=== Chatbot Full Validation Benchmarking ===")
    
    test_cases = [
        {
            "name": "Initial Diagnosis",
            "message": "I have itchy red patches on my elbows with silver scales.",
            "expected_intent": "symptom_description",
            "expected_disease": "Psoriasis"
        },
        {
            "name": "Treatment Query",
            "message": "What is the treatment for psoriasis?",
            "context_disease": "Psoriasis",
            "expected_intent": "ask_treatment"
        },
        {
            "name": "Cause/Trigger Query",
            "message": "What causes this condition?",
            "context_disease": "Psoriasis",
            "expected_intent": "ask_causes"
        },
        {
            "name": "Severity Check",
            "message": "Is this dangerous?",
            "context_disease": "Psoriasis",
            "expected_intent": "ask_severity"
        }
    ]

    pipe = get_inference_pipeline()
    classifier = get_intent_classifier()
    
    results = []
    
    for case in test_cases:
        print(f"\nTesting: {case['name']}")
        msg = case['message']
        
        # 1. Test Intent
        intent, intent_conf = classifier.predict(msg)
        intent_match = intent == case['expected_intent']
        print(f"  - Intent: {intent} (Conf: {intent_conf:.2f}) {'[PASS]' if intent_match else '[FAIL]'}")
        
        # 2. Test Diagnosis (if applicable)
        diag_match = True
        if intent == 'symptom_description':
            pred = pipe.predict_disease(msg)
            disease = pred.get('disease')
            diag_match = disease == case['expected_disease']
            print(f"  - Diagnosis: {disease} {'[PASS]' if diag_match else '[FAIL]'} (Expected: {case['expected_disease']})")
        
        results.append({
            "name": case['name'],
            "intent_pass": intent_match,
            "diag_pass": diag_match
        })

    print("\n=== Summary ===")
    passes = sum(1 for r in results if r['intent_pass'] and r['diag_pass'])
    print(f"Total Success: {passes}/{len(results)}")
    
    if passes == len(results):
        print("CHATBOT VALIDATION: PASSED")
    else:
        print("CHATBOT VALIDATION: FAILED (Review logs)")

if __name__ == "__main__":
    run_benchmark()
