from pathlib import Path
import json
import re

from pypdf import PdfReader

import fitz  # PyMuPDF
import pytesseract
from PIL import Image


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PDF_DIR = PROJECT_ROOT / "data" / "raw_pdfs"
OUTPUT_FILE = PROJECT_ROOT / "data" / "cleaned_docs.json"


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

# If "tesseract --version" works in PowerShell,
# leave this as None.
#
# If Windows cannot find tesseract, set the path below.

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# TEXT CLEANING
# ============================================================

def normalize_text(text: str) -> str:

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Normalize spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces before punctuation
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean each line
    lines = []

    for line in text.split("\n"):

        line = line.strip()

        if line:
            lines.append(line)
        else:
            # Preserve paragraph separation
            if lines and lines[-1] != "":
                lines.append("")

    return "\n".join(lines).strip()


# ============================================================
# PDF TEXT EXTRACTION USING PYPDF
# ============================================================

def extract_with_pypdf(pdf_path: Path):

    reader = PdfReader(str(pdf_path))

    pages = []

    total_characters = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        try:
            text = page.extract_text() or ""
        except Exception as error:

            print(
                f"  pypdf error on page "
                f"{page_number}: {error}"
            )

            text = ""

        total_characters += len(text)

        pages.append({
            "page": page_number,
            "text": text
        })

    return pages, total_characters


# ============================================================
# OCR FALLBACK USING PYMUPDF + TESSERACT
# ============================================================

def extract_with_ocr(pdf_path: Path):

    print("  OCR fallback activated...")

    document = fitz.open(str(pdf_path))

    pages = []

    total_characters = 0

    for page_number, page in enumerate(
        document,
        start=1
    ):

        print(
            f"  OCR page {page_number}/{len(document)}..."
        )

        # Render PDF page as an image.
        #
        # 2x zoom gives OCR considerably more detail
        # than a low-resolution screenshot.
        matrix = fitz.Matrix(2, 2)

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        # Convert rendered page into PIL image
        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        try:

            text = pytesseract.image_to_string(
                image,
                config="--psm 6"
            )

        except Exception as error:

            print(
                f"  OCR error on page "
                f"{page_number}: {error}"
            )

            text = ""

        total_characters += len(text)

        pages.append({
            "page": page_number,
            "text": text
        })

    document.close()

    return pages, total_characters


# ============================================================
# REMOVE REPEATED HEADERS / FOOTERS
# ============================================================

def remove_repeated_headers_footers(pages):

    if len(pages) < 3:
        return pages

    top_lines = []
    bottom_lines = []

    for page in pages:

        lines = [
            line.strip()
            for line in page["text"].split("\n")
            if line.strip()
        ]

        if not lines:
            continue

        top_lines.extend(lines[:2])
        bottom_lines.extend(lines[-2:])

    def get_repeated_lines(lines):

        counts = {}

        for line in lines:

            normalized = re.sub(
                r"\s+",
                " ",
                line
            ).strip().lower()

            if len(normalized) < 5:
                continue

            counts[normalized] = (
                counts.get(normalized, 0) + 1
            )

        return {
            line
            for line, count in counts.items()
            if count >= 3
        }

    repeated_top = get_repeated_lines(top_lines)
    repeated_bottom = get_repeated_lines(bottom_lines)

    cleaned_pages = []

    for page in pages:

        lines = page["text"].split("\n")

        cleaned = []

        for index, line in enumerate(lines):

            normalized = re.sub(
                r"\s+",
                " ",
                line.strip()
            ).lower()

            # Possible repeated header
            if (
                index < 3
                and normalized in repeated_top
            ):
                continue

            # Possible repeated footer
            if (
                index >= len(lines) - 3
                and normalized in repeated_bottom
            ):
                continue

            cleaned.append(line)

        cleaned_pages.append({
            "page": page["page"],
            "text": "\n".join(cleaned)
        })

    return cleaned_pages


# ============================================================
# PROCESS ONE PDF
# ============================================================

def process_pdf(pdf_path: Path, doc_id: str):

    print()
    print("=" * 60)
    print(f"Processing: {pdf_path.name}")
    print("=" * 60)

    # --------------------------------------------------------
    # FIRST TRY: PYPDF
    # --------------------------------------------------------

    print("Trying pypdf extraction...")

    pages, character_count = extract_with_pypdf(
        pdf_path
    )

    print(
        f"pypdf extracted characters: "
        f"{character_count:,}"
    )

    extraction_method = "pypdf"

    # --------------------------------------------------------
    # OCR FALLBACK
    # --------------------------------------------------------

    # If pypdf extracts almost nothing,
    # assume this is a scanned/image PDF.

    if character_count < 100:

        print(
            "Very little text detected."
        )

        print(
            "PDF appears to be scanned."
        )

        pages, character_count = extract_with_ocr(
            pdf_path
        )

        extraction_method = "ocr"

        print(
            f"OCR extracted characters: "
            f"{character_count:,}"
        )

    # --------------------------------------------------------
    # HEADER / FOOTER CLEANING
    # --------------------------------------------------------

    pages = remove_repeated_headers_footers(
        pages
    )

    # --------------------------------------------------------
    # PAGE-BY-PAGE CLEANING
    # --------------------------------------------------------

    page_sections = []

    for page in pages:

        cleaned_page = normalize_text(
            page["text"]
        )

        if cleaned_page:

            page_sections.append(
                f"[PAGE {page['page']}]\n"
                f"{cleaned_page}"
            )

    full_text = "\n\n".join(
        page_sections
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        f"Final cleaned characters: "
        f"{len(full_text):,}"
    )

    if not full_text:

        print(
            "WARNING: No text could be extracted."
        )

    return {

        "doc_id": doc_id,

        "filename": pdf_path.name,

        "extraction_method": extraction_method,

        "page_count": len(pages),

        "character_count": len(full_text),

        "cleaned_text": full_text
    }


# ============================================================
# PROCESS ALL PDFs
# ============================================================

def process_all_pdfs():

    RAW_PDF_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf_files = sorted(
        RAW_PDF_DIR.glob("*.pdf")
    )

    if not pdf_files:

        print(
            "ERROR: No PDF files found in:"
        )

        print(RAW_PDF_DIR)

        return

    print()
    print("=" * 60)
    print("LEXVERIFY AI")
    print("LEGAL PDF EXTRACTION + OCR")
    print("=" * 60)

    print()
    print(
        f"PDF files found: "
        f"{len(pdf_files)}"
    )

    documents = []

    for index, pdf_path in enumerate(
        pdf_files,
        start=1
    ):

        doc_id = f"case_{index:03d}"

        document = process_pdf(
            pdf_path,
            doc_id
        )

        documents.append(document)

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)

    print()
    print(
        f"Documents processed: "
        f"{len(documents)}"
    )

    print()
    print(
        f"Output:"
    )

    print(OUTPUT_FILE)

    print()
    print("Summary:")

    for document in documents:

        print(
            f"{document['doc_id']} | "
            f"{document['extraction_method']} | "
            f"{document['character_count']:,} chars | "
            f"{document['filename']}"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    process_all_pdfs()