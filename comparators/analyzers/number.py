import re
from difflib import SequenceMatcher

from comparators.analyzers.base_analyzer import BaseAnalyzer

from models.aligned_pair import AlignedPair
from models.difference import Difference, DifferenceType
from models.numeric_type import NumericType


class NumberAnalyzer(BaseAnalyzer):

    def detect_type(self, token: str) -> NumericType:

        token = token.strip()

        # -----------------------------
        # Time
        # -----------------------------

        if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", token):
            return NumericType.TIME

        # -----------------------------
        # Date
        # -----------------------------

        if re.fullmatch(
            r"\d{1,4}[/-]\d{1,2}[/-]\d{1,4}",
            token,
        ):
            return NumericType.DATE

        # -----------------------------
        # Phone
        # -----------------------------

        if re.fullmatch(
            r"\+?\d[\d -]{7,}",
            token,
        ):
            return NumericType.PHONE

        # -----------------------------
        # Decimal
        # -----------------------------

        if re.fullmatch(
            r"\d+\.\d+",
            token,
        ):
            return NumericType.DECIMAL

        # -----------------------------
        # Integer
        # -----------------------------

        if re.fullmatch(
            r"\d+",
            token,
        ):
            return NumericType.INTEGER

        # -----------------------------
        # Identifier
        # -----------------------------

        if re.fullmatch(
            r"[A-Za-z]+(?:-[A-Za-z0-9]+)+",
            token,
        ):
            return NumericType.IDENTIFIER

        return NumericType.UNKNOWN

    def analyze(self, pair: AlignedPair) -> list[Difference]:

        if pair.left is None or pair.right is None:
            return []

        left_words = pair.left.comparison_text.split()
        right_words = pair.right.comparison_text.split()

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

            expected_tokens = left_words[i1:i2]
            actual_tokens = right_words[j1:j2]

            if len(expected_tokens) != 1 or len(actual_tokens) != 1:
                continue

            expected = expected_tokens[0]
            actual = actual_tokens[0]

            left_type = self.detect_type(expected)
            right_type = self.detect_type(actual)

            # Ignore if neither side is numeric
            if (
                left_type == NumericType.UNKNOWN
                and right_type == NumericType.UNKNOWN
            ):
                continue

            # If only one side is numeric, let WordAnalyzer handle it.
            if (
                left_type == NumericType.UNKNOWN
                or right_type == NumericType.UNKNOWN
            ):
                continue

            differences.append(
                Difference(
                    pair_index=pair.index,
                    difference_type=DifferenceType.NUMBER,
                    expected=expected,
                    actual=actual,
                    confidence=1.0,
                    metadata={
                        "operation": tag,
                        "numeric_type": (
                            left_type.value
                            if left_type == right_type
                            else NumericType.UNKNOWN.value
                        ),
                        "left_word_index": i1,
                        "right_word_index": j1,
                    },
                )
            )

        return differences