from datasets import load_dataset
from collections import Counter

def list_dermnet_labels():
    print("[Data] Loading DermNet dataset info...")
    ds = load_dataset('exper1ment/dermnet', split='train')
    names = ds.features['label'].names
    labels = ds['label']
    counts = Counter(labels)
    
    print("\n--- DermNet Training Labels ---")
    for i in range(len(names)):
        count = counts.get(i, 0)
        print(f"{i}: {names[i]} ({count} samples)")

if __name__ == "__main__":
    list_dermnet_labels()
