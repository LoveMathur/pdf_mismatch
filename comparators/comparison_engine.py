from models.difference import Difference
from models.logical_aligned_pair import LogicalAlignedPair

from comparators.base import Comparator

import re


class ComparisonEngine:

    #
    # Structural / numbering tokens that never constitute a
    # reportable difference on their own. Includes dotted
    # decimal numbering (1., 4.4., 9.1.2.), letter and roman
    # numbering (a., i., iv.), classic bullets and brackets.
    #
    STRUCTURAL_PATTERN = (
        r"^\d+\)$|"
        r"^\([a-z]\)$|"
        r"^\([ivxlcdm]+\)$|"
        r"^\d+(\.\d+)*\.?$|"
        r"^[a-z]\.$|"
        r"^[ivxlcdm]+\.$"
    )

    #
    # Fillable-field labels. Lines beginning with these labels
    # carry customer-specific values (which are MEANT to differ
    # between an empty template and a filled document), so any
    # difference located on such a line is suppressed.
    #
    # Extend this list with the field patterns used in your
    # document set.
    #
    FIELD_PATTERNS = [
        r"^name\b",
        r"^name\s+of\b",
        r"^address\b",
        r"^date\s+of\s+birth\b",
        r"^dob\b",
        r"^mobile\b",
        r"^phone\b",
        r"^email\b",
        r"^pan\b",
        r"^aadhar\b",
        r"Date:",
        r"^Re:\s+Your\s+Policy\s+No. ",
    ]

    def __init__(
        self,
        comparators: list[Comparator],
    ):

        self.comparators = comparators

        self._field_regexes = [
            re.compile(pattern, re.I)
            for pattern in self.FIELD_PATTERNS
        ]

        self._template_regexes: list[re.Pattern] = []

    def compare(
        self,
        pairs: list[LogicalAlignedPair],
    ) -> list[Difference]:

        #
        # Give comparators that need cross-document context
        # (e.g. InsertDeleteComparator's reflow suppression)
        # the full normalized text of both documents.
        #
        left_full = self._full_text(pairs, side="left")
        right_full = self._full_text(pairs, side="right")

        for comparator in self.comparators:
            if hasattr(comparator, "set_context"):
                comparator.set_context(left_full, right_full)

        differences = []

        for pair in pairs:

            for comparator in self.comparators:

                differences.extend(
                    comparator.compare(pair)
                )

        differences = self._filter_field_lines(differences)

        differences = self._filter_structural_noise(differences)

        differences = self._collapse_global_font_changes(differences)

        return differences

    #
    # A font mapping repeated at least this many times across the
    # document is a generator-level substitution, not individual
    # word edits. It is collapsed into one document-level entry.
    #
    GLOBAL_FONT_THRESHOLD = 15

    def _collapse_global_font_changes(
        self,
        differences: list[Difference],
    ) -> list[Difference]:

        from collections import Counter
        from models.difference import DifferenceCategory

        mapping_counts = Counter()

        for difference in differences:

            font_change = difference.metadata.get("font")

            if (
                difference.category == DifferenceCategory.FORMATTING
                and font_change
                and set(difference.metadata) == {"font"}
            ):
                mapping_counts[
                    (font_change["expected"], font_change["actual"])
                ] += 1

        global_mappings = {
            mapping
            for mapping, count in mapping_counts.items()
            if count >= self.GLOBAL_FONT_THRESHOLD
        }

        if not global_mappings:
            return differences

        collapsed: list[Difference] = []
        reported: set = set()

        for difference in differences:

            font_change = difference.metadata.get("font")

            if not (
                difference.category == DifferenceCategory.FORMATTING
                and font_change
                and set(difference.metadata) == {"font"}
            ):
                collapsed.append(difference)
                continue

            mapping = (
                font_change["expected"],
                font_change["actual"],
            )

            if mapping not in global_mappings:
                collapsed.append(difference)
                continue

            if mapping in reported:
                continue

            reported.add(mapping)

            summary = difference.model_copy()
            summary.description = (
                f"Document-wide font substitution: "
                f"'{mapping[0]}' -> '{mapping[1]}' "
                f"({mapping_counts[mapping]} occurrences)."
            )
            collapsed.append(summary)

        return collapsed

    @staticmethod
    def _full_text(
        pairs: list[LogicalAlignedPair],
        side: str,
    ) -> str:

        chunks = []

        for pair in pairs:

            line = pair.left if side == "left" else pair.right

            if line is None:
                continue

            text = line.text.lower()
            text = re.sub(r"[^a-z0-9]+", " ", text)
            chunks.append(text)

        return re.sub(r"\s+", " ", " ".join(chunks)).strip()

    def _filter_field_lines(
        self,
        differences: list[Difference],
    ) -> list[Difference]:
        """
        Drop differences located on fillable-field lines
        (Name, Address, Policy No, ...).
        """

        filtered: list[Difference] = []

        for difference in differences:

            line = (
                difference.actual_line
                or difference.expected_line
            )

            line_text = (line.text if line else "").strip()

            if line_text and any(
                regex.match(line_text)
                for regex in self._field_regexes
            ):
                continue

            #
            # Template placeholders such as <Name of the
            # Policyholder> or <Pin Code> mark fillable fields.
            # A difference where either side touches a
            # placeholder is the field being filled in,
            # not a document change.
            #
            components = [
                t for t in (
                    difference.expected_text,
                    difference.actual_text,
                    line_text,
                )
                if t
            ]

            if any(
                re.search(r"<[^<>]{1,60}>", t)
                for t in components
            ):
                for t in components:
                    self._collect_templates(t)
                continue

            filtered.append(difference)

        #
        # Second pass: a filled field produces a counterpart
        # without the placeholder ("To Love Mathur" for the
        # template "To <Name of the Policyholder>"). Suppress
        # insertions / deletions / replacements matching a
        # collected template with the placeholder wildcarded.
        #
        if self._template_regexes:

            filtered = [
                difference
                for difference in filtered
                if not self._matches_template(difference)
            ]

        return filtered

    def _collect_templates(
        self,
        text: str,
    ) -> None:

        for line in text.splitlines():

            line = line.strip()

            if "<" not in line:
                continue

            #
            # Require at least a few literal (non-placeholder)
            # characters so templates like "<City><State>" do not
            # become match-everything patterns.
            #
            literal = re.sub(r"<[^<>]{1,60}>", "", line).strip()

            if len(literal) < 3:
                continue

            # "<" and ">" survive re.escape, so placeholder
            # segments can be wildcarded after escaping.
            pattern = re.sub(r"<[^<>]{1,60}>", ".*", re.escape(line))

            try:
                self._template_regexes.append(
                    re.compile(f"^{pattern}$", re.I)
                )
            except re.error:
                pass

    def _matches_template(
        self,
        difference: Difference,
    ) -> bool:

        for text in (
            difference.expected_text,
            difference.actual_text,
        ):

            if not text:
                continue

            candidate = text.strip()

            for regex in self._template_regexes:

                if regex.match(candidate):
                    return True

        return False

    def _filter_structural_noise(
        self,
        differences: list[Difference],
    ) -> list[Difference]:

        filtered: list[Difference] = []

        i = 0

        while i < len(differences):

            current = differences[i]

            current_text = (
                current.expected_text
                if current.expected_text is not None
                else current.actual_text
            )

            # -------------------------------------------------------
            # Ignore isolated structural tokens
            # -------------------------------------------------------

            if current_text:

                text = current_text.strip()

                if (
                    re.fullmatch(
                        self.STRUCTURAL_PATTERN, text, re.I
                    )
                    or text in {"•", "-", "–", "▪"}
                ):
                    i += 1
                    continue

            # -------------------------------------------------------
            # DELETE token immediately followed by INSERT of the
            # same token (content moved, not changed).
            #
            # Only applied when the two differences complement each
            # other (one has expected_text, the other actual_text);
            # previously two unrelated differences that merely
            # mentioned the same word were both dropped.
            # -------------------------------------------------------

            if i + 1 < len(differences):

                nxt = differences[i + 1]

                complementary = (
                    (current.expected_text and not current.actual_text
                     and nxt.actual_text and not nxt.expected_text)
                    or
                    (current.actual_text and not current.expected_text
                     and nxt.expected_text and not nxt.actual_text)
                )

                if complementary:

                    current_text = (
                        current.expected_text or current.actual_text
                    )

                    next_text = (
                        nxt.expected_text or nxt.actual_text
                    )

                    if (
                        current_text
                        and next_text
                        and current_text.strip() == next_text.strip()
                    ):
                        i += 2
                        continue

            filtered.append(current)

            i += 1

        return filtered
