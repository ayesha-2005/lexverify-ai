import sys
import os
import time
from io import BytesIO

# Ensure project root is in sys.path for Streamlit Cloud deployment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

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

if "submitted_query" not in st.session_state:
    st.session_state.submitted_query = ""

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

        # Clear old result immediately
        st.session_state.pipeline_state = None
        st.session_state.submitted_query = ""
        st.session_state.execution_time = None

        st.rerun()


with col2:
    if st.button(
        "🔴 Fake Citation Test",
        use_container_width=True
    ):
        st.session_state.user_query = (
            "What does PLD 2025 SC 999 say about bail?"
        )

        # Clear old result immediately
        st.session_state.pipeline_state = None
        st.session_state.submitted_query = ""
        st.session_state.execution_time = None

        st.rerun()


with col3:
    if st.button(
        "🌐 Out-of-Corpus Query",
        use_container_width=True
    ):
        st.session_state.user_query = (
            "What are foreign maritime tax rates?"
        )

        # Clear old result immediately
        st.session_state.pipeline_state = None
        st.session_state.submitted_query = ""
        st.session_state.execution_time = None

        st.rerun()


# =========================================================
# QUERY FORM
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

    # -----------------------------------------------------
    # IMPORTANT:
    # Clear the previous result BEFORE running a new query.
    # This prevents stale answers from appearing.
    # -----------------------------------------------------

    st.session_state.pipeline_state = None
    st.session_state.execution_time = None
    st.session_state.submitted_query = ""

    # Clean query
    submitted_query = user_question.strip()

    # Save the exact query being processed
    st.session_state.user_query = submitted_query
    st.session_state.submitted_query = submitted_query

    if not submitted_query:

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
                    submitted_query,
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
# PDF GENERATION FUNCTION
# =========================================================

def create_pdf_report(
    query,
    state,
    execution_time=None
):
    """
    Create a PDF report from the verified LexVerify pipeline result.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "LexVerifyTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "LexVerifyHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "LexVerifyBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        spaceAfter=7
    )

    small_style = ParagraphStyle(
        "LexVerifySmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        spaceAfter=5
    )

    story = []

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "⚖️ LexVerify AI",
            title_style
        )
    )

    story.append(
        Paragraph(
            "VERIFIED LEGAL RESEARCH REPORT",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 10))

    # -----------------------------------------------------
    # QUERY
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Legal Query",
            heading_style
        )
    )

    story.append(
        Paragraph(
            query,
            body_style
        )
    )

    # -----------------------------------------------------
    # EXECUTION INFORMATION
    # -----------------------------------------------------

    if execution_time is not None:

        story.append(
            Paragraph(
                f"Execution Time: {execution_time:.2f} seconds",
                small_style
            )
        )

    # -----------------------------------------------------
    # FINAL ANSWER
    # -----------------------------------------------------

    final_answer = state.get(
        "final_answer",
        ""
    )

    story.append(
        Paragraph(
            "Final Answer",
            heading_style
        )
    )

    if final_answer:

        # Convert newlines to HTML breaks for ReportLab
        formatted_answer = (
            str(final_answer)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

        story.append(
            Paragraph(
                formatted_answer,
                body_style
            )
        )

    else:

        story.append(
            Paragraph(
                "No final answer was generated.",
                body_style
            )
        )

    # -----------------------------------------------------
    # VERIFIED CITATIONS
    # -----------------------------------------------------

    verified_citations = state.get(
        "verified_citations",
        []
    )

    story.append(
        Paragraph(
            "Verified Citations",
            heading_style
        )
    )

    if verified_citations:

        citation_data = [
            [
                "Citation",
                "Case",
                "Court",
                "Year"
            ]
        ]

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

            else:

                citation_text = str(citation)
                title = "N/A"
                court = "N/A"
                year = "N/A"

            citation_data.append(
                [
                    str(citation_text),
                    str(title),
                    str(court),
                    str(year)
                ]
            )

        table = Table(
            citation_data,
            colWidths=[
                90,
                180,
                100,
                45
            ],
            repeatRows=1
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#E8F5E9")
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.black
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "FONTNAME",
                        (0, 1),
                        (-1, -1),
                        "Helvetica"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    ),
                ]
            )
        )

        story.append(table)

    else:

        story.append(
            Paragraph(
                "No verified citations found.",
                body_style
            )
        )

    # -----------------------------------------------------
    # REJECTED CITATIONS
    # -----------------------------------------------------

    rejected_citations = state.get(
        "rejected_citations",
        []
    )

    story.append(
        Paragraph(
            "Rejected Citations",
            heading_style
        )
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

            story.append(
                Paragraph(
                    f"✗ REJECTED — {citation_text}",
                    body_style
                )

    else:

        story.append(
            Paragraph(
                "No rejected citations.",
                body_style
            )
        )

    # -----------------------------------------------------
    # RETRIEVED EVIDENCE
    # -----------------------------------------------------

    retrieved_chunks = state.get(
        "retrieved_chunks",
        []
    )

    story.append(
        Paragraph(
            "Retrieved Evidence",
            heading_style
        )
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

            else:

                source = "Unknown source"
                text = str(chunk)

            story.append(
                Paragraph(
                    f"<b>Evidence {index}</b>",
                    body_style
                )
            )

            story.append(
                Paragraph(
                    f"<b>Source:</b> {source}",
                    small_style
                )
            )

            safe_text = (
                str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br/>")
            )

            story.append(
                Paragraph(
                    safe_text,
                    small_style
                )
            )

            story.append(Spacer(1, 5))

    else:

        story.append(
            Paragraph(
                "No retrieved evidence available.",
                body_style
            )
        )

    # -----------------------------------------------------
    # DISCLAIMER
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Disclaimer",
            heading_style
        )
    )

    story.append(
        Paragraph(
            "LexVerify AI is an AI-assisted legal research tool. "
            "Always verify legal information against official "
            "sources and consult a qualified legal professional "
            "when necessary.",
            small_style
        )
    )

    # -----------------------------------------------------
    # BUILD PDF
    # -----------------------------------------------------

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()


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
    # EXPORT VERIFIED REPORT
    # -----------------------------------------------------

    final_answer = state.get(
        "final_answer",
        ""
    )

    submitted_query = st.session_state.get(
        "submitted_query",
        ""
    )


    if final_answer and final_answer.strip():

        st.markdown(
            '<div class="section-title">📄 Export Report</div>',
            unsafe_allow_html=True
        )

        pdf_data = create_pdf_report(
            query=submitted_query,
            state=state,
            execution_time=st.session_state.execution_time
        )

        st.download_button(
            label="⬇️ Download Verified Report (.pdf)",
            data=pdf_data,
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