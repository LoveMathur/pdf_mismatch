from extractors.unified_extractor import UnifiedExtractor
from aligners.logical_aligner import LogicalAligner

from comparators.replace import ReplaceComparator
from comparators.comparison_engine import ComparisonEngine


def main():

    print("=" * 80)
    print("Extracting documents...")
    print("=" * 80)

    extractor = UnifiedExtractor()

    left_doc = extractor.extract(
        "data/document_C.pdf"
    )

    right_doc = extractor.extract(
        "data/document_D.pdf"
    )

    print("✓ Documents extracted")

    print("\n" + "=" * 80)
    print("Aligning...")
    print("=" * 80)

    aligner = LogicalAligner()

    pairs = aligner.align(
        left_doc,
        right_doc,
    )

    print(f"✓ Total aligned pairs : {len(pairs)}")

    print("\n" + "=" * 80)
    print("Running comparison engine...")
    print("=" * 80)

    engine = ComparisonEngine(

        comparators=[

            ReplaceComparator(),

        ]

    )

    differences = engine.compare(
        pairs
    )

    print(f"✓ Total differences : {len(differences)}")

    print("\n" + "=" * 80)
    print("DIFFERENCES")
    print("=" * 80)

    for i, diff in enumerate(differences, start=1):

        print(f"\nDifference #{i}")

        print("-" * 60)

        print(f"Category   : {diff.category}")

        print(f"Severity   : {diff.severity}")

        print(f"Confidence : {diff.confidence}")

        print()

        print("Expected:")
        print(diff.expected_text)

        print()

        print("Actual:")
        print(diff.actual_text)

        print()

        print("Description:")
        print(diff.description)

        print()

        if diff.expected_line:

            print(
                f"Expected Line : Page {diff.expected_line.page}"
            )

        if diff.actual_line:

            print(
                f"Actual Line   : Page {diff.actual_line.page}"
            )

        if diff.expected_word:

            print(
                f"Expected Word : {diff.expected_word.text}"
            )

        if diff.actual_word:

            print(
                f"Actual Word   : {diff.actual_word.text}"
            )

        if diff.metadata:

            print("Metadata:")

            for key, value in diff.metadata.items():

                print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print("Finished")
    print("=" * 80)


if __name__ == "__main__":
    main()