from models.difference import Difference, DifferenceCategory
from models.logical_document import LogicalDocument
from models.logical_table import LogicalTable


class TableComparator:
    """
    Compares detected tables between two documents.

    Mirrors ImageComparator: matches tables by position across
    documents, then reports presence/absence, row/column count
    changes and position changes. Cell content is intentionally
    never compared.
    """

    POSITION_TOLERANCE = 3.0
    MATCH_DISTANCE_THRESHOLD = 0.35

    def compare(
        self,
        left_document: LogicalDocument,
        right_document: LogicalDocument,
    ) -> list[Difference]:

        left_tables = self._flatten(left_document)
        right_tables = self._flatten(right_document)

        matches, unmatched_left, unmatched_right = self._match(
            left_tables,
            right_tables,
        )

        differences: list[Difference] = []

        for left, right in matches:

            difference = self._compare_matched(left, right)

            if difference is not None:
                differences.append(difference)

        for table in unmatched_left:
            differences.append(self._absent(table))

        for table in unmatched_right:
            differences.append(self._present(table))

        return differences

    @staticmethod
    def _flatten(document: LogicalDocument) -> list[LogicalTable]:

        tables: list[LogicalTable] = []

        for page in document.pages:
            tables.extend(page.tables)

        return tables

    def _match(
        self,
        left_tables: list[LogicalTable],
        right_tables: list[LogicalTable],
    ):

        candidates = []

        for left in left_tables:

            for right in right_tables:

                distance = self._distance(left, right)

                if distance > self.MATCH_DISTANCE_THRESHOLD:
                    continue

                candidates.append((distance, left, right))

        candidates.sort(key=lambda c: c[0])

        matched_left_ids: set[str] = set()
        matched_right_ids: set[str] = set()

        matches = []

        for _distance, left, right in candidates:

            if left.id in matched_left_ids:
                continue

            if right.id in matched_right_ids:
                continue

            matched_left_ids.add(left.id)
            matched_right_ids.add(right.id)

            matches.append((left, right))

        unmatched_left = [
            table for table in left_tables
            if table.id not in matched_left_ids
        ]

        unmatched_right = [
            table for table in right_tables
            if table.id not in matched_right_ids
        ]

        return matches, unmatched_left, unmatched_right

    @staticmethod
    def _distance(left: LogicalTable, right: LogicalTable) -> float:

        page_distance = abs(left.page - right.page)

        left_cx = (left.bbox[0] + left.bbox[2]) / 2
        left_cy = (left.bbox[1] + left.bbox[3]) / 2

        right_cx = (right.bbox[0] + right.bbox[2]) / 2
        right_cy = (right.bbox[1] + right.bbox[3]) / 2

        center_distance = (
            (left_cx - right_cx) ** 2 + (left_cy - right_cy) ** 2
        ) ** 0.5 / 600.0

        return page_distance + center_distance

    def _compare_matched(
        self,
        left: LogicalTable,
        right: LogicalTable,
    ) -> Difference | None:

        changes = {}

        if left.row_count != right.row_count:
            changes["rows"] = {
                "expected": left.row_count,
                "actual": right.row_count,
            }

        if left.col_count != right.col_count:
            changes["columns"] = {
                "expected": left.col_count,
                "actual": right.col_count,
            }

        if (
            abs(left.bbox[0] - right.bbox[0]) > self.POSITION_TOLERANCE
            or abs(left.bbox[1] - right.bbox[1]) > self.POSITION_TOLERANCE
        ):
            changes["position"] = {
                "expected": f"({left.bbox[0]:.0f}, {left.bbox[1]:.0f})",
                "actual": f"({right.bbox[0]:.0f}, {right.bbox[1]:.0f})",
            }

        if not changes:
            return None

        return Difference(
            category=DifferenceCategory.TABLE,
            expected_text=(
                f"Table on page {left.page} "
                f"({left.row_count}x{left.col_count})"
            ),
            actual_text=(
                f"Table on page {right.page} "
                f"({right.row_count}x{right.col_count})"
            ),
            description=self._describe(right.page, changes),
            metadata={"page": right.page, "bbox": right.bbox, **changes},
        )

    def _absent(self, table: LogicalTable) -> Difference:

        return Difference(
            category=DifferenceCategory.TABLE,
            expected_text=(
                f"Table on page {table.page} "
                f"({table.row_count}x{table.col_count})"
            ),
            actual_text=None,
            description=(
                f"Page {table.page}: table present in the original "
                f"is missing here."
            ),
            metadata={
                "page": table.page,
                "bbox": table.bbox,
                "presence": "removed",
            },
        )

    def _present(self, table: LogicalTable) -> Difference:

        return Difference(
            category=DifferenceCategory.TABLE,
            expected_text=None,
            actual_text=(
                f"Table on page {table.page} "
                f"({table.row_count}x{table.col_count})"
            ),
            description=(
                f"Page {table.page}: new table found that wasn't in "
                f"the original."
            ),
            metadata={
                "page": table.page,
                "bbox": table.bbox,
                "presence": "added",
            },
        )

    @staticmethod
    def _describe(page: int, changes: dict) -> str:

        pieces = []

        if "rows" in changes:
            pieces.append(
                f"row count changed from {changes['rows']['expected']} "
                f"to {changes['rows']['actual']}"
            )

        if "columns" in changes:
            pieces.append(
                f"column count changed from "
                f"{changes['columns']['expected']} to "
                f"{changes['columns']['actual']}"
            )

        if "position" in changes:
            pieces.append(
                f"position changed from "
                f"{changes['position']['expected']} to "
                f"{changes['position']['actual']}"
            )

        return f"Page {page}: table " + "; ".join(pieces) + "."
