from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DifferenceType(str, Enum):

    CHARACTER = "character"

    WORD = "word"

    INSERTION = "insertion"

    DELETION = "deletion"

    CASE = "case"

    WHITESPACE = "whitespace"

    SPELLING = "spelling"

    FORMATTING = "formatting"

    IMAGE = "image"

    OCR = "ocr"

    NUMBER = "number"


class Difference(BaseModel):

    pair_index: int

    difference_type: DifferenceType

    expected: str | None = None

    actual: str | None = None

    confidence: float = 1.0

    metadata: dict[str, Any] = Field(default_factory=dict)