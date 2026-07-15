from pydantic import BaseModel, Field

from models.logical_word import LogicalWord
from models.span import Span


class LogicalLine(BaseModel):

    id: str

    page: int

    text: str

    bbox: tuple[float, float, float, float]

    words: list[LogicalWord] = Field(default_factory=list)

    spans: list[Span] = Field(default_factory=list)

    block_index: int
    line_index: int

    reading_order: int

    is_header: bool = False
    is_footer: bool = False
    is_table: bool = False
    is_caption: bool = False

    metadata: dict = Field(default_factory=dict)