import re

from comparators.analyzers.base_analyzer import BaseAnalyzer

from models.aligned_pair import AlignedPair
from models.difference import Difference, DifferenceType


class WhitespaceAnalyzer(BaseAnalyzer):

    @staticmethod
    def normalize(text: str) -> str:
        """
        Collapse all whitespace (spaces, tabs, newlines)
        into a single space.
        """
        return re.sub(r"\s+", " ", text).strip()

    def analyze(
        self,
        pair: AlignedPair
    ) -> list[Difference]:

        if pair.left is None or pair.right is None:
            return []

        # IMPORTANT:
        # Use original extracted text, NOT comparison_text.
        left = pair.left.text
        right = pair.right.text

        if left == right:
            return []

        if self.normalize(left) != self.normalize(right):
            return []

        return [

            Difference(

                pair_index=pair.index,

                difference_type=DifferenceType.WHITESPACE,

                expected=left,

                actual=right,

                confidence=1.0,

                metadata={

                    "expected_length": len(left),

                    "actual_length": len(right),

                    "expected_whitespace": len(re.findall(r"\s", left)),

                    "actual_whitespace": len(re.findall(r"\s", right))

                }

            )

        ]