import pymupdf

from models.logical_document import LogicalDocument
from models.logical_page import LogicalPage
from models.logical_line import LogicalLine
from models.logical_word import LogicalWord
from models.span import Span


class UnifiedExtractor:

    #
    # Two dict lines are considered part of the same visual row
    # when their vertical overlap is at least this fraction of
    # the smaller line height. Used to merge split numbering
    # ("3.2." + "Moratorium Option") and table cells into one
    # logical row-line.
    #
    ROW_OVERLAP_RATIO = 0.6

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

            #
            # Merge fragments that share the same visual row.
            # This turns "3.2." + "Moratorium Option" into one
            # line and table cells into one row-line, so the
            # aligner compares rows against rows.
            #
            logical_page.lines = self._merge_row_fragments(
                logical_page.lines
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

        #
        # IMPORTANT:
        #
        # page.get_text("words") numbers blocks over TEXT blocks
        # only, while page_dict["blocks"] also contains image
        # blocks. We therefore keep a separate text-only counter
        # and use it as block_index, so that _attach_words can
        # join both views on the same key.
        #
        text_block_index = -1

        for block in page_dict["blocks"]:

            # Ignore images for now
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
            # Match this word with the span that overlaps it the
            # most horizontally. Center-containment fails for
            # words that straddle two spans or when span boxes
            # are slightly off; overlap is far more forgiving.
            #

            matched_span = None
            best_overlap = 0.0

            for span in logical_line.spans:

                sx0, sy0, sx1, sy1 = span.bbox

                overlap = min(x1, sx1) - max(x0, sx0)

                if overlap > best_overlap:
                    best_overlap = overlap
                    matched_span = span

            #
            # Fallback: inherit from the first non-empty span of
            # the line rather than emitting fake 0.0 / "" values,
            # which downstream formatting comparison would report
            # as differences.
            #
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
        """
        Merge dict "lines" that live on the same visual row into a
        single LogicalLine.

        PDF generators frequently split one visual row into several
        line fragments:

        - list numbering emitted separately from heading text
        - every table cell emitted as its own line
        - tab-separated label / value pairs

        Comparing fragments individually is the main source of
        bullet and table false positives, because the two documents
        rarely fragment the same row the same way.

        Whitespace-only fragments are dropped entirely.
        """

        candidates = [
            line for line in lines
            if line.text.strip()
        ]

        if not candidates:
            return []

        #
        # Sort by vertical position first, then horizontal.
        #
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
        """
        True when `line` vertically overlaps the current row enough
        to be considered part of the same visual row.
        """

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
