from extractors.unified_extractor import UnifiedExtractor
from aligners.logical_aligner import LogicalAligner


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

for pair in pairs:

    print("=" * 80)

    print(pair.alignment)

    print()

    print(pair.left.text if pair.left else None)

    print("----")

    print(pair.right.text if pair.right else None)