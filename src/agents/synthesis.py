import os
from openai import OpenAI
from src.state import AgentState

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
            )
            state["status"] = "synthesis_completed"
            return state

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
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state["user_question"]}
            ],
            temperature=0.0
        )

        state["final_answer"] = response.choices[0].message.content
        state["status"] = "synthesis_completed"

    except Exception as e:
        state["errors"].append(f"Synthesis Error: {str(e)}")
        state["status"] = "synthesis_failed"

    return state