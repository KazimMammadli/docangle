"""docangle - document rotation angle and page orientation (Latin-script documents)."""

from .errors import DocAngleError, ImageReadError, ModelNotFoundError, UndeterminedOrientation
from .consensus import apply_job_consensus
from .pipeline import (
    DocumentOrientationPipeline,
    PipelineConfig,
    Result,
    angular_distance,
    correct_document,
    get_pipeline,
    normalize_angle,
    predict_document,
    predict_document_angle,
    rotate_image_expanded,
    upright,
)

__version__ = "4.5.0"
__all__ = [
    "DocumentOrientationPipeline", "PipelineConfig", "Result", "apply_job_consensus",
    "get_pipeline", "predict_document", "predict_document_angle", "correct_document",
    "normalize_angle", "angular_distance", "rotate_image_expanded", "upright",
    "DocAngleError", "ImageReadError", "ModelNotFoundError", "UndeterminedOrientation",
]
