import json
import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent

PDF_DIR = ROOT / "data" / "raw_pdfs"
OUTPUT_FILE = ROOT / "data" / "cleaned_docs.json"

MIN_TEXT_LENGTH = 50


def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(pdf_path):
    doc = fitz.open(pdf_path)

    page_count = len(doc)
    pages = []
    total_chars = 0
    pages_with_text = 0

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text("text")
        text = clean_text(text)

        if len(text) >= MIN_TEXT_LENGTH:
            pages_with_text += 1

        total_chars += len(text)

        pages.append(
            f"[PAGE {page_number}]\n{text}"
        )

    doc.close()

    return (
        "\n\n".join(pages),
        page_count,
        total_chars,
        pages_with_text
    )


def make_doc_id(filename):

    stem = Path(filename).stem

    existing_match = re.match(r"(case_\d+)", stem)

    if existing_match:
        return existing_match.group(1)

    safe_name = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        stem
    ).strip("_")

    return f"doc_{safe_name.lower()}"


def main():

    if not PDF_DIR.exists():
        raise FileNotFoundError(
            f"PDF directory not found: {PDF_DIR}"
        )

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        raise ValueError("No PDF files found.")

    print("=" * 60)
    print("LEXVERIFY AI — PDF EXTRACTION")
    print("=" * 60)
    print(f"PDF directory: {PDF_DIR}")
    print(f"PDF files found: {len(pdf_files)}")
    print()

    existing_documents = {}

    if OUTPUT_FILE.exists():

        with open(
            OUTPUT_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            old_documents = json.load(f)

        for document in old_documents:
            existing_documents[
                document["filename"]
            ] = document

        print(
            f"Existing cleaned documents found: "
            f"{len(existing_documents)}"
        )

    results = []

    for pdf_path in pdf_files:

        filename = pdf_path.name

        if filename in existing_documents:

            print(f"[KEEP] {filename}")

            results.append(
                existing_documents[filename]
            )

            continue

        print(f"[EXTRACT] {filename}")

        try:

            (
                text,
                page_count,
                char_count,
                pages_with_text
            ) = extract_pdf(pdf_path)

            if char_count == 0:

                print(
                    "  WARNING: No extractable text"
                )

            elif pages_with_text < page_count:

                print(
                    f"  WARNING: "
                    f"{page_count - pages_with_text} "
                    f"pages have little/no text"
                )

            document = {
                "doc_id": make_doc_id(filename),
                "filename": filename,
                "extraction_method": "text",
                "page_count": page_count,
                "character_count": char_count,
                "cleaned_text": text
            }

            results.append(document)

            print(
                f"  Pages: {page_count} | "
                f"Characters: {char_count}"
            )

        except Exception as e:

            print(
                f"  ERROR: {type(e).__name__}: {e}"
            )

    filenames = [
        doc["filename"]
        for doc in results
    ]

    missing = [
        pdf.name
        for pdf in pdf_files
        if pdf.name not in filenames
    ]

    if missing:

        print()
        print(
            "ERROR: Some PDFs were not processed:"
        )

        for filename in missing:
            print(f"  - {filename}")

        raise RuntimeError(
            "Extraction incomplete. "
            "Existing cleaned_docs.json "
            "was NOT overwritten."
        )

    if OUTPUT_FILE.exists():

        backup = OUTPUT_FILE.with_suffix(
            ".backup.json"
        )

        # Do not overwrite an existing backup.
        if backup.exists():
            backup.unlink()

        OUTPUT_FILE.replace(backup)

        print()
        print(f"Backup created: {backup}")

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Documents: {len(results)}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()