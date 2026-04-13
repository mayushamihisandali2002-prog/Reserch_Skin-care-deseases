import torch
from pathlib import Path

def test_load_skin_type_model():
    model_path = (
        Path(__file__).resolve().parents[3]
        / "assets"
        / "models"
        / "skin_type_skincare_recommendation"
        / "skin_type"
        / "skin_type_convnext_cleaned_best.pt"
    )
    if not model_path.exists():
        print(f"Model not found at {model_path}")
        return
        
    print(f"Loading {model_path}...")
    try:
        # Load the checkpoint
        checkpoint = torch.load(str(model_path), map_location="cpu", weights_only=False)
        print(f"Keys in checkpoint: {checkpoint.keys()}")
        
        if "model_name" in checkpoint:
            print(f"Model Name: {checkpoint['model_name']}")
        if "label_map" in checkpoint:
            print(f"Label Map: {checkpoint['label_map']}")
            
    except Exception as e:
        print(f"Error loading model: {e}")

if __name__ == "__main__":
    test_load_skin_type_model()
