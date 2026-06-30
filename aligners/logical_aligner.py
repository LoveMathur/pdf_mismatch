from difflib import SequenceMatcher

from models.logical_document import LogicalDocument
from models.logical_aligned_pair import (
    LogicalAlignedPair,
    AlignmentType,
)

class LogicalAligner:

    def align(
        self,
        left_doc: LogicalDocument,
        right_doc: LogicalDocument,
    ) -> list[LogicalAlignedPair]:

        left_lines = self._flatten(left_doc)

        right_lines = self._flatten(right_doc)

        return self._align_lines(
            left_lines,
            right_lines,
        )
    
    def _flatten(
        self,
        document: LogicalDocument,
    ):

        lines = []

        for page in document.pages:

            lines.extend(page.lines)

        return lines
        
    def _align_lines(
        self,
        left_lines,
        right_lines,
    ):

        matcher = SequenceMatcher(

            None,

            [line.text for line in left_lines],

            [line.text for line in right_lines],

        )

        pairs = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":

                for l, r in zip(
                    left_lines[i1:i2],
                    right_lines[j1:j2]
                ):

                    pairs.append(
                        LogicalAlignedPair(
                            left=l,
                            right=r,
                            alignment=AlignmentType.EQUAL
                        )
                    )

            elif tag == "replace":

                left_chunk = left_lines[i1:i2]
                right_chunk = right_lines[j1:j2]

                max_len = max(len(left_chunk), len(right_chunk))

                for k in range(max_len):

                    left = left_chunk[k] if k < len(left_chunk) else None
                    right = right_chunk[k] if k < len(right_chunk) else None

                    pairs.append(
                        LogicalAlignedPair(
                            left=left,
                            right=right,
                            alignment=AlignmentType.REPLACE,
                        )
                    )

            elif tag == "delete":

                for l in left_lines[i1:i2]:

                    pairs.append(

                        LogicalAlignedPair(

                            left=l,

                            alignment=AlignmentType.DELETE,

                        )

                    )

            elif tag == "insert":

                for r in right_lines[j1:j2]:

                    pairs.append(

                        LogicalAlignedPair(

                            right=r,

                            alignment=AlignmentType.INSERT,

                        )

                    )

        return pairs