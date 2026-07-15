from enum import Enum

from pydantic import BaseModel


class IssueSeverity(str, Enum):

    INFO = "info"

    WARNING = "warning"

    ERROR = "error"

    CRITICAL = "critical"


class IssueDescription(BaseModel):

    title: str

    message: str

    severity: IssueSeverity