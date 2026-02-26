import pickle
import sys

# Load and inspect the model
try:
    with open('assets/models/text_model.pkl', 'rb') as f:
        model = pickle.load(f)
    print(f'Model type: {type(model).__name__}')
    print(f'Model classes: {model.classes_ if hasattr(model, "classes_") else "N/A"}')
    print(f'Has predict: {hasattr(model, "predict")}')
    print(f'Has predict_proba: {hasattr(model, "predict_proba")}')
    
    with open('assets/models/vectorizer.pkl', 'rb') as f:
        vec = pickle.load(f)
    print(f'Vectorizer type: {type(vec).__name__}')
    print(f'Vocab size: {len(vec.vocabulary_) if hasattr(vec, "vocabulary_") else "N/A"}')
    
    # Try a test prediction
    test_text = "I have red itchy skin"
    X = vec.transform([test_text])
    pred = model.predict(X)
    proba = model.predict_proba(X)
    
    print(f'\nTest prediction for "{test_text}":')
    print(f'  Class prediction: {pred[0]}')
    print(f'  Confidence: {max(proba[0]):.3f}')
    print(f'  Class probabilities: {dict(zip(model.classes_, proba[0]))}')
    
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
