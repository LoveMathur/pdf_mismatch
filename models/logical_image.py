from pydantic import BaseModel


class LogicalImage(BaseModel):
    """
    Represents one embedded image placed on a page.

    Only geometry is kept (placement bbox -> dimensions/position).
    Pixel content is intentionally never extracted or compared.
    """

    id: str

    page: int

    bbox: tuple[float, float, float, float]

    width: float

    height: float

    reading_order: int
