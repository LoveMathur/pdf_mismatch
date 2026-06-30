import pymupdf

from models.logical_word import LogicalWord


class WordExtractor:
    """
    Extracts every word from a PDF while preserving
    its exact location and reading order.
    """

    @staticmethod
    def extract(pdf_path: str) -> list[LogicalWord]:

        document = pymupdf.open(pdf_path)

        words: list[LogicalWord] = []

        for page_number, page in enumerate(document, start = 1):

            page_words = page.get_text("words")

            for word in page_words:

                (
                    x0,
                    y0,
                    x1,
                    y1,
                    text,
                    block,
                    line,
                    word_no,
                ) = word

                words.append(

                    LogicalWord(

                        page=page_number,

                        text=text,

                        bbox=(x0, y0, x1, y1),

                        block_index=block,

                        line_index=line,

                        word_index=word_no,

                    )

                )

        document.close()

        return words