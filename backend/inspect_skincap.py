from datasets import load_dataset

def check_skincap():
    print("[Data] Checking joshuachou/SkinCAP...")
    ds = load_dataset("joshuachou/SkinCAP", split="train", streaming=True)
    first = next(iter(ds))
    print(f"Keys: {first.keys()}")
    if 'label' in first:
        print(f"Label: {first['label']}")
    if 'caption' in first:
        print(f"Caption: {first['caption']}")

if __name__ == "__main__":
    check_skincap()
