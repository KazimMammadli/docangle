The before/after figure of README.md (docs/images/before_after.webp).
Input: one phone photo (iPhone 16 Pro Max, HEIC converted to JPEG, 4284x5712 px) of a printed page of README.md lying on a desk.
docangle 4.4.0, default configuration, CPU.

  python -m docangle photo.jpg --json -o upright.jpg

{"file": "photo.jpg", "angle": -30.4, "confidence": 0.999, "quality": "HIGH_CONFIDENCE", "needs_review": false, "reasons": [], "num_lines": 408, "lcnet_score": 0.999, "fine_tilt": -30.39718675957465, "fallback_triggered": false, "pass2_skipped": true, "residual": null, "posterior": [0.99898, 0.00032, 0.00038, 0.00032], "elapsed_ms": 189.35539000085555}

Figure: the photo and upright.jpg, each cropped to the page with a small margin (display only; upright.jpg itself keeps the whole turned frame), scaled to 420x560 px with rounded corners, side by side with an arrow and captions on a transparent background; metadata stripped.
elapsed_ms is one call including decoding, AC power online=0; it is not a speed measurement (chapter 8 has those).
