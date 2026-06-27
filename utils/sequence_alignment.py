from difflib import SequenceMatcher

from models.aligned_pair import AlignedPair, AlignmentType
from models.text_element import TextElement

class SequenceAligner:

    """
    Aligns two sequences of TextElements.
    """

    def align(
        self,
        left: list[TextElement],
        right: list[TextElement]
    ) -> list[AlignedPair]:

        pair_index = 0
        left_text = [element.comparison_text for element in left]
        right_text = [element.comparison_text for element in right]

        matcher = SequenceMatcher(
            None,
            left_text,
            right_text,
            autojunk=False
        )

        aligned: list[AlignedPair] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":

                for l, r in zip(
                    left[i1:i2],
                    right[j1:j2]
                ):

                    aligned.append(
                        AlignedPair(
                            index=pair_index,
                            left=l,
                            right=r,
                            alignment_type=AlignmentType.EQUAL
                        )
                    )
                    pair_index += 1

            elif tag == "replace":

                length = max(i2 - i1, j2 - j1)

                for k in range(length):

                    aligned.append(
                        AlignedPair(
                            index=pair_index,
                            left=left[i1+k] if i1+k < i2 else None,
                            right=right[j1+k] if j1+k < j2 else None,
                            alignment_type=AlignmentType.REPLACE
                        )
                    )
                    pair_index += 1

            elif tag == "delete":

                for item in left[i1:i2]:

                    aligned.append(
                        AlignedPair(
                            index=pair_index,
                            left=item,
                            right=None,
                            alignment_type=AlignmentType.DELETE
                        )
                    )
                    pair_index += 1

            elif tag == "insert":

                for item in right[j1:j2]:

                    aligned.append(
                        AlignedPair(
                            index=pair_index,
                            left=None,
                            right=item,
                            alignment_type=AlignmentType.INSERT
                        )
                    )
                    pair_index += 1

        return aligned