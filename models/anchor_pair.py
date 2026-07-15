from __future__ import annotations

from dataclasses import dataclass

from models.anchor import Anchor


@dataclass(slots=True)
class AnchorPair:
    """
    Represents one matched anchor between
    the left and right document.
    """

    left: Anchor
    right: Anchor

    # Similarity score between the anchors
    similarity: float