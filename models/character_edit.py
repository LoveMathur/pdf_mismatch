from enum import Enum

from pydantic import BaseModel


class CharacterOperation(str, Enum):

    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"


class CharacterEdit(BaseModel):

    pair_index: int

    operation: CharacterOperation

    left_start: int
    left_end: int

    right_start: int
    right_end: int

    expected_fragment: str
    actual_fragment: str