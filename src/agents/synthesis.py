from typing import List, Dict, Any, Set

from openai import OpenAI
from src.state import AgentState


# ============================================================
# Source Classification
# ============================================================

TRUSTED_DOCUMENT_TYPES = {
    "statute",
    "constitution",
}


def _verified_source_files(
    verified_citations: List[Dict[str, Any]]
) -> Set[str]:
    """
    Return source files belonging to citations that passed
    the deterministic Truth Registry verification.
    """

    sources = set()

    for item in verified_citations:
        source = item.get("source", "")

        if source:
            sources.add(
                str(source).strip()
            )

    return sources


def _is_trusted_non_case_source(
    chunk: Dict[str, Any]
) -> bool:
    """
    Statutes and the Constitution are trusted corpus sources.

    They do not require case-citation verification because
    they are primary legal source documents rather than
    judicial precedents.
    """

    document_type = str(
        chunk.get("document_type", "")
    ).strip().lower()

    return document_type in TRUSTED_DOCUMENT_TYPES


def _is_verified_case_evidence(
    chunk: Dict[str, Any],
    verified_source_files: Set[str]
) -> bool:
    """
    A judgment chunk is eligible only when its own source file
    belongs to a citation that passed the Truth Registry gate.

    This prevents an unrelated chunk from a verified judgment
    being treated as automatically verified.
    """

    document_type = str(
        chunk.get("document_type", "judgment")
    ).strip().lower()

    if document_type != "judgment":
        return False

    source_file = str(
        chunk.get("source_file", "")
    ).strip()

    return (
        bool(source_file)
        and source_file in verified_source_files
    )


# ============================================================
# Evidence Selection
# ============================================================

