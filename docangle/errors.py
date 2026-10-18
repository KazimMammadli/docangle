class DocAngleError(Exception):
    """Base class for all docangle errors."""


class ModelNotFoundError(DocAngleError, FileNotFoundError):
    """A required ONNX model file is missing."""


class ImageReadError(DocAngleError, ValueError):
    """An input image could not be read or has an unsupported type/shape."""


class UndeterminedOrientation(DocAngleError):
    """The page has no usable content, so no angle can be given."""

    def __init__(self, reason: str):
        super().__init__(f"orientation undetermined: {reason}")
        self.reason = reason
