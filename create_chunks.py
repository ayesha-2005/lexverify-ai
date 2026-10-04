import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent

CLEANED_DOCS = ROOT / "data" / "cleaned_docs.json"
METADATA_FILE = ROOT / "data" / "metadata.json"
CHUNKS_FILE = ROOT / "data" / "chunks.json"


# ============================================================
# EXISTING CASE METADATA
# ============================================================

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


# ============================================================
# NEW DOCUMENT METADATA
# ============================================================

DOCUMENT_METADATA = {

    "03_FECTO_Belarus_PLD_2005_605.pdf": {
        "document_type": "judgment",
        "document_title": "FECTO Belarus Case",
        "area": "Constitutional / Legal",
        "topic": "Constitutional Law",
        "citations": ["PLD 2005 Supreme Court 605"]
    },

    "04_Mobashir_Hassan_PLD_2010_265.pdf": {
        "document_type": "judgment",
        "document_title": "Mobashir Hassan Case",
        "area": "Constitutional / Criminal Law",
        "topic": "Accountability / Constitutional Law",
        "citations": ["PLD 2010 Supreme Court 265"]
    },

    "05_Imran_Khan_v_Nawaz_Sharif_PLD_2017_692.pdf": {
        "document_type": "judgment",
        "document_title": "Imran Khan v. Nawaz Sharif",
        "area": "Constitutional Law",
        "topic": "Constitutional Law",
        "citations": ["PLD 2017 Supreme Court 692"]
    },

    "06_Reko_Diq_Presidential_Reference_2022.pdf": {
        "document_type": "judgment",
        "document_title": "Reko Diq Presidential Reference",
        "area": "Constitutional Law",
        "topic": "Presidential Reference",
        "citations": []
    },

    "07_Justice_Qazi_Faez_Isa_PLD_2021_SC_1.pdf": {
        "document_type": "judgment",
        "document_title": "Justice Qazi Faez Isa Case",
        "area": "Constitutional Law",
        "topic": "Constitutional Petition",
        "citations": ["PLD 2021 Supreme Court 1"]
    },

    "Arbitration_Act_1940.pdf": {
        "document_type": "statute",
        "document_title": "Arbitration Act, 1940",
        "area": "Civil Law",
        "topic": "Arbitration",
        "citations": []
    },

    "Companies_Act_2017.pdf": {
        "document_type": "statute",
        "document_title": "Companies Act, 2017",
        "area": "Corporate Law",
        "topic": "Company Law",
        "citations": []
    },

    "Constitution_1973.pdf": {
        "document_type": "constitution",
        "document_title": "Constitution of the Islamic Republic of Pakistan, 1973",
        "area": "Constitutional Law",
        "topic": "Constitutional Law",
        "citations": []
    },

    "Contract_Act_1872.pdf": {
        "document_type": "statute",
        "document_title": "Contract Act, 1872",
        "area": "Civil Law",
        "topic": "Contract Law",
        "citations": []
    },

    "CrPC_1898.pdf": {
        "document_type": "statute",
        "document_title": "Code of Criminal Procedure, 1898",
        "area": "Criminal Law",
        "topic": "Criminal Procedure",
        "citations": ["Cr.P.C. 1898"]
    },

    "Family_Courts_Act_1964.pdf": {
        "document_type": "statute",
        "document_title": "Family Courts Act, 1964",
        "area": "Family Law",
        "topic": "Family Courts",
        "citations": []
    },

    "Limitation_Act_1908.pdf": {
        "document_type": "statute",
        "document_title": "Limitation Act, 1908",
        "area": "Civil Law",
        "topic": "Limitation",
        "citations": []
    },

    "PPC_1860.pdf": {
        "document_type": "statute",
        "document_title": "Pakistan Penal Code, 1860",
        "area": "Criminal Law",
        "topic": "Criminal Offences",
        "citations": []
    },

    "QSO_1984.pdf": {
        "document_type": "statute",
        "document_title": "Qanun-e-Shahadat Order, 1984",
        "area": "Evidence Law",
        "topic": "Law of Evidence",
        "citations": []
    },

    "SC_Practice_final_Procedure_Act_2023.pdf": {
        "document_type": "statute",
        "document_title": "Supreme Court Practice and Procedure Act, 2023",
        "area": "Constitutional Law",
        "topic": "Supreme Court Procedure",
        "citations": []
    },

    "Specific_Relief_Act_1877.pdf": {
        "document_type": "statute",
        "document_title": "Specific Relief Act, 1877",
        "area": "Civil Law",
        "topic": "Specific Relief",
        "citations": []
    },

    "Transfer_of_Property_Act_1882.pdf": {
        "document_type": "statute",
        "document_title": "Transfer of Property Act, 1882",
        "area": "Property Law",
        "topic": "Transfer of Property",
        "citations": []
    }
}


