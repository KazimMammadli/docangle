"""
Downloads the Tobacco3482 real-document data set from Hugging Face and makes a stratified
train/val/test split (80/10/10, seed 42), then generates the procedural background textures that
the photo simulator (bench/degrade.py) uses.

Data-leak protection:
  - every document belongs to exactly ONE split (train, val or test)
  - the category balance is kept proportional in every split (stratified)
  - the split is recorded in split_info.json
  - assertions confirm that the splits do not intersect
"""
import os
import json
import random
import numpy as np
from PIL import Image, ImageFilter
from sklearn.model_selection import train_test_split
from datasets import load_dataset
from tqdm import tqdm

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SPLITS_DIR = os.path.join(DATA_DIR, "splits")
TRAIN_DIR = os.path.join(SPLITS_DIR, "train")
VAL_DIR = os.path.join(SPLITS_DIR, "val")
TEST_DIR = os.path.join(SPLITS_DIR, "test")
BGS_DIR = os.path.join(DATA_DIR, "backgrounds")
SPLIT_INFO_PATH = os.path.join(SPLITS_DIR, "split_info.json")

SEED = 42


def download_and_split_tobacco3482():
    """
    Download Tobacco3482, split it (stratified) and save the pages.
    """
    print("=" * 65)
    print("Downloading the Tobacco3482 real-document data set...")
    print("   Source: Hugging Face 'maveriq/tobacco3482'")
    print("=" * 65)

    # 1. Load the data set
    ds = load_dataset("maveriq/tobacco3482", split="train")
    label_names = ds.features["label"].names
    print(f"{len(ds)} documents found. Categories: {label_names}")

    # 2. List all documents with their indices and labels
    indices = list(range(len(ds)))
    labels = [ds[i]["label"] for i in indices]

    # 3. Stratified split: 80% train, 10% val, 10% test
    random.seed(SEED)
    np.random.seed(SEED)

    train_idx, temp_idx, train_labels, temp_labels = train_test_split(
        indices, labels, test_size=0.20, stratify=labels, random_state=SEED
    )
    val_idx, test_idx, _, _ = train_test_split(
        temp_idx, temp_labels, test_size=0.50, stratify=temp_labels, random_state=SEED
    )

    print("\nSplit result:")
    print(f"   Train: {len(train_idx)} documents ({len(train_idx)/len(ds)*100:.1f}%)")
    print(f"   Val:   {len(val_idx)} documents ({len(val_idx)/len(ds)*100:.1f}%)")
    print(f"   Test:  {len(test_idx)} documents ({len(test_idx)/len(ds)*100:.1f}%)")

    # 4. Data-leak check
    train_set = set(train_idx)
    val_set = set(val_idx)
    test_set = set(test_idx)
    assert len(train_set & val_set) == 0, "DATA LEAK: train and val intersect"
    assert len(train_set & test_set) == 0, "DATA LEAK: train and test intersect"
    assert len(val_set & test_set) == 0, "DATA LEAK: val and test intersect"
    assert len(train_set) + len(val_set) + len(test_set) == len(ds), "documents were lost in the split"
    print("Data-leak check passed (no intersection)")

    # 5. Save every split to disk
    split_info = {"seed": SEED, "total": len(ds), "label_names": label_names, "splits": {}}

    for split_name, split_indices, split_dir in [
        ("train", train_idx, TRAIN_DIR),
        ("val", val_idx, VAL_DIR),
        ("test", test_idx, TEST_DIR),
    ]:
        os.makedirs(split_dir, exist_ok=True)
        category_counts = {}
        filenames = []

        for idx in tqdm(split_indices, desc=f"  saving {split_name}"):
            item = ds[idx]
            img = item["image"].convert("RGB")
            label_id = item["label"]
            label_str = label_names[label_id]

            category_counts[label_str] = category_counts.get(label_str, 0) + 1
            filename = f"{label_str}_{idx:04d}.jpg"
            filenames.append(filename)
            img.save(os.path.join(split_dir, filename), quality=95)

        split_info["splits"][split_name] = {
            "count": len(split_indices),
            "categories": category_counts,
            "files": filenames,
        }

        print(f"   {split_name}: {dict(sorted(category_counts.items()))}")

    # 6. Write the split information as JSON
    with open(SPLIT_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(split_info, f, ensure_ascii=False, indent=2)
    print(f"\nSplit information saved: {SPLIT_INFO_PATH}")

    # 7. Final data-leak check, by file name
    train_files = set(split_info["splits"]["train"]["files"])
    val_files = set(split_info["splits"]["val"]["files"])
    test_files = set(split_info["splits"]["test"]["files"])
    assert len(train_files & val_files) == 0, "FILE DATA LEAK: train and val intersect"
    assert len(train_files & test_files) == 0, "FILE DATA LEAK: train and test intersect"
    assert len(val_files & test_files) == 0, "FILE DATA LEAK: val and test intersect"
    print("File-name data-leak check passed")

    print("\n" + "=" * 65)
    print("Tobacco3482 downloaded and split.")
    print("=" * 65)


def generate_realistic_backgrounds(count=20):
    """
    Generate desk, scanner and office background textures (procedural, so they can be shared).
    """
    print(f"\nGenerating {count} background textures...")
    os.makedirs(BGS_DIR, exist_ok=True)

    for idx in range(count):
        bg_w, bg_h = 1024, 1024
        bg_type = idx % 5  # 5 different types

        if bg_type == 0:
            # wooden desk
            base_r = random.randint(110, 170)
            base_g = random.randint(70, 110)
            base_b = random.randint(40, 75)
            arr = np.zeros((bg_h, bg_w, 3), dtype=np.float32)
            noise = np.random.normal(0, 12, (bg_h, 1)).astype(np.float32)
            import cv2
            grain = cv2.resize(noise, (bg_w, bg_h))
            arr[:, :, 0] = np.clip(base_r + grain, 0, 255)
            arr[:, :, 1] = np.clip(base_g + grain * 0.7, 0, 255)
            arr[:, :, 2] = np.clip(base_b + grain * 0.4, 0, 255)
            img = Image.fromarray(arr.astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(radius=0.8)
            )
        elif bg_type == 1:
            # grey / charcoal office desk
            base_val = random.randint(50, 180)
            noise = np.clip(
                np.random.normal(base_val, 8, (bg_h, bg_w, 3)), 0, 255
            ).astype(np.uint8)
            img = Image.fromarray(noise).filter(ImageFilter.GaussianBlur(radius=0.5))
        elif bg_type == 2:
            # marble / granite surface
            base_val = random.randint(180, 230)
            arr = np.full((bg_h, bg_w, 3), base_val, dtype=np.float32)
            veins = np.random.normal(0, 25, (bg_h, bg_w, 3)).astype(np.float32)
            arr = np.clip(arr + veins, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=1.5))
        elif bg_type == 3:
            # dark leather desk mat
            base_r = random.randint(30, 60)
            base_g = random.randint(30, 60)
            base_b = random.randint(35, 70)
            noise = np.random.normal(0, 5, (bg_h, bg_w, 3)).astype(np.float32)
            arr = np.zeros((bg_h, bg_w, 3), dtype=np.float32)
            arr[:, :, 0] = np.clip(base_r + noise[:, :, 0], 0, 255)
            arr[:, :, 1] = np.clip(base_g + noise[:, :, 1], 0, 255)
            arr[:, :, 2] = np.clip(base_b + noise[:, :, 2], 0, 255)
            img = Image.fromarray(arr.astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(radius=0.4)
            )
        else:
            # scanner bed (white / light grey, flatbed scanner)
            base_val = random.randint(235, 252)
            noise = np.random.normal(0, 2, (bg_h, bg_w, 3)).astype(np.float32)
            arr = np.clip(base_val + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)

        img.save(os.path.join(BGS_DIR, f"bg_texture_{idx:03d}.jpg"), quality=90)

    print(f"{count} background textures written to {BGS_DIR}")


if __name__ == "__main__":
    print("=" * 65)
    print("Preparing the Tobacco3482 data set")
    print("=" * 65)
    download_and_split_tobacco3482()
    generate_realistic_backgrounds(count=20)
    print("\n" + "=" * 65)
    print(f"Train pages: {TRAIN_DIR}")
    print(f"Val pages:   {VAL_DIR}")
    print(f"Test pages:  {TEST_DIR}")
    print(f"Backgrounds: {BGS_DIR}")
    print("=" * 65)
