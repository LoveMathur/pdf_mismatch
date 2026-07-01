import pymupdf

from models.logical_document import LogicalDocument
from models.logical_page import LogicalPage
from models.logical_line import LogicalLine
from models.logical_word import LogicalWord
from models.span import Span


class UnifiedExtractor:

    def extract(
        self,
        pdf_path: str,
    ) -> LogicalDocument:

        document = pymupdf.open(pdf_path)

        pages = []

        for page_number, page in enumerate(document, start=1):

            logical_page = self._extract_page(
                page,
                page_number,
            )

            self._attach_words(
                page,
                logical_page,
            )

            pages.append(logical_page)
        
        document.close()

        return LogicalDocument(
            file_name=pdf_path,
            pages=pages,
        )
                    
    def _extract_page(
        self,
        page,
        page_number: int,
    ) -> LogicalPage:

        page_dict = page.get_text("dict")

        logical_lines = []

        reading_order = 0

        for block_index, block in enumerate(page_dict["blocks"]):

            # Ignore images for now
            if block["type"] != 0:
                continue

            logical_line_index = 0

            for line in block.get("lines", []):

                spans = []

                line_text = ""

                for span in line.get("spans", []):

                    span_text = span.get("text", "")

                    line_text += span_text

                    spans.append(

                        Span(

                            text=span_text,

                            font=span.get("font", ""),

                            size=float(span.get("size", 0)),

                            color=int(span.get("color", 0)),

                            bbox=tuple(span.get("bbox", (0, 0, 0, 0))),

                        )

                    )

                logical_lines.append(

                    LogicalLine(

                        id=f"page_{page_number}_line_{reading_order}",

                        page=page_number,

                        text=line_text,

                        bbox=tuple(line.get("bbox", (0, 0, 0, 0))),

                        spans=spans,

                        reading_order=reading_order,

                        block_index=block_index,

                        line_index=logical_line_index,

                    )
                )

                logical_line_index += 1

                reading_order += 1

        return LogicalPage(

            page_number=page_number,

            width=float(page.rect.width),

            height=float(page.rect.height),

            lines=logical_lines,

        )
    
    def _attach_words(
        self,
        page,
        logical_page: LogicalPage,
    ) -> None:
        """
        Populate each LogicalLine with LogicalWords and inherit
        formatting information from the enclosing span.
        """

        line_lookup = {}

        for line in logical_page.lines:

            line_lookup[
                (
                    line.block_index,
                    line.line_index,
                )
            ] = line

        words = page.get_text("words")

        for word in words:

            (
                x0,
                y0,
                x1,
                y1,
                text,
                block_no,
                line_no,
                word_no,
            ) = word

            logical_line = line_lookup.get(
                (
                    block_no,
                    line_no,
                )
            )

            if logical_line is None:
                continue

            #
            # Match this word with the span that contains it.
            #

            matched_span = None

            word_center_x = (x0 + x1) / 2
            word_center_y = (y0 + y1) / 2

            for span in logical_line.spans:

                sx0, sy0, sx1, sy1 = span.bbox

                if (
                    sx0 <= word_center_x <= sx1
                    and
                    sy0 <= word_center_y <= sy1
                ):
                    matched_span = span
                    break

            logical_line.words.append(

                LogicalWord(

                    id=f"{logical_line.id}_word_{word_no}",

                    page=logical_page.page_number,

                    word_index=word_no,

                    text=text,

                    bbox=(x0, y0, x1, y1),

                    font=matched_span.font if matched_span else "",

                    font_size=matched_span.size if matched_span else 0.0,

                    color=matched_span.color if matched_span else 0,

                    flags=0,

                    rotation=0.0,

                )

            )