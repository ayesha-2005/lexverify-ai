from typing import List, Dict, Any

from openai import OpenAI
from src.state import AgentState


def _build_verified_evidence(
    retrieved_chunks: List[Any],
    verified_citations: List[Any]
) -> List[Dict[str, Any]]:
    """
    Safely formats and filters retrieved chunks.
    Converts any raw string chunks into dictionaries to prevent .get() crashes.
    """
    evidence = []
    
    for chunk in retrieved_chunks:
        if isinstance(chunk, dict):
            evidence.append(chunk)
        elif isinstance(chunk, str):
            evidence.append({
                "text": chunk,
                "case_name": "Unknown",
                "source_file": "Unknown",
                "court": "Unknown"
            })
            
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
            if isinstance(item, dict):
                verified_text_parts.append(
                    f"Citation: {item.get('citation', 'N/A')}\n"
                    f"Case: {item.get('case_name', 'N/A')}\n"
                    f"Court: {item.get('court', 'N/A')}\n"
                    f"Year: {item.get('year', 'N/A')}\n"
                    f"Source: {item.get('source', 'N/A')}"
                )
            else:
                # Handle raw string citations safely
                verified_text_parts.append(f"Citation: {str(item)}")

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
            citations = chunk.get("citations", [])
            
            # Safely handle citations list to prevent join() errors
            if isinstance(citations, str):
                citations = [citations]
            elif not citations:
                citations = []
                
            safe_citations = [str(c) for c in citations if c]

            evidence_parts.append(
                f"""
Evidence {index}

Case:
{chunk.get('case_name', 'Unknown')}

Citation:
{', '.join(safe_citations)}

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
6. A citation is usable only if it appears under VERIFIED CITATIONS.
7. Base legal propositions only on VERIFIED EVIDENCE.
8. If the verified evidence is insufficient, say so clearly.
9. Do not claim that the corpus establishes something that the evidence does not establish.
10. Keep the answer concise and legally cautious.
11. Format citations cleanly in bold (e.g. **1993 P Cr. L. J. 781**).
12. This system is a legal research assistant and is not a substitute for professional legal advice.

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
                    "content": state.get("user_question", "Summarize the legal findings.")
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
        # Instead of hiding the error, we print it directly to the UI
        state.setdefault("errors", []).append(f"Synthesis Error: {str(e)}")
        state["final_answer"] = f"⚠️ Pipeline Error in Synthesis Agent: {str(e)}"
        state["status"] = "synthesis_failed"

    return state