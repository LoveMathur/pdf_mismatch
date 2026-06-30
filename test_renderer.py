from extractors.unified_extractor import UnifiedExtractor
from aligners.logical_aligner import LogicalAligner

from comparators.replace import ReplaceComparator
from comparators.comparison_engine import ComparisonEngine

from renderer.pdf_renderer import PDFRenderer


def main():

    print("=" * 80)
    print("STEP 1 : Extracting Documents")
    print("=" * 80)

    extractor = UnifiedExtractor()

    left_document = extractor.extract(
        "data/document_C.pdf"
    )

    right_document = extractor.extract(
        "data/document_D.pdf"
    )

    print("✓ Documents extracted")

    print()

    print("=" * 80)
    print("STEP 2 : Aligning Documents")
    print("=" * 80)

    aligner = LogicalAligner()

    aligned_pairs = aligner.align(
        left_document,
        right_document,
    )

    print(f"✓ Total aligned pairs : {len(aligned_pairs)}")

    print()

    print("=" * 80)
    print("STEP 3 : Comparing")
    print("=" * 80)

    engine = ComparisonEngine(

        comparators=[

            ReplaceComparator(),

        ]

    )

    differences = engine.compare(
        aligned_pairs
    )

    print(f"✓ Total differences : {len(differences)}")

    print()

    print("=" * 80)
    print("STEP 4 : Rendering")
    print("=" * 80)

    renderer = PDFRenderer()

    renderer.render(

        input_pdf="data/document_D.pdf",

        output_pdf="output/annotated_document_D.pdf",

        differences=differences,

    )

    print()

    print("=" * 80)
    print("Pipeline completed successfully")
    print("=" * 80)


if __name__ == "__main__":
    main()