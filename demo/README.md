---
title: docangle
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
pinned: false
license: mit
short_description: Document orientation and rotation angle, with a review flag
---

# docangle demo

A small web page for [docangle](https://github.com/KazimMammadli/docangle): upload a scanned or photographed page and see its rotation angle, the confidence, the review flag and the straightened page.

Run it on your machine:

```bash
pip install docangle gradio
python app.py
```

Deploy it as a Hugging Face Space: create a Space with the Gradio SDK, then upload `app.py`, `requirements.txt` and this `README.md` to its root. The first request downloads the three models (36.0 MB) from the GitHub release and keeps them for the life of the Space.
