from difflib import SequenceMatcher

from rapidfuzz.distance import Levenshtein

from comparators.analyzers.base_analyzer import BaseAnalyzer

from models.aligned_pair import AlignedPair
from models.difference import Difference, DifferenceType


class WordAnalyzer(BaseAnalyzer):

    CHARACTER_DISTANCE = 2

    def analyze(
        self,
        pair: AlignedPair
    ) -> list[Difference]:

        if pair.left is None or pair.right is None:
            return []

        left_words = pair.left.comparison_text.split()
        right_words = pair.right.comparison_text.split()

        matcher = SequenceMatcher(
            None,
            left_words,
            right_words,
            autojunk=False
        )

        differences = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":
                continue

            expected = " ".join(left_words[i1:i2])
            actual = " ".join(right_words[j1:j2])

            # ------------------------------------
            # Ignore pure case changes
            # ------------------------------------

            if expected.lower() == actual.lower():
                continue

            # ------------------------------------
            # Ignore numeric changes
            # ------------------------------------

            if expected.replace(".", "").replace(":", "").isdigit() \
               and actual.replace(".", "").replace(":", "").isdigit():

                continue

            # ------------------------------------
            # Ignore tiny character edits
            # (Character / Spelling analyzer)
            # ------------------------------------

            distance = Levenshtein.distance(
                expected,
                actual
            )

            if distance <= self.CHARACTER_DISTANCE:
                continue

            differences.append(

                Difference(

                    pair_index=pair.index,

                    difference_type=DifferenceType.WORD,

                    expected=expected,

                    actual=actual,

                    confidence=matcher.ratio(),

                    metadata={

                        "operation": tag,

                        "left_word_index": i1,

                        "right_word_index": j1,

                        "distance": distance

                    }

                )

            )

        return differences