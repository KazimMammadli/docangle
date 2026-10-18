import os
import sys
import cv2

# IMPORTANT: switch off OpenCV's own threading, to avoid clashes between PyTorch num_workers
# and OpenCV threads (and a CPU deadlock).
cv2.setNumThreads(0)

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import argparse
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.dataset import DocumentRotationDataset
from src.model import DocumentAngleModel, compute_angular_error_deg


def train_angle_model(
    train_doc_dir="data/splits/train",
    val_doc_dir="data/splits/val",
    bg_dir="data/backgrounds",
    epochs=15,
    batch_size=32,
    lr=1e-3,
    samples_per_epoch=5000,
    val_samples=600,
    angle_range=180.0,
    img_size=256,
    backbone="large",
    checkpoint_path="best_model.pth",
    onnx_path="document_angle_detector.onnx"
):
    # Data-leak check: the train and val folders must differ
    train_abs = os.path.abspath(train_doc_dir)
    val_abs = os.path.abspath(val_doc_dir)
    assert train_abs != val_abs, "DATA LEAK: train and val are the same folder"

    # The train and val file lists must not intersect
    train_files = set(os.listdir(train_abs)) if os.path.isdir(train_abs) else set()
    val_files = set(os.listdir(val_abs)) if os.path.isdir(val_abs) else set()
    overlap = train_files & val_files
    assert len(overlap) == 0, f"DATA LEAK: {len(overlap)} shared files found: {list(overlap)[:5]}"

    # Enable TensorFloat32 for Ampere / RTX 3060 Tensor Cores
    if torch.cuda.is_available():
        torch.set_float32_matmul_precision("high")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = (device.type == "cuda")

    train_doc_count = len([f for f in os.listdir(train_abs) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]) if os.path.isdir(train_abs) else 0
    val_doc_count = len([f for f in os.listdir(val_abs) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]) if os.path.isdir(val_abs) else 0

    print("=" * 65)
    print(f"Document angle training starts | device: {device}")
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print("   Optimisation: TensorFloat-32 + FP16 mixed precision (AMP)")
    print(f"   Angle range: [-{angle_range}, +{angle_range}] degrees (full 360 supported)")
    print(f"   Epoxalar: {epochs}, Batch Size: {batch_size}")
    print(f"   Train documents: {train_doc_count} ({samples_per_epoch} samples per epoch)")
    print(f"   Val documents: {val_doc_count} ({val_samples} samples per epoch)")
    print("   Data-leak check passed (train and val do not intersect)")
    print("=" * 65)

    # Prepare datasets and loaders
    train_dataset = DocumentRotationDataset(
        doc_dir_or_images=train_doc_dir,
        bg_dir_or_images=bg_dir,
        samples_per_epoch=samples_per_epoch,
        img_size=img_size,
        angle_range=angle_range,
        is_train=True
    )
    val_dataset = DocumentRotationDataset(
        doc_dir_or_images=val_doc_dir,
        bg_dir_or_images=bg_dir,
        samples_per_epoch=val_samples,
        img_size=img_size,
        angle_range=angle_range,
        is_train=False
    )

    num_workers = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=(num_workers > 0),
        drop_last=True  # guard: a last batch of one sample would break the BatchNorm layers
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=(num_workers > 0)
    )

    # Initialize model, loss, optimizer, scaler, scheduler
    model = DocumentAngleModel(backbone=backbone, pretrained=True).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_mae = float("inf")
    start_total_time = time.time()

    try:
        for epoch in range(1, epochs + 1):
            epoch_start = time.time()
            model.train()
            total_train_loss = 0.0

            pbar = tqdm(train_loader, desc=f"Epoch {epoch:02d}/{epochs:02d} [train]")
            for images, targets, _ in pbar:
                images = images.to(device, non_blocking=True)
                targets = targets.to(device, non_blocking=True)

                optimizer.zero_grad(set_to_none=True)

                # Mixed precision forward pass
                with torch.amp.autocast("cuda", enabled=use_amp, dtype=torch.float16):
                    outputs = model(images)
                    loss = criterion(outputs, targets)

                scaler.scale(loss).backward()
                
                # guard: gradient clipping against exploding gradients (NaN/Inf)
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
                
                scaler.step(optimizer)
                scaler.update()

                total_train_loss += loss.item()
                pbar.set_postfix({"Loss": f"{loss.item():.5f}"})

            scheduler.step()
            avg_train_loss = total_train_loss / len(train_loader)

            # Validation phase
            model.eval()
            total_val_loss = 0.0
            angular_errors = []

            with torch.no_grad():
                for images, targets, _ in val_loader:
                    images = images.to(device, non_blocking=True)
                    targets = targets.to(device, non_blocking=True)

                    with torch.amp.autocast("cuda", enabled=use_amp, dtype=torch.float16):
                        outputs = model(images)
                        loss = criterion(outputs, targets)

                    total_val_loss += loss.item()
                    errors = compute_angular_error_deg(outputs.float(), targets.float())
                    angular_errors.extend(errors.cpu().tolist())

            avg_val_loss = total_val_loss / len(val_loader)
            val_mae = sum(angular_errors) / len(angular_errors)
            acc_1deg = sum(1 for e in angular_errors if e <= 1.0) / len(angular_errors) * 100.0
            acc_2deg = sum(1 for e in angular_errors if e <= 2.0) / len(angular_errors) * 100.0
            epoch_duration = time.time() - epoch_start

            print(
                f"Epoch [{epoch:02d}/{epochs:02d}] ({epoch_duration:.1f}s) | "
                f"Train Loss: {avg_train_loss:.5f} | Val Loss: {avg_val_loss:.5f} | "
                f"Val MAE: {val_mae:.2f}° | Acc(≤1°): {acc_1deg:.1f}% | Acc(≤2°): {acc_2deg:.1f}%"
            )

            if val_mae < best_val_mae:
                best_val_mae = val_mae
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "best_val_mae": best_val_mae,
                    "angle_range": angle_range
                }, checkpoint_path)
                print(f"  new best model saved: val MAE = {best_val_mae:.2f} degrees")

    except KeyboardInterrupt:
        print("\nTraining interrupted by the user (Ctrl+C)")
        print("Saving the model reached so far...")
        interrupted_path = checkpoint_path.replace(".pth", "_interrupted.pth")
        torch.save({
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "best_val_mae": best_val_mae,
            "angle_range": angle_range
        }, interrupted_path)
        checkpoint_path = interrupted_path  # Update path for ONNX export
        print(f"Interrupted model saved to: {interrupted_path}")

    total_time = time.time() - start_total_time
    print("=" * 65)
    print(f"Training finished. Total time: {total_time:.1f} s.")
    print(f"Best validation MAE: {best_val_mae:.2f} degrees")
    print("=" * 65)

    # Export best model to ONNX
    print("Exporting the best model to ONNX...")
    from src.export_onnx import export_to_onnx
    export_to_onnx(checkpoint_path, onnx_path, img_size=img_size, backbone=backbone)

    return model, best_val_mae


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Document Angle Detection Training")
    parser.add_argument("--train-dir", type=str, default="data/splits/train", help="Train split directory")
    parser.add_argument("--val-dir", type=str, default="data/splits/val", help="Val split directory")
    parser.add_argument("--bg-dir", type=str, default="data/backgrounds", help="Background textures directory")
    parser.add_argument("--backbone", type=str, default="large", choices=["small", "large"], help="Backbone model size")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--samples", type=int, default=5000, help="Training samples per epoch")
    parser.add_argument("--val-samples", type=int, default=600, help="Validation samples per epoch")
    parser.add_argument("--angle-range", type=float, default=180.0, help="Rotation range [-range, +range] in degrees")
    parser.add_argument("--img-size", type=int, default=256, help="Model input size (HxW)")
    parser.add_argument("--checkpoint", type=str, default="best_model.pth", help="Checkpoint save path")
    parser.add_argument("--onnx", type=str, default="document_angle_detector.onnx", help="ONNX export path")

    args = parser.parse_args()

    train_angle_model(
        train_doc_dir=args.train_dir,
        val_doc_dir=args.val_dir,
        bg_dir=args.bg_dir,
        backbone=args.backbone,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        samples_per_epoch=args.samples,
        val_samples=args.val_samples,
        angle_range=args.angle_range,
        img_size=args.img_size,
        checkpoint_path=args.checkpoint,
        onnx_path=args.onnx
    )
