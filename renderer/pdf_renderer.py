import pymupdf

from models.difference import Difference, DifferenceCategory


class PDFRenderer:

    HIGHLIGHT_COLOR = (1, 1, 0)      # Yellow
    COMMENT_COLOR = (1, 0.9, 0.2)

    def render(
        self,
        input_pdf: str,
        output_pdf: str,
        differences: list[Difference],
    ) -> None:

        document = pymupdf.open(input_pdf)

        for difference in differences:

            self._render_difference(
                document,
                difference,
            )

        document.save(
            output_pdf,
            garbage=4,
            deflate=True,
        )

        document.close()

        print()
        print("=" * 80)
        print(f"Annotated PDF saved to:\n{output_pdf}")
        print("=" * 80)

    #
    # Categories that are reported in the dashboard only. Image and
    # table checks work off page geometry, not a LogicalLine/Word,
    # so there's no meaningful single spot on the page to highlight
    # anyway -- and it was explicitly asked that these never get
    # marked on the rendered PDF.
    #
    DASHBOARD_ONLY_CATEGORIES = (
        DifferenceCategory.IMAGE,
        DifferenceCategory.TABLE,
    )

    def _render_difference(
        self,
        document,
        difference: Difference,
    ):

        if difference.category in self.DASHBOARD_ONLY_CATEGORIES:
            return

        target = self._choose_target(
            difference
        )

        if target is None:
            return

        page_number, bbox = target

        page = document[page_number]

        self._highlight(
            page,
            bbox,
        )

        self._add_comment(
            page,
            bbox,
            difference,
        )

    def _choose_target(
        self,
        difference: Difference,
    ):

        if difference.actual_word:

            return (
                difference.actual_word.page - 1,
                difference.actual_word.bbox,
            )

        if difference.actual_line:

            return (
                difference.actual_line.page - 1,
                difference.actual_line.bbox,
            )

        if difference.expected_word:

            return (
                difference.expected_word.page - 1,
                difference.expected_word.bbox,
            )

        if difference.expected_line:

            return (
                difference.expected_line.page - 1,
                difference.expected_line.bbox,
            )

        return None
    
    def _highlight(
        self,
        page,
        bbox,
    ):

        annot = page.add_highlight_annot(
            pymupdf.Rect(bbox)
        )

        annot.set_colors(
            stroke=self.HIGHLIGHT_COLOR
        )

        annot.update()

    def _add_comment(
        self,
        page,
        bbox,
        difference: Difference,
    ):

        message = (
            f"{difference.category}\n\n"
            f"Expected : {difference.expected_text}\n"
            f"Actual   : {difference.actual_text}\n\n"
            f"{difference.description}"
        )

        annot = page.add_text_annot(

            pymupdf.Point(
                bbox[2] + 5,
                bbox[1],
            ),

            message,

        )

        annot.update()