from typing import List

from pydantic import BaseModel, computed_field

from .span import Span


class Line(BaseModel):

    bbox: tuple[float, float, float, float]

    spans: List[Span]

    @computed_field
    @property
    def text(self) -> str:
        return "".join(span.text for span in self.spans)