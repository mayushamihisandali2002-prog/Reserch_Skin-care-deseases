
import sys
from pathlib import Path

# Fix path to include backend
sys.path.insert(0, str(Path.cwd()))

from inference.intent_classifier import get_intent_classifier

clf = get_intent_classifier()

test_cases = [
    "Hello", # other
    "I have chickenpox", # symptom_description
    "Is this contagious?", # ask_causes
    "Will I die?", # ask_severity (extreme)
    "Should I wash it with soap?", # ask_advice
    "Give me the price of the medicine", # ask_treatment (distractor)
    "What is the capital of France?", # other
    "My skin is dry like a desert", # symptom_description (metaphor)
    "How long until I see progress?", # ask_healing
    "It's spreading to my back", # ask_worsening
    "I am an oily person", # ask_skin_type
    "I'm confused", # general_question
]

print(f"{'Text':<35} | {'Predicted Intent':<20} | {'Conf':<6}")
print("-" * 65)
for text in test_cases:
    intent, conf = clf.predict(text)
    print(f"{text:<35} | {intent:<20} | {conf:.2f}")
