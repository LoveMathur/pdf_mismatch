from models.difference import Difference, DifferenceCategory
from models.logical_document import LogicalDocument
from models.logical_image import LogicalImage


class ImageComparator:
    """
    Compares embedded images between two documents.

    Unlike the text comparators, this works directly off the two
    LogicalDocuments rather than a LogicalAlignedPair -- images have
    no textual content for the aligner to match on, so they get
    their own lightweight position-based matching instead. Only
    presence/absence, placement dimensions and position are
    checked; pixel content is intentionally never compared.
    """

    #
    # A matched-but-changed image is only reported if it moved or
    # resized by more than this many points -- avoids flagging
    # sub-pixel extraction jitter.
    #
    POSITION_TOLERANCE = 3.0
    SIZE_TOLERANCE = 3.0

    #
    # How far apart (page distance + normalized center distance)
    # two images may be and still be considered the same image
    # that moved, rather than two unrelated images.
    #
    MATCH_DISTANCE_THRESHOLD = 0.35

    def compare(
        self,
        left_document: LogicalDocument,
        right_document: LogicalDocument,
    ) -> list[Difference]:

        left_images = self._flatten(left_document)
        right_images = self._flatten(right_document)

        matches, unmatched_left, unmatched_right = self._match(
            left_images,
            right_images,
        )

        differences: list[Difference] = []

        for left, right in matches:

            difference = self._compare_matched(left, right)

            if difference is not None:
                differences.append(difference)

        for image in unmatched_left:
            differences.append(self._absent(image))

        for image in unmatched_right:
            differences.append(self._present(image))

        return differences

    @staticmethod
    def _flatten(document: LogicalDocument) -> list[LogicalImage]:

        images: list[LogicalImage] = []

        for page in document.pages:
            images.extend(page.images)

        return images

    def _match(
        self,
        left_images: list[LogicalImage],
        right_images: list[LogicalImage],
    ):
        """
        Greedy nearest-match, same spirit as the anchor matching
        the text aligner already does: score every candidate pair,
        then take the best-scoring pairs first under a one-to-one
        constraint.
        """

        candidates = []

        for left in left_images:

            for right in right_images:

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
            image for image in left_images
            if image.id not in matched_left_ids
        ]

        unmatched_right = [
            image for image in right_images
            if image.id not in matched_right_ids
        ]

        return matches, unmatched_left, unmatched_right

    @staticmethod
    def _distance(left: LogicalImage, right: LogicalImage) -> float:
        """
        Lower means more likely to be the same image. Page distance
        dominates; center-point distance (normalized to a typical
        page width so it tolerates moderate movement) and a size
        term both contribute, so a genuinely different image sitting
        near where one was removed doesn't get matched to it just
        because it happens to be nearby.
        """

        page_distance = abs(left.page - right.page)

        left_cx = (left.bbox[0] + left.bbox[2]) / 2
        left_cy = (left.bbox[1] + left.bbox[3]) / 2

        right_cx = (right.bbox[0] + right.bbox[2]) / 2
        right_cy = (right.bbox[1] + right.bbox[3]) / 2

        center_distance = (
            (left_cx - right_cx) ** 2 + (left_cy - right_cy) ** 2
        ) ** 0.5 / 600.0

        left_diag = (left.width ** 2 + left.height ** 2) ** 0.5
        right_diag = (right.width ** 2 + right.height ** 2) ** 0.5

        size_distance = abs(left_diag - right_diag) / max(
            left_diag, right_diag, 1.0
        )

        return page_distance + center_distance + size_distance * 0.5

    def _compare_matched(
        self,
        left: LogicalImage,
        right: LogicalImage,
    ) -> Difference | None:

        changes = {}

        if (
            abs(left.width - right.width) > self.SIZE_TOLERANCE
            or abs(left.height - right.height) > self.SIZE_TOLERANCE
        ):
            changes["dimensions"] = {
                "expected": f"{left.width:.0f}x{left.height:.0f}",
                "actual": f"{right.width:.0f}x{right.height:.0f}",
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
            category=DifferenceCategory.IMAGE,
            expected_text=f"Image on page {left.page}",
            actual_text=f"Image on page {right.page}",
            description=self._describe(right.page, changes),
            metadata={"page": right.page, "bbox": right.bbox, **changes},
        )

    def _absent(self, image: LogicalImage) -> Difference:

        return Difference(
            category=DifferenceCategory.IMAGE,
            expected_text=f"Image on page {image.page}",
            actual_text=None,
            description=(
                f"Page {image.page}: image present in the original "
                f"is missing here."
            ),
            metadata={
                "page": image.page,
                "bbox": image.bbox,
                "presence": "removed",
            },
        )

    def _present(self, image: LogicalImage) -> Difference:

        return Difference(
            category=DifferenceCategory.IMAGE,
            expected_text=None,
            actual_text=f"Image on page {image.page}",
            description=(
                f"Page {image.page}: new image found that wasn't in "
                f"the original."
            ),
            metadata={
                "page": image.page,
                "bbox": image.bbox,
                "presence": "added",
            },
        )

    @staticmethod
    def _describe(page: int, changes: dict) -> str:

        pieces = []

        if "dimensions" in changes:
            pieces.append(
                f"dimensions changed from "
                f"{changes['dimensions']['expected']} to "
                f"{changes['dimensions']['actual']} (pt)"
            )

        if "position" in changes:
            pieces.append(
                f"position changed from "
                f"{changes['position']['expected']} to "
                f"{changes['position']['actual']}"
            )

        return f"Page {page}: image " + "; ".join(pieces) + "."
