from extractors.unified_extractor import UnifiedExtractor
#from aligners.logical_aligner import LogicalAligner
from aligners.robust_logical_aligner import RobustLogicalAligner

from models.logical_aligned_pair import AlignmentType

from comparators.replace import ReplaceComparator
from comparators.comparison_engine import ComparisonEngine
from comparators.insert_delete import InsertDeleteComparator
from comparators.analyzers.formatting import FormattingComparator


from renderer.pdf_renderer import PDFRenderer


def main():

    print("=" * 80)
    print("STEP 1 : Extracting Documents")
    print("=" * 80)

    extractor = UnifiedExtractor()

    left_document = extractor.extract(
        "data/Sample-Policy-Document_LIC.pdf"
    )

    right_document = extractor.extract(
        "data/Changed_Policy-Document_LIC.pdf"
    )

    print("✓ Documents extracted")

    print()

    print("=" * 80)
    print("STEP 2 : Aligning Documents")
    print("=" * 80)
    #aligner =LogicalAligner()
    aligner = RobustLogicalAligner()

    aligned_pairs = aligner.align(
        left_document,
        right_document,
    )

    for pair in aligned_pairs:
            if (
                pair.left
                and pair.right
                and pair.alignment == AlignmentType.EQUAL
            ):

                left_norm = aligner._normalize_line_text(pair.left.text)
                right_norm = aligner._normalize_line_text(pair.right.text)

                if left_norm != right_norm:

                    print("=" * 80)
                    print("ACTUAL FALSE EQUAL")
                    print(repr(left_norm))
                    print("----")
                    print(repr(right_norm))


    print(f"✓ Total aligned pairs : {len(aligned_pairs)}")

    print()

    print("=" * 80)
    print("STEP 3 : Comparing")
    print("=" * 80)

    engine = ComparisonEngine(

        comparators=[

            ReplaceComparator(),
            FormattingComparator(),
            InsertDeleteComparator(),

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

        input_pdf="data/Changed_Policy-Document_LIC.pdf",

        output_pdf="output/annotated_Changed_Policy-Document_LIC.pdf",

        differences=differences,

    )

    print()

    print("=" * 80)
    print("Pipeline completed successfully")
    print("=" * 80)

if __name__ == "__main__":
    main()