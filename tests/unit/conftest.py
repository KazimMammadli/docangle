import glob
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _skip_when_weights_are_missing():
    """A copy of the repository without the own model weights (models/README.md) cannot run the pipeline: its tests are skipped, not failed."""
    from docangle.errors import ModelNotFoundError
    try:
        yield
    except ModelNotFoundError as e:
        pytest.skip(f"model weights not installed (see models/README.md): {str(e)[:120]}")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item):
    yield from _skip_when_weights_are_missing()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    yield from _skip_when_weights_are_missing()


@pytest.fixture(scope="session")
def pipe():
    from docangle import DocumentOrientationPipeline
    return DocumentOrientationPipeline()


@pytest.fixture(scope="session")
def az_pages():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "az_test_pages", "*.png")))
    if len(files) < 6:
        pytest.skip("data/az_test_pages not available")
    # one page from several documents
    picks = [f for f in files if "docD_page_003" in f or "docB_page_002" in f
             or "docA_page_050" in f or "docE_page_004" in f]
    return picks or files[:4]
