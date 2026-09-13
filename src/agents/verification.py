import json
import os
import re
from typing import Any, Dict, List

from src.state import AgentState


# ============================================================
# CITATION PATTERNS
# ============================================================

# Reporter-first:
# PLD 2022 Supreme Court 743
# PLD 2022 SC 743
# PLJ 2018 Lahore High Court 123
REPORTER_FIRST_REGEX = re.compile(
    r"""
    \b
    (?P<reporter>
        PLD|PLJ|SCMR|YLR|CLC|PCrLJ|PTD|PLC|GBLR|KLR|PSC|SCP
    )
    \s+
    (?P<year>\d{4})
    \s+
    (?P<court>
        Supreme\s+Court|
        Federal\s+Shariat\s+Court|
        Lahore\s+High\s+Court|
        Sindh\s+High\s+Court|
        Peshawar\s+High\s+Court|
        Balochistan\s+High\s+Court|
        Baluchistan\s+High\s+Court|
        Islamabad\s+High\s+Court|
        SC|LHC|SHC|PHC|BHC|IHC|HC
    )
    \s+
    (?P<page>\d+)
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)


# Year-first:
# 2022 PLD Supreme Court 743
# 2022 PLD SC 743
YEAR_FIRST_REGEX = re.compile(
    r"""
    \b
    (?P<year>\d{4})
    \s+
    (?P<reporter>
        PLD|PLJ|SCMR|YLR|CLC|PCrLJ|PTD|PLC|GBLR|KLR|PSC|SCP
    )
    \s+
    (?P<court>
        Supreme\s+Court|
        Federal\s+Shariat\s+Court|
        Lahore\s+High\s+Court|
        Sindh\s+High\s+Court|
        Peshawar\s+High\s+Court|
        Balochistan\s+High\s+Court|
        Baluchistan\s+High\s+Court|
        Islamabad\s+High\s+Court|
        SC|LHC|SHC|PHC|BHC|IHC|HC
    )
    \s+
    (?P<page>\d+)
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)


# ============================================================
# NORMALIZE COURT
# ============================================================

def normalize_court(court: str) -> str:

    court = court.upper().strip()

    replacements = {
        "SUPREME COURT": "SC",
        "FEDERAL SHARIAT COURT": "FSC",
        "LAHORE HIGH COURT": "LHC",
        "SINDH HIGH COURT": "SHC",
        "PESHAWAR HIGH COURT": "PHC",
        "BALOCHISTAN HIGH COURT": "BHC",
        "BALUCHISTAN HIGH COURT": "BHC",
        "ISLAMABAD HIGH COURT": "IHC",
        "HIGH COURT": "HC",
    }

    return replacements.get(
        court,
        court
    )


# ============================================================
# NORMALIZE CITATION
# ============================================================

def normalize_citation(citation: str) -> str:

    if not citation:
        return ""

    citation = str(citation).strip()

    # --------------------------------------------
    # Try reporter-first
    # --------------------------------------------

    match = REPORTER_FIRST_REGEX.search(
        citation
    )

    if match:

        reporter = (
            match.group("reporter")
            .upper()
        )

        year = match.group("year")

        court = normalize_court(
            match.group("court")
        )

        page = match.group("page")

        return (
            f"{reporter} "
            f"{year} "
            f"{court} "
            f"{page}"
        )

    # --------------------------------------------
    # Try year-first
    # --------------------------------------------

    match = YEAR_FIRST_REGEX.search(
        citation
    )

    if match:

        reporter = (
            match.group("reporter")
            .upper()
        )

        year = match.group("year")

        court = normalize_court(
            match.group("court")
        )

        page = match.group("page")

        return (
            f"{reporter} "
            f"{year} "
            f"{court} "
            f"{page}"
        )

    return ""


# ============================================================
# EXTRACT CITATIONS
# ============================================================

def extract_citations_from_text(
    text: str
) -> List[str]:

    if not text:
        return []

    citations = []

    # --------------------------------------------
    # Reporter-first citations
    # --------------------------------------------

    for match in REPORTER_FIRST_REGEX.finditer(
        text
    ):

        citations.append(
            match.group(0).strip()
        )

    # --------------------------------------------
    # Year-first citations
    # --------------------------------------------

    for match in YEAR_FIRST_REGEX.finditer(
        text
    ):

        citation = match.group(0).strip()

        if citation not in citations:

            citations.append(
                citation
            )

    return list(
        dict.fromkeys(
            citations
        )
    )


# ============================================================
# EXTRACT CITATIONS FROM RETRIEVED CHUNKS
# ============================================================

def extract_citations_from_chunks(
    chunks: List[Dict[str, Any]]
) -> List[str]:

    citations = []

    for chunk in chunks or []:

        # ====================================================
        # STRUCTURED CITATIONS
        # ====================================================

        structured = chunk.get(
            "citations",
            []
        )

        if isinstance(
            structured,
            str
        ):

            citations.extend(
                extract_citations_from_text(
                    structured
                )
            )

        elif isinstance(
            structured,
            list
        ):

            for item in structured:

                if not item:
                    continue

                citations.extend(
                    extract_citations_from_text(
                        str(item)
                    )
                )

        # ====================================================
        # RAW EVIDENCE TEXT
        # ====================================================

        text = chunk.get(
            "text",
            ""
        )

        if text:

            citations.extend(
                extract_citations_from_text(
                    text
                )
            )

    return list(
        dict.fromkeys(
            citation.strip()
            for citation in citations
            if citation and citation.strip()
        )
    )


