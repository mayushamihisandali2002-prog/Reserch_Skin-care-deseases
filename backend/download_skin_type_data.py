from datasets import load_dataset
import os
from pathlib import Path
from PIL import Image
from tqdm import tqdm

def download_skin_types():
    print("[Data] Downloading skin type dataset from HF...")
    try:
        from datasets import load_dataset
        print("[Data] Streaming dima806/skin_types_image_detection...")
        ds = load_dataset("dima806/skin_types_image_detection", split="train", streaming=True)
        
        output_dir = Path("assets/data/skin_types")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # dima806 labels: 0:dry, 1:normal, 2:oily
        label_map = {0: "dry", 1: "normal", 2: "oily"}
        
        counts = {k: 0 for k in label_map.values()}
        limit_per_class = 200 # Sufficient for a demo/stable training
        
        print(f"[Data] Saving up to {limit_per_class} images per class to {output_dir}...")
        for i, item in enumerate(ds):
            # Debug: print the FIRST item structure
            if i == 0:
                print(f"[Debug] First sample keys: {item.keys()}")
                print(f"[Debug] First sample label: {item['label']} (type: {type(item['label'])})")
                
            label_id = item["label"]
            
            # If label_id is already a string like "Combination"
            if isinstance(label_id, str):
                label_name = label_id.lower()
            else:
                label_name = label_map.get(label_id, "unknown")
            
            if label_name not in counts:
                print(f"[Warning] Unknown label: {label_name}")
                counts[label_name] = 0 # add it
                
            if counts[label_name] >= limit_per_class:
                if all(c >= limit_per_class for c in counts.values() if c < 1000): # only check expected
                    break
                continue
                
            class_dir = output_dir / label_name
            class_dir.mkdir(exist_ok=True)
            
            image = item["image"]
            image_path = class_dir / f"img_{counts[label_name]}.jpg"
            image.save(image_path)
            counts[label_name] += 1
            
            if i % 10 == 0:
                print(f"   Progress: {counts}", end="\r")
                
        print("\n[Done] Skin type dataset prepared.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_skin_types()
