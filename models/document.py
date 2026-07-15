from pydantic import BaseModel

from typing import List

from .page import Page


class Document(BaseModel):

    file_name: str

    pages: List[Page]