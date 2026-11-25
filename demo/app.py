"""Gradio demo of docangle: upload a scanned or photographed page, see how it is turned and the straightened page.

  pip install docangle gradio && python app.py
"""
import cv2
import gradio as gr

import docangle

MAX_SIDE = 3000   # shortcut: the input is shrunk to this long side to bound memory and time on a small server; the angle does not depend on it
NOTE = ("Latin-script documents only; other scripts were not tested. Do not upload confidential documents. "
        "The project's own model weights are for research and evaluation use.")


try:
    import spaces
    gpu = spaces.GPU(duration=10)   # ZeroGPU Spaces insist on a GPU function; docangle runs on the CPU, the allocation only satisfies the platform
except ImportError:                 # a laptop or a CPU Space
    def gpu(fn):
        return fn


@gpu
def analyze(image):
    if image is None:
        raise gr.Error("Upload an image first.")
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)       # Gradio gives RGB, docangle takes OpenCV's BGR
    side = max(bgr.shape[:2])
    if side > MAX_SIDE:
        bgr = cv2.resize(bgr, None, fx=MAX_SIDE / side, fy=MAX_SIDE / side, interpolation=cv2.INTER_AREA)
    upright, r = docangle.get_pipeline().correct(bgr)
    if upright is None:
        return None, f"**No angle:** {', '.join(r.reasons) or 'the page could not be analysed'} (blank, too small or unreadable)."
    verdict = "**yes, send it to a person**" if r.needs_review else "no"
    text = (f"**Angle:** {r.angle:+.1f}° (counter-clockwise positive, range -180 to +180)  \n"
            f"**Confidence:** {r.confidence:.2f}  \n"
            f"**Needs review:** {verdict}  \n"
            f"**Reasons:** {', '.join(r.reasons) or 'none'}  \n"
            f"**Analysis time:** {r.elapsed_ms:.0f} ms")
    return cv2.cvtColor(upright, cv2.COLOR_BGR2RGB), text


demo = gr.Interface(
    fn=analyze,
    inputs=gr.Image(type="numpy", image_mode="RGB", label="Page photo or scan"),
    outputs=[gr.Image(label="Straightened page"), gr.Markdown()],
    title="docangle: how is this page turned?",
    description="Finds the rotation of a scanned or photographed page anywhere in [-180°, +180°] and says when it is not sure. "
                f"[Code and benchmark on GitHub](https://github.com/KazimMammadli/docangle). {NOTE}",
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()
