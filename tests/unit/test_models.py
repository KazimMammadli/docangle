import hashlib
import io
import json
import os

import pytest

from docangle import _models
from docangle.errors import ModelNotFoundError

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAME = "pp_lcnet_doc_ori.onnx"


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.delenv("DOCANGLE_MODELS_DIR", raising=False)
    monkeypatch.setattr(_models, "_REPO_MODELS", str(tmp_path / "no_repo_models"))
    monkeypatch.setattr(_models, "_CACHE", str(tmp_path / "cache"))
    return tmp_path / "cache"


def _serve(monkeypatch, payload):
    monkeypatch.setattr(_models.urllib.request, "urlopen", lambda url, timeout: io.BytesIO(payload))


def test_hashes_match_the_manifest():
    path = os.path.join(ROOT, "models", "manifest.json")
    if not os.path.isfile(path):
        pytest.skip("models/manifest.json not available")
    manifest = json.load(open(path))
    assert {k: v["sha256"] for k, v in manifest.items() if k in _models.SHA256} == _models.SHA256


def test_override_dir_is_never_downloaded(cache, monkeypatch, tmp_path):
    monkeypatch.setenv("DOCANGLE_MODELS_DIR", str(tmp_path / "mine"))
    monkeypatch.setattr(_models.urllib.request, "urlopen", lambda *a, **k: pytest.fail("must not download"))
    assert _models.get(NAME) == str(tmp_path / "mine" / NAME)


def test_download_is_verified_and_cached(cache, monkeypatch):
    payload = b"model bytes"
    monkeypatch.setitem(_models.SHA256, NAME, hashlib.sha256(payload).hexdigest())
    _serve(monkeypatch, payload)
    p = _models.get(NAME)
    assert open(p, "rb").read() == payload and p == str(cache / NAME)
    monkeypatch.setattr(_models.urllib.request, "urlopen", lambda *a, **k: pytest.fail("second call must use the cache"))
    assert _models.get(NAME) == p


def test_wrong_checksum_is_rejected_and_leaves_nothing(cache, monkeypatch):
    _serve(monkeypatch, b"tampered")
    with pytest.raises(ModelNotFoundError, match="sha256"):
        _models.get(NAME)
    assert os.listdir(cache) == []


def test_offline_gives_a_clear_error(cache, monkeypatch):
    def boom(url, timeout):
        raise OSError("no network")
    monkeypatch.setattr(_models.urllib.request, "urlopen", boom)
    with pytest.raises(ModelNotFoundError, match="DOCANGLE_MODELS_DIR"):
        _models.get(NAME)
    assert os.listdir(cache) == []
