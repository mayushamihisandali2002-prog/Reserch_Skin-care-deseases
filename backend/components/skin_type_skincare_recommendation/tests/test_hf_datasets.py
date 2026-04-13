import os
from datasets import load_dataset

datasets_to_try = [
    "joshuachou/SkinCAP",
    "redlessone/Derm1M",
    "isic-archive/isic-2019",
]

for ds_name in datasets_to_try:
    print(f"Trying {ds_name}...")
    try:
        ds = load_dataset(ds_name, split="train", streaming=True)
        # Try to get one item
        for item in ds:
            print(f"SUCCESS: {ds_name} is accessible. Labels: {item.keys()}")
            break
    except Exception as e:
        print(f"FAILED: {ds_name}. Error: {e}")
