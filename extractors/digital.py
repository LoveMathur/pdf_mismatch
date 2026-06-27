import pymupdf

from models.document import Document
from models.page import Page
from models.text_block import TextBlock
from models.line import Line
from models.span import Span


class DigitalPDFExtractor:
    """
    Extracts structured information from a digital PDF.

    Output hierarchy:

    Document
        └── Page
              └── TextBlock
                    └── Line
                          └── Span
    """

    def extract(self, pdf_path: str) -> Document:

        pdf = pymupdf.open(pdf_path)

        pages = []

        for page_number, page in enumerate(pdf, start=1):

            page_dict = page.get_text("dict")

            blocks = []

            block_number = 0

            for block in page_dict["blocks"]:

                # Ignore images for now.
                # Phase 3 will handle image extraction.
                if block["type"] != 0:
                    continue

                lines = []

                for line in block.get("lines", []):

                    spans = []

                    for span in line.get("spans", []):

                        spans.append(
                            Span(
                                text=span.get("text", ""),
                                font=span.get("font", ""),
                                size=float(span.get("size", 0)),
                                color=int(span.get("color", 0)),
                                bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                            )
                        )

                    lines.append(
                        Line(
                            bbox=tuple(line.get("bbox", (0, 0, 0, 0))),
                            spans=spans
                        )
                    )

                blocks.append(
                    TextBlock(
                        block_number=block_number,
                        bbox=tuple(block.get("bbox", (0, 0, 0, 0))),
                        lines=lines,
                    )
                )

                block_number += 1

            pages.append(
                Page(
                    number=page_number,
                    width=page.rect.width,
                    height=page.rect.height,
                    blocks=blocks,
                )
            )

        pdf.close()

        return Document(
            file_name=pdf_path,
            pages=pages,
        )