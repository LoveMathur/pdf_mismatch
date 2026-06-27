from models.aligned_pair import AlignmentType, AlignedPair
from models.difference import Difference, DifferenceType

from comparators.base import BaseComparator


class InsertionDeletionComparator(BaseComparator):

    def compare(
        self,
        pairs: list[AlignedPair]
    ) -> list[Difference]:

        differences: list[Difference] = []

        for pair in pairs:

            if pair.alignment_type == AlignmentType.INSERT:

                differences.append(
                    Difference(
                        pair_index=pair.index,
                        difference_type=DifferenceType.INSERTION,
                        expected=None,
                        actual=pair.right.text,
                    )
                )

            elif pair.alignment_type == AlignmentType.DELETE:

                differences.append(
                    Difference(
                        pair_index=pair.index,
                        difference_type=DifferenceType.DELETION,
                        expected=pair.left.text,
                        actual=None,
                    )
                )

        return differences