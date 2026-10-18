import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import torch
import onnx
import onnxruntime as ort
import numpy as np
from src.model import DocumentAngleModel


def export_to_onnx(
    checkpoint_path="best_model.pth",
    onnx_output_path="document_angle_detector.onnx",
    img_size=256,
    backbone="large",
    opset_version=14
):
    """
    Exports trained PyTorch DocumentAngleModel to an optimized ONNX format.
    Validates output parity between PyTorch and ONNX Runtime.
    """
    device = torch.device("cpu")
    model = DocumentAngleModel(backbone=backbone, pretrained=False)
    
    if os.path.exists(checkpoint_path):
        ckpt = torch.load(checkpoint_path, map_location=device)
        state_dict = ckpt.get("model_state_dict", ckpt)
        model.load_state_dict(state_dict)
        print(f"Weights loaded: {checkpoint_path}")
    else:
        print(f"{checkpoint_path} not found, exporting the current weights.")

    model.to(device)
    model.eval()

    dummy_input = torch.randn(1, 3, img_size, img_size, dtype=torch.float32)

    # Dynamic batch size support
    dynamic_axes = {
        "input_image": {0: "batch_size"},
        "sin_cos_output": {0: "batch_size"}
    }

    torch.onnx.export(
        model,
        dummy_input,
        onnx_output_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["input_image"],
        output_names=["sin_cos_output"],
        dynamic_axes=dynamic_axes
    )

    # Validate ONNX graph
    onnx_model = onnx.load(onnx_output_path)
    onnx.checker.check_model(onnx_model)
    file_size_mb = os.path.getsize(onnx_output_path) / (1024 * 1024)
    print(f"ONNX model exported: {onnx_output_path} ({file_size_mb:.2f} MB)")

    # Parity verification with ONNX Runtime
    session = ort.InferenceSession(onnx_output_path, providers=["CPUExecutionProvider"])
    with torch.no_grad():
        pt_out = model(dummy_input).numpy()
    
    ort_inputs = {session.get_inputs()[0].name: dummy_input.numpy()}
    ort_out = session.run(None, ort_inputs)[0]

    max_diff = np.max(np.abs(pt_out - ort_out))
    print(f"PyTorch vs ONNX output difference (max): {max_diff:.2e}")
    assert max_diff < 1e-4, "error: PyTorch and ONNX outputs disagree"
    print("Model check passed.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="best_model.pth")
    parser.add_argument("--onnx", type=str, default="document_angle_detector.onnx")
    parser.add_argument("--img-size", type=int, default=256)
    args = parser.parse_args()
    
    export_to_onnx(args.checkpoint, args.onnx, args.img_size)
