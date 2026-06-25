from pydantic import BaseModel

class Word(BaseModel):
    text: str

    page: int

    bbox: tuple

    line_no: int

    block_no: int