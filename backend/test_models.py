"""
Smoke test — loads both real models and runs a quick prediction.
Run from the backend/ directory:
    python test_models.py
"""
import sys
from pathlib import Path

# Make sure inference package is importable
sys.path.insert(0, str(Path(__file__).parent))

from inference.config import (
    DISTILBERT_MODEL_DIR,
    IMAGE_MODEL_PATH,
    DISEASE_LABELS,
)

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

def sep(title=""):
    print("\n" + "─" * 60)
    if title:
        print(f"  {title}")
        print("─" * 60)

# ── 1. Check file-system paths ────────────────────────────────────────────────
sep("1 / PATH CHECK")
print(f"  DistilBERT dir : {DISTILBERT_MODEL_DIR}")
print(f"  Exists         : {DISTILBERT_MODEL_DIR.exists()}")
print(f"  Image model    : {IMAGE_MODEL_PATH}")
print(f"  Exists         : {IMAGE_MODEL_PATH.exists()}")

bert_dir_ok = DISTILBERT_MODEL_DIR.exists()
img_file_ok = IMAGE_MODEL_PATH.exists()
print(f"\n  {PASS if bert_dir_ok else FAIL}  DistilBERT directory")
print(f"  {PASS if img_file_ok else FAIL}  ResNet-18 .pt file")

# ── 2. DistilBERT text model ──────────────────────────────────────────────────
sep("2 / DISTILBERT TEXT MODEL")
if bert_dir_ok:
    from inference.distilbert_model import DistilBertTextModel
    bert = DistilBertTextModel(DISTILBERT_MODEL_DIR)
    if bert.loaded:
        samples = [
            "I have red itchy dry patches on my arms for two weeks",
            "my skin has large scaly white plaques on my elbows",
            "pimples and blackheads on my face with oily skin",
        ]
        print()
        for txt in samples:
            disease, conf, probs = bert.predict(txt)
            bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
            print(f"  [{bar}] {conf*100:5.1f}%  →  {disease}")
            print(f"  Input: \"{txt[:55]}…\"" if len(txt)>55 else f"  Input: \"{txt}\"")
            print()
        print(f"  {PASS}  DistilBERT inference OK")
    else:
        print(f"  {FAIL}  DistilBERT failed to load")
else:
    print(f"  {WARN} Skipped — directory missing")

# ── 3. ResNet-18 image model ──────────────────────────────────────────────────
sep("3 / RESNET-18 IMAGE MODEL")
if img_file_ok:
    from inference.image_model import ResNetImageModel
    resnet = ResNetImageModel(IMAGE_MODEL_PATH)
    if resnet.loaded:
        # Create a synthetic 224×224 test image (pink-ish skin tone)
        from PIL import Image
        import numpy as np
        arr = np.full((224, 224, 3), [220, 170, 140], dtype=np.uint8)
        pil = Image.fromarray(arr)
        disease, conf, probs = resnet.predict_from_pil(pil)
        bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
        print(f"\n  Synthetic skin-tone image:")
        print(f"  [{bar}] {conf*100:5.1f}%  →  {disease}")
        print(f"\n  All class probabilities:")
        for idx, label in DISEASE_LABELS.items():
            p = probs[idx] if idx < len(probs) else 0.0
            b = "█" * int(p * 20) + "░" * (20 - int(p * 20))
            print(f"    {label:<15} [{b}] {p*100:5.1f}%")
        print(f"\n  {PASS}  ResNet-18 inference OK")
    else:
        print(f"  {FAIL}  ResNet-18 failed to load")
else:
    print(f"  {WARN} Skipped — .pt file missing")

# ── 4. Full pipeline (fusion) ─────────────────────────────────────────────────
sep("4 / FULL INFERENCE PIPELINE")
from inference import get_inference_pipeline
pipeline = get_inference_pipeline()

result = pipeline.predict_from_text("I have severe itching and red inflamed skin on my hands")
print(f"\n  Text prediction:")
print(f"    Disease    : {result['disease']}")
print(f"    Confidence : {result['confidence']*100:.1f}%")
print(f"    Treatments : {len(result['treatments'])} found")
for t in result['treatments'][:2]:
    print(f"      • {t['medicine']}")
print(f"    Model used : {result['model_used']}")
print(f"\n  {PASS}  Pipeline OK")

# ── 5. Chat intent routing ─────────────────────────────────────────────────────
sep("5 / INTENT CLASSIFIER")
from inference.intent_classifier import get_intent_classifier
clf = get_intent_classifier()
tests = [
    ("I have red itchy skin on my elbows",       "symptom_description"),
    ("what is the treatment for this",            "ask_treatment"),
    ("what is eczema",                            "ask_about_disease"),
    ("hello there",                               "other"),
]
print()
all_ok = True
for text, expected in tests:
    intent, conf = clf.predict(text)
    ok = intent == expected
    if not ok:
        all_ok = False
    mark = PASS if ok else WARN
    print(f"  {mark}  \"{text[:45]}\"")
    print(f"       → {intent} ({conf*100:.0f}%) [expected: {expected}]")
    print()
print(f"  {PASS if all_ok else WARN}  Intent classifier {'OK' if all_ok else 'check warnings above'}")

sep("DONE")
print("  All checks complete.\n")
