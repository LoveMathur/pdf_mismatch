from extractors.unified_extractor import UnifiedExtractor


def main():

    extractor = UnifiedExtractor()

    document = extractor.extract(
        "data/document_D.pdf"
    )

    print("=" * 80)

    print(document.file_name)

    print("=" * 80)

    for page in document.pages:

        print(f"\nPAGE {page.page_number}")

        for line in page.lines:

            print("=" * 60)
            print(line.text)

            for word in line.words:
                print(
                    f"   {word.word_index}: {word.text}"
                )
                
if __name__ == "__main__":
    main()