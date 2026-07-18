from pydantic import BaseModel


class LogicalTable(BaseModel):
    """
    Represents one detected table placed on a page.

    Only shape/geometry is kept (row/column count, bbox). Cell
    content is intentionally never extracted or compared.
    """

    id: str

    page: int

    bbox: tuple[float, float, float, float]

    row_count: int

    col_count: int

    reading_order: int
