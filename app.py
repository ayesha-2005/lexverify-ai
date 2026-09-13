import sys
import os
import time
from io import BytesIO

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

# =========================================================
# PATH SETUP
# =========================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()


# =========================================================
# PROJECT IMPORTS
# =========================================================

from src.orchestrator import run_lexverify_pipeline


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="LexVerify AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 25px;
    }

    .verified-box {
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        background-color: #f3fff5;
        margin-bottom: 10px;
    }

    .rejected-box {
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
        background-color: #fff5f5;
        margin-bottom: 10px;
    }

    .answer-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        line-height: 1.7;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LOCAL UI FUNCTIONS
# =========================================================
# These functions were previously imported from
# src.ui.components.
# They are now inside app.py so Streamlit Cloud does not
# depend on that module.

def render_header():
    """Render application header."""

    st.markdown(
        '<div class="main-title">⚖️ LexVerify AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Research. Retrieve. Verify. Respond."
        "</div>",
        unsafe_allow_html=True,
    )


def render_workflow_status(state):
    """Render four-agent workflow status."""

    research_completed = state.get(
        "research_completed",
        False,
    )

    retrieval_completed = state.get(
        "retrieval_completed",
        False,
    )

    verification_completed = state.get(
        "verification_completed",
        False,
    )

    synthesis_completed = state.get(
        "synthesis_completed",
        False,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Research",
            "✓ Completed"
            if research_completed
            else "Pending",
        )

    with col2:
        st.metric(
            "Retrieval",
            "✓ Completed"
            if retrieval_completed
            else "Pending",
        )

    with col3:
        st.metric(
            "Verification",
            "✓ Completed"
            if verification_completed
            else "Pending",
        )

    with col4:
        st.metric(
            "Synthesis",
            "✓ Completed"
            if synthesis_completed
            else "Pending",
        )


def render_verification_summary(state):
    """Render citation verification summary."""

    verified = state.get(
        "verified_citations",
        [],
    )

    rejected = state.get(
        "rejected_citations",
        [],
    )

    evidence = state.get(
        "retrieved_chunks",
        [],
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Verified",
            len(verified),
        )

    with col2:
        st.metric(
            "Rejected",
            len(rejected),
        )

    with col3:
        st.metric(
            "Evidence Chunks",
            len(evidence),
        )


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
# OPENAI / GROQ CLIENT
# =========================================================

