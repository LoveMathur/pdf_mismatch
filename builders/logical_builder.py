from __future__ import annotations

from models.bounding_box import BoundingBox
from models.logical_element import (
    LogicalElement,
    LogicalElementType,
)
from models.text_element import TextElement


class LogicalBuilder:
    """
    Converts raw TextElements into LogicalElements.

    Version 2 intentionally performs only a lightweight transformation.

    No semantic understanding is performed here.

    Future builders (FieldBuilder, TemplateBuilder, etc.)
    will operate on LogicalElements.
    """

    @staticmethod
    def build(
        text_elements: list[TextElement],
    ) -> list[LogicalElement]:

        logical_elements: list[LogicalElement] = []

        for order, element in enumerate(text_elements):

            logical_elements.append(

                LogicalElement(

                    source_elements=[element],

                    text=element.text,

                    comparison_text=LogicalBuilder._normalize(
                        element.text
                    ),

                    page_number=element.page_number,

                    bbox=element.bbox,

                    reading_order=order,

                    element_type=LogicalElementType.TEXT,

                )

            )

        return logical_elements

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalize text used during comparison.

        This is intentionally conservative.

        Future analyzers can still access the original text.
        """

        return " ".join(text.split())