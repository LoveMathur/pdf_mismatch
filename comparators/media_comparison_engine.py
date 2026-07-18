from comparators.analyzers.image_comparator import ImageComparator
from comparators.analyzers.table_comparator import TableComparator

from models.difference import Difference
from models.logical_document import LogicalDocument


class MediaComparisonEngine:
    """
    Compares non-textual page objects (images, tables) between two
    documents.

    Deliberately separate from ComparisonEngine: images and tables
    have no LogicalAlignedPair to hook into -- there's nothing to
    align against, they're geometric objects, not text -- so this
    engine works directly off the two LogicalDocuments and produces
    plain Difference objects that slot into the same downstream
    list the renderer and dashboard already consume. The existing
    text pipeline (aligner + ComparisonEngine + its 3 comparators)
    is not touched by this at all.
    """

    def __init__(self):
        self.image_comparator = ImageComparator()
        self.table_comparator = TableComparator()

    def compare(
        self,
        left_document: LogicalDocument,
        right_document: LogicalDocument,
    ) -> list[Difference]:

        differences: list[Difference] = []

        differences.extend(
            self.image_comparator.compare(left_document, right_document)
        )

        differences.extend(
            self.table_comparator.compare(left_document, right_document)
        )

        return differences
