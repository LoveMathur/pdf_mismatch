import string

from models.character_category import CharacterCategory


class CharacterClassifier:

    @staticmethod
    def classify(
        left: str,
        right: str
    ) -> CharacterCategory:

        text = left + right

        if not text:
            return CharacterCategory.MIXED

        # -----------------------------
        # Pure letters
        # -----------------------------

        if all(ch.isalpha() for ch in text):
            return CharacterCategory.LETTER

        # -----------------------------
        # Pure digits
        # -----------------------------

        if all(ch.isdigit() for ch in text):
            return CharacterCategory.DIGIT

        # -----------------------------
        # Pure whitespace
        # -----------------------------

        if all(ch.isspace() for ch in text):
            return CharacterCategory.WHITESPACE

        # -----------------------------
        # Pure punctuation
        # -----------------------------

        if all(ch in string.punctuation for ch in text):
            return CharacterCategory.PUNCTUATION

        # -----------------------------
        # Unicode / Symbols
        # -----------------------------

        if any(ord(ch) > 127 for ch in text):
            return CharacterCategory.UNICODE

        if any(not ch.isalnum() for ch in text):
            return CharacterCategory.SYMBOL

        return CharacterCategory.MIXED