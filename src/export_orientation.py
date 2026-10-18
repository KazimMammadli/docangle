"""Export a trained OrientNet checkpoint to ONNX and verify parity.  python -m src.export_orientation models/orient_cls_v1.pt"""
import sys

import numpy as np
import onnxruntime as ort
import torch

from .train_orientation import OrientNet


def main(ckpt_path: str, out_path: str = None):
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    m = OrientNet(pretrained=False)
    m.load_state_dict(ck["model"]); m.eval()
    S = ck["size"]
    out_path = out_path or ckpt_path.replace(".pt", ".onnx")
    x = torch.randn(2, 1, S, S)
    torch.onnx.export(m, x, out_path, input_names=["x"], output_names=["logits"], dynamic_axes={"x": {0: "n"}, "logits": {0: "n"}},
                      opset_version=17, dynamo=False)
    sess = ort.InferenceSession(out_path, providers=["CPUExecutionProvider"])
    with torch.no_grad():
        ref = m(x).numpy()
    diff = float(np.abs(ref - sess.run(None, {"x": x.numpy()})[0]).max())
    print(f"exported {out_path}  max|diff|={diff:.2e}  epoch={ck['epoch']}  val={ck['val']}")
    assert diff < 1e-3


if __name__ == "__main__":
    main(*sys.argv[1:])
