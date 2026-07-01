from difflib import SequenceMatcher

from comparators.base import Comparator

from models.difference import (
    Difference,
    DifferenceCategory,
    Severity,
)

from models.difference_group import DifferenceGroup

from models.logical_aligned_pair import (
    AlignmentType,
    LogicalAlignedPair,
)


class ReplaceComparator(Comparator):
    """
    Detects replacements inside one aligned pair.

    Each SequenceMatcher opcode produces exactly one
    DifferenceGroup.
    """

    def compare(
        self,
        pair: LogicalAlignedPair,
    ):

        print("=" * 80)
        print("ALIGNMENT :", pair.alignment)
        print("LEFT      :", pair.left is not None)
        print("RIGHT     :", pair.right is not None)

        if pair.left:
            print("LEFT TEXT :", pair.left.text)

        if pair.right:
            print("RIGHT TEXT:", pair.right.text)

        if pair.alignment != AlignmentType.REPLACE:
            return []

        return self._compare_words(pair)
    
    def _compare_words(
        self,
        pair: LogicalAlignedPair,
    ) -> list[DifferenceGroup]:

        left_words = pair.left.words
        right_words = pair.right.words

        matcher = SequenceMatcher(

            a=[w.text for w in left_words],

            b=[w.text for w in right_words],

            autojunk=False,

        )

        groups: list[DifferenceGroup] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":
                continue

            group = self._create_group(

                pair=pair,

                tag=tag,

                left_words=left_words[i1:i2],

                right_words=right_words[j1:j2],

            )

            groups.append(group)

        return groups
    
    def _create_group(
        self,
        pair: LogicalAlignedPair,
        tag: str,
        left_words,
        right_words,
    ) -> DifferenceGroup:

        differences: list[Difference] = []

        max_len = max(
            len(left_words),
            len(right_words),
        )

        for index in range(max_len):

            left = (
                left_words[index]
                if index < len(left_words)
                else None
            )

            right = (
                right_words[index]
                if index < len(right_words)
                else None
            )

            differences.append(
                self._build_difference(
                    pair,
                    tag,
                    left,
                    right,
                )
            )

        # ------------------------------
        # Compute page and bbox
        # ------------------------------

        words = [w for w in right_words if w is not None]

        if not words:
            words = [w for w in left_words if w is not None]

        page = words[0].page

        x0 = min(w.bbox[0] for w in words)
        y0 = min(w.bbox[1] for w in words)
        x1 = max(w.bbox[2] for w in words)
        y1 = max(w.bbox[3] for w in words)

        return DifferenceGroup(

            differences=differences,

            page=page,

            bbox=(x0, y0, x1, y1),

        )
    
    def _build_difference(
        self,
        pair: LogicalAlignedPair,
        tag: str,
        left_word,
        right_word,
    ) -> Difference:

        category = self._determine_category(
            left_word,
            right_word,
            tag,
        )

        description = self._build_description(
            left_word,
            right_word,
            tag,
        )

        metadata = {
            "operation": tag,
        }

        if left_word is not None:
            metadata["expected_word_index"] = left_word.word_index

        if right_word is not None:
            metadata["actual_word_index"] = right_word.word_index

        return Difference(

            category=category,

            severity=Severity.WARNING,

            confidence=1.0,

            expected_line=pair.left,

            actual_line=pair.right,

            expected_word=left_word,

            actual_word=right_word,

            expected_text=(
                left_word.text
                if left_word
                else None
            ),

            actual_text=(
                right_word.text
                if right_word
                else None
            ),

            description=description,

            metadata=metadata,

        )
    
    def _determine_category(
        self,
        left_word,
        right_word,
        operation: str,
    ) -> DifferenceCategory:

        if operation == "insert":
            return DifferenceCategory.INSERTION

        if operation == "delete":
            return DifferenceCategory.DELETION

        if left_word is None or right_word is None:
            return DifferenceCategory.WORD

        left = left_word.text
        right = right_word.text

        if left == right:
            return DifferenceCategory.WORD

        if any(ch.isdigit() for ch in left + right):
            return DifferenceCategory.NUMBER

        if len(left) == len(right):

            distance = sum(
                a != b
                for a, b in zip(left, right)
            )

            if distance == 1:
                return DifferenceCategory.CHARACTER

        return DifferenceCategory.WORD
    
    def _build_description(
        self,
        left_word,
        right_word,
        operation: str,
    ) -> str:

        left = left_word.text if left_word else "∅"
        right = right_word.text if right_word else "∅"

        if operation == "replace":
            return f"'{left}' changed to '{right}'."

        if operation == "insert":
            return f"'{right}' inserted."

        if operation == "delete":
            return f"'{left}' removed."

        return "Difference detected."