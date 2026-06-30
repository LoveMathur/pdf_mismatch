from comparators.base import Comparator
from models.difference import Difference, DifferenceCategory, Severity
from models.logical_aligned_pair import AlignmentType, LogicalAlignedPair


class InsertionDeletionComparator(Comparator):
    """
    Identifies inserted and deleted lines between two documents.
    """

    def compare(
        self,
        pair: LogicalAlignedPair,
    ) -> list[Difference]:

        if pair.alignment == AlignmentType.INSERT:
            if pair.right is None:
                return []
            return [
                Difference(
                    category=DifferenceCategory.INSERTION,
                    severity=Severity.WARNING,
                    actual_line=pair.right,
                    actual_text=pair.right.text,
                    description=f"Line was inserted: '{pair.right.text}'",
                )
            ]

        elif pair.alignment == AlignmentType.DELETE:
            if pair.left is None:
                return []
            return [
                Difference(
                    category=DifferenceCategory.DELETION,
                    severity=Severity.ERROR,
                    expected_line=pair.left,
                    expected_text=pair.left.text,
                    description=f"Line was deleted: '{pair.left.text}'",
                )
            ]

        return []