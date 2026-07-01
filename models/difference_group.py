from pydantic import BaseModel, Field

from models.difference import Difference


class DifferenceGroup(BaseModel):
    """
    Represents one logical change consisting
    of one or more Difference objects.
    """

    differences: list[Difference] = Field(default_factory=list)

    bbox: tuple[float, float, float, float]

    page: int

    title: str = ""

    message: str = ""