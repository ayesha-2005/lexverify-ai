from typing import List, Dict, Any

from openai import OpenAI
from src.state import AgentState

<<<<<<< HEAD
def run_synthesis_agent(state: AgentState, client: OpenAI) -> AgentState:
    """
    Agent 4: Synthesis Agent. Answers user question using ONLY verified citations.
    """
    try:
        verified_citations = state.get("verified_citations", [])
        rejected_citations = state.get("rejected_citations", [])
        retrieved_chunks = state.get("retrieved_chunks", [])

        # STRICT GATE: Refuse if no verified citations exist
        if not verified_citations:
            state["final_answer"] = (
                "No verified legal precedent was confirmed in the Truth Registry "
                "to answer this specific query. Unverified citations from retrieved text have been excluded."
=======

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
>>>>>>> origin/rag-data-pipeline
            )

            state["status"] = "synthesis_completed"

            return state

<<<<<<< HEAD
        verified_text = "\n".join(
            [f"- Citation: {item.get('citation', 'N/A')} | Title: {item.get('title', 'N/A')} | Court: {item.get('court', 'N/A')}" 
             for item in verified_citations]
        )

        chunk_text = "\n".join(
            [f"- Source: {c.get('source_file', 'Unknown')} | Text: {c.get('text', '')}" 
             for c in retrieved_chunks]
        )

        system_prompt = (
            "You are the LexVerify AI Synthesis Agent specializing in Pakistani Case Law.\n"
            "STRICT RULES:\n"
            "1. Answer using ONLY precedents explicitly listed under VERIFIED CITATIONS.\n"
            "2. DO NOT cite or mention any case titles or volumes that are not listed under VERIFIED CITATIONS.\n\n"
            f"VERIFIED CITATIONS:\n{verified_text}\n\n"
            f"RETRIEVED CONTEXT CHUNKS:\n{chunk_text}"
=======
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
>>>>>>> origin/rag-data-pipeline
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
<<<<<<< HEAD
        state["errors"].append(f"Synthesis Error: {str(e)}")
=======
        state.setdefault(
            "errors",
            []
        ).append(
            f"Synthesis Error: {str(e)}"
        )

>>>>>>> origin/rag-data-pipeline
        state["status"] = "synthesis_failed"

    return state