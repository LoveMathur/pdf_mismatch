from __future__ import annotations

from dataclasses import dataclass

from models.logical_line import LogicalLine


@dataclass(slots=True)
class AlignmentRegion:
    """
    Represents one independent region bounded by two
    consecutive anchors.

    The region stores both the original indices and the
    sliced logical lines for easy downstream alignment.
    """

    left_start: int
    left_end: int

    right_start: int
    right_end: int

    left_lines: list[LogicalLine]
    right_lines: list[LogicalLine]