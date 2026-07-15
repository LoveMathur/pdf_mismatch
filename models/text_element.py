from pydantic import BaseModel, computed_field

class TextElement(BaseModel):

    id: int

    page: int

    block: int

    line: int

    text: str

    normalized_text: str | None = None

    bbox: tuple[float, float, float, float]

    @computed_field
    @property
    def comparison_text(self) -> str:
        return self.normalized_text or self.text