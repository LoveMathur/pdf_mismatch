from extractors.word_extractor import WordExtractor
from extractors.digital import DigitalPDFExtractor

from utils.flattener import DocumentFlattener
from utils.sequence_alignment import SequenceAligner

from builders.annotation_builder import AnnotationBuilder

from renderer.pdf_renderer import PDFRenderer

from comparators.insertion_deletion import InsertionDeletionComparator
from comparators.replace import ReplaceComparator


extractor = DigitalPDFExtractor()

left_doc = extractor.extract("data/document_C.pdf")
right_doc = extractor.extract("data/document_D.pdf")

flattener = DocumentFlattener()

left = flattener.flatten(left_doc)
right = flattener.flatten(right_doc)

aligner = SequenceAligner()

pairs = aligner.align(left, right)

comparators = [

    InsertionDeletionComparator(),

    ReplaceComparator()

]

differences = []

for comparator in comparators:

    differences.extend(

        comparator.compare(pairs)

    )
    # ------------------------------------------------------------------
    # Build annotations
    # ------------------------------------------------------------------

    annotation_builder = AnnotationBuilder()


    annotations = annotation_builder.build(
        differences=differences,
        aligned_pairs=pairs,
    )

print("=" * 80)
print(f"Total Differences: {len(differences)}")
print("=" * 80)

for diff in differences:

    print("=" * 80)

    print(diff.difference_type.value.upper())

    print()

    print("Expected : ", diff.expected)

    print("Actual   : ", diff.actual)

    print("Metadata : ", diff.metadata)

    print("Confidence:", diff.confidence)

    # ------------------------------------------------------------------
    # Render annotated PDF
    # ------------------------------------------------------------------

renderer = PDFRenderer()

renderer.render(

    input_pdf="data/document_D.pdf",

    output_pdf="output/annotated_document_D.pdf",

    annotations=annotations,

    )
print("Annotated PDF saved to:")
print("output/annotated_document_D.pdf")