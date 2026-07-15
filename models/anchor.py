from __future__ import annotations

from dataclasses import dataclass

from models.logical_line import LogicalLine


@dataclass(slots=True)
class Anchor:
    """
    Represents a stable synchronization point in a document.

    An Anchor wraps a LogicalLine together with metadata used
    during anchor detection and matching.
    """

    line: LogicalLine

    # Position within the flattened document
    index: int

    # Computed importance score
    score: float

    # Normalized text used during matching
    normalized_text: str