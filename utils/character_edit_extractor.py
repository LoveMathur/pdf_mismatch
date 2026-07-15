from difflib import SequenceMatcher

from models.character_edit import CharacterEdit, CharacterOperation


class CharacterEditExtractor:

    @staticmethod
    def extract(
        left: str,
        right: str,
        pair_index: int
    ) -> list[CharacterEdit]:

        matcher = SequenceMatcher(
            None,
            left,
            right,
            autojunk=False
        )

        edits: list[CharacterEdit] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":
                continue

            operation = {
                "replace": CharacterOperation.REPLACE,
                "delete": CharacterOperation.DELETE,
                "insert": CharacterOperation.INSERT,
            }[tag]

            edits.append(

                CharacterEdit(

                    pair_index=pair_index,

                    operation=operation,

                    left_start=i1,
                    left_end=i2,

                    right_start=j1,
                    right_end=j2,

                    expected_fragment=left[i1:i2],

                    actual_fragment=right[j1:j2]

                )

            )

        return edits