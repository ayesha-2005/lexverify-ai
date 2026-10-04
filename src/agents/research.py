"""
Research Agent for LexVerify AI.

Responsibilities:
- Understand the user's legal question.
- Determine the appropriate legal source type.
- Extract useful legal keywords.
- Generate search queries for the retrieval agent.
- Keep source classification deterministic for important legal patterns.
"""

import json
import re
from typing import Any, Dict

from openai import OpenAI


MODEL_NAME = "openai/gpt-oss-20b"


def deterministic_source_classification(question: str) -> str:
    """
    Deterministically classify the legal question into:

    - statute
    - constitution
    - case_law
    - mixed

    Deterministic rules are used to prevent the LLM from choosing an
    inappropriate source type for obvious legal questions.
    """

    q = question.lower().strip()

    # ---------------------------------------------------------
    # SPECIAL CASE: comparative pre-arrest vs post-arrest bail
    # ---------------------------------------------------------
    # These questions need both statutory material and case law.
    if (
        "pre-arrest bail" in q
        and "post-arrest bail" in q
        and any(
            word in q
            for word in [
                "difference",
                "compare",
                "comparison",
                "versus",
                "vs",
            ]
        )
    ):
        return "mixed"

    # ---------------------------------------------------------
    # Constitution signals
    # ---------------------------------------------------------
    constitution_patterns = [
        "constitution",
        "constitutional",
        "article ",
        "fundamental rights",
        "constitutional right",
    ]

    # ---------------------------------------------------------
    # Statute signals
    # ---------------------------------------------------------
    statute_patterns = [
        "section ",
        "section",
        "sec ",
        "act ",
        "statute",
        "provision",
        "provisions",
        "code",
        "law provides",
        "what does",
        "what is section",
    ]

    # ---------------------------------------------------------
    # Known Pakistani statutes
    # ---------------------------------------------------------
    known_statutes = [
        "criminal procedure code",
        "code of criminal procedure",
        "cr.p.c",
        "crpc",
        "pakistan penal code",
        "penal code",
        "ppc",
        "qanoon-e-shahadat",
        "qanoon e shahadat",
        "evidence act",
        "anti-terrorism act",
        "narcotic",
        "control of narcotic substances",
        "nab ordinance",
        "prevention of electronic crimes",
        "peco",
    ]

    # ---------------------------------------------------------
    # Case-law signals
    # ---------------------------------------------------------
    case_law_patterns = [
        "case law",
        "case-law",
        "court",
        "courts",
        "judgment",
        "judgments",
        "judicial",
        "judge",
        "judges",
        "decision",
        "decisions",
        "held",
        "holding",
        "precedent",
        "authority",
        "authorities",
        "what have pakistani courts",
        "what do pakistani courts",
    ]

    has_constitution = any(
        pattern in q for pattern in constitution_patterns
    )

    has_statute = (
        any(pattern in q for pattern in statute_patterns)
        or any(statute in q for statute in known_statutes)
    )

    has_case_law = any(
        pattern in q for pattern in case_law_patterns
    )

    # ---------------------------------------------------------
    # Classification priority
    # ---------------------------------------------------------

    if has_constitution and has_case_law:
        return "mixed"

    if has_constitution:
        return "constitution"

    if has_statute and has_case_law:
        return "mixed"

    if has_statute:
        return "statute"

    if has_case_law:
        return "case_law"

    # When the question is ambiguous, allow retrieval to search
    # across the legal corpus.
    return "mixed"


def _clean_search_queries(queries: Any) -> list:
    """
    Clean and deduplicate search queries.
    """

    if not isinstance(queries, list):
        return []

    cleaned = []

    for query in queries:
        if not isinstance(query, str):
            continue

        query = re.sub(r"\s+", " ", query).strip()

        if not query:
            continue

        if query not in cleaned:
            cleaned.append(query)

    return cleaned[:3]


def _clean_key_terms(key_terms: Any) -> list:
    """
    Clean and deduplicate extracted legal keywords.
    """

    if not isinstance(key_terms, list):
        return []

    cleaned = []

    for term in key_terms:
        if not isinstance(term, str):
            continue

        term = re.sub(r"\s+", " ", term).strip()

        if not term:
            continue

        if term not in cleaned:
            cleaned.append(term)

    return cleaned[:15]


