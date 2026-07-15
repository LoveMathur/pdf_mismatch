from renderer.annotation_target import AnnotationTarget

from models.aligned_pair import AlignedPair
from models.difference import Difference
from models.issue_description import IssueDescription


class IssueLocalizer:
    """
    Temporary implementation.

    Since WordMapper has been removed, annotations are attached to the
    entire logical line (TextElement). Once the comparison engine is
    migrated to LogicalLine, this class will annotate individual words
    directly without any mapping.
    """

    @staticmethod
    def build_targets(
        issue: IssueDescription,
        difference: Difference,
        pair: AlignedPair,
    ) -> list[AnnotationTarget]:

        # -----------------------------
        # Determine which side to annotate
        # -----------------------------
        element = pair.right if pair.right is not None else pair.left

        if element is None:
            return []

        return [

            AnnotationTarget(

                difference=difference,

                page=element.page,

                bbox=element.bbox,

                title=issue.title,

                message=issue.message,

                severity=issue.severity,

            )

        ]