def create_groq_client():
    """
    Create an OpenAI-compatible client connected to Groq.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )


# =========================================================
# PDF GENERATION
# =========================================================

def create_pdf_report(
    query,
    state,
    execution_time=None,
):
    """
    Generate a PDF research report containing:

    - Legal query
    - Final answer
    - Verified citations
    - Rejected citations
    - Retrieved evidence
    - Disclaimer
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "LexVerifyTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=26,
        spaceAfter=15,
    )

    heading_style = ParagraphStyle(
        "LexVerifyHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "LexVerifyBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        spaceAfter=8,
    )

    small_style = ParagraphStyle(
        "LexVerifySmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.grey,
    )

    story = []

    # =====================================================
    # TITLE
    # =====================================================

    story.append(
        Paragraph(
            "LexVerify AI",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Research. Retrieve. Verify. Respond.",
            small_style,
        )
    )

    story.append(
        Spacer(1, 15)
    )

    # =====================================================
    # LEGAL QUERY
    # =====================================================

    story.append(
        Paragraph(
            "Legal Query",
            heading_style,
        )
    )

    safe_query = (
        str(query)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    story.append(
        Paragraph(
            safe_query,
            body_style,
        )
    )

    if execution_time is not None:

        story.append(
            Paragraph(
                f"Execution Time: {execution_time:.2f} seconds",
                small_style,
            )
        )

    story.append(
        Spacer(1, 10)
    )

    # =====================================================
    # FINAL ANSWER
    # =====================================================

    story.append(
        Paragraph(
            "Final Answer",
            heading_style,
        )
    )

    final_answer = state.get(
        "final_answer",
        "",
    )

    if not final_answer:

        final_answer = (
            "No final answer was generated because the "
            "verification pipeline did not produce "
            "sufficient verified evidence."
        )

    safe_answer = (
        str(final_answer)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )

    story.append(
        Paragraph(
            safe_answer,
            body_style,
        )
    )

    # =====================================================
    # VERIFIED CITATIONS
    # =====================================================

    story.append(
        Paragraph(
            "Verified Citations",
            heading_style,
        )
    )

    verified_citations = state.get(
        "verified_citations",
        [],
    )

    if verified_citations:

        table_data = [
            [
                Paragraph(
                    "<b>Citation</b>",
                    body_style,
                ),
                Paragraph(
                    "<b>Case</b>",
                    body_style,
                ),
                Paragraph(
                    "<b>Court</b>",
                    body_style,
                ),
                Paragraph(
                    "<b>Year</b>",
                    body_style,
                ),
            ]
        ]

        for item in verified_citations:

            if not isinstance(item, dict):
                continue

            citation = item.get(
                "citation",
                "",
            )

            case_name = item.get(
                "case_name",
                "",
            )

            court = item.get(
                "court",
                "",
            )

            year = item.get(
                "year",
                "",
            )

            table_data.append(
                [
                    Paragraph(
                        str(citation),
                        body_style,
                    ),
                    Paragraph(
                        str(case_name),
                        body_style,
                    ),
                    Paragraph(
                        str(court),
                        body_style,
                    ),
                    Paragraph(
                        str(year),
                        body_style,
                    ),
                ]
            )

        if len(table_data) > 1:

            table = Table(
                table_data,
                colWidths=[
                    95,
                    190,
                    100,
                    45,
                ],
                repeatRows=1,
            )

            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.lightgrey,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                    ]
                )
            )

            story.append(table)

        else:

            story.append(
                Paragraph(
                    "No verified citations were available.",
                    body_style,
                )
            )

    else:

        story.append(
            Paragraph(
                "No verified citations were found.",
                body_style,
            )
        )

    # =====================================================
    # REJECTED CITATIONS
    # =====================================================

    story.append(
        Paragraph(
            "Rejected / Unverified Citations",
            heading_style,
        )
    )

    rejected_citations = state.get(
        "rejected_citations",
        [],
    )

    if rejected_citations:

        for item in rejected_citations:

            if isinstance(item, dict):

                citation_text = item.get(
                    "citation",
                    item.get(
                        "text",
                        str(item),
                    ),
                )

            else:

                citation_text = str(item)

            safe_citation = (
                str(citation_text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            story.append(
                Paragraph(
                    f"REJECTED — {safe_citation}",
                    body_style,
                )
            )

    else:

        story.append(
            Paragraph(
                "No rejected citations.",
                body_style,
            )
        )

    # =====================================================
    # RETRIEVED EVIDENCE
    # =====================================================

    story.append(
        Paragraph(
            "Retrieved Evidence",
            heading_style,
        )
    )

    evidence_chunks = state.get(
        "retrieved_chunks",
        [],
    )

    if evidence_chunks:

        for index, chunk in enumerate(
            evidence_chunks,
            start=1,
        ):

            if not isinstance(chunk, dict):
                continue

            source_file = chunk.get(
                "source_file",
                chunk.get(
                    "source",
                    "Unknown source",
                ),
            )

            text = chunk.get(
                "text",
                chunk.get(
                    "content",
                    "",
                ),
            )

            safe_source = (
                str(source_file)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
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
                    f"<b>Evidence {index}</b> — "
                    f"{safe_source}",
                    body_style,
                )
            )

            story.append(
                Paragraph(
                    safe_text,
                    body_style,
                )
            )

    else:

        story.append(
            Paragraph(
                "No retrieved evidence was available.",
                body_style,
            )
        )

    # =====================================================
    # DISCLAIMER
    # =====================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Disclaimer",
            heading_style,
        )
    )

    disclaimer = (
        "LexVerify AI is a legal research assistance tool. "
        "It does not provide legal advice and should not be "
        "treated as a substitute for professional legal "
        "judgment. Citations and evidence shown in this "
        "report are limited to the application's verified "
        "corpus."
    )

    story.append(
        Paragraph(
            disclaimer,
            body_style,
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    doc.build(story)

    return buffer.getvalue()


# =========================================================
# HEADER
# =========================================================

render_header()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚖️ LexVerify AI")

    st.markdown(
        """
        **Citation-grounded Pakistani legal research**

        The system retrieves evidence from the legal corpus,
        verifies citations against the Truth Registry,
        and only then generates the final response.
        """
    )

    st.divider()

    st.subheader("Demo Queries")

    bail_button = st.button(
        "Bail Standards",
        use_container_width=True,
    )

    fake_button = st.button(
        "Fake Citation Test",
        use_container_width=True,
    )

    corpus_button = st.button(
        "Out-of-Corpus Query",
        use_container_width=True,
    )

    st.divider()

    st.caption(
        "LexVerify AI • Hackathon Prototype"
    )


# =========================================================
# SAMPLE QUERY HANDLERS
# =========================================================

if bail_button:

    st.session_state.user_query = (
        "What is the bail standard in non-bailable offenses?"
    )

    st.session_state.submitted_query = ""
    st.session_state.pipeline_state = None
    st.session_state.execution_time = None

    st.rerun()


if fake_button:

    st.session_state.user_query = (
        "What does PLD 2025 SC 999 say about bail?"
    )

    st.session_state.submitted_query = ""
    st.session_state.pipeline_state = None
    st.session_state.execution_time = None

    st.rerun()


if corpus_button:

    st.session_state.user_query = (
        "What are foreign maritime tax rates?"
    )

    st.session_state.submitted_query = ""
    st.session_state.pipeline_state = None
    st.session_state.execution_time = None

    st.rerun()


# =========================================================
# MAIN INPUT
# =========================================================

st.subheader(
    "Ask a Legal Research Question"
)

user_question = st.text_area(
    "Enter your question",
    height=120,
    placeholder=(
        "Example: What are the principles governing "
        "bail in cases of prolonged detention?"
    ),
    key="user_query",
)


# =========================================================
# SEARCH BUTTON
# =========================================================

search_clicked = st.button(
    "🔎 Research & Verify",
    type="primary",
    use_container_width=True,
)


# =========================================================
# PIPELINE EXECUTION
# =========================================================

if search_clicked:

    submitted_query = (
        user_question.strip()
    )

    if not submitted_query:

        st.warning(
            "Please enter a legal research question."
        )

    else:

        # -------------------------------------------------
        # CLEAR PREVIOUS RESULTS
        # -------------------------------------------------

        st.session_state.pipeline_state = None
        st.session_state.execution_time = None
        st.session_state.submitted_query = ""

        st.session_state.user_query = submitted_query
        st.session_state.submitted_query = submitted_query

        # -------------------------------------------------
        # GROQ CLIENT
        # -------------------------------------------------

        client = create_groq_client()

        if client is None:

            st.error(
                "GROQ_API_KEY is not configured. "
                "Please add it to Streamlit Secrets."
            )

            st.stop()

        # -------------------------------------------------
        # RUN PIPELINE
        # -------------------------------------------------

        start_time = time.time()

        with st.spinner(
            "LexVerify AI is researching, retrieving, "
            "verifying and synthesizing..."
        ):

            try:

                state = run_lexverify_pipeline(
                    submitted_query,
                    client,
                )

                execution_time = (
                    time.time() - start_time
                )

                st.session_state.pipeline_state = state

                st.session_state.execution_time = (
                    execution_time
                )

            except Exception as exc:

                execution_time = (
                    time.time() - start_time
                )

                st.session_state.execution_time = (
                    execution_time
                )

                st.error(
                    f"Pipeline error: {exc}"
                )

                st.stop()


# =========================================================
# DISPLAY RESULTS
# =========================================================

state = st.session_state.pipeline_state


if state is not None:

    st.divider()

    # =====================================================
    # WORKFLOW STATUS
    # =====================================================

    st.subheader(
        "Agent Workflow"
    )

    render_workflow_status(
        state
    )

    # =====================================================
    # VERIFICATION SUMMARY
    # =====================================================

    st.divider()

    st.subheader(
        "Citation Verification"
    )

    render_verification_summary(
        state
    )

    # =====================================================
    # VERIFIED CITATIONS
    # =====================================================

    verified_citations = state.get(
        "verified_citations",
        [],
    )

    if verified_citations:

        st.subheader(
            "✅ Verified Citations"
        )

        for item in verified_citations:

            if not isinstance(item, dict):
                continue

            citation = item.get(
                "citation",
                "Unknown citation",
            )

            case_name = item.get(
                "case_name",
                "Unknown case",
            )

            court = item.get(
                "court",
                "Unknown court",
            )

            year = item.get(
                "year",
                "Unknown year",
            )

            st.markdown(
                f"""
                <div class="verified-box">

                <b>✓ {citation}</b><br>

                <b>Case:</b> {case_name}<br>

                <b>Court:</b> {court}<br>

                <b>Year:</b> {year}

                </div>
                """,
                unsafe_allow_html=True,
            )

    # =====================================================
    # REJECTED CITATIONS
    # =====================================================

    rejected_citations = state.get(
        "rejected_citations",
        [],
    )

    if rejected_citations:

        st.subheader(
            "❌ Rejected / Unverified Citations"
        )

        for item in rejected_citations:

            if isinstance(item, dict):

                citation = item.get(
                    "citation",
                    item.get(
                        "text",
                        str(item),
                    ),
                )

                reason = item.get(
                    "reason",
                    "Citation could not be verified.",
                )

            else:

                citation = str(item)

                reason = (
                    "Citation could not be verified."
                )

            st.markdown(
                f"""
                <div class="rejected-box">

                <b>✗ {citation}</b><br>

                {reason}

                </div>
                """,
                unsafe_allow_html=True,
            )

    # =====================================================
    # FINAL ANSWER
    # =====================================================

    st.divider()

    st.subheader(
        "🧠 Final Answer"
    )

    final_answer = state.get(
        "final_answer",
        "",
    )

    if final_answer:

        st.markdown(
            f"""
            <div class="answer-box">

            {final_answer}

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.warning(
            "No final answer was generated."
        )

    # =====================================================
    # RETRIEVED EVIDENCE
    # =====================================================

    st.divider()

    st.subheader(
        "📚 Retrieved Evidence"
    )

    evidence_chunks = state.get(
        "retrieved_chunks",
        [],
    )

    if evidence_chunks:

        for index, chunk in enumerate(
            evidence_chunks,
            start=1,
        ):

            if not isinstance(chunk, dict):
                continue

            source_file = chunk.get(
                "source_file",
                chunk.get(
                    "source",
                    "Unknown source",
                ),
            )

            text = chunk.get(
                "text",
                chunk.get(
                    "content",
                    "",
                ),
            )

            with st.expander(
                f"Evidence {index} — {source_file}"
            ):

                st.markdown(
                    text
                )

    else:

        st.info(
            "No evidence chunks were retrieved."
        )

    # =====================================================
    # EXECUTION TIME
    # =====================================================

    execution_time = (
        st.session_state.execution_time
    )

    if execution_time is not None:

        st.caption(
            f"Pipeline execution time: "
            f"{execution_time:.2f} seconds"
        )

    # =====================================================
    # PDF DOWNLOAD
    # =====================================================

    st.divider()

    st.subheader(
        "📄 Export Research Report"
    )

    try:

        pdf_bytes = create_pdf_report(
            st.session_state.submitted_query,
            state,
            execution_time,
        )

        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=(
                "lexverify_ai_legal_research_report.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as exc:

        st.error(
            f"Unable to generate PDF report: {exc}"
        )


# =========================================================
# EMPTY STATE
# =========================================================

else:

    st.info(
        "Enter a legal research question or select "
        "a demo query from the sidebar to begin."
    )

    st.markdown(
        """
        ### How LexVerify AI works

        **1. Research Agent**  
        Extracts useful legal search terms from your question.

        **2. Retrieval Agent**  
        Searches the Pakistani judgment corpus using FAISS.

        **3. Verification Agent**  
        Checks citation candidates against the Truth Registry.

        **4. Synthesis Agent**  
        Generates the final response using verified citations
        and retrieved evidence only.
        """
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "LexVerify AI — Citation-grounded Pakistani legal research. "
    "For research assistance only; not legal advice."
)