# ============================================================
# PAGE SPLITTING
# ============================================================

def split_pages(text):

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


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks():

    with open(
        CLEANED_DOCS,
        "r",
        encoding="utf-8"
    ) as f:
        documents = json.load(f)

    all_chunks = []
    all_metadata = []

    chunk_counter = 1

    CHUNK_SIZE = 1500
    OVERLAP = 250

    skipped = []

    for document in documents:

        doc_id = document["doc_id"]
        filename = document["filename"]

        # ----------------------------------------------------
        # Existing cases
        # ----------------------------------------------------

        if doc_id in CASE_METADATA:

            info = CASE_METADATA[doc_id]

            document_type = "judgment"

            base_metadata = {
                "case_id": doc_id,
                "case_name": info["case_name"],
                "citations": info["citations"],
                "court": info["court"],
                "date": info["date"],
                "area": info["area"],
                "topic": info["topic"],
                "sections": info["sections"],
                "principles": info["principles"],
                "document_type": document_type
            }

        # ----------------------------------------------------
        # New documents
        # ----------------------------------------------------

        elif filename in DOCUMENT_METADATA:

            info = DOCUMENT_METADATA[filename]

            base_metadata = {
                "case_id": None,
                "case_name": info["document_title"],
                "citations": info.get("citations", []),
                "court": None,
                "date": None,
                "area": info["area"],
                "topic": info["topic"],
                "sections": [],
                "principles": [],
                "document_type": info["document_type"]
            }

        else:

            print(
                f"WARNING: No metadata found for "
                f"{filename}"
            )

            skipped.append(filename)
            continue

        pages = split_pages(
            document["cleaned_text"]
        )

        for page_data in pages:

            page_number = page_data["page"]
            page_text = page_data["text"]

            start = 0

            while start < len(page_text):

                end = min(
                    start + CHUNK_SIZE,
                    len(page_text)
                )

                chunk_text = page_text[
                    start:end
                ].strip()

                if chunk_text:

                    chunk_id = (
                        f"chunk_{chunk_counter:05d}"
                    )

                    metadata = {
                        "chunk_id": chunk_id,
                        "case_id": base_metadata["case_id"],
                        "case_name": base_metadata["case_name"],
                        "citations": base_metadata["citations"],
                        "court": base_metadata["court"],
                        "date": base_metadata["date"],
                        "area": base_metadata["area"],
                        "topic": base_metadata["topic"],
                        "sections": base_metadata["sections"],
                        "principles": base_metadata["principles"],
                        "document_type": base_metadata["document_type"],
                        "source_file": filename,
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

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        CHUNKS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_chunks,
            f,
            ensure_ascii=False,
            indent=2
        )

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_metadata,
            f,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    document_types = {}

    for chunk in all_chunks:

        doc_type = chunk["document_type"]

        document_types[doc_type] = (
            document_types.get(doc_type, 0) + 1
        )

    source_files = set(
        chunk["source_file"]
        for chunk in all_chunks
    )

    print("=" * 60)
    print("CHUNKING COMPLETE")
    print("=" * 60)

    print(f"Documents loaded : {len(documents)}")
    print(f"Documents chunked: {len(source_files)}")
    print(f"Chunks           : {len(all_chunks)}")
    print(f"Metadata records  : {len(all_metadata)}")

    print()
    print("Document types:")

    for doc_type, count in sorted(
        document_types.items()
    ):
        print(
            f"  {doc_type}: {count} chunks"
        )

    if skipped:

        print()
        print("Skipped documents:")

        for filename in skipped:
            print(f"  - {filename}")

    print()
    print("Created:")
    print(CHUNKS_FILE)
    print(METADATA_FILE)

    if all_chunks:

        print()
        print("First chunk:")

        print(
            json.dumps(
                all_chunks[0],
                ensure_ascii=False,
                indent=2
            )
        )


if __name__ == "__main__":
    create_chunks()