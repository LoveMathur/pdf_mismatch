from comparators.base import Comparator

from models.difference_group import DifferenceGroup
from models.logical_aligned_pair import LogicalAlignedPair


class ComparisonEngine:
    """
    Runs every comparator over every aligned pair.
    """

    def __init__(
        self,
        comparators: list[Comparator],
    ):
        self.comparators = comparators

    def compare(
        self,
        aligned_pairs: list[LogicalAlignedPair],
    ) -> list[DifferenceGroup]:

        groups: list[DifferenceGroup] = []

        for pair in aligned_pairs:

            for comparator in self.comparators:

                result = comparator.compare(pair)

                if result:
                    groups.extend(result)

        return groups