from difflib import SequenceMatcher

from comparators.base import Comparator


from models.difference import (
    Difference,
    DifferenceCategory,
)

from models.logical_aligned_pair import (
    AlignmentType,
    LogicalAlignedPair,
)


class FormattingComparator(Comparator):
    """
    Detects formatting differences between logically aligned lines.

    Unlike ReplaceComparator, this comparator also evaluates
    AlignmentType.EQUAL because formatting may change while
    textual content remains identical.

    Text replacements are ignored intentionally since they are
    already handled by ReplaceComparator.
    """

    FONT_SIZE_TOLERANCE = 0.5

    POSITION_TOLERANCE = 2.0

    COLOR_TOLERANCE = 16

    def compare(
        self,
        pair: LogicalAlignedPair,
    ) -> list[Difference]:

        #
        # Formatting comparison is only meaningful when
        # both sides contain a line.
        #

        if pair.left is None or pair.right is None:
            return []

        #
        # Ignore page decorations.
        #

        if (
            pair.left.is_header
            or pair.right.is_header
            or pair.left.is_footer
            or pair.right.is_footer
        ):
            return []

        #
        # We only support equal and replace.
        #

        if pair.alignment not in (
            AlignmentType.EQUAL,
            AlignmentType.REPLACE,
        ):
            return []

        differences = []

        differences.extend(
            self._compare_word_formatting(
                pair.left,
                pair.right,
            )
        )

        #
        # Layout comparison will be added later.
        #
        # differences.extend(
        #     self._compare_line_layout(...)
        # )

        return differences

    def _compare_word_formatting(
        self,
        left_line,
        right_line,
    ) -> list[Difference]:

        differences = []

        #
        # Compare identical words.
        #
        # SequenceMatcher guarantees we only compare words
        # whose textual content matches.
        #

        matcher = SequenceMatcher(

            None,

            [w.text for w in left_line.words],

            [w.text for w in right_line.words],

        )

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            #
            # Only identical words can have formatting
            # differences.
            #

            if tag != "equal":
                continue

            left_words = left_line.words[i1:i2]
            right_words = right_line.words[j1:j2]

            for left_word, right_word in zip(
                left_words,
                right_words,
            ):

                difference = self._compare_single_word(
                    left_word,
                    right_word,
                    left_line,
                    right_line,
                )

                if difference is not None:
                    differences.append(
                        difference
                    )

        return differences

    def _compare_single_word(
        self,
        left_word,
        right_word,
        left_line,
        right_line,
    ) -> Difference | None:

        changes = {}

        #
        # Words whose span lookup failed carry placeholder
        # formatting (font="", size=0). Comparing placeholders
        # produces phantom formatting differences, so skip them.
        #

        if (
            left_word.font_size == 0.0
            or right_word.font_size == 0.0
        ):
            return None

        #
        # Font family.
        #
        # Subset prefixes ("ABCDEF+Calibri") and vendor naming
        # variants are stripped before comparing, otherwise two
        # visually identical fonts embedded by different tools
        # would be reported as differences.
        #

        left_font = self._normalize_font(left_word.font)
        right_font = self._normalize_font(right_word.font)

        if left_font != right_font:

            changes["font"] = {
                "expected": left_word.font,
                "actual": right_word.font,
            }

        #
        # Font Size
        #

        if abs(
            left_word.font_size -
            right_word.font_size
        ) > self.FONT_SIZE_TOLERANCE:

            changes["font_size"] = {

                "expected": left_word.font_size,

                "actual": right_word.font_size,

            }

        #
        # Color
        #

        if not self._colors_match(
            left_word.color,
            right_word.color,
        ):

            changes["text_color"] = {

                "expected": left_word.color,

                "actual": right_word.color,

            }

        #
        # Font Flags
        #

        #
        # Only style bits are meaningful for comparison. The
        # Serif / Monospace bits describe the font family (already
        # compared above) and differ between PDF generators.
        #
        STYLE_MASK = (1 << 0) | (1 << 1) | (1 << 4)

        if (left_word.flags & STYLE_MASK) != (right_word.flags & STYLE_MASK):

            changes["flags"] = {

                "expected": self._decode_flags(
                    left_word.flags
                ),

                "actual": self._decode_flags(
                    right_word.flags
                ),

            }

        #
        # Rotation
        #

        if abs(
            left_word.rotation -
            right_word.rotation
        ) > 0.1:

            changes["rotation"] = {

                "expected": left_word.rotation,

                "actual": right_word.rotation,

            }


        if not changes:
            return None

        return Difference(

            category=DifferenceCategory.FORMATTING,

            expected_line=left_line,

            actual_line=right_line,

            expected_word=left_word,

            actual_word=right_word,

            expected_text=left_word.text,

            actual_text=right_word.text,

            description=self._build_description(
                left_word,
                changes,
            ),

            metadata=changes,

        )
    
    #
    # Metric-compatible substitutions performed automatically by
    # document generators (LibreOffice, Ghostscript ...). These
    # render identically and must not be reported as differences.
    #
    FONT_ALIASES = {
        "liberationserif": "timesnewroman",
        "nimbusroman": "timesnewroman",
        "liberationsans": "arial",
        "helvetica": "arial",
        "nimbussans": "arial",
        "liberationmono": "couriernew",
        "nimbusmono": "couriernew",
        "nimbusmonops": "couriernew",
        "carlito": "calibri",
        "caladea": "cambria",
    }

    @classmethod
    def _colors_match(
        cls,
        left: int,
        right: int,
    ) -> bool:

        if left == right:
            return True

        lr, lg, lb = (left >> 16) & 255, (left >> 8) & 255, left & 255
        rr, rg, rb = (right >> 16) & 255, (right >> 8) & 255, right & 255

        return (
            abs(lr - rr) <= cls.COLOR_TOLERANCE
            and abs(lg - rg) <= cls.COLOR_TOLERANCE
            and abs(lb - rb) <= cls.COLOR_TOLERANCE
        )

    @classmethod
    def _normalize_font(cls, font: str) -> str:

        # Strip subset prefix: "ABCDEF+Calibri" -> "Calibri"
        if "+" in font:
            font = font.split("+", 1)[1]

        # Compare on letters only: "Times New Roman,Bold" and
        # "TimesNewRoman-Bold" are the same font.
        normalized = "".join(
            c for c in font.lower() if c.isalpha()
        )

        for alias, canonical in cls.FONT_ALIASES.items():
            if normalized.startswith(alias):
                normalized = canonical + normalized[len(alias):]
                break

        return normalized

    def _decode_flags(
        self,
        flags: int,
    ) -> list[str]:

        decoded = []

        #
        # PyMuPDF font flags
        #

        if flags & (1 << 0):
            decoded.append("Superscript")

        if flags & (1 << 1):
            decoded.append("Italic")

        if flags & (1 << 2):
            decoded.append("Serif")

        if flags & (1 << 3):
            decoded.append("Monospace")

        if flags & (1 << 4):
            decoded.append("Bold")

        return decoded


    def _build_description(
        self,
        word,
        changes,
    ) -> str:

        lines = [

            f"Formatting changed for '{word.text}'",

            "",

        ]

        for field, values in changes.items():

            lines.append(
                f"{field.replace('_', ' ').title()}:"
            )

            lines.append(
                f"Expected : {values['expected']}"
            )

            lines.append(
                f"Actual   : {values['actual']}"
            )

            lines.append("")

        return "\n".join(lines)