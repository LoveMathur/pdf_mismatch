from difflib import SequenceMatcher

from rapidfuzz.distance import Levenshtein

from comparators.analyzers.base_analyzer import BaseAnalyzer

from models.aligned_pair import AlignedPair
from models.difference import Difference, DifferenceType


class SpellingAnalyzer(BaseAnalyzer):

    MAX_DISTANCE = 2
    MIN_SIMILARITY = 0.80

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

            if tag != "replace":
                continue

            # Only compare single-word replacements.
            if (i2 - i1) != 1 or (j2 - j1) != 1:
                continue

            expected = left_words[i1]
            actual = right_words[j1]

            # Ignore case-only changes.
            if expected.lower() == actual.lower():
                continue

            # Only alphabetic words.
            if not expected.isalpha():
                continue

            if not actual.isalpha():
                continue

            distance = Levenshtein.distance(
                expected.lower(),
                actual.lower()
            )

            if distance > self.MAX_DISTANCE:
                continue

            similarity = Levenshtein.normalized_similarity(
                expected.lower(),
                actual.lower()
            )

            if similarity < self.MIN_SIMILARITY:
                continue

            differences.append(

                Difference(

                    pair_index=pair.index,

                    difference_type=DifferenceType.SPELLING,

                    expected=expected,

                    actual=actual,

                    confidence=similarity,

                    metadata={

                        "operation": tag,

                        "left_word_index": i1,

                        "right_word_index": j1,

                        "distance": distance,

                        "similarity": similarity

                    }

                )

            )

        return differences