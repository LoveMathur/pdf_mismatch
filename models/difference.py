from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from models.logical_line import LogicalLine
from models.logical_word import LogicalWord


class DifferenceCategory(str, Enum):
    INSERTION = "insertion"
    DELETION = "deletion"
    CHARACTER = "character"
    WORD = "word"
    NUMBER = "number"
    FORMATTING = "formatting"
    ORDER = "order"
    IMAGE = "image"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Difference(BaseModel):
    """
    Represents one detected difference between two documents.

    This object is the primary output of the comparison engine.
    It contains both the semantic information (what changed)
    and the localization information (where it changed).
    """

    # -------------------------------------------------------
    # Classification
    # -------------------------------------------------------

    category: DifferenceCategory

    severity: Severity = Severity.WARNING

    confidence: float = 1.0

    # -------------------------------------------------------
    # Context
    # -------------------------------------------------------

    expected_line: LogicalLine | None = None

    actual_line: LogicalLine | None = None

    expected_word: LogicalWord | None = None

    actual_word: LogicalWord | None = None

    # -------------------------------------------------------
    # Human-readable values
    # -------------------------------------------------------

    expected_text: str | None = None

    actual_text: str | None = None

    description: str = ""

    # -------------------------------------------------------
    # Extra information
    # -------------------------------------------------------

    metadata: dict[str, Any] = Field(default_factory=dict)