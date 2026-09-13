import os
from openai import OpenAI
from src.state import AgentState

def run_synthesis_agent(state: AgentState, client: OpenAI) -> AgentState:
    """
    Agent 4: Synthesis Agent. Answers user question using ONLY verified citations
    and retrieved context chunks. Refuses to speculate or cite rejected authorities.
    """
    try:
        verified_citations = state.get("verified_citations", [])
        rejected_citations = state.get("rejected_citations", [])
        retrieved_chunks = state.get("retrieved_chunks", [])

        # Fallback check: Refuse to generate if no verified context or chunks exist
        if not verified_citations and not retrieved_chunks:
            state["final_answer"] = (
                "No verified legal precedent was found in the database "
                "to answer this specific question."
            )
            state["status"] = "synthesis_completed"
            return state

        # Format verified citations
        verified_text = "\n".join(
            [f"- Citation: {item.get('citation', 'N/A')} | Title: {item.get('case_name', item.get('title', 'N/A'))} | Court: {item.get('court', 'N/A')}" 
             for item in verified_citations]
        )
        if not verified_text:
            verified_text = "None verified."

        # Format rejected citations to explicitly blacklist them in prompt
        rejected_text = "\n".join(
            [f"- Rejected: {item if isinstance(item, str) else item.get('citation', str(item))}"
             for item in rejected_citations]
        )
        if not rejected_text:
            rejected_text = "None."

        # Format retrieved context chunks
        chunk_text = "\n".join(
            [f"- Source: {c.get('source_file', c.get('source_doc', 'Unknown'))} | Text: {c.get('text', '')}" 
             for c in retrieved_chunks]
        )

        system_prompt = (
            "You are the LexVerify AI Synthesis Agent specializing in Pakistani Case Law.\n"
            "Your task is to answer the user's legal question using ONLY the provided verified citations and retrieved text chunks.\n\n"
            "STRICT CITATION FILTERING RULES:\n"
            "1. Base your answer strictly on the VERIFIED CITATIONS provided below.\n"
            "2. DO NOT cite, mention, summarize, or refer to any case law, title, authority, or volume number listed under REJECTED CITATIONS.\n"
            "3. If raw text chunks mention case names or authorities (e.g., Zaheer Illahi, unverified PLD/SCMR volumes) that are listed in REJECTED CITATIONS or missing from VERIFIED CITATIONS, you MUST EXCLUDE them completely from your analysis.\n"
            "4. Only cite precedents explicitly validated in the VERIFIED CITATIONS list.\n\n"
            f"VERIFIED CITATIONS (ONLY USE THESE):\n{verified_text}\n\n"
            f"REJECTED / UNVERIFIED CITATIONS (STRICTLY FORBIDDEN — DO NOT MENTION): \n{rejected_text}\n\n"
            f"RETRIEVED CONTEXT CHUNKS:\n{chunk_text}"
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state["user_question"]}
            ],
            temperature=0.1
        )

        state["final_answer"] = response.choices[0].message.content
        state["status"] = "synthesis_completed"

    except Exception as e:
        state["errors"].append(f"Synthesis Agent Error: {str(e)}")
        state["status"] = "synthesis_failed"

    return state