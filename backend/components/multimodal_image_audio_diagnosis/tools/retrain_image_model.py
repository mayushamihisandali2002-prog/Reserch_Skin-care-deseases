"""
Improved ResNet-50 fine-tuning for 30-class skin disease classification.
Includes:
 - Automatic directory creation
 - Aggressive data augmentation (compensates for small dataset)
 - Learning rate scheduler (CosineAnnealingLR)
 - Best-model checkpointing
 - ResNet-50 backbone for better feature extraction
 - Works from both backend/ and project root
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms, datasets, models
from pathlib import Path
import os

BACKEND_DIR = Path(__file__).resolve().parents[3]

# ─── Paths (auto-detect root vs backend/ as CWD) ──────────────────────────────
_here = Path.cwd()
if (_here / "assets").exists():
    BASE = _here
elif (_here.parent / "backend" / "assets").exists():
    BASE = _here
else:
    BASE = _here

DATA_ROOT = (
    BACKEND_DIR
    / "assets"
    / "data"
    / "multimodal_image_audio_diagnosis"
    / "research_dataset"
)
NEW_MODEL_PATH = (
    BACKEND_DIR
    / "assets"
    / "models"
    / "multimodal_image_audio_diagnosis"
    / "image_best_finetuned.pt"
)

NUM_CLASSES = 30
IMAGE_SIZE  = 224
BATCH_SIZE  = 16
EPOCHS      = 15      # 15 epochs for high-accuracy training with ResNet-50

# ─── Data transforms ──────────────────────────────────────────────────────────
# Heavy augmentation for training (compensates for per-class count)
train_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.6, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(45),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.1),
    transforms.RandomGrayscale(p=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def main():
    # ── Pre-flight checks ─────────────────────────────────────────────────────
    if not DATA_ROOT.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATA_ROOT}. "
            "Run fetch_research_images.py first."
        )
    NEW_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[ResNet] Data  : {DATA_ROOT}")
    print(f"[ResNet] Output: {NEW_MODEL_PATH}")

    # ── Load dataset ──────────────────────────────────────────────────────────
    full_dataset = datasets.ImageFolder(root=DATA_ROOT, transform=train_transform)
    print(f"[ResNet] Found {len(full_dataset)} images across {len(full_dataset.classes)} classes")

    # 80 / 20 split — use augmentation ONLY on train, vanilla on val
    train_size = max(1, int(0.8 * len(full_dataset)))
    val_size   = len(full_dataset) - train_size
    train_idx, val_idx = torch.utils.data.random_split(
        range(len(full_dataset)), [train_size, val_size]
    )

    # Build separate val dataset with no augmentation
    val_dataset_plain = datasets.ImageFolder(root=DATA_ROOT, transform=val_transform)

    from torch.utils.data import Subset
    train_set = Subset(full_dataset,      list(train_idx.indices))
    val_set   = Subset(val_dataset_plain, list(val_idx.indices))

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_set,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # ── Build model (ImageNet pretrained ResNet-50) ──────────────────────────
    print("[ResNet] Loading ImageNet pretrained ResNet-50 …")
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

    # Freeze backbone, only train classifier head initially (1/3 of epochs)
    for name, param in model.named_parameters():
        if "fc" not in name:
            param.requires_grad = False

    model.fc = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.fc.in_features, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, NUM_CLASSES)
    )
    # Put model on device (CPU or CUDA)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    print(f"[ResNet] Using device: {device}")

    # ── Optimiser & scheduler ─────────────────────────────────────────────────
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=1e-3, weight_decay=1e-3
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    best_acc   = 0.0
    unfreeze_epoch = max(1, EPOCHS // 3)   # unfreeze backbone at 1/3 of training

    # ── Training loop ─────────────────────────────────────────────────────────
    for epoch in range(1, EPOCHS + 1):

        # Unfreeze all layers partway through for fine-tuning
        if epoch == unfreeze_epoch:
            print("[ResNet] ❄️  Unfreezing backbone for deep fine-tuning …")
            for param in model.parameters():
                param.requires_grad = True
            # Lower LR for backbone to preserve features
            optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-3)
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS - epoch + 1)

        model.train()
        running_loss = 0.0
        for i, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)
            
            if (i + 1) % 10 == 0:
                print(f"   Batch {i+1}/{len(train_loader)} | Loss: {loss.item():.4f}")
        
        epoch_loss = running_loss / len(train_loader.dataset)

        # Validation
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                total   += labels.size(0)
                correct += (preds == labels).sum().item()

        val_acc = correct / total * 100 if total > 0 else 0.0
        lr_now  = optimizer.param_groups[0]["lr"]
        print(f"Epoch {epoch:2d}/{EPOCHS} | Loss: {epoch_loss:.4f} | Val Acc: {val_acc:.2f}% | LR: {lr_now:.6f}")

        # Save best model
        if val_acc >= best_acc:
            best_acc = val_acc
            torch.save(model, str(NEW_MODEL_PATH))
            print(f"   💾 Saved best model (acc={best_acc:.2f}%)")

        scheduler.step()

    print(f"\n✅ Training complete. Best Val Acc: {best_acc:.2f}%")
    print(f"   Model saved → {NEW_MODEL_PATH}")

if __name__ == "__main__":
    main()
