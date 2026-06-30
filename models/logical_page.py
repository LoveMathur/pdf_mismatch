from pydantic import BaseModel, Field

from models.logical_line import LogicalLine


class LogicalPage(BaseModel):
    """
    Represents one page in the logical document.
    """

    page_number: int

    width: float

    height: float

    lines: list[LogicalLine] = Field(default_factory=list)

    metadata: dict = Field(default_factory=dict)

    model_config = {
        "arbitrary_types_allowed": True
    }