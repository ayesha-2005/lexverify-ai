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
from fpdf import FPDF

# =========================================================
# PDF HELPER FUNCTION
# =========================================================
# =========================================================
# PDF HELPER FUNCTION
# =========================================================

def generate_pdf_report(user_question, final_answer, verified_citations, rejected_citations, retrieved_chunks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Effective page width to prevent margin overflow errors
    epw = pdf.epw 
    
    # Title Header
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(epw, 10, "LEXVERIFY AI - VERIFIED LEGAL RESEARCH REPORT", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Legal Query
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(epw, 6, "LEGAL QUERY:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(epw, 6, user_question.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(4)
    
    # Final Answer
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(epw, 6, "FINAL LEGAL ANALYSIS:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(epw, 6, final_answer.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(4)
    
    # Verified Citations
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(epw, 6, "VERIFIED CITATIONS:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    if verified_citations:
        for c in verified_citations:
            if isinstance(c, dict):
                c_str = c.get('citation', c.get('title', str(c)))
            else:
                c_str = str(c)
            pdf.multi_cell(epw, 6, f"- [VERIFIED] {c_str}".encode('latin-1', 'replace').decode('latin-1'))
    else:
        pdf.multi_cell(epw, 6, "No verified citations found.")
    pdf.ln(4)

    # Rejected Citations (Fixed long-string parsing issue)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(epw, 6, "REJECTED CITATIONS:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    if rejected_citations:
        for c in rejected_citations:
            if isinstance(c, dict):
                c_str = c.get('citation', str(c))
            else:
                c_str = str(c)
            pdf.multi_cell(epw, 6, f"- [REJECTED] {c_str}".encode('latin-1', 'replace').decode('latin-1'))
    else:
        pdf.multi_cell(epw, 6, "No rejected citations.")
    pdf.ln(4)

    # Disclaimer
    pdf.set_font("Helvetica", style="I", size=8)
    pdf.multi_cell(epw, 5, "Disclaimer: LexVerify AI is an AI-assisted legal research tool. Always verify legal information against official sources.")
    
    return bytes(pdf.output())


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
# INITIALIZE SESSION STATE
# =========================================================

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = None

if "execution_time" not in st.session_state:
    st.session_state.execution_time = None


# =========================================================
# SAMPLE QUERIES
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
# QUERY INPUT
# =========================================================

st.markdown(
    '<div class="query-card">',
    unsafe_allow_html=True
)

user_question = st.text_input(
    "Enter your legal query:",
    key="user_query",
    placeholder=(
        "e.g. What is the bail standard in non-bailable offenses?"
    ),
    label_visibility="collapsed"
)

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# SEARCH BUTTON
# =========================================================

search_col1, search_col2, search_col3 = st.columns(
    [1, 2, 1]
)

with search_col2:

    search_clicked = st.button(
        "🔍 Search & Verify",
        type="primary",
        use_container_width=True
    )


# =========================================================
# PIPELINE EXECUTION
# =========================================================

if search_clicked:

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

                # Required backend integration
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

            st.error(
                "LexVerify pipeline encountered an error."
            )

            st.exception(e)

            state = None


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
    # AGENT WORKFLOW
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
    # VERIFICATION SUMMARY
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
    # EXPORT VERIFIED REPORT (PDF)
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

        pdf_bytes = generate_pdf_report(
            user_question=user_question,
            final_answer=final_answer,
            verified_citations=verified_citations,
            rejected_citations=rejected_citations,
            retrieved_chunks=retrieved_chunks
        )

        st.download_button(
            label="⬇️ Download Verified Report (.pdf)",
            data=pdf_bytes,
            file_name="lexverify_verified_report.pdf",
            mime="application/pdf",
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