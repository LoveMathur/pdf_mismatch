from pydantic import BaseModel

class Span(BaseModel):

    text: str

    font: str

    size: float

    color: int

    bbox: tuple[float, float, float, float]