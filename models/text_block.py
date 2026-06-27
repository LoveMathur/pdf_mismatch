from typing import List

from pydantic import BaseModel, computed_field

from .line import Line


class TextBlock(BaseModel):

    block_number: int

    bbox: tuple[float, float, float, float]

    lines: List[Line]

    @computed_field
    @property
    def text(self) -> str:
        return "\n".join(
            line.text.rstrip()
            for line in self.lines
        )