import re

import pymupdf

from models.logical_document import LogicalDocument
from models.logical_page import LogicalPage
from models.logical_line import LogicalLine
from models.logical_word import LogicalWord
from models.logical_image import LogicalImage
from models.logical_table import LogicalTable
from models.span import Span


class UnifiedExtractor:

    ROW_OVERLAP_RATIO = 0.6

    #
    # A line is a header/footer *candidate* when it sits inside the
    # top/bottom margin band of the page (ratio of page height).
    # It only becomes header/footer once it also repeats across
    # pages -- position alone would misclassify one-off content
    # that happens to start near the page edge.
    #
    HEADER_ZONE_RATIO = 0.08
    FOOTER_ZONE_RATIO = 0.08
    MIN_BOILERPLATE_REPEATS = 2

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

            logical_page.lines = self._merge_row_fragments(
                logical_page.lines
            )

            logical_page.images = self._extract_images(
                page,
                page_number,
            )

            logical_page.tables = self._extract_tables(
                page,
                page_number,
            )

            pages.append(logical_page)

        document.close()

        self._mark_header_footer(pages)

        return LogicalDocument(
            file_name=pdf_path,
            pages=pages,
        )

    def _mark_header_footer(
        self,
        pages: list[LogicalPage],
    ) -> None:
        """
        Flag recurring top/bottom boilerplate (letterhead, "Page X of Y",
        confidentiality footers ...) so comparators can ignore it.

        A line only qualifies when it BOTH sits inside the page's
        margin band AND its (digit-collapsed) text repeats across
        multiple pages. This is what lets re-pagination -- which
        changes how many times a footer/header repeats, or what
        number it shows -- stop being reported as inserted/deleted
        content.
        """

        if len(pages) < self.MIN_BOILERPLATE_REPEATS:
            return

        buckets: dict[tuple, list] = {}

        for page in pages:

            if not page.height:
                continue

            header_limit = page.height * self.HEADER_ZONE_RATIO
            footer_limit = page.height * (1 - self.FOOTER_ZONE_RATIO)

            for line in page.lines:

                text = line.text.strip()

                if not text:
                    continue

                if line.bbox[3] <= header_limit:
                    zone = "header"
                elif line.bbox[1] >= footer_limit:
                    zone = "footer"
                else:
                    continue

                key = (zone, self._boilerplate_key(text))
                buckets.setdefault(key, []).append(line)

        for (zone, _key), lines in buckets.items():

            if len(lines) < self.MIN_BOILERPLATE_REPEATS:
                continue

            for line in lines:
                if zone == "header":
                    line.is_header = True
                else:
                    line.is_footer = True

    @staticmethod
    def _boilerplate_key(text: str) -> str:
        """
        Normalize header/footer text for repetition grouping, so
        "Page 3 of 10" and "Page 4 of 11" are recognised as the same
        recurring template instead of unrelated one-off lines.
        """
        text = re.sub(r"\d+", "#", text.lower())
        return re.sub(r"\s+", " ", text).strip()

    def _extract_page(
        self,
        page,
        page_number: int,
    ) -> LogicalPage:

        page_dict = page.get_text("dict")

        logical_lines = []

        reading_order = 0

        text_block_index = -1

        for block in page_dict["blocks"]:

            if block["type"] != 0:
                continue

            text_block_index += 1

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
                            flags=int(span.get("flags", 0)),
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
                        block_index=text_block_index,
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

    def _extract_images(
        self,
        page,
        page_number: int,
    ) -> list[LogicalImage]:
        """
        Extract placed images as geometry only (bbox -> dimensions
        and position). Pixel content is intentionally never read.
        """

        images = []

        for order, info in enumerate(page.get_image_info()):

            bbox = tuple(info.get("bbox", (0, 0, 0, 0)))

            images.append(
                LogicalImage(
                    id=f"page_{page_number}_image_{order}",
                    page=page_number,
                    bbox=bbox,
                    width=bbox[2] - bbox[0],
                    height=bbox[3] - bbox[1],
                    reading_order=order,
                )
            )

        return images

    def _extract_tables(
        self,
        page,
        page_number: int,
    ) -> list[LogicalTable]:
        """
        Extract detected tables as shape only (row/column count,
        bbox). Cell content is intentionally never read.

        Table detection is heuristic (ruling lines / whitespace
        alignment); a page with no table-like structure simply
        yields an empty list.
        """

        tables = []

        try:
            found = page.find_tables()
        except Exception:
            return tables

        for order, table in enumerate(found.tables):

            tables.append(
                LogicalTable(
                    id=f"page_{page_number}_table_{order}",
                    page=page_number,
                    bbox=tuple(table.bbox),
                    row_count=table.row_count,
                    col_count=table.col_count,
                    reading_order=order,
                )
            )

        return tables

    def _attach_words(
        self,
        page,
        logical_page: LogicalPage,
    ) -> None:

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

            matched_span = None
            best_overlap = 0.0

            for span in logical_line.spans:

                sx0, sy0, sx1, sy1 = span.bbox

                overlap = min(x1, sx1) - max(x0, sx0)

                if overlap > best_overlap:
                    best_overlap = overlap
                    matched_span = span

            if matched_span is None:
                for span in logical_line.spans:
                    if span.text.strip():
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
                    flags=matched_span.flags if matched_span else 0,
                    rotation=0.0,
                )
            )

    def _merge_row_fragments(
        self,
        lines: list[LogicalLine],
    ) -> list[LogicalLine]:

        candidates = [
            line for line in lines
            if line.text.strip()
        ]

        if not candidates:
            return []

        candidates.sort(
            key=lambda l: (round(l.bbox[1], 1), l.bbox[0])
        )

        rows: list[list[LogicalLine]] = []

        for line in candidates:

            if rows and self._same_row(rows[-1], line):
                rows[-1].append(line)
            else:
                rows.append([line])

        merged: list[LogicalLine] = []

        for reading_order, row in enumerate(rows):

            row.sort(key=lambda l: l.bbox[0])

            if len(row) == 1:
                row[0].reading_order = reading_order
                merged.append(row[0])
                continue

            first = row[0]

            text = " ".join(
                fragment.text.strip()
                for fragment in row
                if fragment.text.strip()
            )

            bbox = (
                min(f.bbox[0] for f in row),
                min(f.bbox[1] for f in row),
                max(f.bbox[2] for f in row),
                max(f.bbox[3] for f in row),
            )

            words: list[LogicalWord] = []
            spans: list[Span] = []

            for fragment in row:
                words.extend(fragment.words)
                spans.extend(fragment.spans)

            words.sort(key=lambda w: w.bbox[0])

            merged.append(
                LogicalLine(
                    id=first.id,
                    page=first.page,
                    text=text,
                    bbox=bbox,
                    spans=spans,
                    words=words,
                    reading_order=reading_order,
                    block_index=first.block_index,
                    line_index=first.line_index,
                )
            )

        return merged

    def _same_row(
        self,
        row: list[LogicalLine],
        line: LogicalLine,
    ) -> bool:

        row_top = min(f.bbox[1] for f in row)
        row_bottom = max(f.bbox[3] for f in row)

        top = line.bbox[1]
        bottom = line.bbox[3]

        overlap = min(row_bottom, bottom) - max(row_top, top)

        height = min(
            row_bottom - row_top,
            bottom - top,
        )

        if height <= 0:
            return False

        return (overlap / height) >= self.ROW_OVERLAP_RATIO