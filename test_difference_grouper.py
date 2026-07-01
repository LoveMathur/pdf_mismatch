from extractors.unified_extractor import UnifiedExtractor
from aligners.logical_aligner import LogicalAligner

from comparators.replace import ReplaceComparator
from comparators.comparison_engine import ComparisonEngine

from post_processors.difference_grouper import DifferenceGrouper


extractor = UnifiedExtractor()

left = extractor.extract(
    "data/document_C.pdf"
)

right = extractor.extract(
    "data/document_D.pdf"
)

aligner = LogicalAligner()

pairs = aligner.align(
    left,
    right,
)

engine = ComparisonEngine(
    comparators=[
        ReplaceComparator(),
    ]
)

differences = engine.compare(
    pairs
)

print("=" * 80)
print(f"Atomic differences : {len(differences)}")
print("=" * 80)

grouper = DifferenceGrouper()

groups = grouper.group(
    differences
)

print(f"Groups : {len(groups)}")

for i, group in enumerate(groups, start=1):

    print()
    print("=" * 80)

    print(f"GROUP {i}")

    print("=" * 80)

    print(group.title)

    print()

    print(group.message)

    print()

    print("Words:")

    for difference in group.differences:

        print(
            difference.expected_text,
            "→",
            difference.actual_text,
        )