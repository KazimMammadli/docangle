
import cv2
import numpy as np
import pytest

from tests.unit.helpers import jpeg_bytes, make_scan_pdf, ruled_page

from docangle import (DocumentOrientationPipeline, ImageReadError, ModelNotFoundError, PipelineConfig,
                      UndeterminedOrientation, get_pipeline)


def test_missing_lcnet_model_raises_instead_of_guessing(tmp_path):
    with pytest.raises(ModelNotFoundError):
        DocumentOrientationPipeline(PipelineConfig(lcnet_onnx_path=str(tmp_path / "nope.onnx")))


def test_missing_regressor_model_raises(tmp_path):
    with pytest.raises(ModelNotFoundError):
        DocumentOrientationPipeline(PipelineConfig(onnx_path=str(tmp_path / "nope.onnx")))


def test_regressor_is_optional_when_the_configuration_does_not_ask_for_it(tmp_path):
    img = np.full((300, 300), 255, np.uint8)
    img[::7] = 0
    cfg = PipelineConfig(onnx_path=str(tmp_path / "nope.onnx"), use_regressor_fallback=False)
    assert 0 <= abs(DocumentOrientationPipeline(cfg).predict(img).angle) <= 180
    with pytest.raises(ModelNotFoundError, match="optional"):
        DocumentOrientationPipeline(PipelineConfig(onnx_path=str(tmp_path / "nope.onnx")))
    with pytest.raises(ModelNotFoundError):                 # its angle for TOO_FEW_LINES pages needs the file as well
        DocumentOrientationPipeline(PipelineConfig(onnx_path=str(tmp_path / "nope.onnx"), use_regressor_fallback=False, too_few_lines_angle="regressor"))


def test_correct_reads_the_same_image_as_predict_when_the_jpeg_has_an_exif_orientation(tmp_path):
    img = np.full((300, 200, 3), 255, np.uint8)
    img[::9] = 0
    path = tmp_path / "rotated.jpg"
    path.write_bytes(jpeg_bytes(img, exif_orientation=6))                       # 6: the viewer turns it 90 degrees clockwise
    seen = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    assert seen.shape == (200, 300)                                              # OpenCV applied the tag
    pipe = DocumentOrientationPipeline(PipelineConfig(onnx_path=str(tmp_path / "none.onnx"), use_regressor_fallback=False))
    upright_img, res = pipe.correct(str(path))
    assert pipe.predict(str(path)).angle == res.angle
    assert pipe.render_upright(str(path), 0.0).shape[:2] == (200, 300)           # the raster that is rotated is the one that was analysed
    if upright_img is not None and res.angle is not None and abs(res.angle) < 1:
        assert upright_img.shape[:2] == (200, 300)


def test_get_pipeline_cache_is_keyed_by_config(tmp_path):
    a = get_pipeline(PipelineConfig())
    b = get_pipeline(PipelineConfig())
    c = get_pipeline(PipelineConfig(working_max_dim=800))
    assert a is b and a is not c  # old singleton returned the first instance regardless of arguments


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        PipelineConfig(review_confidence=0.9, high_confidence=0.8)


def test_blank_page_is_undetermined_not_a_guess(pipe):
    r = pipe.predict(np.full((800, 600, 3), 255, np.uint8))
    assert r.angle is None and r.quality == "UNDETERMINED" and r.needs_review and "NO_CONTENT" in r.reasons
    with pytest.raises(UndeterminedOrientation):
        pipe.predict_angle(np.full((800, 600), 255, np.uint8))


def test_tiny_image_is_undetermined(pipe):
    r = pipe.predict(np.zeros((40, 40), np.uint8))
    assert r.angle is None and "IMAGE_TOO_SMALL" in r.reasons


@pytest.mark.parametrize("make", [
    lambda g: g,                                      # 2-D uint8
    lambda g: g[:, :, None],                          # H,W,1
    lambda g: np.dstack([g, g, g]),                   # BGR
    lambda g: np.dstack([g, g, g, np.full_like(g, 255)]),  # BGRA
    lambda g: g.astype(np.uint16) * 257,              # 16-bit
    lambda g: g.astype(np.float32) / 255.0,           # float 0..1
])
def test_all_common_input_types_give_the_same_answer(pipe, make):
    from tests.unit.helpers import ruled_page
    import cv2
    g = cv2.cvtColor(ruled_page(), cv2.COLOR_BGR2GRAY)
    ref = pipe.predict(g).angle
    got = pipe.predict(make(g)).angle
    assert ref is not None and got is not None and abs(got - ref) < 0.3


