from renderer.annotation_target import AnnotationTarget

from interpreters.issue_formatter import IssueFormatter
from interpreters.issue_localizer import IssueLocalizer

from models.aligned_pair import AlignedPair
from models.difference import Difference
from models.logical_word import LogicalWord


class AnnotationBuilder:
    """
    Converts comparison differences into renderer-ready
    annotation targets.

    The builder itself performs no localization.
    """

    @staticmethod
    def build(
        differences: list[Difference],
        aligned_pairs: list[AlignedPair],
    ) -> list[AnnotationTarget]:

        annotations: list[AnnotationTarget] = []

        for difference in differences:

            if difference.pair_index >= len(aligned_pairs):
                continue

            pair = aligned_pairs[difference.pair_index]

            issue = IssueFormatter.format(difference)

            targets = IssueLocalizer.build_targets(

                issue=issue,
                difference=difference,
                pair=pair,

            )

            annotations.extend(targets)

        return annotations