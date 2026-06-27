from extractors.digital import DigitalPDFExtractor

from utils.flattener import DocumentFlattener
from utils.sequence_alignment import SequenceAligner

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