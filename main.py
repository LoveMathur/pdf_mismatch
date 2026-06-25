from extractors.digital import DigitalPDFExtractor

extractor = DigitalPDFExtractor()
doc1 = extractor.extract(pdf1)
doc2 = extractor.extract(pdf2)

normalizer = DocumentNormalizer()
doc1 = normalizer.normalize(doc1)
doc2 = normalizer.normalize(doc2)

comparator = TextComparator()
result = comparator.compare(doc1, doc2)

ReportGenerator().generate(result)