from pydantic import BaseModel, Field


class LogicalWord(BaseModel):
    """
    Smallest semantic unit of the document.
    """

    id: str

    page: int

    word_index: int

    text: str

    bbox: tuple[float, float, float, float]

    font: str = ""

    font_size: float = 0.0

    color: int = 0

    flags: int = 0

    rotation: float = 0.0

    metadata: dict = Field(default_factory=dict)

    model_config = {
        "arbitrary_types_allowed": True
    }