import json
import os
from openai import OpenAI
from src.state import AgentState

def run_research_agent(state: AgentState, client: OpenAI) -> AgentState:
    """
    Analyzes user question, identifies legal intent, and generates search queries
    without generating fake citations.
    """
    system_prompt = (
        "You are the LexVerify AI Research Agent specializing in Pakistani Case Law.\n"
        "Your job is to analyze the user's legal question and break it down into structured research parameters.\n"
        "CRITICAL RULE: DO NOT invent, generate, or assume any legal citations (e.g., PLD, SCMR, CLC).\n"
        "Return ONLY a valid JSON object with the following keys:\n"
        "  'legal_intent': Short summary of the legal issue\n"
        "  'key_terms': Array of legal keywords\n"
        "  'search_queries': Array of 2-3 semantic search strings optimized for vector retrieval\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state["user_question"]}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        research_plan = json.loads(content)
        
        state["research_plan"] = research_plan
        state["status"] = "research_completed"
        
    except Exception as e:
        state["errors"].append(f"Research Agent Error: {str(e)}")
        state["research_plan"] = {
            "legal_intent": state["user_question"],
            "key_terms": [],
            "search_queries": [state["user_question"]]
        }
        state["status"] = "research_failed"
        
    return state