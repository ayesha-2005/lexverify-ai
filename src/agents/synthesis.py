from typing import List, Dict, Any

from openai import OpenAI
from src.state import AgentState


def _verified_source_files(
    verified_citations: List[Dict[str, Any]]
) -> set:
    sources = set()

    for item in verified_citations:
        source = item.get("source", "")

        if source:
            sources.add(source.strip())

    return sources


def _build_verified_evidence(
    retrieved_chunks: List[Dict[str, Any]],
    verified_citations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Keep ONLY chunks belonging to cases whose citations
    passed the deterministic Truth Registry gate.
    """

    verified_sources = _verified_source_files(
        verified_citations
    )

    evidence = []

    for chunk in retrieved_chunks:
        source_file = chunk.get(
            "source_file",
            ""
        ).strip()

        if source_file in verified_sources:
            evidence.append(chunk)

    return evidence


def run_synthesis_agent(
    state: AgentState,
    client: OpenAI
) -> AgentState:
    """
    Agent 4: Synthesis Agent.

    The LLM receives ONLY evidence belonging to cases
    whose citations passed the deterministic Truth Gate.
    """

    try:
        verified_citations = state.get(
            "verified_citations",
            []
        )

        retrieved_chunks = state.get(
            "retrieved_chunks",
            []
        )

        # ==================================================
        # STRICT TRUTH GATE
        # ==================================================

        if not verified_citations:
            state["final_answer"] = (
                "No verified legal precedent was found "
                "in the Truth Registry for this query. "
                "The retrieved material did not contain "
                "a verified citation that could safely "
                "support an answer."
            )

            state["status"] = "synthesis_completed"

            return state

        # ==================================================
        # ONLY VERIFIED EVIDENCE
        # ==================================================

        verified_evidence = _build_verified_evidence(
            retrieved_chunks,
            verified_citations
        )

        if not verified_evidence:
            state["final_answer"] = (
                "Verified citations were found in the "
                "Truth Registry, but no matching retrieved "
                "evidence was available to safely answer "
                "this query."
            )

            state["status"] = "synthesis_completed"

            return state

        # ==================================================
        # VERIFIED CITATIONS
        # ==================================================

        verified_text_parts = []

        for item in verified_citations:
            verified_text_parts.append(
                f"Citation: {item.get('citation', 'N/A')}\n"
                f"Case: {item.get('case_name', 'N/A')}\n"
                f"Court: {item.get('court', 'N/A')}\n"
                f"Year: {item.get('year', 'N/A')}\n"
                f"Source: {item.get('source', 'N/A')}"
            )

        verified_text = "\n\n".join(
            verified_text_parts
        )

        # ==================================================
        # VERIFIED EVIDENCE
        # ==================================================

        evidence_parts = []

        for index, chunk in enumerate(
            verified_evidence,
            start=1
        ):
            citations = chunk.get(
                "citations",
                []
            )

            if isinstance(citations, str):
                citations = [citations]

            evidence_parts.append(
                f"""
Evidence {index}

Case:
{chunk.get('case_name', 'Unknown')}

Citation:
{', '.join(citations)}

Court:
{chunk.get('court', 'Unknown')}

Date:
{chunk.get('date', 'Unknown')}

Source:
{chunk.get('source_file', 'Unknown')}

Page:
{chunk.get('page', 'Unknown')}

Text:
{chunk.get('text', '')}
"""
            )

        evidence_text = "\n".join(
            evidence_parts
        )

        # ==================================================
        # STRICT SYNTHESIS PROMPT
        # ==================================================

        system_prompt = f"""
You are the LexVerify AI Synthesis Agent specializing
in Pakistani case law.

Answer the user's question using ONLY the verified
citations and verified evidence supplied below.

STRICT RULES:

1. Use only cases listed under VERIFIED CITATIONS.

2. Do not introduce another case name.

3. Do not introduce another legal citation.

4. Do not invent citations.

5. Do not cite cases merely mentioned inside the evidence.

6. A citation is usable only if it appears under
   VERIFIED CITATIONS.

7. Base legal propositions only on VERIFIED EVIDENCE.

8. If the verified evidence is insufficient, say so clearly.

9. Do not claim that the corpus establishes something
   that the evidence does not establish.

10. Keep the answer concise and legally cautious.

11. This system is a legal research assistant and is not
    a substitute for professional legal advice.

VERIFIED CITATIONS
==================

{verified_text}

VERIFIED EVIDENCE
=================

{evidence_text}
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": state["user_question"]
                }
            ],
            temperature=0.0
        )

        answer = (
            response.choices[0]
            .message
            .content
        )

        if not answer:
            answer = (
                "No answer could be generated from "
                "the verified evidence."
            )

        state["final_answer"] = answer
        state["status"] = "synthesis_completed"

    except Exception as e:
        state.setdefault(
            "errors",
            []
        ).append(
            f"Synthesis Error: {str(e)}"
        )

        state["status"] = "synthesis_failed"

    return state
This is what in Verificatio.py:
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

    # Helper function to strip raw HTML tags from registry fields
    def strip_html_tags(val: Any) -> str:
        if not val or not isinstance(val, str):
            return str(val) if val is not None else ""
        return re.sub(r'<[^>]*>', '', val).strip()

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
                                strip_html_tags(official_citation),

                            "case_name":
                                strip_html_tags(
                                    metadata.get(
                                        "case_name",
                                        metadata.get("title", ""),
                                    )
                                ),

                            "court":
                                strip_html_tags(
                                    metadata.get(
                                        "court",
                                        "",
                                    )
                                ),

                            "year":
                                strip_html_tags(
                                    metadata.get(
                                        "year",
                                        "",
                                    )
                                ),

                            "source":
                                strip_html_tags(
                                    metadata.get(
                                        "source",
                                        "",
                                    )
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
                        strip_html_tags(citation)
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