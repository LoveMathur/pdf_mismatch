import re

from comparators.base import Comparator
from comparators.replace import ReplaceComparator

from models.difference import (
    Difference,
    DifferenceCategory,
)

from models.logical_aligned_pair import (
    AlignmentType,
    LogicalAlignedPair,
)


class InsertDeleteComparator(Comparator):
    """
    Reports lines that exist in only one of the two documents.

    The previous InsertionDeletionComparator targeted the legacy
    AlignedPair API and was never registered in the pipeline, so
    INSERT / DELETE pairs produced no differences at all.

    Reflow protection
    -----------------
    Paragraph rewrap turns one physical line into different
    physical lines, which the aligner legitimately classifies as
    INSERT + DELETE. To avoid reporting these as differences, the
    comparator suppresses any inserted/deleted line whose
    normalized text already appears inside the full text of the
    other document. Only genuinely new / removed content survives.

    The ComparisonEngine calls set_context() once per run.
    """

    MIN_LENGTH = 4

    def __init__(self):
        self._left_full = ""
        self._right_full = ""

    def set_context(
        self,
        left_full_text: str,
        right_full_text: str,
    ) -> None:
        self._left_full = left_full_text
        self._right_full = right_full_text

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def compare(
        self,
        pair: LogicalAlignedPair,
    ) -> list[Difference]:

        if pair.alignment == AlignmentType.INSERT:
            line = pair.right
            other_full = self._left_full
            category = DifferenceCategory.INSERTION
        elif pair.alignment == AlignmentType.DELETE:
            line = pair.left
            other_full = self._right_full
            category = DifferenceCategory.DELETION
        else:
            return []

        if line is None:
            return []

        text = line.text.strip()

        if len(text) < self.MIN_LENGTH:
            return []

        # Pure structural / numbering tokens
        if re.fullmatch(
            ReplaceComparator.BULLET_PATTERN, text, re.I
        ):
            return []

        # Page decorations
        if re.fullmatch(r"page\s*\|?\s*\d+(\s+of\s+\d+)?", text, re.I):
            return []

        #
        # Reflow suppression: if the content already exists in the
        # other document, this line is a rewrap artefact rather
        # than an insertion / deletion.
        #
        normalized = self._normalize(text)

        if normalized and normalized in other_full:
            return []

        if category == DifferenceCategory.INSERTION:
            expected_text, actual_text = None, text
            expected_line, actual_line = None, line
            description = f"Content inserted: '{text[:80]}'"
        else:
            expected_text, actual_text = text, None
            expected_line, actual_line = line, None
            description = f"Content removed: '{text[:80]}'"

        return [
            Difference(
                category=category,
                expected_line=expected_line,
                actual_line=actual_line,
                expected_text=expected_text,
                actual_text=actual_text,
                description=description,
            )
        ]
