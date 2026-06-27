from dataclasses import dataclass
from difflib import SequenceMatcher

from rapidfuzz.distance import Levenshtein


@dataclass
class SimilarityResult:

    similarity: float

    levenshtein_distance: int

    edit_operations: list


class TextSimilarity:

    @staticmethod
    def compare(
        left: str,
        right: str
    ) -> SimilarityResult:

        matcher = SequenceMatcher(
            None,
            left,
            right,
            autojunk=False
        )

        return SimilarityResult(

            similarity=matcher.ratio(),

            levenshtein_distance=Levenshtein.distance(
                left,
                right
            ),

            edit_operations=matcher.get_opcodes()

        )

    @staticmethod
    def ratio(
        left: str,
        right: str
    ) -> float:

        return Levenshtein.normalized_similarity(
            left,
            right
        )

    @staticmethod
    def distance(
        left: str,
        right: str
    ) -> int:

        return Levenshtein.distance(
            left,
            right
        )