def _extract_json(content: str) -> Dict[str, Any]:
    """
    Safely extract a JSON object from an LLM response.
    """

    content = content.strip()

    # Remove markdown fences if the model added them.
    content = re.sub(
        r"^```(?:json)?\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"\s*```$",
        "",
        content,
        flags=re.IGNORECASE,
    )

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try extracting the first JSON object from surrounding text.
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def _fallback_research_plan(question: str) -> Dict[str, Any]:
    """
    Deterministic fallback when the LLM cannot produce a valid plan.
    """

    source_type = deterministic_source_classification(question)

    return {
        "legal_intent": question,
        "source_type": source_type,
        "key_terms": [
            term
            for term in [
                "Pakistan",
                "law",
                "legal",
                "bail",
            ]
            if term.lower() in question.lower()
            or term in ["Pakistan", "law", "legal"]
        ],
        "search_queries": [
            question,
            f"{question} Pakistan law",
            f"{question} Pakistani legal provisions",
        ],
    }


def run_research_agent(
    state: Dict[str, Any],
    client: OpenAI,
) -> Dict[str, Any]:
    """
    Run the Research Agent.

    The LLM creates the initial research plan, while deterministic
    classification overrides source_type when the user's question
    contains strong legal signals.
    """

    question = state["user_question"]

    deterministic_source_type = deterministic_source_classification(
        question
    )

    system_prompt = """
You are the Research Agent for LexVerify AI, a Pakistani legal
research system.

Your job is to analyze the user's legal question and produce a
structured research plan.

Return ONLY valid JSON with exactly these fields:

{
  "legal_intent": "short description of what the user wants",
  "source_type": "statute | constitution | case_law | mixed",
  "key_terms": ["important legal terms"],
  "search_queries": [
    "strong retrieval query 1",
    "strong retrieval query 2",
    "strong retrieval query 3"
  ]
}

Rules:

1. Do not invent case names.
2. Do not invent citations.
3. Do not invent section numbers.
4. Use Pakistani legal terminology where appropriate.
5. Generate 2-3 strong retrieval queries.
6. Search queries should contain the important legal concepts.
7. If the question requires both statutory law and judicial interpretation,
   use "mixed".
8. Keep key_terms concise.
9. Return JSON only.
"""

    user_prompt = f"""
User's legal question:

{question}

Prepare the research plan.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content or ""

        plan = _extract_json(content)

        if not plan:
            plan = _fallback_research_plan(question)

        legal_intent = str(
            plan.get("legal_intent") or question
        ).strip()

        llm_source_type = str(
            plan.get("source_type") or ""
        ).strip().lower()

        valid_source_types = {
            "statute",
            "constitution",
            "case_law",
            "mixed",
        }

        if llm_source_type not in valid_source_types:
            llm_source_type = deterministic_source_type

        # -----------------------------------------------------
        # IMPORTANT:
        # Deterministic classification wins over the LLM when
        # the question has a clear legal source signal.
        # -----------------------------------------------------
        if deterministic_source_type != "mixed":
            source_type = deterministic_source_type
        else:
            # For mixed questions, preserve the deterministic
            # mixed classification.
            source_type = "mixed"

        key_terms = _clean_key_terms(
            plan.get("key_terms", [])
        )

        search_queries = _clean_search_queries(
            plan.get("search_queries", [])
        )

        # Fallback if the LLM returned empty arrays.
        if not key_terms:
            fallback_plan = _fallback_research_plan(question)
            key_terms = fallback_plan["key_terms"]

        if not search_queries:
            fallback_plan = _fallback_research_plan(question)
            search_queries = fallback_plan["search_queries"]

        # Ensure the user's original question remains searchable.
        if question not in search_queries:
            search_queries.insert(0, question)

        search_queries = search_queries[:3]

        research_plan = {
            "legal_intent": legal_intent,
            "source_type": source_type,
            "key_terms": key_terms,
            "search_queries": search_queries,
        }

        state["research_plan"] = research_plan
        state["extracted_keywords"] = key_terms
        state["status"] = "research_completed"

        return state

    except Exception as exc:
        fallback_plan = _fallback_research_plan(question)

        state["research_plan"] = fallback_plan
        state["extracted_keywords"] = fallback_plan["key_terms"]
        state.setdefault("errors", []).append(
            f"Research Agent fallback: {str(exc)}"
        )
        state["status"] = "research_completed"

        return state