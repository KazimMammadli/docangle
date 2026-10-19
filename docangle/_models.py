"""Locate the pipeline's model files; download them once from the GitHub Release when a PyPI install has none.

Order: ``DOCANGLE_MODELS_DIR`` (only that folder, never a download) -> the repository's ``models/`` -> the user cache -> download.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import urllib.request

from .errors import ModelNotFoundError

_REPO_MODELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
_RELEASE_URL = "https://github.com/KazimMammadli/docangle/releases/download/v4.4.0/"
_CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache"), "docangle")
# sha256 of the files attached to the release; tests/unit/test_models.py keeps them equal to models/manifest.json
SHA256 = {
    "pp_lcnet_doc_ori.onnx": "7ab8929b28265e3e6906fc44d966e735727f23a37ec042a3ad391667e5c13068",
    "orient_cls_v4.onnx": "886426f28b7586517b0a5444137bff7ee508992fa48a1ba77242e7d099aa9f9c",
    "document_angle_detector_large.onnx": "01f778baee9f121d29c6a096f774dd1a752d6f54bbc7f8eac84d932350f453da",
}


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def get(name: str) -> str:
    """Path of the model file ``name``; it may be downloaded (and verified) on the first call."""
    override = os.environ.get("DOCANGLE_MODELS_DIR")
    if override:
        return os.path.join(override, name)
    for folder in (_REPO_MODELS, _CACHE):
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            return p
    return _download(name)


def _download(name: str) -> str:
    url = _RELEASE_URL + name
    dest = os.path.join(_CACHE, name)
    print(f"docangle: downloading {name} from {url} to {_CACHE} (first use only). The project's own weights are "
          f"for research and evaluation use, see {_RELEASE_URL.rsplit('/releases', 1)[0]}/blob/main/models/README.md", file=sys.stderr)
    try:
        os.makedirs(_CACHE, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_CACHE, suffix=".part")
        try:
            with os.fdopen(fd, "wb") as out, urllib.request.urlopen(url, timeout=60) as resp:
                while block := resp.read(1 << 20):
                    out.write(block)
            if _sha256(tmp) != SHA256[name]:
                raise ModelNotFoundError(f"downloaded {name} does not match its expected sha256; not using it")
            os.replace(tmp, dest)           # atomic: a half-written file is never taken for a model
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    except OSError as e:
        raise ModelNotFoundError(
            f"model file {name} is not installed and could not be downloaded ({e}). Download it from {url} into {_CACHE}, "
            f"or point DOCANGLE_MODELS_DIR at a folder that contains it.") from e
    return dest
