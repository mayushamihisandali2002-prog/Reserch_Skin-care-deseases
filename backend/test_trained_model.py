"""Quick test of the trained DistilBERT model"""
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

model_dir = 'assets/models/distilbert'
print('Loading model...')
tokenizer = DistilBertTokenizerFast.from_pretrained(model_dir)
model = DistilBertForSequenceClassification.from_pretrained(model_dir)
model.eval()
print('Model loaded!')

tests = [
    ('I have dry itchy patches on my arms', 'Eczema'),
    ('My skin reacted badly to a new soap', 'Dermatitis'),
    ('Thick silvery scales on my elbows', 'Psoriasis'),
    ('Pimples and oily skin on my face', 'Acne'),
    ('Sudden hives all over my body', 'Urticaria'),
    ('Red itchy inflamed dry skin', 'Eczema'),
    ('Flaky dandruff on my scalp', 'Dermatitis'),
    ('Raised red plaques with white scales', 'Psoriasis'),
    ('Blackheads and whiteheads breakout', 'Acne'),
    ('Itchy welts all over my body', 'Urticaria'),
]

id2label = {int(k): v for k, v in model.config.id2label.items()}
correct = 0
print()
for text, expected in tests:
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=128)
    with torch.no_grad():
        probs = F.softmax(model(**inputs).logits, dim=-1)[0].numpy()
    pred_id = int(probs.argmax())
    pred = id2label[pred_id]
    conf = probs[pred_id]
    is_correct = pred == expected
    correct += int(is_correct)
    sym = '✅' if is_correct else '❌'
    print(f'{sym} "{text[:40]}..."')
    print(f'   Predicted: {pred} ({conf:.1%}) | Expected: {expected}')

print(f'\nAccuracy: {correct}/{len(tests)} ({correct/len(tests):.0%})')
