import json
import re

from openai import OpenAI
from src.state import AgentState


# ============================================================
# Deterministic Source Classification
# ============================================================

def deterministic_source_classification(
    user_question: str
) -> str:
    """
    Deterministically classify the primary legal source needed
    for the user's question.

    Possible results:
        - statute
        - constitution
        - case_law
        - mixed

    This function only controls retrieval classification.
    It does NOT answer the legal question.
    """

    question = str(
        user_question or ""
    ).strip().lower()

    # --------------------------------------------------------
    # Constitution indicators
    # --------------------------------------------------------

    constitution_patterns = [
        r"\bconstitution\b",
        r"\bconstitutional\b",
        r"\barticle\s+\d+\b",
        r"\bfundamental\s+rights?\b",
        r"\bconstitutional\s+right\b",
    ]

    has_constitution = any(
        re.search(pattern, question)
        for pattern in constitution_patterns
    )

    # --------------------------------------------------------
    # Statute indicators
    # --------------------------------------------------------

    statute_patterns = [
        r"\bsection\s+\d+[a-z]?\b",
        r"\bsec\.\s*\d+[a-z]?\b",
        r"\bact\b",
        r"\bcode\b",
        r"\bstatute\b",
        r"\bstatutory\b",
        r"\bprovision\b",
        r"\bprovisions\b",
        r"\blaw\s+provides\b",
        r"\bwhat\s+does\s+.*\s+say\b",
    ]

    has_statute = any(
        re.search(pattern, question)
        for pattern in statute_patterns
    )

    # --------------------------------------------------------
    # Known Pakistani statutes / legal instruments
    # --------------------------------------------------------

    known_statutes = [
        "criminal procedure code",
        "code of criminal procedure",
        "crpc",
        "pakistan penal code",
        "penal code",
        "ppc",
        "qanoon-e-shahadat",
        "qso",
        "contract act",
        "companies act",
        "limitation act",
        "specific relief act",
        "transfer of property act",
        "family courts act",
        "arbitration act",
        "supreme court practice and procedure act",
    ]

    has_known_statute = any(
        term in question
        for term in known_statutes
    )

    # --------------------------------------------------------
    # Case-law indicators
    # --------------------------------------------------------

    case_law_patterns = [
        r"\bcase law\b",
        r"\bcase-law\b",
        r"\bcourt[s]?\b",
        r"\bjudgment[s]?\b",
        r"\bjudicial\b",
        r"\bjudge[s]?\b",
        r"\bdecision[s]?\b",
        r"\bheld\b",
        r"\bholding\b",
        r"\bprecedent[s]?\b",
        r"\bauthorit(?:y|ies)\b",
        r"\bwhat\s+have\s+pakistani\s+courts\b",
        r"\bwhat\s+do\s+pakistani\s+courts\b",
    ]

    has_case_law = any(
        re.search(pattern, question)
        for pattern in case_law_patterns
    )

    # --------------------------------------------------------
    # Deterministic classification priority
    # --------------------------------------------------------

    # Constitution + court/case-law language means both
    # constitutional material and judicial interpretation
    # may be relevant.
    if has_constitution and has_case_law:
        return "mixed"

    if has_constitution:
        return "constitution"

    # Explicit statute + court language means both primary
    # statutory law and case law may be relevant.
    if (
        (has_statute or has_known_statute)
        and has_case_law
    ):
        return "mixed"

    if has_statute or has_known_statute:
        return "statute"

    if has_case_law:
        return "case_law"

    # Conservative default when no strong signal exists.
    return "mixed"


# ============================================================
# Research Agent
# ============================================================

