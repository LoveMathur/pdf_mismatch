from enum import Enum

from pydantic import BaseModel

from models.logical_line import LogicalLine


class AlignmentType(str, Enum):

    EQUAL = "equal"

    REPLACE = "replace"

    INSERT = "insert"

    DELETE = "delete"


class LogicalAlignedPair(BaseModel):

    left: LogicalLine | None = None

    right: LogicalLine | None = None

    alignment: AlignmentType