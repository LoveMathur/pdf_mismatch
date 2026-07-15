from enum import Enum

from pydantic import BaseModel

from models.text_element import TextElement


class AlignmentType(str, Enum):
    EQUAL = "equal"
    REPLACE = "replace"
    INSERT = "insert"
    DELETE = "delete"


class AlignedPair(BaseModel):
    """
    Represents two aligned text elements.
    """

    index: int

    left: TextElement | None = None

    right: TextElement | None = None

    alignment_type: AlignmentType