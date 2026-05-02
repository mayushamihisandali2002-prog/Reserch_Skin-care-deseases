from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from inference.config import DISEASE_LABELS, DISTILBERT_MODEL_DIR, IMAGE_MODEL_PATH


PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"


def sep(title: str = "") -> None:
    print("\n" + "-" * 60)
    if title:
        print(f"  {title}")
        print("-" * 60)


def main() -> None:
    sep("1 / PATH CHECK")
    print(f"  DistilBERT dir : {DISTILBERT_MODEL_DIR}")
    print(f"  Exists         : {DISTILBERT_MODEL_DIR.exists()}")
    print(f"  Image model    : {IMAGE_MODEL_PATH}")
    print(f"  Exists         : {IMAGE_MODEL_PATH.exists()}")

    bert_dir_ok = DISTILBERT_MODEL_DIR.exists()
    img_file_ok = IMAGE_MODEL_PATH.exists()
    print(f"\n  {PASS if bert_dir_ok else FAIL} DistilBERT directory")
    print(f"  {PASS if img_file_ok else FAIL} ResNet-18 artifact")

    sep("2 / DISTILBERT TEXT MODEL")
    if bert_dir_ok:
        from components.conversational_diagnosis_assistant.distilbert_model import (
            DistilBertTextModel,
        )

        bert = DistilBertTextModel(DISTILBERT_MODEL_DIR)
        if bert.loaded:
            samples = [
                "I have red itchy dry patches on my arms for two weeks",
                "my skin has large scaly white plaques on my elbows",
                "pimples and blackheads on my face with oily skin",
            ]
            print()
            for txt in samples:
                disease, confidence, _probs = bert.predict(txt)
                bar = "X" * int(confidence * 20) + "." * (20 - int(confidence * 20))
                print(f"  [{bar}] {confidence*100:5.1f}% -> {disease}")
                print(
                    f'  Input: "{txt[:55]}..."' if len(txt) > 55 else f'  Input: "{txt}"'
                )
                print()
            print(f"  {PASS} DistilBERT inference OK")
        else:
            print(f"  {FAIL} DistilBERT failed to load")
    else:
        print(f"  {WARN} Skipped - directory missing")

    sep("3 / RESNET-18 IMAGE MODEL")
    if img_file_ok:
        import numpy as np
        from PIL import Image

        from components.multimodal_image_audio_diagnosis.image_model import (
            ResNetImageModel,
        )

        resnet = ResNetImageModel(IMAGE_MODEL_PATH)
        if resnet.loaded:
            arr = np.full((224, 224, 3), [220, 170, 140], dtype=np.uint8)
            pil = Image.fromarray(arr)
            disease, confidence, probs = resnet.predict_from_pil(pil)
            bar = "X" * int(confidence * 20) + "." * (20 - int(confidence * 20))
            print("\n  Synthetic skin-tone image:")
            print(f"  [{bar}] {confidence*100:5.1f}% -> {disease}")
            print("\n  All class probabilities:")
            for idx, label in DISEASE_LABELS.items():
                probability = probs[idx] if idx < len(probs) else 0.0
                prob_bar = "X" * int(probability * 20) + "." * (
                    20 - int(probability * 20)
                )
                print(f"    {label:<15} [{prob_bar}] {probability*100:5.1f}%")
            print(f"\n  {PASS} ResNet-18 inference OK")
        else:
            print(f"  {FAIL} ResNet-18 failed to load")
    else:
        print(f"  {WARN} Skipped - artifact missing")

    sep("4 / FULL INFERENCE PIPELINE")
    from components.multimodal_image_audio_diagnosis import get_inference_pipeline

    pipeline = get_inference_pipeline()
    result = pipeline.predict_from_text(
        "I have severe itching and red inflamed skin on my hands"
    )
    print("\n  Text prediction:")
    print(f"    Disease    : {result['disease']}")
    print(f"    Confidence : {result['confidence']*100:.1f}%")
    print(f"    Treatments : {len(result['treatments'])} found")
    for treatment in result["treatments"][:2]:
        print(f"      - {treatment['medicine']}")
    print(f"    Model used : {result['model_used']}")
    print(f"\n  {PASS} Pipeline OK")

    sep("5 / INTENT CLASSIFIER")
    from components.conversational_diagnosis_assistant.intent_classifier import (
        get_intent_classifier,
    )

    classifier = get_intent_classifier()
    tests = [
        ("I have red itchy skin on my elbows", "symptom_description"),
        ("what is the treatment for this", "ask_treatment"),
        ("what is eczema", "ask_about_disease"),
        ("hello there", "other"),
    ]
    print()
    all_ok = True
    for text, expected in tests:
        intent, confidence = classifier.predict(text)
        ok = intent == expected
        if not ok:
            all_ok = False
        mark = PASS if ok else WARN
        print(f'  {mark} "{text[:45]}"')
        print(f"       -> {intent} ({confidence*100:.0f}%) [expected: {expected}]")
        print()
    print(f"  {PASS if all_ok else WARN} Intent classifier summary")

    sep("DONE")
    print("  All checks complete.\n")


if __name__ == "__main__":
    main()
