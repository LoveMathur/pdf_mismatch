from enum import Enum


class NumericType(str, Enum):

    INTEGER = "integer"

    DECIMAL = "decimal"

    DATE = "date"

    TIME = "time"

    PHONE = "phone"

    IDENTIFIER = "identifier"

    UNKNOWN = "unknown"