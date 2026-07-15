from __future__ import annotations

import re
from typing import List
import unicodedata
from rapidfuzz import fuzz

from models.logical_document import LogicalDocument
from models.logical_line import LogicalLine
from models.logical_aligned_pair import LogicalAlignedPair, AlignmentType
from models.anchor import Anchor
from models.anchor_pair import AnchorPair
from models.alignment_region import AlignmentRegion


class RobustLogicalAligner:
    """
    A production-oriented logical aligner designed to be resilient against:

    - PDF -> Word -> PDF conversions
    - Line reflow
    - Paragraph rewrapping
    - Split / merged logical lines
    - Moderate insertions and deletions

    This aligner follows a hierarchical pipeline:

        1. Detect anchors
        2. Match anchors
        3. Build independent regions
        4. Align each region
        5. Merge aligned pairs
    """

    def __init__(
        self,
        anchor_similarity: float = 90.0,
        local_similarity: float = 80.0,
    ):
        self.anchor_similarity = anchor_similarity
        self.local_similarity = local_similarity


    def _determine_alignment(
        self,
        left: LogicalLine | None,
        right: LogicalLine | None,
    ) -> AlignmentType:

        if left is None:
            return AlignmentType.INSERT

        if right is None:
            return AlignmentType.DELETE

        left_text = self._left_cache[id(left)]
        right_text = self._right_cache[id(right)]

        if left_text == right_text:
            return AlignmentType.EQUAL

        return AlignmentType.REPLACE
    
    
    def align(
        self,
        left_document: LogicalDocument,
        right_document: LogicalDocument,
    ) -> List[LogicalAlignedPair]:

        left_lines = self._flatten_document(left_document)
        right_lines = self._flatten_document(right_document)

        self._left_cache = {
            id(line): self._normalize_line_text(line.text)
            for line in left_lines
        }

        self._right_cache = {
            id(line): self._normalize_line_text(line.text)
            for line in right_lines
        }

        left_anchors = self._detect_anchors(left_lines)
        right_anchors = self._detect_anchors(right_lines)

        anchor_pairs = self._align_anchor_sequences(
            left_anchors,
            right_anchors,
        )

        regions = self._build_regions(
            left_lines,
            right_lines,
            anchor_pairs,
        )

        aligned_pairs: List[LogicalAlignedPair] = []

        for region in regions:
            aligned_pairs.extend(
                self._align_region(region)
            )
        
        return aligned_pairs


    def _align_anchor_sequences(
        self,
        left_anchors: list[Anchor],
        right_anchors: list[Anchor],
    ) -> list[AnchorPair]:
        """
        Align anchor sequences using dynamic programming.

        Unlike greedy matching, this guarantees:
        - one-to-one matching
        - monotonic ordering
        - globally optimal anchor alignment
        """

        GAP = -50

        rows = len(left_anchors) + 1
        cols = len(right_anchors) + 1

        dp = [
            [0.0 for _ in range(cols)]
            for _ in range(rows)
        ]

        # -------------------------
        # Initialize borders
        # -------------------------

        for i in range(1, rows):
            dp[i][0] = dp[i - 1][0] + GAP

        for j in range(1, cols):
            dp[0][j] = dp[0][j - 1] + GAP

        # -------------------------
        # Fill DP matrix
        # -------------------------

        for i in range(1, rows):

            left = left_anchors[i - 1]

            for j in range(1, cols):

                right = right_anchors[j - 1]

                similarity = fuzz.ratio(
                    left.normalized_text,
                    right.normalized_text,
                )

                # Penalize anchors that are far apart
                position_similarity = 100 - (
                    abs(left.index - right.index)
                    / max(len(left_anchors), len(right_anchors))
                ) * 100

                score = (
                    similarity * 0.8
                    + position_similarity * 0.2
                )

                if score >= self.anchor_similarity:

                    diagonal = dp[i - 1][j - 1] + score

                else:

                    diagonal = float("-inf")

                up = dp[i - 1][j] + GAP
                left_gap = dp[i][j - 1] + GAP

                dp[i][j] = max(
                    diagonal,
                    up,
                    left_gap,
                )

        # -------------------------
        # Traceback
        # -------------------------

        i = len(left_anchors)
        j = len(right_anchors)

        pairs: list[AnchorPair] = []

        while i > 0 or j > 0:

            if i > 0 and j > 0:

                left = left_anchors[i - 1]
                right = right_anchors[j - 1]

                similarity = fuzz.ratio(
                    left.normalized_text,
                    right.normalized_text,
                )

                position_similarity = 100 - (
                    abs(left.index - right.index)
                    / max(len(left_anchors), len(right_anchors))
                ) * 100

                score = (
                    similarity * 0.8
                    + position_similarity * 0.2
                )

                if score >= self.anchor_similarity:

                    expected = dp[i - 1][j - 1] + score

                    if abs(dp[i][j] - expected) < 1e-6:

                        pairs.append(
                            AnchorPair(
                                left=left,
                                right=right,
                                similarity=score,
                            )
                        )

                        i -= 1
                        j -= 1
                        continue

            if (
                i > 0
                and abs(dp[i][j] - (dp[i - 1][j] + GAP)) < 1e-6
            ):
                i -= 1
                continue

            j -= 1

        pairs.reverse()

        return pairs

    def _align_region(
        self,
        region: AlignmentRegion,
    ) -> list[LogicalAlignedPair]:
        """
        Align a single logical region.

        Each region is aligned independently using the
        weighted DP aligner.
        """

        paired_lines = self._pair_region_lines(
            region.left_lines,
            region.right_lines,
        )

        aligned_pairs: list[LogicalAlignedPair] = []

        for left, right in paired_lines:

            aligned_pairs.append(
                LogicalAlignedPair(
                    left=left,
                    right=right,
                    alignment=self._determine_alignment(
                        left,
                        right,
                    ),
                )
            )

        return aligned_pairs


    def _detect_anchors(
        self,
        lines: list[LogicalLine],
    ) -> list[Anchor]:
        """
        Detect stable synchronization anchors.

        The scoring intentionally favours headings and
        structural lines while suppressing headers,
        footers and page numbers.
        """

        anchors: list[Anchor] = []

        for index, line in enumerate(lines):

            text = line.text.strip()

            if not text:
                continue

            normalized = self._normalize_anchor_text(text)

            score = self._score_anchor(text)

            if score < 5:
                continue

            anchors.append(
                Anchor(
                    line=line,
                    index=index,
                    score=score,
                    normalized_text=normalized,
                )
            )

        return anchors
    
    def _normalize_anchor_text(
        self,
        text: str,
    ) -> str:

        text = text.lower()

        text = re.sub(r"[^a-z0-9 ]", " ", text)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _normalize_line_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize extracted PDF text before deciding
        whether two aligned lines are actually identical.
        """
        import unicodedata

        text = unicodedata.normalize("NFKC", text)
        # Normalize unicode whitespace
        text = (
            text
            .replace("\u00A0", " ")
            .replace("\u2007", " ")
            .replace("\u2009", " ")
            .replace("\u202F", " ")
            .replace("\u200B", "")
            .replace("\u00AD", "")
        )
        
        # Collapse repeated whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove spaces before punctuation
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)

        # Remove spaces immediately after opening brackets
        text = re.sub(r"([(\[]) +", r"\1", text)

        # Remove spaces immediately before closing brackets
        text = re.sub(r" +([)\]])", r"\1", text)

        return text.strip()

    def _structure_bonus(
        self,
        left: str,
        right: str,
    ) -> float:
        """
        Give a bonus to short structural lines so the DP
        prefers matching them instead of deleting/reinserting them.
        """

        left = left.strip()
        right = right.strip()

        if left != right:
            return 0.0

        # Numbered bullets
        if re.fullmatch(r"\d+\)", left):
            return 35.0

        # Roman numerals
        if re.fullmatch(r"[IVXLC]+\)", left):
            return 35.0

        # PART A, PART B ...
        if left.upper().startswith("PART"):
            return 30.0

        # Headings
        if left.isupper() and len(left) < 50:
            return 25.0

        # Very short identical structural lines
        if len(left) <= 12:
            return 20.0

        return 0.0
    
    def _is_horizontal_rule(
        self,
        text: str,
    ) -> bool:
        """
        Returns True if the line is essentially a horizontal rule
        or page separator.

        Examples:
        ----------
        ____________
        ------------
        ============
        ************
        """

        stripped = text.strip()

        if len(stripped) < 3:
            return False

        return bool(
            re.fullmatch(
                r"([_\-=*~.])\1{2,}",
                stripped,
            )
        )
    
    def _score_anchor(
        self,
        text: str,
    ) -> float:

        score = 0.0

        stripped = text.strip()

        upper = stripped.upper()

        # -------------------------
        # Ignore obvious junk
        # -------------------------

        if re.fullmatch(r"page\s+\d+\s+of\s+\d+", stripped.lower()):
            return -100

        if self._is_horizontal_rule(stripped):
            return -100

        if len(stripped) < 3:
            return -100

        # -------------------------
        # Headings
        # -------------------------

        first_word = upper.split(maxsplit=1)[0]

        match first_word:

            case "PART":
                score += 10

            case "SECTION":
                score += 10

            case "ANNEXURE":
                score += 10

            case "CHAPTER":
                score += 10

            case "PREAMBLE":
                score += 10

            case _:
                pass
        # -------------------------
        # Looks like heading
        # -------------------------

        if stripped.isupper():
            score += 8

        if stripped.endswith(":"):
            score += 3

        # -------------------------
        # Long unique line
        # -------------------------

        if len(stripped) > 25:
            score += 2

        # Mostly alphabetic

        alpha = sum(c.isalpha() for c in stripped)

        if alpha > len(stripped) * 0.6:
            score += 2

        return score

    def _match_anchors(
        self,
        left_anchors: list[Anchor],
        right_anchors: list[Anchor],
    ) -> list[AnchorPair]:
        """
        Match anchor candidates using one-to-one
        greedy similarity matching.
        """

        candidates = []

        for left in left_anchors:

            for right in right_anchors:

                similarity = fuzz.ratio(
                    left.normalized_text,
                    right.normalized_text,
                )

                if similarity < self.anchor_similarity:
                    continue

                candidates.append(
                    (
                        similarity,
                        left,
                        right,
                    )
                )

        candidates.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        matched_left = set()
        matched_right = set()

        pairs: list[AnchorPair] = []

        for similarity, left, right in candidates:

            if left.index in matched_left:
                continue

            if right.index in matched_right:
                continue

            matched_left.add(left.index)
            matched_right.add(right.index)

            pairs.append(
                AnchorPair(
                    left=left,
                    right=right,
                    similarity=similarity,
                )
            )

        pairs = self._filter_monotonic_pairs(pairs)

        return pairs

    def _filter_monotonic_pairs(
        self,
        pairs: list[AnchorPair],
    ) -> list[AnchorPair]:
        """
        Ensure that anchor matches preserve document order.

        Any anchor pair that would create a crossing alignment
        is discarded.

        Example

        LEFT

        A
        B
        C

        RIGHT

        A
        C
        B

        Pair(C,B) will be removed.
        """

        if not pairs:
            return []

        pairs.sort(
            key=lambda pair: pair.left.index
        )

        filtered: list[AnchorPair] = []

        last_right_index = -1

        for pair in pairs:

            if pair.right.index <= last_right_index:
                continue

            filtered.append(pair)

            last_right_index = pair.right.index

        return filtered
    
    def _flatten_document(
        self,
        document: LogicalDocument,
    ) -> list[LogicalLine]:
        """
        Flatten a LogicalDocument into a single ordered list
        of LogicalLines.

        The original reading order determined by the extractor
        is preserved.
        """

        lines: list[LogicalLine] = []

        for page in document.pages:

            lines.extend(page.lines)

        return lines
    
    def _build_regions(
        self,
        left_lines: list[LogicalLine],
        right_lines: list[LogicalLine],
        anchor_pairs: list[AnchorPair],
    ) -> list[AlignmentRegion]:
        """
        Split both documents into independent alignment regions.

        Regions are bounded by consecutive anchor pairs.

        Implicit START and END boundaries are added so that
        every logical line belongs to exactly one region.
        """

        regions: list[AlignmentRegion] = []

        # ----------------------------------------------------
        # No anchors found
        # ----------------------------------------------------

        if not anchor_pairs:

            regions.append(
                AlignmentRegion(
                    left_start=0,
                    left_end=len(left_lines),

                    right_start=0,
                    right_end=len(right_lines),

                    left_lines=left_lines,
                    right_lines=right_lines,
                )
            )

            return regions

        # ----------------------------------------------------
        # START -> First Anchor
        # ----------------------------------------------------

        first = anchor_pairs[0]

        regions.append(
            AlignmentRegion(
                left_start=0,
                left_end=first.left.index,

                right_start=0,
                right_end=first.right.index,

                left_lines=left_lines[0:first.left.index],
                right_lines=right_lines[0:first.right.index],
            )
        )

        # ----------------------------------------------------
        # Between consecutive anchors
        # ----------------------------------------------------

        for previous, current in zip(anchor_pairs, anchor_pairs[1:]):

            regions.append(
                AlignmentRegion(
                    left_start=previous.left.index,
                    left_end=current.left.index,

                    right_start=previous.right.index,
                    right_end=current.right.index,

                    left_lines=left_lines[previous.left.index:current.left.index],
                    right_lines=right_lines[previous.right.index:current.right.index],
                )
            )

        # ----------------------------------------------------
        # Last Anchor -> END
        # ----------------------------------------------------

        last = anchor_pairs[-1]

        regions.append(
            AlignmentRegion(
                left_start=last.left.index,
                left_end=len(left_lines),

                right_start=last.right.index,
                right_end=len(right_lines),

                left_lines=left_lines[last.left.index:],
                right_lines=right_lines[last.right.index:],
            )
        )

        return regions
    
    def _pair_region_lines(
        self,
        left_lines: list[LogicalLine],
        right_lines: list[LogicalLine],
    ) -> list[
        tuple[
            LogicalLine | None,
            LogicalLine | None,
        ]
    ]:

        matrix = self._compute_dp_matrix(
            left_lines,
            right_lines,
        )

        return self._traceback_alignment(
            matrix,
            left_lines,
            right_lines,
        )

    def _compute_dp_matrix(
        self,
        left_lines: list[LogicalLine],
        right_lines: list[LogicalLine],
    ) -> list[list[float]]:
        """
        Build a weighted alignment matrix.

        Match score comes from RapidFuzz similarity.

        Gap penalty discourages unnecessary insertions
        and deletions while still allowing them.
        """

        GAP = -30

        rows = len(left_lines) + 1
        cols = len(right_lines) + 1

        dp = [
            [0.0 for _ in range(cols)]
            for _ in range(rows)
        ]

        # -----------------------------
        # Initialize borders
        # -----------------------------

        for i in range(1, rows):
            dp[i][0] = dp[i - 1][0] + GAP

        for j in range(1, cols):
            dp[0][j] = dp[0][j - 1] + GAP

        # -----------------------------
        # Fill matrix
        # -----------------------------

        for i in range(1, rows):

            for j in range(1, cols):

                left_text = self._left_cache[id(left_lines[i - 1])]
                right_text = self._right_cache[id(right_lines[j - 1])]

                similarity = fuzz.ratio(
                    left_text,
                    right_text,
                )

                similarity += self._structure_bonus(
                    left_text,
                    right_text,
                )

                if similarity >= self.local_similarity:

                    diagonal = (
                        dp[i - 1][j - 1]
                        + similarity
                    )

                else:

                    diagonal = float("-inf")

                up = dp[i - 1][j] + GAP

                left = dp[i][j - 1] + GAP

                dp[i][j] = max(
                    diagonal,
                    up,
                    left,
                )

        return dp
    
    def _traceback_alignment(
        self,
        dp: list[list[float]],
        left_lines: list[LogicalLine],
        right_lines: list[LogicalLine],
    ) -> list[tuple[LogicalLine | None, LogicalLine | None]]:
        """
        Recover the optimal alignment from the DP matrix.

        Returns a sequence of paired logical lines where
        unmatched lines are represented by None.
        """

        GAP = -30

        i = len(left_lines)
        j = len(right_lines)

        pairs: list[
            tuple[
                LogicalLine | None,
                LogicalLine | None,
            ]
        ] = []

        while i > 0 or j > 0:

            # -------------------------
            # Diagonal
            # -------------------------

            if i > 0 and j > 0:

                left_text = self._left_cache[id(left_lines[i - 1])]
                right_text = self._right_cache[id(right_lines[j - 1])]

                similarity = fuzz.ratio(
                    left_text,
                    right_text,
                )

                similarity += self._structure_bonus(
                    left_text,
                    right_text,
                )

                if similarity >= self.local_similarity:

                    expected = (
                        dp[i - 1][j - 1]
                        + similarity
                    )

                    if abs(dp[i][j] - expected) < 1e-6:

                        pairs.append(
                            (
                                left_lines[i - 1],
                                right_lines[j - 1],
                            )
                        )

                        i -= 1
                        j -= 1
                        continue

            # -------------------------
            # Up
            # -------------------------

            if (
                i > 0
                and abs(dp[i][j] - (dp[i - 1][j] + GAP)) < 1e-6
            ):

                pairs.append(
                    (
                        left_lines[i - 1],
                        None,
                    )
                )

                i -= 1

                continue

            # -------------------------
            # Left
            # -------------------------

            pairs.append(
                (
                    None,
                    right_lines[j - 1],
                )
            )

            j -= 1

        pairs.reverse()

        return pairs