def _build_verified_evidence(
    retrieved_chunks: List[Dict[str, Any]],
    verified_citations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build evidence that is safe to pass to the Synthesis Agent.

    Rules:

    1. Judgment chunks require a verified Truth Registry
       citation whose source matches the judgment file.

    2. Statute chunks are trusted as primary statutory sources.

    3. Constitution chunks are trusted as primary constitutional
       sources.

    4. Unknown/unclassified sources are excluded.
    """

    verified_sources = _verified_source_files(
        verified_citations
    )

    evidence = []

    for chunk in retrieved_chunks:

        if _is_verified_case_evidence(
            chunk,
            verified_sources
        ):
            evidence.append(chunk)
            continue

        if _is_trusted_non_case_source(chunk):
            evidence.append(chunk)
            continue

    return evidence


# ============================================================
# Evidence Formatting
# ============================================================

def _format_verified_case_authorities(
    verified_citations: List[Dict[str, Any]]
) -> str:
    """
    Format only Truth Registry-verified judicial authorities.
    """

    if not verified_citations:
        return "None"

    parts = []

    for item in verified_citations:

        parts.append(
            f"""
Citation:
{item.get('citation', 'N/A')}

Matched Citation:
{item.get('matched_citation', 'N/A')}

Case:
{item.get('case_name', 'N/A')}

Court:
{item.get('court', 'N/A')}

Year:
{item.get('year', 'N/A')}

Source:
{item.get('source', 'N/A')}

Verification:
{item.get('match_type', 'N/A')} match,
score {item.get('match_score', 'N/A')}
"""
        )

    return "\n".join(parts)


def _format_evidence(
    evidence: List[Dict[str, Any]]
) -> str:
    """
    Format retrieved evidence while explicitly identifying
    the legal source type.
    """

    parts = []

    for index, chunk in enumerate(
        evidence,
        start=1
    ):

        document_type = str(
            chunk.get("document_type", "")
        ).strip().lower()

        if document_type == "judgment":
            source_type = "VERIFIED JUDICIAL AUTHORITY"
        elif document_type == "statute":
            source_type = "TRUSTED STATUTORY SOURCE"
        elif document_type == "constitution":
            source_type = "TRUSTED CONSTITUTIONAL SOURCE"
        else:
            source_type = "UNKNOWN SOURCE"

        citations = chunk.get(
            "citations",
            []
        )

        if isinstance(citations, str):
            citations = [citations]

        citation_text = ", ".join(
            str(c)
            for c in citations
            if c
        )

        parts.append(
            f"""
Evidence {index}

SOURCE TYPE:
{source_type}

Document Type:
{chunk.get('document_type', 'Unknown')}

Case:
{chunk.get('case_name', 'N/A')}

Citation:
{citation_text or 'N/A'}

Court:
{chunk.get('court', 'N/A')}

Date:
{chunk.get('date', 'N/A')}

Source File:
{chunk.get('source_file', 'N/A')}

Page:
{chunk.get('page', 'N/A')}

Sections:
{chunk.get('sections', [])}

Text:
{chunk.get('text', '')}
"""
        )

    return "\n".join(parts)


# ============================================================
# Synthesis Agent
# ============================================================

def run_synthesis_agent(
    state: AgentState,
    client: OpenAI
) -> AgentState:
    """
    Agent 4: Synthesis Agent.

    Evidence policy:

    - Judicial judgments require Truth Registry verification.
    - Statutes are trusted primary legal sources.
    - The Constitution is a trusted primary legal source.
    - Unknown/unclassified sources are excluded.

    The LLM must ground substantive claims only in the
    supplied evidence.
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

        # ----------------------------------------------------
        # 1. Build safe evidence
        # ----------------------------------------------------

        verified_evidence = _build_verified_evidence(
            retrieved_chunks,
            verified_citations
        )

        # ----------------------------------------------------
        # 2. No usable evidence
        # ----------------------------------------------------

        if not verified_evidence:

            if not verified_citations:

                state["final_answer"] = (
                    "No verified legal precedent or trusted "
                    "statutory/constitutional evidence was found "
                    "in the retrieved corpus for this query."
                )

            else:

                state["final_answer"] = (
                    "Verified judicial citations were found, "
                    "but no matching retrieved evidence was "
                    "available to safely support an answer."
                )

            state["status"] = "synthesis_completed"

            return state

        # ----------------------------------------------------
        # 3. Prepare evidence
        # ----------------------------------------------------

        verified_authorities_text = (
            _format_verified_case_authorities(
                verified_citations
            )
        )

        evidence_text = _format_evidence(
            verified_evidence
        )

        # ----------------------------------------------------
        # 4. Synthesis instructions
        # ----------------------------------------------------

        system_prompt = f"""
You are the LexVerify AI Synthesis Agent specializing
in Pakistani law.

Your task is to answer the user's question using ONLY
the supplied evidence.

IMPORTANT SOURCE RULES
======================

There are two different categories of trusted evidence.

CATEGORY 1 — VERIFIED JUDICIAL AUTHORITIES
-------------------------------------------

A judgment may be used only when its source file corresponds
to a citation that passed the deterministic Truth Registry.

The verified authorities are listed below.

CATEGORY 2 — TRUSTED PRIMARY LEGAL SOURCES
------------------------------------------

Statutes and the Constitution in the supplied evidence are
trusted primary legal source documents.

They do NOT need to appear in the case-citation Truth Registry.

Do not treat a statute or constitutional provision as a
judicial precedent.

STRICT GROUNDING RULES
======================

1. Use ONLY information explicitly supported by the supplied
   evidence.

2. Do not use outside legal knowledge.

3. Do not invent legal rules, sections, case holdings,
   conditions, facts, dates, courts, or citations.

4. Do not introduce a case that is not present in the
   VERIFIED JUDICIAL AUTHORITIES or supplied evidence.

5. Do not introduce a citation that is not present in the
   supplied evidence.

6. Citation verification does NOT automatically prove that
   every statement in that case is supported.

7. A retrieved judgment chunk may support a claim only when
   the text of that chunk supports the claim.

8. Statutory claims must be supported by the supplied
   statutory evidence.

9. Constitutional claims must be supported by the supplied
   constitutional evidence.

10. Do not infer a legal rule merely because it is generally
    known or likely to be true.

11. If the supplied evidence does not answer part of the
    question, explicitly state that the available evidence
    is insufficient for that part.

12. Prefer a narrower evidence-supported answer over a broad
    answer containing unsupported legal generalizations.

13. Clearly distinguish between:
    - what a statute says,
    - what the Constitution provides,
    - what a court decided,
    - and what cannot be established from the supplied evidence.

14. Do not treat cases merely mentioned inside another judgment
    as independently verified authorities.

15. Do not fabricate citations.

16. Keep the answer concise and legally cautious.

17. This system is a legal research assistant and is not a
    substitute for professional legal advice.

VERIFIED JUDICIAL AUTHORITIES
=============================

{verified_authorities_text}

RETRIEVED TRUSTED EVIDENCE
==========================

{evidence_text}
"""

        # ----------------------------------------------------
        # 5. LLM synthesis
        # ----------------------------------------------------

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
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
                "the supplied legal evidence."
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
