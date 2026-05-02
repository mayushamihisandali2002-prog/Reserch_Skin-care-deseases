from __future__ import annotations

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from components.conversational_diagnosis_assistant.intent_classifier import (  # noqa: E402
    get_intent_classifier,
)


def main() -> None:
    classifier = get_intent_classifier()
    test_cases = [
        "Hello",
        "I have chickenpox",
        "Is this contagious?",
        "Will I die?",
        "Should I wash it with soap?",
        "Give me the price of the medicine",
        "What is the capital of France?",
        "My skin is dry like a desert",
        "How long until I see progress?",
        "It's spreading to my back",
        "I am an oily person",
        "I'm confused",
    ]

    print(f"{'Text':<35} | {'Predicted Intent':<20} | {'Conf':<6}")
    print("-" * 65)
    for text in test_cases:
        intent, confidence = classifier.predict(text)
        print(f"{text:<35} | {intent:<20} | {confidence:.2f}")


if __name__ == "__main__":
    main()
