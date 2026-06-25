import pymupdf

from models.document import Document
from models.page import Page
from models.word import Word


class DigitalPDFExtractor:

    def extract(self, pdf_path: str):

        pdf = pymupdf.open(pdf_path)

        pages = []

        for page_index, page in enumerate(pdf):

            words = []

            extracted = page.get_text("dict")

            for block in extracted:

                x0, y0, x1, y1, text, block_no, line_no, word_no = block

                words.append(
                    Word(
                        text=text,
                        page=page_index + 1,
                        bbox=(x0, y0, x1, y1),
                        line_no=line_no,
                        block_no=block_no,
                    )
                )

            pages.append(
                Page(
                    page_number=page_index + 1,
                    words=words,
                )
            )

        return Document(
            file_name=pdf_path,
            pages=pages,
        )