# ============================================================
# VERIFICATION AGENT
# ============================================================

def run_verification_agent(
    state: AgentState,
    truth_registry_path: str = "data/truth_registry.json",
) -> AgentState:

    try:

        # ====================================================
        # 1. CHECK TRUTH REGISTRY
        # ====================================================

        if not os.path.exists(
            truth_registry_path
        ):

            state["errors"].append(
                f"Truth Registry not found: "
                f"{truth_registry_path}"
            )

            state["status"] = (
                "verification_failed"
            )

            return state

        # ====================================================
        # 2. LOAD TRUTH REGISTRY
        # ====================================================

        with open(
            truth_registry_path,
            "r",
            encoding="utf-8",
        ) as f:

            truth_registry = json.load(f)

        # ====================================================
        # 3. NORMALIZE TRUTH REGISTRY
        # ====================================================

        normalized_registry = {}

        for raw_key, metadata in (
            truth_registry.items()
        ):

            normalized_key = (
                normalize_citation(
                    raw_key
                )
            )

            if normalized_key:

                normalized_registry[
                    normalized_key
                ] = {
                    "citation": raw_key,
                    "metadata": metadata,
                }

        # ====================================================
        # 4. GET RETRIEVED EVIDENCE
        # ====================================================

        retrieved_chunks = state.get(
            "retrieved_chunks",
            []
        )

        # ====================================================
        # 5. EXTRACT DIRECTLY FROM EVIDENCE
        # ====================================================

        evidence_citations = (
            extract_citations_from_chunks(
                retrieved_chunks
            )
        )

        # ====================================================
        # 6. GET RETRIEVAL AGENT CANDIDATES
        # ====================================================

        retrieval_candidates = (
            state.get(
                "candidate_citations",
                []
            )
        )

        candidates = []

        # Evidence is the primary source.
        candidates.extend(
            evidence_citations
        )

        # Retrieval candidates are secondary.
        for candidate in retrieval_candidates:

            if not candidate:
                continue

            parsed = (
                extract_citations_from_text(
                    str(candidate)
                )
            )

            candidates.extend(
                parsed
            )

        # Remove duplicates.
        candidates = list(
            dict.fromkeys(
                candidate.strip()
                for candidate in candidates
                if candidate and candidate.strip()
            )
        )

        # ====================================================
        # 7. FALLBACK EXTRACTION
        # ====================================================

        if not candidates:

            fallback_text = (
                state.get(
                    "user_question",
                    ""
                )
                + " "
                + " ".join(
                    chunk.get(
                        "text",
                        ""
                    )
                    for chunk in retrieved_chunks
                )
            )

            candidates = (
                extract_citations_from_text(
                    fallback_text
                )
            )

        # ====================================================
        # 8. VERIFY
        # ====================================================

        verified = []
        rejected = []

        seen_verified = set()
        seen_rejected = set()

        for citation in candidates:

            normalized = (
                normalize_citation(
                    citation
                )
            )

            # Ignore anything that isn't a
            # complete recognized citation.
            if not normalized:
                continue

            registry_entry = (
                normalized_registry.get(
                    normalized
                )
            )

            # =================================================
            # VERIFIED
            # =================================================

            if registry_entry:

                official_citation = (
                    registry_entry[
                        "citation"
                    ]
                )

                metadata = (
                    registry_entry[
                        "metadata"
                    ]
                )

                if normalized not in seen_verified:

                    verified.append(
                        {
                            "citation":
                                official_citation,

                            "case_name":
                                metadata.get(
                                    "case_name",
                                    "",
                                ),

                            "court":
                                metadata.get(
                                    "court",
                                    "",
                                ),

                            "year":
                                metadata.get(
                                    "year",
                                    "",
                                ),

                            "source":
                                metadata.get(
                                    "source",
                                    "",
                                ),

                            "verified":
                                True,
                        }
                    )

                    seen_verified.add(
                        normalized
                    )

            # =================================================
            # REJECTED
            # =================================================

            else:

                if normalized not in seen_rejected:

                    rejected.append(
                        citation
                    )

                    seen_rejected.add(
                        normalized
                    )

        # ====================================================
        # 9. DEBUG INFORMATION
        # ====================================================

        # This makes future debugging much easier.
        state["errors"].append(
            "Verification debug — "
            f"Evidence citations: {evidence_citations} | "
            f"Final candidates: {candidates} | "
            f"Verified: {[v['citation'] for v in verified]}"
        )

        # ====================================================
        # 10. SAVE RESULTS
        # ====================================================

        state[
            "verified_citations"
        ] = verified

        state[
            "rejected_citations"
        ] = rejected

        state[
            "status"
        ] = "verification_completed"

        return state

    except Exception as e:

        state[
            "errors"
        ].append(
            "Verification Agent Error: "
            + str(e)
        )

        state[
            "status"
        ] = "verification_failed"

        return state