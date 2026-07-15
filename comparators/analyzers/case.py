from comparators.analyzers.base_analyzer import BaseAnalyzer

from models.aligned_pair import AlignedPair
from models.difference import Difference, DifferenceType


class CaseAnalyzer(BaseAnalyzer):

    def analyze(
        self,
        pair: AlignedPair
    ) -> list[Difference]:

        if pair.left is None or pair.right is None:
            return []

        left = pair.left.comparison_text
        right = pair.right.comparison_text

        # Ignore identical strings
        if left == right:
            return []

        # Detect pure case differences
        if left.lower() != right.lower():
            return []

        return [

            Difference(

                pair_index=pair.index,

                difference_type=DifferenceType.CASE,

                expected=pair.left.text,

                actual=pair.right.text,

                confidence=1.0,

                metadata={

                    "expected": left,

                    "actual": right,

                    "expected_lower": left.lower(),

                    "actual_lower": right.lower()

                }

            )

        ]