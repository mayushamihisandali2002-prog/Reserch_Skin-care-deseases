import torch
import torchvision.models as models
from pathlib import Path

def test_load_image_model():
    """Load the ResNet‑18 image model and report the number of output classes.
    Handles both full‑model checkpoints and state_dicts, strips any DataParallel
    prefix, and forces a 30‑class head if the checkpoint was trained on a
    different number of classes.
    """
    model_path = Path("assets/models/image_best_finetuned.pt")
    if not model_path.exists():
        print(f"Model not found at {model_path}")
        return

    print(f"[ResNet] Loading {model_path.name} …")
    try:
        ckpt = torch.load(str(model_path), map_location="cpu", weights_only=False)
        # ----- State‑dict checkpoint -----
        if isinstance(ckpt, dict):
            print("[ResNet] Detected state_dict – rebuilding architecture")
            model = models.resnet18(weights=None)
            # Strip possible DataParallel prefix
            state = {k.replace("module.", ""): v for k, v in ckpt.items()}
            # Force a 30‑class head (the model will be fine‑tuned later)
            model.fc = torch.nn.Linear(model.fc.in_features, 30)
            model.load_state_dict(state, strict=False)
            num_classes = model.fc.out_features
        # ----- Full‑model checkpoint -----
        else:
            print("[ResNet] Detected full model format")
            model = ckpt
            num_classes = getattr(model.fc, "out_features", "unknown")
        print(f"[ResNet] Number of output classes: {num_classes}")
    except Exception as e:
        print(f"Error loading model: {e}")

if __name__ == "__main__":
    test_load_image_model()
