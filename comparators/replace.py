from difflib import SequenceMatcher

from comparators.base import Comparator

from models.difference import (
    Difference,
    DifferenceCategory,
)

from models.logical_aligned_pair import (
    AlignmentType,
    LogicalAlignedPair,
)


class ReplaceComparator(Comparator):

    def compare(
        self,
        pair: LogicalAlignedPair,
    ) -> list[Difference]:

        if pair.alignment != AlignmentType.REPLACE:
            return []

        if pair.left is None or pair.right is None:
            return []

        return self._compare_words(
            pair.left,
            pair.right,
        )

    def _compare_words(
        self,
        left_line,
        right_line,
    ) -> list[Difference]:

        differences = []

        matcher = SequenceMatcher(

            None,

            [w.text for w in left_line.words],

            [w.text for w in right_line.words],

        )

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":
                continue

            left_words = left_line.words[i1:i2]
            right_words = right_line.words[j1:j2]

            max_len = max(
                len(left_words),
                len(right_words),
            )

            for k in range(max_len):

                left_word = (
                    left_words[k]
                    if k < len(left_words)
                    else None
                )

                right_word = (
                    right_words[k]
                    if k < len(right_words)
                    else None
                )

                differences.append(

                    Difference(

                        category=self._classify(
                            left_word,
                            right_word,
                        ),

                        expected_line=left_line,

                        actual_line=right_line,

                        expected_word=left_word,

                        actual_word=right_word,

                        expected_text=(
                            left_word.text
                            if left_word
                            else None
                        ),

                        actual_text=(
                            right_word.text
                            if right_word
                            else None
                        ),

                        description=self._description(
                            left_word,
                            right_word,
                        ),

                    )

                )

        return differences

    def _classify(
        self,
        left_word,
        right_word,
    ) -> DifferenceCategory:

        if left_word is None or right_word is None:
            return DifferenceCategory.WORD

        if any(
            c.isdigit()
            for c in left_word.text + right_word.text
        ):
            return DifferenceCategory.NUMBER

        return DifferenceCategory.WORD

    def _description(
        self,
        left_word,
        right_word,
    ) -> str:

        if left_word and right_word:

            return (
                f"'{left_word.text}' changed to "
                f"'{right_word.text}'."
            )

        if left_word:

            return (
                f"'{left_word.text}' removed."
            )

        return (
            f"'{right_word.text}' inserted."
        )