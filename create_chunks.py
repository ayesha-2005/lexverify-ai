import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLEANED_DOCS = ROOT / "data" / "cleaned_docs.json"
METADATA_FILE = ROOT / "data" / "metadata.json"
CHUNKS_FILE = ROOT / "data" / "chunks.json"


# Case metadata based on the curated legal corpus
CASE_METADATA = {
    "case_001": {
        "case_name": "Muhammad Shafique v. The State and another",
        "citations": ["PLJ 2018 Cr.C. 656", "2018 YLR 323"],
        "court": "Lahore High Court",
        "date": "2017-05-18",
        "area": "Criminal Law",
        "topic": "Pre-arrest Bail",
        "sections": [
            "420 PPC",
            "468 PPC",
            "471 PPC",
            "497 Cr.P.C.",
            "498 Cr.P.C.",
            "498-A Cr.P.C."
        ],
        "principles": [
            "Pre-arrest Bail",
            "Fair Trial",
            "Mala Fide",
            "Due Process",
            "Multiple Criminal Cases"
        ]
    },

    "case_002": {
        "case_name": "Malik Nazir Ahmed v. Syed Shamas-ul-Abbas and others",
        "citations": [
            "2016 PSC Crl. 213",
            "2016 PLD Supreme Court 171"
        ],
        "court": "Supreme Court of Pakistan",
        "date": "2015-12-22",
        "area": "Criminal Law",
        "topic": "Pre-arrest Bail",
        "sections": [
            "498 Cr.P.C.",
            "489-F PPC"
        ],
        "principles": [
            "Pre-arrest Bail",
            "Mala Fide",
            "Investigation",
            "No Recovery"
        ]
    },

    "case_003": {
        "case_name": "Zeeshan S/o Gul Hussain v. The State & another",
        "citations": [
            "2024 SCMR 1716",
            "2024 SCP 253"
        ],
        "court": "Supreme Court of Pakistan",
        "date": "2024-07-26",
        "area": "Criminal Law",
        "topic": "Post-arrest Bail",
        "sections": [
            "302 PPC",
            "324 PPC",
            "427 PPC",
            "34 PPC"
        ],
        "principles": [
            "Further Inquiry",
            "Rule of Consistency",
            "Abscondence",
            "Non-recovery of Weapon",
            "Post-arrest Bail"
        ]
    },

    "case_004": {
        "case_name": "Tahira Batool v. The State and another",
        "citations": [
            "PLD 2022 SC 764"
        ],
        "court": "Supreme Court of Pakistan",
        "date": "2022-08-19",
        "area": "Criminal Law",
        "topic": "Post-arrest Bail",
        "sections": [
            "395 PPC",
            "412 PPC",
            "497 Cr.P.C."
        ],
        "principles": [
            "Bail to Woman Accused",
            "First Proviso to Section 497(1) Cr.P.C.",
            "Prohibitory Clause",
            "Bail as Rule",
            "Exceptions to Bail"
        ]
    },

    "case_005": {
        "case_name": "Asif Ali Zardari v. The State",
        "citations": [
            "1993 P Cr. L. J. 781"
        ],
        "court": "Sindh High Court",
        "date": "1993-01-31",
        "area": "Criminal Law",
        "topic": "Bail / Delay in Trial",
        "sections": [
            "497 Cr.P.C.",
            "498 Cr.P.C.",
            "497(2) Cr.P.C.",
            "561-A Cr.P.C."
        ],
        "principles": [
            "Bail on Prolonged Detention",
            "Delay in Trial",
            "Retrospective Operation of Statutes",
            "Vested Rights",
            "Further Inquiry",
            "Bail as a Statutory Right",
            "Special Court Bail Jurisdiction"
        ]
    },

    "case_006": {
        "case_name": "Mirza Javed Iqbal v. The State",
        "citations": [
            "K.L.R. 2001 Criminal Cases 185"
        ],
        "court": "High Court of Azad Jammu and Kashmir",
        "date": "2001-03-02",
        "area": "Criminal Law",
        "topic": "Bail",
        "sections": [
            "497 Cr.P.C.",
            "498 Cr.P.C.",
            "561-A Cr.P.C."
        ],
        "principles": [
            "Bail",
            "Cancellation of Warrant",
            "Special-law Jurisdiction",
            "Abscondence",
            "Sections 87 and 88 Cr.P.C."
        ]
    },

    "case_007": {
        "case_name": "Syed Raza Hussain Bukhari v. The State through D.A.G. & others",
        "citations": [
            "PLD 2022 Supreme Court 743"
        ],
        "court": "Supreme Court of Pakistan",
        "date": "2022-08-10",
        "area": "Criminal Law",
        "topic": "Post-arrest Bail / Delay in Trial",
        "sections": [
            "497 Cr.P.C.",
            "498 Cr.P.C.",
            "561-A Cr.P.C.",
            "420 PPC",
            "468 PPC",
            "471 PPC",
            "409 PPC",
            "5(2) Prevention of Corruption Act, 1947"
        ],
        "principles": [
            "Delay in Conclusion of Trial",
            "Third Proviso to Section 497(1) Cr.P.C.",
            "Constitutional Jurisdiction",
            "Fundamental Right to Liberty",
            "Fair Trial and Due Process",
            "Article 199",
            "Section 561-A Cr.P.C.",
            "Special Court Bail Jurisdiction"
        ]
    }
}


