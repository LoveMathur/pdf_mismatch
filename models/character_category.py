from enum import Enum


class CharacterCategory(str, Enum):

    LETTER = "letter"

    DIGIT = "digit"

    PUNCTUATION = "punctuation"

    SYMBOL = "symbol"

    WHITESPACE = "whitespace"

    UNICODE = "unicode"

    MIXED = "mixed"