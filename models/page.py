from pydantic import BaseModel

from typing import List

from .text_block import TextBlock


class Page(BaseModel):

    number: int

    width: float

    height: float

    blocks: List[TextBlock]