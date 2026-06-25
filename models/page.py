from pydantic import BaseModel
from typing import List
from .word import Word

class Page(BaseModel):

    page_number: int

    words: List[Word]