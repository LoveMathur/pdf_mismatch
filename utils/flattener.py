from typing import List

from models.document import Document
from models.text_element import TextElement


class DocumentFlattener:
    """
    Converts the hierarchical Document model into
    a flat sequence of TextElements.
    """

    def flatten(self, document: Document) -> List[TextElement]:

        element_id = 0
        
        flattened: List[TextElement] = []

        for page in document.pages:

            for block in page.blocks:

                for line_index, line in enumerate(block.lines):

                    flattened.append(
                        TextElement(
                            id=element_id,
                            page=page.number,
                            block=block.block_number,
                            line=line_index,
                            text=line.text,
                            bbox=line.bbox
                        )
                    )
                    element_id += 1
        return flattened