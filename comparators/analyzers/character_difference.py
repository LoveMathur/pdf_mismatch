from comparators.analyzers.base_analyzer import BaseAnalyzer

from models.aligned_pair import AlignedPair
from models.difference import Difference, DifferenceType

from utils.character_edit_extractor import CharacterEditExtractor
from utils.text_similarity import TextSimilarity


class CharacterDifferenceAnalyzer(BaseAnalyzer):

    """
    Detects small non-linguistic character edits.

    Examples:
        fox -> f0x
        O -> 0
        @ -> A
        - -> –
        © -> (c)

    Pure alphabetic edits are ignored because they are handled
    by SpellingAnalyzer.

    Large edits are ignored because they are handled by
    WordAnalyzer.
    """

    MAX_FRAGMENT_LENGTH = 2

    @staticmethod
    def is_alpha_or_empty(text: str) -> bool:
        return text == "" or text.isalpha()

    def analyze(
        self,
        pair: AlignedPair
    ) -> list[Difference]:

        if pair.left is None or pair.right is None:
            return []

        similarity = TextSimilarity.compare(
            pair.left.comparison_text,
            pair.right.comparison_text
            )

        if similarity.similarity < 0.90:
            return []

        edits = CharacterEditExtractor.extract(
            pair.left.comparison_text,
            pair.right.comparison_text,
            pair.index
        )

        differences = []

        for edit in edits:

            expected = edit.expected_fragment
            actual = edit.actual_fragment

            # --------------------------------------------------
            # Ignore large edits.
            # These belong to WordAnalyzer.
            # --------------------------------------------------

            if max(len(expected), len(actual)) > self.MAX_FRAGMENT_LENGTH:
                continue

            # --------------------------------------------------
            # Ignore pure alphabetic edits.
            # These belong to SpellingAnalyzer.
            # --------------------------------------------------

            if (
                self.is_alpha_or_empty(expected)
                and
                self.is_alpha_or_empty(actual)
            ):
                continue

            differences.append(

                Difference(

                    pair_index=pair.index,

                    difference_type=DifferenceType.CHARACTER,

                    expected=pair.left.text,

                    actual=pair.right.text,

                    confidence=1.0,

                    metadata={

                        "operation": edit.operation.value,

                        "expected_fragment": expected,

                        "actual_fragment": actual,

                        "left_start": edit.left_start,

                        "left_end": edit.left_end,

                        "right_start": edit.right_start,

                        "right_end": edit.right_end

                    }

                )

            )

        return differences