def run_research_agent(
    state: AgentState,
    client: OpenAI
) -> AgentState:
    """
    Agent 1: Research Agent.

    Analyzes the user's legal question and generates
    source-aware semantic search queries.

    The agent identifies whether the question is primarily about:
        - statute
        - constitution
        - case law
        - mixed legal sources

    A deterministic classifier acts as a safety fallback
    when the LLM classification is missing, invalid, or
    inconsistent with explicit source signals in the question.

    IMPORTANT:
    This agent must NEVER invent legal citations.
    """

    system_prompt = """
You are the LexVerify AI Research Agent specializing in Pakistani law.

Your task is to analyze the user's legal research question and convert it
into structured retrieval parameters.

The legal corpus contains three source types:

1. STATUTE
   Examples:
   - Code of Criminal Procedure, 1898
   - Pakistan Penal Code, 1860
   - Contract Act, 1872
   - other Pakistani Acts and statutes

2. CONSTITUTION
   - Constitution of Pakistan, 1973

3. CASE LAW
   - Pakistani court judgments and judicial decisions

STRICT RULES:

1. DO NOT invent legal citations.

2. DO NOT provide case names unless they are explicitly present
   in the user's question.

3. DO NOT answer the legal question.

4. Identify the primary source type needed to answer the question.

5. Use:
   - "statute" when the question asks what a section, Act, Code,
     statutory provision, or law says.
   - "constitution" when the question asks about a constitutional
     provision, constitutional right, or the Constitution.
   - "case_law" when the question specifically asks about court
     decisions, judicial principles, holdings, or what courts have
     applied.
   - "mixed" when both statutory/constitutional law and judicial
     decisions are useful.

6. Search queries must be semantic and must help the retrieval system
   find the relevant evidence in the legal corpus.

7. For STATUTE questions, include at least one query explicitly using
   the name of the relevant Act/Code and section if that information
   is present in the user's question.

8. For CONSTITUTION questions, include at least one query explicitly
   referring to the Constitution of Pakistan and the relevant article
   if present.

9. For CASE LAW questions, generate queries focused on Pakistani
   judicial decisions and legal principles.

10. For MIXED questions, generate queries covering both the primary
    legal source and relevant Pakistani case law.

11. Do not assume that a legal provision exists if the user did not
    mention it.

12. Do not invent section numbers, article numbers, case names,
    citations, courts, or years.

13. Generate 2-3 strong search queries.

14. Return ONLY valid JSON.

Required JSON structure:

{
    "legal_intent": "short summary of the legal issue",
    "source_type": "statute | constitution | case_law | mixed",
    "key_terms": ["keyword1", "keyword2"],
    "search_queries": [
        "semantic search query 1",
        "semantic search query 2",
        "semantic search query 3"
    ]
}

IMPORTANT:

The "source_type" is a retrieval classification only.
It is NOT a legal conclusion.

For example:

Question:
"What does section 497 of the Criminal Procedure Code say about bail?"

Good output:
{
    "legal_intent": "bail under section 497 of the Criminal Procedure Code",
    "source_type": "statute",
    "key_terms": [
        "section 497",
        "bail",
        "Criminal Procedure Code"
    ],
    "search_queries": [
        "Section 497 Code of Criminal Procedure 1898 bail",
        "Code of Criminal Procedure 1898 section 497 provisions on bail",
        "section 497 criminal procedure bail"
    ]
}

Do not answer the question itself.
"""

    # --------------------------------------------------------
    # Safe defaults
    # --------------------------------------------------------

    legal_intent = state["user_question"]
    source_type = "mixed"
    key_terms = []
    search_queries = []

    try:

        # ====================================================
        # LLM Research
        # ====================================================

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
            temperature=0.1
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Research Agent returned an empty response."
            )

        # ----------------------------------------------------
        # Clean possible markdown JSON fences
        # ----------------------------------------------------

        content = content.strip()

        if content.startswith("```"):
            content = content.replace(
                "```json",
                ""
            )
            content = content.replace(
                "```",
                ""
            )
            content = content.strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        research_plan = json.loads(content)

        if not isinstance(research_plan, dict):
            raise ValueError(
                "Research Agent response is not a JSON object."
            )

        # ----------------------------------------------------
        # Read fields
        # ----------------------------------------------------

        legal_intent = research_plan.get(
            "legal_intent",
            state["user_question"]
        )

        llm_source_type = research_plan.get(
            "source_type"
        )

        key_terms = research_plan.get(
            "key_terms",
            []
        )

        search_queries = research_plan.get(
            "search_queries",
            []
        )

        # ====================================================
        # Deterministic Source Classification
        # ====================================================

        deterministic_type = (
            deterministic_source_classification(
                state["user_question"]
            )
        )

        allowed_source_types = {
            "statute",
            "constitution",
            "case_law",
            "mixed"
        }

        # ----------------------------------------------------
        # If LLM classification is invalid/missing,
        # use deterministic classification.
        # ----------------------------------------------------

        if llm_source_type not in allowed_source_types:

            source_type = deterministic_type

        else:

            source_type = llm_source_type

        # ----------------------------------------------------
        # Explicit statute/constitution signals override
        # an incompatible LLM classification.
        # ----------------------------------------------------

        if deterministic_type in {
            "statute",
            "constitution"
        }:

            source_type = deterministic_type

        # ----------------------------------------------------
        # Mixed classification from deterministic analysis
        # should not be silently discarded.
        # ----------------------------------------------------

        elif deterministic_type == "mixed":

            if llm_source_type in allowed_source_types:
                source_type = llm_source_type
            else:
                source_type = "mixed"

        # ----------------------------------------------------
        # Case-law deterministic classification
        # ----------------------------------------------------

        elif deterministic_type == "case_law":

            if llm_source_type in allowed_source_types:
                source_type = llm_source_type
            else:
                source_type = "case_law"

        # ====================================================
        # Validate key terms
        # ====================================================

        if not isinstance(
            key_terms,
            list
        ):
            key_terms = []

        key_terms = [
            str(term).strip()
            for term in key_terms
            if str(term).strip()
        ]

        # ====================================================
        # Validate search queries
        # ====================================================

        if not isinstance(
            search_queries,
            list
        ):
            search_queries = []

        search_queries = [
            str(q).strip()
            for q in search_queries
            if str(q).strip()
        ]

        # ----------------------------------------------------
        # Guaranteed fallback query
        # ----------------------------------------------------

        if not search_queries:

            search_queries = [
                state["user_question"]
            ]

        # ====================================================
        # Final Research Plan
        # ====================================================

        research_plan = {
            "legal_intent": str(
                legal_intent
            ),
            "source_type": source_type,
            "key_terms": key_terms,
            "search_queries": search_queries[:3]
        }

        state["research_plan"] = research_plan
        state["extracted_keywords"] = key_terms
        state["status"] = "research_completed"

        print(
            "RESEARCH COMPLETED:",
            research_plan
        )

    except Exception as e:

        # ====================================================
        # Deterministic fallback when LLM research fails
        # ====================================================

        source_type = (
            deterministic_source_classification(
                state["user_question"]
            )
        )

        if not search_queries:
            search_queries = [
                state["user_question"]
            ]

        print(
            "RESEARCH ERROR:",
            str(e)
        )

        state["errors"].append(
            f"Research Agent Error: {str(e)}"
        )

        state["research_plan"] = {
            "legal_intent": str(
                legal_intent
            ),
            "source_type": source_type,
            "key_terms": key_terms,
            "search_queries": search_queries[:3]
        }

        state["extracted_keywords"] = key_terms

        state["status"] = "research_failed"

    return state