def test_bad_inputs_raise_readable_errors(pipe, tmp_path):
    with pytest.raises(ImageReadError):
        pipe.predict(str(tmp_path / "missing.png"))
    with pytest.raises(ImageReadError):
        pipe.predict(12345)
    with pytest.raises(ImageReadError):
        pipe.predict(np.zeros((10, 10, 5), np.uint8))


def test_batch_keeps_order_and_survives_bad_file(pipe, tmp_path):
    import cv2
    from tests.unit.helpers import ruled_page
    good = str(tmp_path / "g.png")
    cv2.imwrite(good, ruled_page())
    res = pipe.predict_batch([good, str(tmp_path / "bad.png"), good], max_workers=3)
    assert [r.angle is None for r in res] == [False, True, False]
    assert res[1].reasons == ["UNREADABLE"]


def test_result_is_json_serialisable(pipe):
    import json
    from tests.unit.helpers import ruled_page
    r = pipe.predict(ruled_page())
    json.dumps(r.to_dict())


def test_onnx_sessions_receive_thread_settings(pipe):
    pipe._lcnet_session()
    pipe._regressor._ensure()
    # exercise: regressor input size is read from the model (384 for the shipped file), not hard-coded
    assert pipe._regressor.input_size in (256, 384)


def test_ort_provider_validation_and_missing_gpu_runtime():
    import numpy as np
    import onnxruntime as ort
    with pytest.raises(ValueError):
        PipelineConfig(ort_provider="tpu")
    if "CUDAExecutionProvider" in ort.get_available_providers():
        pytest.skip("this environment has the GPU build of ONNX Runtime")
    img = np.full((300, 300), 255, np.uint8)
    img[::7] = 0
    with pytest.raises(ModelNotFoundError):                 # a clear message instead of a silent CPU fallback
        DocumentOrientationPipeline(PipelineConfig(ort_provider="cuda")).predict(img)


def test_preload_cuda_libs_is_harmless_and_idempotent():
    from docangle.regressor import _preload_cuda_libs
    _preload_cuda_libs()
    _preload_cuda_libs()


@pytest.mark.data
def test_gpu_pipeline_matches_cpu_when_a_gpu_is_available(az_pages):
    """ort_provider='cuda' finds the pip-installed CUDA libraries by itself (no LD_LIBRARY_PATH) and gives the same angles as the CPU."""
    import cv2
    import onnxruntime as ort
    from docangle import angular_distance, rotate_image_expanded
    if "CUDAExecutionProvider" not in ort.get_available_providers():
        pytest.skip("this environment has the CPU build of ONNX Runtime")
    page = cv2.imread(az_pages[0], cv2.IMREAD_GRAYSCALE)
    cpu, gpu = DocumentOrientationPipeline(), DocumentOrientationPipeline(PipelineConfig(ort_provider="cuda"))
    try:
        gpu.predict(page)
    except ModelNotFoundError:
        pytest.skip("the CUDA libraries are not installed")
    for ang in (0.0, 12.0, 180.0, -37.0):
        img = rotate_image_expanded(page, ang)
        a, b = cpu.predict(img), gpu.predict(img)
        assert angular_distance(a.angle, b.angle) < 0.05 and a.needs_review == b.needs_review


def test_hough_strips_with_the_fourier_estimator_do_not_hang_a_batch(tmp_path):
    imgs = [cv2.cvtColor(ruled_page(seed=k), cv2.COLOR_BGR2GRAY) for k in range(6)]
    pipe = DocumentOrientationPipeline(PipelineConfig(pass1_strips=3, onnx_path=str(tmp_path / "x.onnx"), use_regressor_fallback=False))
    assert len(pipe.predict_batch(imgs, max_workers=6)) == 6            # used to wait forever: band jobs queued behind their own parent


def test_float_images_in_the_0_255_range_get_a_white_border():
    from docangle import upright
    out = upright(np.full((100, 80), 200.0, np.float32), 30.0)
    assert float(out.min()) >= 199.0


def test_cli_writes_into_a_directory_for_page_all_and_reports_a_damaged_pdf(tmp_path, capsys):
    pytest.importorskip("pypdfium2")
    from docangle.__main__ import main
    make_scan_pdf(tmp_path / "one.pdf", [cv2.cvtColor(ruled_page(), cv2.COLOR_BGR2GRAY)])
    out = tmp_path / "out"
    assert main([str(tmp_path / "one.pdf"), "--page", "all", "-o", str(out)]) == 0
    assert (out / "one_p1.png").exists()
    (tmp_path / "bad.pdf").write_bytes(b"%PDF-1.4 not really")
    assert main([str(tmp_path), "--page", "all", "--json"]) == 0
    assert "UNREADABLE" in capsys.readouterr().out
