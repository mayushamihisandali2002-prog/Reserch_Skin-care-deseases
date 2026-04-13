from __future__ import annotations

import argparse
import json
import random
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, log_loss, top_k_accuracy_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets


BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from components.multimodal_image_audio_diagnosis.image_model import ResNetImageModel
from inference.config import IMAGE_MODEL_PATH, RESEARCH_DATASET_DIR


class FeatureMLPHead(nn.Module):
    def __init__(self, input_dim: int, num_classes: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train an MLP classifier head on raw ResNet image features."
    )
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--cache-path",
        type=Path,
        default=IMAGE_MODEL_PATH.with_name("image_best_finetuned_raw_features.npz"),
    )
    parser.add_argument(
        "--output-model",
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


def extract_raw_features(
    image_model: ResNetImageModel,
    cache_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    if cache_path.exists():
        cached = np.load(cache_path, allow_pickle=False)
        return cached["features"].astype(np.float32), cached["labels"].astype(np.int64)

    dataset = datasets.ImageFolder(
        root=str(image_model.dataset_dir),
        transform=image_model.transform,
    )
    loader = DataLoader(dataset, batch_size=16, shuffle=False, num_workers=0)

    features: list[np.ndarray] = []
    labels: list[np.ndarray] = []

    with torch.no_grad():
        for images, batch_labels in loader:
            _, batch_features = image_model._forward_logits_and_features(images, torch)
            features.append(batch_features.cpu().numpy().astype(np.float32))
            labels.append(batch_labels.cpu().numpy().astype(np.int64))

    all_features = np.concatenate(features, axis=0)
    all_labels = np.concatenate(labels, axis=0)
    np.savez(cache_path, features=all_features, labels=all_labels)
    return all_features, all_labels


def fit_head(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    num_classes: int,
    epochs: int,
    batch_size: int,
) -> tuple[FeatureMLPHead, dict[str, float], int]:
    model = FeatureMLPHead(x_train.shape[1], num_classes)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.03)

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train)),
        batch_size=batch_size,
        shuffle=True,
    )

    best_state = deepcopy(model.state_dict())
    best_top1 = 0.0
    best_top3 = 0.0
    best_epoch = 1

    for epoch in range(1, epochs + 1):
        model.train()
        for batch_features, batch_labels in train_loader:
            optimizer.zero_grad()
            logits = model(batch_features)
            loss = criterion(logits, batch_labels)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_logits = model(torch.from_numpy(x_val))
            val_probs = torch.softmax(val_logits, dim=1).numpy()

        top1 = float(accuracy_score(y_val, val_probs.argmax(axis=1)))
        top3 = float(
            top_k_accuracy_score(
                y_val,
                val_probs,
                k=3,
                labels=list(range(num_classes)),
            )
        )
        print(f"epoch={epoch} val_top1={top1:.4f} val_top3={top3:.4f}")

        if (top1, top3) >= (best_top1, best_top3):
            best_top1 = top1
            best_top3 = top3
            best_epoch = epoch
            best_state = deepcopy(model.state_dict())

    best_model = FeatureMLPHead(x_train.shape[1], num_classes)
    best_model.load_state_dict(best_state)
    return (
        best_model,
        {"top1": round(best_top1, 4), "top3": round(best_top3, 4)},
        best_epoch,
    )


