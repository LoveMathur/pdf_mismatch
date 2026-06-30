from enum import Enum

from pydantic import BaseModel

from models.difference import Difference


class AnnotationSeverity(str, Enum):
    """
    Importance of the detected issue.
    """

    INFO = "info"

    WARNING = "warning"

    ERROR = "error"

    CRITICAL = "critical"


class AnnotationTarget(BaseModel):
    """
    Renderer-independent annotation target.

    This object tells the renderer:

    - where to draw
    - what to display
    - why the issue exists

    It intentionally contains no rendering logic.
    """

    difference: Difference

    page: int

    bbox: tuple[float, float, float, float]

    title: str

    message: str

    severity: AnnotationSeverity = AnnotationSeverity.WARNING