import json
from openai import OpenAI
from src.state import AgentState


def run_research_agent(
    state: AgentState,
    client: OpenAI
) -> AgentState:
    """
    Agent 1: Research Agent.

    Analyzes the user's legal question and generates
    structured semantic search queries.

    IMPORTANT:
    This agent must NEVER invent legal citations.
    """

    system_prompt = """
You are the LexVerify AI Research Agent specializing in Pakistani Case Law.

Your task is to analyze the user's legal research question and convert it
into structured retrieval parameters.

STRICT RULES:
1. DO NOT invent legal citations.
2. DO NOT provide case names unless they are explicitly present in the user's question.
3. DO NOT answer the legal question.
4. Generate semantic search queries that will help the retrieval system
   find relevant Pakistani case-law evidence.
5. Return ONLY valid JSON.

Required JSON structure:

{
    "legal_intent": "short summary of the legal issue",
    "key_terms": ["keyword1", "keyword2"],
    "search_queries": [
        "semantic search query 1",
        "semantic search query 2",
        "semantic search query 3"
    ]
}

Generate 2-3 strong semantic search queries.
"""

    try:
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
            temperature=0.1
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Research Agent returned an empty response."
            )

        # -----------------------------------------------------
        # Clean possible markdown JSON fences
        # -----------------------------------------------------

        content = content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        # -----------------------------------------------------
        # Parse JSON
        # -----------------------------------------------------

        research_plan = json.loads(content)

        # -----------------------------------------------------
        # Validate required fields
        # -----------------------------------------------------

        if not isinstance(research_plan, dict):
            raise ValueError(
                "Research Agent response is not a JSON object."
            )

        legal_intent = research_plan.get(
            "legal_intent",
            state["user_question"]
        )

        key_terms = research_plan.get(
            "key_terms",
            []
        )

        search_queries = research_plan.get(
            "search_queries",
            []
        )

        # Ensure correct types
        if not isinstance(key_terms, list):
            key_terms = []

        if not isinstance(search_queries, list):
            search_queries = []

        # Remove empty queries
        search_queries = [
            str(q).strip()
            for q in search_queries
            if str(q).strip()
        ]

        # -----------------------------------------------------
        # Guaranteed fallback query
        # -----------------------------------------------------

        if not search_queries:
            search_queries = [
                state["user_question"]
            ]

        research_plan = {
            "legal_intent": str(legal_intent),
            "key_terms": key_terms,
            "search_queries": search_queries[:3]
        }

        state["research_plan"] = research_plan
        state["status"] = "research_completed"

        print("RESEARCH COMPLETED:", research_plan)

    except Exception as e:

        # -----------------------------------------------------
        # Safe fallback
        # -----------------------------------------------------

        print("RESEARCH ERROR:", str(e))

        state["errors"].append(
            f"Research Agent Error: {str(e)}"
        )

        state["research_plan"] = {
            "legal_intent": state["user_question"],
            "key_terms": [],
            "search_queries": [
                state["user_question"]
            ]
        }

        state["status"] = "research_failed"

    return state
