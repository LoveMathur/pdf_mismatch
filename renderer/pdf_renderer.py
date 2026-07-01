import pymupdf

from models.difference import Difference
from models.difference_group import DifferenceGroup


class PDFRenderer:

    HIGHLIGHT_COLOR = (1, 1, 0)      # Yellow
    COMMENT_COLOR = (1, 0.9, 0.2)

    def render(
        self,
        input_pdf: str,
        output_pdf: str,
        groups: list[DifferenceGroup],
    ) -> None:

        document = pymupdf.open(input_pdf)

        for group in groups:

            self._render_difference(
                document,
                group,
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

    def _render_difference(
        self,
        document,
        group,
    ):

        page = document[group.page - 1]

        self._highlight(
            page,
            group.bbox,
        )

        self._add_comment(
            page,
            group,
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
        group,
    ):

        annot = page.add_text_annot(

        pymupdf.Point(

            group.bbox[2] + 5,

            group.bbox[1],

        ),

        f"{group.title}\n\n{group.message}",

    )

        annot.update()
            