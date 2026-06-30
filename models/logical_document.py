from pydantic import BaseModel, Field

from models.logical_page import LogicalPage


class LogicalDocument(BaseModel):
    """
    Root logical representation of a PDF.
    """

    file_name: str

    pages: list[LogicalPage] = Field(default_factory=list)

    metadata: dict = Field(default_factory=dict)

    model_config = {
        "arbitrary_types_allowed": True
    }