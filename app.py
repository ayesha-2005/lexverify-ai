import sys
import os

# Ensure project root is in sys.path for Streamlit Cloud deployment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from src.orchestrator import run_lexverify_pipeline
from src.ui.components import (
    load_custom_css,
    render_header,
    render_agent_status,
    render_verification_summary,
    render_response_panel,
    render_engine_metrics,
    render_execution_time,
    render_footer,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# GROQ CLIENT
# =========================================================

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="LexVerify AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# LOAD UI
# =========================================================

load_custom_css()

render_engine_metrics()
render_header()


# =========================================================
# SESSION STATE
# =========================================================

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = None

if "execution_time" not in st.session_state:
    st.session_state.execution_time = None


# =========================================================
# QUESTION SECTION
# =========================================================

st.markdown(
    '<div class="section-title">🔎 Ask a Legal Question</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="section-description">
        Enter a Pakistani legal research question or try one of the
        demo scenarios below.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SAMPLE QUERIES
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "⚖️ Bail Standards",
        use_container_width=True
    ):
        st.session_state.user_query = (
            "What is the bail standard in non-bailable offenses?"
        )
        st.rerun()


with col2:
    if st.button(
        "🔴 Fake Citation Test",
        use_container_width=True
    ):
        st.session_state.user_query = (
            "Check precedent PLD 2025 SC 999"
        )
        st.rerun()


with col3:
    if st.button(
        "🌐 Out-of-Corpus Query",
        use_container_width=True
    ):
        st.session_state.user_query = (
            "What are foreign maritime tax rates?"
        )
        st.rerun()


# =========================================================
# QUERY FORM
# ENTER KEY ALSO SUBMITS THE FORM
# =========================================================

with st.form(
    key="legal_query_form",
    clear_on_submit=False
):

    user_question = st.text_input(
        "Enter your legal query:",
        value=st.session_state.user_query,
        placeholder=(
            "e.g. What is the bail standard in non-bailable offenses?"
        ),
        label_visibility="collapsed"
    )

    search_clicked = st.form_submit_button(
        "🔍 Search & Verify",
        type="primary",
        use_container_width=True
    )


# =========================================================
# PIPELINE EXECUTION
# =========================================================

if search_clicked:

    # Save latest query
    st.session_state.user_query = user_question

    if not user_question.strip():

        st.warning(
            "Please enter a legal question first."
        )

    else:

        start_time = time.perf_counter()

        try:

            with st.spinner(
                "Running Research → Retrieval → "
                "Verification → Synthesis..."
            ):

                state = run_lexverify_pipeline(
                    user_question,
                    client
                )

            execution_time = (
                time.perf_counter() - start_time
            )

            st.session_state.pipeline_state = state
            st.session_state.execution_time = execution_time

        except Exception as e:

            execution_time = (
                time.perf_counter() - start_time
            )

            st.session_state.execution_time = execution_time
            st.session_state.pipeline_state = None

            st.error(
                "LexVerify pipeline encountered an error."
            )

            st.exception(e)


# =========================================================
# DISPLAY RESULTS
# =========================================================

state = st.session_state.pipeline_state


if state is not None:

    # -----------------------------------------------------
    # EXECUTION TIMER
    # -----------------------------------------------------

    if st.session_state.execution_time is not None:

        render_execution_time(
            st.session_state.execution_time
        )


    # -----------------------------------------------------
    # AGENT WORKFLOW STATUS
    # -----------------------------------------------------

    status = {
        "research": "completed",
        "retrieval": "completed",
        "verification": "completed",
        "synthesis": "completed",
    }

    pipeline_status = state.get(
        "status",
        ""
    )


    if pipeline_status == "research_failed":

        status = {
            "research": "failed",
            "retrieval": "pending",
            "verification": "pending",
            "synthesis": "pending",
        }


    elif pipeline_status == "retrieval_failed":

        status = {
            "research": "completed",
            "retrieval": "failed",
            "verification": "pending",
            "synthesis": "pending",
        }


    elif pipeline_status == "verification_failed":

        status = {
            "research": "completed",
            "retrieval": "completed",
            "verification": "failed",
            "synthesis": "pending",
        }


    elif pipeline_status == "synthesis_failed":

        status = {
            "research": "completed",
            "retrieval": "completed",
            "verification": "completed",
            "synthesis": "failed",
        }


    render_agent_status(status)


    # -----------------------------------------------------
    # DATA FROM PIPELINE
    # -----------------------------------------------------

    verified_citations = state.get(
        "verified_citations",
        []
    )

    rejected_citations = state.get(
        "rejected_citations",
        []
    )

    retrieved_chunks = state.get(
        "retrieved_chunks",
        []
    )


    # -----------------------------------------------------
    # VERIFICATION SUMMARY
    # -----------------------------------------------------

    render_verification_summary(
        verified_count=len(verified_citations),
        rejected_count=len(rejected_citations),
        evidence_count=len(retrieved_chunks)
    )


    # -----------------------------------------------------
    # RESPONSE PANEL
    # -----------------------------------------------------

    render_response_panel(state)


    # -----------------------------------------------------
    # EXPORT VERIFIED REPORT (TXT)
    # -----------------------------------------------------

    final_answer = state.get(
        "final_answer",
        ""
    )


    if final_answer and final_answer.strip():

        st.markdown(
            '<div class="section-title">📄 Export Report</div>',
            unsafe_allow_html=True
        )


        report_lines = []

        report_lines.append(
            "LEXVERIFY AI — VERIFIED LEGAL RESEARCH REPORT"
        )

        report_lines.append(
            "=" * 55
        )

        report_lines.append("")

        report_lines.append(
            f"Legal Query: {user_question}"
        )

        report_lines.append("")

        report_lines.append(
            "FINAL ANSWER"
        )

        report_lines.append(
            "-" * 55
        )

        report_lines.append(
            final_answer
        )

        report_lines.append("")


        # -------------------------------------------------
        # VERIFIED CITATIONS
        # -------------------------------------------------

        report_lines.append(
            "VERIFIED CITATIONS"
        )

        report_lines.append(
            "-" * 55
        )


        if verified_citations:

            for citation in verified_citations:

                if isinstance(citation, dict):

                    citation_text = citation.get(
                        "citation",
                        "Unknown citation"
                    )

                    title = citation.get(
                        "title",
                        citation.get(
                            "case_name",
                            "Unknown Case"
                        )
                    )

                    court = citation.get(
                        "court",
                        "Unknown Court"
                    )

                    year = citation.get(
                        "year",
                        "N/A"
                    )

                    report_lines.append(
                        f"✓ VERIFIED — {citation_text}"
                    )

                    report_lines.append(
                        f"Case: {title}"
                    )

                    report_lines.append(
                        f"Court: {court}"
                    )

                    report_lines.append(
                        f"Year: {year}"
                    )

                    report_lines.append("")

                else:

                    report_lines.append(
                        f"✓ VERIFIED — {citation}"
                    )

        else:

            report_lines.append(
                "No verified citations found."
            )


        # -------------------------------------------------
        # REJECTED CITATIONS
        # -------------------------------------------------

        report_lines.append("")

        report_lines.append(
            "REJECTED CITATIONS"
        )

        report_lines.append(
            "-" * 55
        )


        if rejected_citations:

            for citation in rejected_citations:

                if isinstance(citation, dict):

                    citation_text = citation.get(
                        "citation",
                        str(citation)
                    )

                else:

                    citation_text = str(citation)

                report_lines.append(
                    f"✗ REJECTED — {citation_text}"
                )

        else:

            report_lines.append(
                "No rejected citations."
            )


        # -------------------------------------------------
        # RETRIEVED EVIDENCE
        # -------------------------------------------------

        report_lines.append("")

        report_lines.append(
            "RETRIEVED EVIDENCE"
        )

        report_lines.append(
            "-" * 55
        )


        if retrieved_chunks:

            for index, chunk in enumerate(
                retrieved_chunks,
                start=1
            ):

                if isinstance(chunk, dict):

                    source = chunk.get(
                        "source_file",
                        chunk.get(
                            "source_doc",
                            "Unknown source"
                        )
                    )

                    text = chunk.get(
                        "text",
                        ""
                    )

                    report_lines.append(
                        f"Evidence {index}"
                    )

                    report_lines.append(
                        f"Source: {source}"
                    )

                    report_lines.append(
                        text
                    )

                    report_lines.append("")

                else:

                    report_lines.append(
                        f"Evidence {index}:"
                    )

                    report_lines.append(
                        str(chunk)
                    )

                    report_lines.append("")

        else:

            report_lines.append(
                "No retrieved evidence available."
            )


        # -------------------------------------------------
        # DISCLAIMER
        # -------------------------------------------------

        report_lines.append("")

        report_lines.append(
            "DISCLAIMER"
        )

        report_lines.append(
            "-" * 55
        )

        report_lines.append(
            "LexVerify AI is an AI-assisted legal research tool. "
            "Always verify legal information against official "
            "sources and consult a qualified legal professional "
            "when necessary."
        )


        report_content = "\n".join(
            report_lines
        )


        st.download_button(
            label="⬇️ Download Verified Report (.txt)",
            data=report_content,
            file_name="lexverify_verified_report.txt",
            mime="text/plain",
            use_container_width=True
        )


    # -----------------------------------------------------
    # DISCLAIMER
    # -----------------------------------------------------

    st.info(
        "⚖️ LexVerify AI is an AI-assisted legal research tool. "
        "Always verify legal information against official sources "
        "and consult a qualified legal professional when necessary."
    )


# =========================================================
# FOOTER
# =========================================================

render_footer()