def split_pages(text):
    """
    Split OCR text using the [PAGE N] markers already present
    in cleaned_docs.json.
    """
    pattern = r"\[PAGE\s+(\d+)\]"
    matches = list(re.finditer(pattern, text))

    pages = []

    for i, match in enumerate(matches):
        page_number = int(match.group(1))

        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        page_text = text[start:end].strip()

        if page_text:
            pages.append({
                "page": page_number,
                "text": page_text
            })

    return pages


def create_chunks():
    with open(CLEANED_DOCS, "r", encoding="utf-8") as f:
        documents = json.load(f)

    all_chunks = []
    all_metadata = []

    chunk_counter = 1

    # Characters per chunk.
    # Keeping this moderate works well for legal retrieval.
    CHUNK_SIZE = 1500
    OVERLAP = 250

    for document in documents:

        case_id = document["doc_id"]

        if case_id not in CASE_METADATA:
            print(f"WARNING: No metadata found for {case_id}")
            continue

        case_info = CASE_METADATA[case_id]

        pages = split_pages(document["cleaned_text"])

        for page_data in pages:

            page_number = page_data["page"]
            page_text = page_data["text"]

            start = 0

            while start < len(page_text):

                end = min(start + CHUNK_SIZE, len(page_text))

                chunk_text = page_text[start:end].strip()

                if chunk_text:

                    chunk_id = f"chunk_{chunk_counter:05d}"

                    metadata = {
                        "chunk_id": chunk_id,
                        "case_id": case_id,
                        "case_name": case_info["case_name"],
                        "citations": case_info["citations"],
                        "court": case_info["court"],
                        "date": case_info["date"],
                        "area": case_info["area"],
                        "topic": case_info["topic"],
                        "sections": case_info["sections"],
                        "principles": case_info["principles"],
                        "source_file": document["filename"],
                        "page": page_number
                    }

                    chunk = {
                        **metadata,
                        "text": chunk_text
                    }

                    all_chunks.append(chunk)
                    all_metadata.append(metadata)

                    chunk_counter += 1

                if end >= len(page_text):
                    break

                start = end - OVERLAP

    # Save chunks
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    # Save metadata
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("CHUNKING COMPLETE")
    print("=" * 60)
    print("Documents:", len(documents))
    print("Chunks:", len(all_chunks))
    print("Metadata records:", len(all_metadata))
    print()
    print("Created:")
    print(CHUNKS_FILE)
    print(METADATA_FILE)

    if all_chunks:
        print()
        print("First chunk:")
        print(json.dumps(all_chunks[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    create_chunks()