from models.difference import DifferenceType
from models.difference import Difference

from models.issue_description import (
    IssueDescription,
    IssueSeverity,
)


class IssueFormatter:
    """
    Converts low-level Difference objects into
    reviewer-friendly descriptions.
    """

    @staticmethod
    def format(
        difference: Difference,
    ) -> IssueDescription:

        match difference.difference_type:

            case DifferenceType.NUMBER:

                return IssueDescription(

                    title="Numeric Value Changed",

                    message=(
                        f"Expected '{difference.expected}' "
                        f"but found '{difference.actual}'."
                    ),

                    severity=IssueSeverity.ERROR,
                )

            case DifferenceType.SPELLING:

                return IssueDescription(

                    title="Possible Spelling Mistake",

                    message=(
                        f"Expected '{difference.expected}' "
                        f"but found '{difference.actual}'."
                    ),

                    severity=IssueSeverity.WARNING,
                )

            case DifferenceType.CHARACTER:

                return IssueDescription(

                    title="Character Difference",

                    message=(
                        f"Expected '{difference.expected}' "
                        f"but found '{difference.actual}'."
                    ),

                    severity=IssueSeverity.WARNING,
                )

            case DifferenceType.CASE:

                return IssueDescription(

                    title="Capitalization Difference",

                    message=(
                        "Only capitalization differs."
                    ),

                    severity=IssueSeverity.INFO,
                )

            case DifferenceType.WHITESPACE:

                return IssueDescription(

                    title="Whitespace Difference",

                    message=(
                        "Spacing or line breaks differ."
                    ),

                    severity=IssueSeverity.INFO,
                )

            case DifferenceType.WORD:

                return IssueDescription(

                    title="Text Changed",

                    message=(
                        f"Expected '{difference.expected}' "
                        f"but found '{difference.actual}'."
                    ),

                    severity=IssueSeverity.ERROR,
                )

            case DifferenceType.INSERTION:

                return IssueDescription(

                    title="Unexpected Content",

                    message=(
                        f"Inserted text: '{difference.actual}'."
                    ),

                    severity=IssueSeverity.WARNING,
                )

            case DifferenceType.DELETION:

                return IssueDescription(

                    title="Missing Content",

                    message=(
                        f"Missing text: '{difference.expected}'."
                    ),

                    severity=IssueSeverity.ERROR,
                )

            case _:

                return IssueDescription(

                    title="Difference Detected",

                    message="Review this modification.",

                    severity=IssueSeverity.WARNING,
                )