#!/usr/bin/env python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import timm
from pathlib import Path
import json
import argparse

def train_skin_type(data_dir, output_path, epochs=10, batch_size=16, lr=1e-4):
    data_dir = Path(data_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    dataset = datasets.ImageFolder(str(data_dir), transform=transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    
    num_classes = len(dataset.classes)
    label_map = {name: i for i, name in enumerate(dataset.classes)}
    print(f"[Training] Classes: {dataset.classes}")

    # Using convnext_tiny as expected by the inference code
    print("[Model] Initializing convnext_tiny...")
    model = timm.create_model("convnext_tiny", pretrained=True, num_classes=num_classes)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Model] Using device: {device}")
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr)

    print(f"[Training] Starting - {epochs} epochs")
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * imgs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += imgs.size(0)
            
        print(f"  Epoch {epoch} | Loss: {running_loss/total:.4f} | Acc: {correct/total*100:.2f}%")

    # Save in the specific format expected by SkinTypeModel
    checkpoint = {
        "model_name": "convnext_tiny",
        "model_state": model.state_dict(),
        "label_map": label_map
    }
    torch.save(checkpoint, str(output_path))
    
    # Also save label map as JSON
    label_map_path = output_path.parent / "label_map_skin_type.json"
    with open(label_map_path, "w") as f:
        json.dump(label_map, f, indent=2)
        
    print(f"[Done] Model saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default="assets/data/skin_types")
    parser.add_argument("--output-path", type=str, default="assets/models/skin_type/skin_type_convnext_cleaned_best.pt")
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()
    
    train_skin_type(args.data_dir, args.output_path, epochs=args.epochs)