def tune_blend_alpha(
    image_model: ResNetImageModel,
    logits: np.ndarray,
    features: np.ndarray,
    labels: np.ndarray,
    num_classes: int,
) -> dict[str, float]:
    proto_rows: list[np.ndarray] = []
    for feature in features:
        proto = image_model._prototype_probabilities(feature)
        if proto is None:
            proto = np.zeros(num_classes, dtype=np.float32)
        proto_rows.append(proto)

    prototype_probs = np.stack(proto_rows, axis=0)
    best_metrics: dict[str, float] | None = None

    def expected_calibration_error(
        confidences: np.ndarray,
        correctness: np.ndarray,
        num_bins: int = 10,
    ) -> float:
        ece = 0.0
        total = len(confidences)
        for bin_index in range(num_bins):
            lower = bin_index / num_bins
            upper = (bin_index + 1) / num_bins
            mask = (
                ((confidences >= lower) & (confidences < upper))
                | ((bin_index == num_bins - 1) & (confidences == 1.0))
            )
            if not np.any(mask):
                continue
            bin_conf = float(np.mean(confidences[mask]))
            bin_acc = float(np.mean(correctness[mask]))
            ece += (float(np.sum(mask)) / total) * abs(bin_acc - bin_conf)
        return float(ece)

    for temperature in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0):
        scaled_logits = logits / temperature
        scaled_logits = scaled_logits - np.max(scaled_logits, axis=1, keepdims=True)
        exp_scores = np.exp(scaled_logits)
        head_probs = exp_scores / np.clip(
            np.sum(exp_scores, axis=1, keepdims=True),
            1e-8,
            None,
        )

        for alpha in np.arange(0.0, 1.01, 0.05):
            mixed = (alpha * head_probs) + ((1.0 - alpha) * prototype_probs)
            mixed = mixed / np.clip(mixed.sum(axis=1, keepdims=True), 1e-8, None)
            predictions = mixed.argmax(axis=1)
            confidences = mixed[np.arange(len(mixed)), predictions]
            correctness = (predictions == labels).astype(np.float32)
            top1 = float(accuracy_score(labels, predictions))
            top3 = float(
                top_k_accuracy_score(
                    labels,
                    mixed,
                    k=3,
                    labels=list(range(num_classes)),
                )
            )
            calibration_error = expected_calibration_error(confidences, correctness)
            nll = float(log_loss(labels, mixed, labels=list(range(num_classes))))
            metrics = {
                "logit_temperature": round(float(temperature), 2),
                "logit_blend_weight": round(float(alpha), 2),
                "prototype_blend_weight": round(float(1.0 - alpha), 2),
                "top1": round(top1, 4),
                "top3": round(top3, 4),
                "ece": round(calibration_error, 4),
                "nll": round(nll, 4),
            }
            if best_metrics is None:
                best_metrics = metrics
                continue
            if (
                metrics["top1"],
                -metrics["ece"],
                metrics["top3"],
                -metrics["nll"],
            ) > (
                best_metrics["top1"],
                -best_metrics["ece"],
                best_metrics["top3"],
                -best_metrics["nll"],
            ):
                best_metrics = metrics

    assert best_metrics is not None
    return best_metrics


def train_final_head(
    features: np.ndarray,
    labels: np.ndarray,
    num_classes: int,
    batch_size: int,
    epochs: int,
) -> FeatureMLPHead:
    model = FeatureMLPHead(features.shape[1], num_classes)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.03)

    loader = DataLoader(
        TensorDataset(torch.from_numpy(features), torch.from_numpy(labels)),
        batch_size=batch_size,
        shuffle=True,
    )

    for _ in range(epochs):
        model.train()
        for batch_features, batch_labels in loader:
            optimizer.zero_grad()
            logits = model(batch_features)
            loss = criterion(logits, batch_labels)
            loss.backward()
            optimizer.step()

    return model


def inject_head(base_model: nn.Module, trained_head: FeatureMLPHead) -> nn.Module:
    deployed = deepcopy(base_model)
    deployed.fc = nn.Sequential(
        nn.Linear(2048, 512),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(512, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, 30),
    )
    deployed.fc.load_state_dict(trained_head.layers.state_dict())
    return deployed


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    image_model = ResNetImageModel(IMAGE_MODEL_PATH, RESEARCH_DATASET_DIR)
    if not image_model.loaded:
        raise RuntimeError("Base image model failed to load.")

    features, labels = extract_raw_features(image_model, args.cache_path)
    num_classes = len(np.unique(labels))

    x_train, x_val, y_train, y_val = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=args.seed,
        stratify=labels,
    )

    best_model, holdout_metrics, best_epoch = fit_head(
        x_train,
        y_train,
        x_val,
        y_val,
        num_classes=num_classes,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )

    with torch.no_grad():
        val_logits = best_model(torch.from_numpy(x_val))
        val_logits_np = val_logits.numpy().astype(np.float32)

    operating_point = tune_blend_alpha(
        image_model=image_model,
        logits=val_logits_np,
        features=x_val,
        labels=y_val,
        num_classes=num_classes,
    )

    final_head = train_final_head(
        features,
        labels,
        num_classes=num_classes,
        batch_size=args.batch_size,
        epochs=best_epoch,
    )

    base_model = torch.load(IMAGE_MODEL_PATH, map_location="cpu", weights_only=False)
    candidate_model = inject_head(base_model, final_head)
    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    torch.save(candidate_model, args.output_model)

    metrics = {
        "source_model": str(IMAGE_MODEL_PATH),
        "candidate_model": str(args.output_model),
        "cache_path": str(args.cache_path),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "seed": args.seed,
        "samples": int(len(labels)),
        "classes": int(num_classes),
        "holdout_head_metrics": holdout_metrics,
        "best_epoch": int(best_epoch),
        "recommended_operating_point": operating_point,
        "recommended_blend": {
            "alpha_logits": operating_point["logit_blend_weight"],
            "top1": operating_point["top1"],
            "top3": operating_point["top3"],
        },
    }
    args.metrics_output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
