from difflib import SequenceMatcher

from rapidfuzz.distance import Levenshtein

from comparators.analyzers.base_analyzer import BaseAnalyzer

from models.aligned_pair import AlignedPair
from models.difference import Difference, DifferenceType


class WordAnalyzer(BaseAnalyzer):

    CHARACTER_DISTANCE = 2

    def analyze(
        self,
        pair: AlignedPair,
    ) -> list[Difference]:

        # ----------------------------------------------------
        # Pair must exist
        # ----------------------------------------------------

        if pair.left is None or pair.right is None:
            return []

        # ----------------------------------------------------
        # Only REPLACE pairs need word analysis
        # ----------------------------------------------------

        if pair.alignment.name != "REPLACE":
            return []

        left_text = pair.left.comparison_text.strip()
        right_text = pair.right.comparison_text.strip()

        # ----------------------------------------------------
        # Skip identical text
        # ----------------------------------------------------

        if left_text == right_text:
            return []

        left_words = left_text.split()
        right_words = right_text.split()

        # ----------------------------------------------------
        # Skip if tokenization is identical
        # ----------------------------------------------------

        if left_words == right_words:
            return []

        matcher = SequenceMatcher(
            None,
            left_words,
            right_words,
            autojunk=False,
        )

        differences = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":
                continue

            expected = " ".join(left_words[i1:i2])
            actual = " ".join(right_words[j1:j2])

            # ------------------------------------
            # Ignore empty edits
            # ------------------------------------

            if not expected and not actual:
                continue

            # ------------------------------------
            # Ignore case-only edits
            # ------------------------------------

            if expected.lower() == actual.lower():
                continue

            # ------------------------------------
            # Ignore whitespace-only edits
            # ------------------------------------

            if (
                " ".join(expected.split())
                ==
                " ".join(actual.split())
            ):
                continue

            # ------------------------------------
            # Ignore structural bullets
            # ------------------------------------

            structural = {
                "1)", "2)", "3)", "4)", "5)", "6)", "7)", "8)", "9)",
                "(i)", "(ii)", "(iii)", "(iv)", "(v)",
                "(a)", "(b)", "(c)", "(d)",
                "-", "•"
            }

            if (
                expected.strip() in structural
                or actual.strip() in structural
            ):
                continue

            # ------------------------------------
            # Ignore pure numeric edits
            # ------------------------------------

            if (
                expected.replace(".", "").replace(":", "").isdigit()
                and
                actual.replace(".", "").replace(":", "").isdigit()
            ):
                continue

            # ------------------------------------
            # Leave spelling mistakes to CharacterAnalyzer
            # ------------------------------------

            distance = Levenshtein.distance(
                expected,
                actual,
            )

            if distance <= self.CHARACTER_DISTANCE:
                continue

            # ------------------------------------
            # Ignore huge paragraph reflow blocks
            # ------------------------------------

            if (
                len(expected.split()) > 12
                and
                len(actual.split()) > 12
            ):
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

                        "distance": distance,

                    },

                )

            )

        return differences