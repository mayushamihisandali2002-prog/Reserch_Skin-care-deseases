"""
Train a lightweight linear classifier on top of the deployed image model's
visual embeddings.

This is faster than full CNN retraining and lets us verify whether the current
backbone features are stronger than the shipped classifier head.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from inference.config import IMAGE_MODEL_PATH, RESEARCH_DATASET_DIR
from components.multimodal_image_audio_diagnosis.image_model import ResNetImageModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train an embedding-space image head.")
    parser.add_argument(
        "--epochs",
        type=int,
        default=40,
        help="Number of epochs for the linear head.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for embedding-head training.",
    )
    parser.add_argument(
        "--rebuild-embeddings",
        action="store_true",
        help="Recompute embedding cache even if it already exists.",
    )
    return parser.parse_args()


def topk_accuracy(logits: torch.Tensor, labels: torch.Tensor, k: int) -> float:
    topk = torch.topk(logits, k=k, dim=1).indices
    hits = (topk == labels.unsqueeze(1)).any(dim=1)
    return float(hits.float().mean().item())


def extract_embeddings(
    model: ResNetImageModel,
    cache_path: Path,
    rebuild: bool,
) -> tuple[np.ndarray, np.ndarray]:
    if cache_path.exists() and not rebuild:
        cached = np.load(cache_path, allow_pickle=False)
        return cached["embeddings"].astype(np.float32), cached["labels"].astype(np.int64)

    dataset = datasets.ImageFolder(root=str(model.dataset_dir), transform=model.transform)
    loader = DataLoader(dataset, batch_size=16, shuffle=False, num_workers=0)

    embeddings: list[np.ndarray] = []
    labels: list[np.ndarray] = []

    with torch.no_grad():
        for images, batch_labels in loader:
            _, features = model._forward_logits_and_features(images, torch)
            feature_batch = features.cpu().numpy().astype(np.float32)
            feature_batch /= np.clip(
                np.linalg.norm(feature_batch, axis=1, keepdims=True),
                1e-8,
                None,
            )
            embeddings.append(feature_batch)
            labels.append(batch_labels.cpu().numpy().astype(np.int64))

    all_embeddings = np.concatenate(embeddings, axis=0)
    all_labels = np.concatenate(labels, axis=0)
    np.savez(cache_path, embeddings=all_embeddings, labels=all_labels)
    return all_embeddings, all_labels


def train_head(
    features: np.ndarray,
    labels: np.ndarray,
    num_classes: int,
    epochs: int,
    batch_size: int,
) -> tuple[dict[str, torch.Tensor], dict[str, float], int]:
    x_train, x_val, y_train, y_val = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    x_train = torch.from_numpy(x_train).float()
    y_train = torch.from_numpy(y_train).long()
    x_val = torch.from_numpy(x_val).float()
    y_val = torch.from_numpy(y_val).long()

    train_dataset = torch.utils.data.TensorDataset(x_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    head = nn.Linear(features.shape[1], num_classes)
    optimizer = torch.optim.AdamW(head.parameters(), lr=2e-3, weight_decay=1e-3)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)

    best_state = None
    best_metrics = {"val_top1": 0.0, "val_top3": 0.0}
    best_epoch = 1

    for epoch in range(1, epochs + 1):
        head.train()
        for batch_features, batch_labels in train_loader:
            optimizer.zero_grad()
            logits = head(batch_features)
            loss = criterion(logits, batch_labels)
            loss.backward()
            optimizer.step()

        head.eval()
        with torch.no_grad():
            val_logits = head(x_val)
            val_top1 = float((val_logits.argmax(dim=1) == y_val).float().mean().item())
            val_top3 = topk_accuracy(val_logits, y_val, k=min(3, num_classes))

        if (
            val_top1 > best_metrics["val_top1"]
            or (
                abs(val_top1 - best_metrics["val_top1"]) < 1e-6
                and val_top3 >= best_metrics["val_top3"]
            )
        ):
            best_state = {
                "weight": head.weight.detach().clone(),
                "bias": head.bias.detach().clone(),
            }
            best_metrics = {
                "val_top1": round(val_top1, 4),
                "val_top3": round(val_top3, 4),
            }
            best_epoch = epoch

    return best_state, best_metrics, best_epoch


def train_final_head(
    features: np.ndarray,
    labels: np.ndarray,
    num_classes: int,
    epochs: int,
    batch_size: int,
) -> nn.Linear:
    x_all = torch.from_numpy(features).float()
    y_all = torch.from_numpy(labels).long()
    dataset = torch.utils.data.TensorDataset(x_all, y_all)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    head = nn.Linear(features.shape[1], num_classes)
    optimizer = torch.optim.AdamW(head.parameters(), lr=2e-3, weight_decay=1e-3)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)

    for _ in range(epochs):
        head.train()
        for batch_features, batch_labels in loader:
            optimizer.zero_grad()
            logits = head(batch_features)
            loss = criterion(logits, batch_labels)
            loss.backward()
            optimizer.step()

    return head


def main() -> None:
    args = parse_args()
    torch.manual_seed(42)
    np.random.seed(42)

    model = ResNetImageModel(model_path=IMAGE_MODEL_PATH, dataset_dir=RESEARCH_DATASET_DIR)
    if not model.loaded:
        raise RuntimeError("Base image model failed to load.")

    cache_path = IMAGE_MODEL_PATH.with_name(f"{IMAGE_MODEL_PATH.stem}_embeddings.npz")
    output_path = IMAGE_MODEL_PATH.with_name(f"{IMAGE_MODEL_PATH.stem}_embedding_head.npz")
    metrics_path = IMAGE_MODEL_PATH.with_name(f"{IMAGE_MODEL_PATH.stem}_embedding_head.json")

    embeddings, labels = extract_embeddings(model, cache_path, rebuild=args.rebuild_embeddings)
    best_state, best_metrics, best_epoch = train_head(
        embeddings,
        labels,
        model.output_classes,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    final_head = train_final_head(
        embeddings,
        labels,
        model.output_classes,
        epochs=best_epoch,
        batch_size=args.batch_size,
    )

    np.savez(
        output_path,
        weight=final_head.weight.detach().cpu().numpy().astype(np.float32),
        bias=final_head.bias.detach().cpu().numpy().astype(np.float32),
        labels=np.asarray(
            [model.source_label_map[idx] for idx in range(len(model.source_label_map))],
            dtype="<U64",
        ),
        best_epoch=np.asarray([best_epoch], dtype=np.int32),
    )

    metrics = {
        "embedding_dim": int(embeddings.shape[1]),
        "samples": int(len(labels)),
        "classes": int(model.output_classes),
        "best_epoch": int(best_epoch),
        "holdout_top1": best_metrics["val_top1"],
        "holdout_top3": best_metrics["val_top3"],
        "output_path": str(output_path),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
