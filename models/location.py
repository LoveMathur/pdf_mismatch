from pydantic import BaseModel


class Location(BaseModel):
    """
    Represents the location of text inside a PDF.
    """

    page: int

    bbox: tuple[float, float, float, float]

    text: str

    confidence: float = 1.0