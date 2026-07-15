from difflib import SequenceMatcher
import re
import unicodedata

from rapidfuzz.distance import Levenshtein

from comparators.base import Comparator

from models.difference import (
    Difference,
    DifferenceCategory,
)

from models.logical_aligned_pair import (
    AlignmentType,
    LogicalAlignedPair,
)


class ReplaceComparator(Comparator):

    CHARACTER_DISTANCE = 2

    #
    # Structural / numbering tokens that must never be reported
    # on their own. Covers:
    #
    #   1)   (a)   (ii)   bullets
    #   1.   4.4.  9.1.2. dotted decimal numbering
    #   a.   B.    i.  iv.  x.   letter / roman numbering
    #
    BULLET_PATTERN = (
        r"^\d+\)$|"
        r"^\([ivxlcdm]+\)$|"
        r"^\([a-z]\)$|"
        r"^[•\-–▪o]$|"
        r"^\d+(\.\d+)*\.?$|"
        r"^[a-z]\.$|"
        r"^[ivxlcdm]+\.$"
    )

    def compare(
        self,
        pair: LogicalAlignedPair,
    ) -> list[Difference]:

        if pair.alignment != AlignmentType.REPLACE:
            return []

        if pair.left is None or pair.right is None:
            return []

        return self._compare_words(
            pair.left,
            pair.right,
        )

    @staticmethod
    def _normalize_token(text: str) -> str:
        """
        Normalize a word token the same way the aligner normalizes
        line text, so that unicode variants (NBSP, soft hyphen,
        ligatures, smart quotes vs straight quotes …) do not show
        up as word differences.
        """

        text = unicodedata.normalize("NFKC", text)

        text = (
            text
            .replace("\u00A0", " ")
            .replace("\u200B", "")
            .replace("\u00AD", "")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201C", '"')
            .replace("\u201D", '"')
        )

        return text.strip()

    def _compare_words(
        self,
        left_line,
        right_line,
    ) -> list[Difference]:

        differences = []

        left_words = left_line.words
        right_words = right_line.words

        left_tokens = [
            self._normalize_token(w.text) for w in left_words
        ]
        right_tokens = [
            self._normalize_token(w.text) for w in right_words
        ]

        # Fast exit
        if left_tokens == right_tokens:
            return []

        matcher = SequenceMatcher(
            None,
            left_tokens,
            right_tokens,
            autojunk=False,
        )

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":
                continue

            expected_text = " ".join(left_tokens[i1:i2]).strip()
            actual_text = " ".join(right_tokens[j1:j2]).strip()

            if not expected_text and not actual_text:
                continue

            # Ignore whitespace-only changes, including missing
            # or extra spaces between tokens ("9.10.1. If" vs
            # "9.10.1.If"), which are generator artefacts.
            if (
                expected_text.replace(" ", "")
                ==
                actual_text.replace(" ", "")
            ):
                continue

            # Ignore bullets / numbering
            if (
                re.fullmatch(self.BULLET_PATTERN, expected_text, re.I)
                or
                re.fullmatch(self.BULLET_PATTERN, actual_text, re.I)
            ):
                continue

            category = None

            #
            # Small edits (Levenshtein <= CHARACTER_DISTANCE) are
            # spelling / character substitutions. They used to be
            # skipped here "for the CharacterComparator", but no
            # such comparator is registered in the pipeline, so
            # they were silently lost. Report them as CHARACTER.
            #
            if expected_text and actual_text:

                if (
                    Levenshtein.distance(
                        expected_text,
                        actual_text,
                    )
                    <= self.CHARACTER_DISTANCE
                ):
                    category = DifferenceCategory.CHARACTER

            # Suppress paragraph-reflow explosions
            if (
                category is None
                and len(expected_text.split()) > 10
                and len(actual_text.split()) > 10
            ):
                continue

            expected_word = (
                left_words[i1]
                if i1 < len(left_words)
                else None
            )

            actual_word = (
                right_words[j1]
                if j1 < len(right_words)
                else None
            )

            differences.append(
                Difference(
                    category=category or self._classify(
                        expected_word,
                        actual_word,
                    ),

                    expected_line=left_line,
                    actual_line=right_line,

                    expected_word=expected_word,
                    actual_word=actual_word,

                    expected_text=expected_text or None,
                    actual_text=actual_text or None,

                    description=self._description(
                        expected_word,
                        actual_word,
                    ),

                    confidence=matcher.ratio(),

                    metadata={
                        "operation": tag,
                    },
                )
            )

        return differences

    def _classify(
        self,
        left_word,
        right_word,
    ) -> DifferenceCategory:

        if left_word is None or right_word is None:
            return DifferenceCategory.WORD

        if any(
            c.isdigit()
            for c in left_word.text + right_word.text
        ):
            return DifferenceCategory.NUMBER

        return DifferenceCategory.WORD

    def _description(
        self,
        left_word,
        right_word,
    ) -> str:

        if left_word and right_word:

            return (
                f"'{left_word.text}' changed to "
                f"'{right_word.text}'."
            )

        if left_word:

            return (
                f"'{left_word.text}' removed."
            )

        return (
            f"'{right_word.text}' inserted."
        )
