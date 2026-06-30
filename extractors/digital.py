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

                # Ignore non-text blocks for now.
                if block["type"] != 0:
                    continue

                lines = []

                for line_index, line in enumerate(block.get("lines", [])):

                    spans = []

                    line_text_parts = []

                    for span in line.get("spans", []):

                        text = span.get("text", "")

                        line_text_parts.append(text)

                        spans.append(
                            Span(
                                text=text,
                                font=span.get("font", ""),
                                size=float(span.get("size", 0)),
                                color=int(span.get("color", 0)),
                                bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                            )
                        )

                    line_bbox = tuple(line.get("bbox", (0, 0, 0, 0)))
                    line_text = "".join(line_text_parts)

                    # -----------------------------
                    # DEBUG OUTPUT
                    # -----------------------------
                    print("=" * 80)
                    print(f"PAGE : {page_number}")
                    print(f"BLOCK: {block_number}")
                    print(f"LINE : {line_index}")
                    print(f"TEXT : {repr(line_text)}")
                    print(f"BBOX : {line_bbox}")

                    lines.append(
                        Line(
                            bbox=line_bbox,
                            spans=spans,
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