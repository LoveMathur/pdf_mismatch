from models.difference import Difference
from models.logical_aligned_pair import LogicalAlignedPair

from comparators.base import Comparator


class ComparisonEngine:

    def __init__(
        self,
        comparators: list[Comparator],
    ):

        self.comparators = comparators

    def compare(
        self,
        pairs: list[LogicalAlignedPair],
    ) -> list[Difference]:

        differences = []

        for pair in pairs:

            for comparator in self.comparators:

                differences.extend(
                    comparator.compare(pair)
                )

        return differences