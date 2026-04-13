from __future__ import annotations

import argparse
import json
import random
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from inference.config import IMAGE_MODEL_PATH, RESEARCH_DATASET_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Continue fine-tuning the deployed image model on a fixed split."
    )
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=IMAGE_MODEL_PATH.with_name("image_best_finetuned_candidate.pt"),
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=IMAGE_MODEL_PATH.with_name("image_best_finetuned_candidate.json"),
    )
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def build_transforms(image_size: int = 224) -> tuple[transforms.Compose, transforms.Compose]:
    train_transform = transforms.Compose(
        [
            transforms.Resize((256, 256)),
            transforms.RandomResizedCrop(image_size, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )
    return train_transform, val_transform


def freeze_for_cpu_finetuning(model: nn.Module) -> None:
    for param in model.parameters():
        param.requires_grad = False

    for module in [model.layer4, model.fc]:
        for param in module.parameters():
            param.requires_grad = True


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, float]:
    model.eval()
    correct = 0
    total = 0
    top3_hits = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=1)
            preds = probs.argmax(dim=1)
            correct += int((preds == labels).sum().item())
            total += int(labels.size(0))
            top3 = torch.topk(probs, k=min(3, probs.shape[1]), dim=1).indices
            top3_hits += int((top3 == labels.unsqueeze(1)).any(dim=1).sum().item())

    if total == 0:
        return 0.0, 0.0
    return correct / total, top3_hits / total


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    if not IMAGE_MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {IMAGE_MODEL_PATH}")
    if not RESEARCH_DATASET_DIR.exists():
        raise FileNotFoundError(f"Dataset not found: {RESEARCH_DATASET_DIR}")

    train_transform, val_transform = build_transforms()
    train_dataset_full = datasets.ImageFolder(
        root=str(RESEARCH_DATASET_DIR),
        transform=train_transform,
    )
    val_dataset_full = datasets.ImageFolder(
        root=str(RESEARCH_DATASET_DIR),
        transform=val_transform,
    )

    indices = np.arange(len(train_dataset_full))
    labels = np.asarray(train_dataset_full.targets)
    train_idx, val_idx = train_test_split(
        indices,
        test_size=0.2,
        random_state=args.seed,
        stratify=labels,
    )

    train_loader = DataLoader(
        Subset(train_dataset_full, train_idx.tolist()),
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
    )
    val_loader = DataLoader(
        Subset(val_dataset_full, val_idx.tolist()),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    device = torch.device("cpu")
    model = torch.load(IMAGE_MODEL_PATH, map_location=device, weights_only=False)
    freeze_for_cpu_finetuning(model)
    model = model.to(device)

    optimizer = optim.AdamW(
        [
            {"params": model.layer4.parameters(), "lr": 2e-5},
            {"params": model.fc.parameters(), "lr": 2e-4},
        ],
        weight_decay=1e-4,
    )
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_state = deepcopy(model).cpu()
    best_top1, best_top3 = evaluate(model, val_loader, device)
    history: list[dict[str, float]] = [
        {"epoch": 0, "val_top1": round(best_top1, 4), "val_top3": round(best_top3, 4)}
    ]

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            running_loss += float(loss.item()) * int(images.size(0))

        scheduler.step()
        val_top1, val_top3 = evaluate(model, val_loader, device)
        epoch_loss = running_loss / max(len(train_idx), 1)
        history.append(
            {
                "epoch": epoch,
                "train_loss": round(epoch_loss, 4),
                "val_top1": round(val_top1, 4),
                "val_top3": round(val_top3, 4),
            }
        )
        print(
            f"epoch={epoch} train_loss={epoch_loss:.4f} "
            f"val_top1={val_top1:.4f} val_top3={val_top3:.4f}"
        )

        if (val_top1, val_top3) >= (best_top1, best_top3):
            best_top1, best_top3 = val_top1, val_top3
            best_state = deepcopy(model).cpu()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(best_state, args.output)

    metrics = {
        "source_model": str(IMAGE_MODEL_PATH),
        "candidate_model": str(args.output),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "seed": args.seed,
        "train_samples": int(len(train_idx)),
        "val_samples": int(len(val_idx)),
        "best_val_top1": round(best_top1, 4),
        "best_val_top3": round(best_top3, 4),
        "history": history,
    }
    args.metrics_output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
