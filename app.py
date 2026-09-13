```python
import sys
import os
import time
from io import BytesIO
from html import escape

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
# PROJECT IMPORT
# KEEP CURRENT WORKING BACKEND
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
# PREVIOUS LEXVERIFY-STYLE CSS
# =========================================================

st.markdown(
    """
    <style>

    /* -----------------------------------------------------
       GLOBAL
    ----------------------------------------------------- */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* -----------------------------------------------------
       HEADER
    ----------------------------------------------------- */

    .main-title {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }

    .subtitle {
        font-size: 18px;
        color: #6b7280;
        margin-bottom: 28px;
    }

    /* -----------------------------------------------------
       SECTION TITLES
    ----------------------------------------------------- */

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 4px;
    }

    .section-description {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 18px;
    }

    /* -----------------------------------------------------
       METRIC CARDS
    ----------------------------------------------------- */

    .metric-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
        text-align: center;
        min-height: 105px;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 750;
    }

    .metric-label {
        font-size: 13px;
        color: #6b7280;
        margin-top: 4px;
    }

    /* -----------------------------------------------------
       STATUS CARDS
    ----------------------------------------------------- */

    .status-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
        margin-bottom: 8px;
        text-align: center;
    }

    .status-completed {
        border-left: 5px solid #28a745;
        background: #f3fff5;
    }

    .status-failed {
        border-left: 5px solid #dc3545;
        background: #fff5f5;
    }

    .status-pending {
        border-left: 5px solid #9ca3af;
        background: #f9fafb;
    }

    .status-name {
        font-size: 14px;
        font-weight: 700;
    }

    .status-value {
        font-size: 13px;
        margin-top: 5px;
    }

    /* -----------------------------------------------------
       VERIFIED CITATIONS
    ----------------------------------------------------- */

    .verified-box {
        padding: 16px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        background-color: #f3fff5;
        margin-bottom: 10px;
    }

    .verified-title {
        font-size: 16px;
        font-weight: 700;
    }

    /* -----------------------------------------------------
       REJECTED CITATIONS
    ----------------------------------------------------- */

    .rejected-box {
        padding: 16px;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
        background-color: #fff5f5;
        margin-bottom: 10px;
    }

    .rejected-title {
        font-size: 16px;
        font-weight: 700;
    }

    /* -----------------------------------------------------
       FINAL ANSWER
    ----------------------------------------------------- */

    .answer-box {
        padding: 22px;
        border-radius: 12px;
        background-color: #f8f9fa;
        border: 1px solid #e1e5e9;
        line-height: 1.75;
        font-size: 16px;
        margin-top: 8px;
    }

    /* -----------------------------------------------------
       EVIDENCE
    ----------------------------------------------------- */

    .evidence-intro {
        color: #6b7280;
        margin-bottom: 12px;
    }

    /* -----------------------------------------------------
       SIDEBAR
    ----------------------------------------------------- */

    [data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    /* -----------------------------------------------------
       BUTTONS
    ----------------------------------------------------- */

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* -----------------------------------------------------
       FOOTER
    ----------------------------------------------------- */

    .footer-text {
        text-align: center;
        color: #9ca3af;
        font-size: 12px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# UI FUNCTIONS
# =========================================================

def render_engine_metrics():
    """Top-level LexVerify engine metrics."""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value">4</div>
                <div class="metric-label">AI Agents</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value">FAISS</div>
                <div class="metric-label">Vector Retrieval</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value">Truth</div>
                <div class="metric-label">Citation Registry</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value">PDF</div>
                <div class="metric-label">Verified Reports</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_header():
    """Render the previous LexVerify header."""

    st.markdown(
        '<div class="main-title">⚖️ LexVerify AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="subtitle">
            Research. Retrieve. Verify. Respond.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_execution_time(execution_time):
    """Display pipeline execution time."""

    if execution_time is None:
        return

    st.caption(
        f"⏱️ Pipeline execution time: "
        f"{execution_time:.2f} seconds"
    )


def render_agent_status(status):
    """Render the four-agent workflow."""

    st.markdown(
        '<div class="section-title">🤖 Agent Workflow</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-description">
            Track the Research → Retrieval → Verification → Synthesis pipeline.
        </div>
        """,
        unsafe_allow_html=True,
    )

    agents = [
        ("Research Agent", "research"),
        ("Retrieval Agent", "retrieval"),
        ("Verification Agent", "verification"),
        ("Synthesis Agent", "synthesis"),
    ]

    columns = st.columns(4)

    for column, (name, key) in zip(columns, agents):

        current_status = status.get(
            key,
            "pending",
        )

        if current_status == "completed":

            css_class = "status-completed"
            icon = "✓"
            label = "Completed"

        elif current_status == "failed":

            css_class = "status-failed"
            icon = "✗"
            label = "Failed"

        else:

            css_class = "status-pending"
            icon = "•"
            label = "Pending"

        with column:

            st.markdown(
                f"""
                <div class="status-card {css_class}">
                    <div class="status-name">
                        {escape(name)}
                    </div>
                    <div class="status-value">
                        {icon} {label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_verification_summary(
    verified_count,
    rejected_count,
    evidence_count,
):
    """Render verification summary cards."""

    st.markdown(
        '<div class="section-title">🔐 Verification Summary</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(3)

    with columns[0]:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {verified_count}
                </div>
                <div class="metric-label">
                    ✓ Verified Citations
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with columns[1]:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {rejected_count}
                </div>
                <div class="metric-label">
                    ✗ Rejected Citations
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with columns[2]:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {evidence_count}
                </div>
                <div class="metric-label">
                    📚 Evidence Chunks
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_response_panel(state):
    """Render the final answer in the previous response-panel style."""

    st.markdown(
        '<div class="section-title">🧠 Research Response</div>',
        unsafe_allow_html=True,
    )

    final_answer = state.get(
        "final_answer",
        "",
    )

    if final_answer and final_answer.strip():

        safe_answer = escape(
            str(final_answer)
        ).replace(
            "\n",
            "<br>",
        )

        st.markdown(
            f"""
            <div class="answer-box">
                {safe_answer}
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.info(
            "No final answer was generated."
        )


def render_footer():
    """Render application footer."""

    st.divider()

    st.markdown(
        """
        <div class="footer-text">
            LexVerify AI — Citation-grounded Pakistani legal research.
            For research assistance only; not legal advice.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SESSION STATE
# =========================================================

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = None

if "execution_time" not in st.session_state:
    st.session_state.execution_time = None

if "submitted_query" not in st.session_state:
    st.session_state.submitted_query = ""


# =========================================================
# GROQ CLIENT
# =========================================================

def create_groq_client():

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

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
    Generate the verified LexVerify AI PDF report.
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

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # QUERY
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Legal Query",
            heading_style,
        )
    )

    story.append(
        Paragraph(
            escape(str(query)),
            body_style,
        )
    )

    if execution_time is not None:

        story.append(
            Paragraph(
                f"Execution Time: "
                f"{execution_time:.2f} seconds",
                small_style,
            )
        )

    story.append(
        Spacer(1, 10)
    )

    # -----------------------------------------------------
    # FINAL ANSWER
    # -----------------------------------------------------

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
            "No final answer was generated because "
            "the verification pipeline did not produce "
            "sufficient verified evidence."
        )

    safe_answer = (
        escape(str(final_answer))
        .replace("\n", "<br/>")
    )

    story.append(
        Paragraph(
            safe_answer,
            body_style,
        )
    )

    # -----------------------------------------------------
    # VERIFIED CITATIONS
    # -----------------------------------------------------

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
                item.get(
                    "title",
                    "",
                ),
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
                        escape(str(citation)),
                        body_style,
                    ),
                    Paragraph(
                        escape(str(case_name)),
                        body_style,
                    ),
                    Paragraph(
                        escape(str(court)),
                        body_style,
                    ),
                    Paragraph(
                        escape(str(year)),
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

    # -----------------------------------------------------
    # REJECTED CITATIONS
    # -----------------------------------------------------

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

            story.append(
                Paragraph(
                    "REJECTED — "
                    + escape(str(citation_text)),
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

    # -----------------------------------------------------
    # RETRIEVED EVIDENCE
    # -----------------------------------------------------

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

            story.append(
                Paragraph(
                    f"<b>Evidence {index}</b> — "
                    f"{escape(str(source_file))}",
                    body_style,
                )
            )

            story.append(
                Paragraph(
                    escape(
                        str(text)
                    ).replace(
                        "\n",
                        "<br/>",
                    ),
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

    # -----------------------------------------------------
    # DISCLAIMER
    # -----------------------------------------------------

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
        "LexVerify AI is a legal research assistance "
        "tool. It does not provide legal advice and "
        "should not be treated as a substitute for "
        "professional legal judgment. Citations and "
        "evidence shown in this report are limited to "
        "the application's verified corpus."
    )

    story.append(
        Paragraph(
            disclaimer,
            body_style,
        )
    )

    # -----------------------------------------------------
    # BUILD
    # -----------------------------------------------------

    doc.build(story)

    return buffer.getvalue()


# =========================================================
# TOP HEADER
# =========================================================

render_engine_metrics()

render_header()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## ⚖️ LexVerify AI"
    )

    st.markdown(
        """
        **Citation-grounded Pakistani legal research**

        LexVerify AI retrieves relevant Pakistani
        judgment evidence, verifies citations against
        a deterministic Truth Registry, and generates
        responses only from verified evidence.
        """
    )

    st.divider()

    st.markdown(
        "### 🎯 Demo Scenarios"
    )

    bail_button = st.button(
        "⚖️ Bail Standards",
        use_container_width=True,
    )

    fake_button = st.button(
        "🔴 Fake Citation Test",
        use_container_width=True,
    )

    corpus_button = st.button(
        "🌐 Out-of-Corpus Query",
        use_container_width=True,
    )

    st.divider()

    st.markdown(
        """
        **Pipeline**

        1. 🔎 Research
        2. 📚 Retrieval
        3. 🔐 Verification
        4. 🧠 Synthesis
        """
    )

    st.divider()

    st.caption(
        "LexVerify AI • Hackathon Prototype"
    )


# =========================================================
# DEMO QUERY HANDLERS
# =========================================================

if bail_button:

    st.session_state.user_query = (
        "What is the bail standard in non-bailable offenses?"
    )

    st.session_state.pipeline_state = None
    st.session_state.execution_time = None

    st.rerun()


if fake_button:

    st.session_state.user_query = (
        "Check precedent PLD 2025 SC 999"
    )

    st.session_state.pipeline_state = None
    st.session_state.execution_time = None

    st.rerun()


if corpus_button:

    st.session_state.user_query = (
        "What are foreign maritime tax rates?"
    )

    st.session_state.pipeline_state = None
    st.session_state.execution_time = None

    st.rerun()


# =========================================================
# QUESTION SECTION
# =========================================================

st.markdown(
    '<div class="section-title">🔎 Ask a Legal Question</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-description">
        Enter a Pakistani legal research question or try one
        of the demo scenarios below.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SAMPLE QUERY BUTTONS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    if st.button(
        "⚖️ Bail Standards",
        use_container_width=True,
        key="main_bail_demo",
    ):

        st.session_state.user_query = (
            "What is the bail standard in non-bailable offenses?"
        )

        st.session_state.pipeline_state = None
        st.session_state.execution_time = None

        st.rerun()


with col2:

    if st.button(
        "🔴 Fake Citation Test",
        use_container_width=True,
        key="main_fake_demo",
    ):

        st.session_state.user_query = (
            "Check precedent PLD 2025 SC 999"
        )

        st.session_state.pipeline_state = None
        st.session_state.execution_time = None

        st.rerun()


with col3:

    if st.button(
        "🌐 Out-of-Corpus Query",
        use_container_width=True,
        key="main_corpus_demo",
    ):

        st.session_state.user_query = (
            "What are foreign maritime tax rates?"
        )

        st.session_state.pipeline_state = None
        st.session_state.execution_time = None

        st.rerun()


# =========================================================
# QUERY FORM
# ENTER KEY ALSO SUBMITS
# =========================================================

with st.form(
    key="legal_query_form",
    clear_on_submit=False,
):

    user_question = st.text_input(
        "Enter your legal query:",
        value=st.session_state.user_query,
        placeholder=(
            "e.g. What is the bail standard in "
            "non-bailable offenses?"
        ),
        label_visibility="collapsed",
    )

    search_clicked = st.form_submit_button(
        "🔍 Search & Verify",
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

    st.session_state.user_query = (
        submitted_query
    )

    if not submitted_query:

        st.warning(
            "Please enter a legal question first."
        )

    else:

        # -------------------------------------------------
        # CLEAR OLD RESULTS
        # -------------------------------------------------

        st.session_state.pipeline_state = None
        st.session_state.execution_time = None

        # -------------------------------------------------
        # CLIENT
        # -------------------------------------------------

        client = create_groq_client()

        if client is None:

            st.error(
                "GROQ_API_KEY is not configured. "
                "Please add it to Streamlit Secrets."
            )

            st.stop()

        # -------------------------------------------------
        # RUN
        # -------------------------------------------------

        start_time = time.perf_counter()

        try:

            with st.spinner(
                "Running Research → Retrieval → "
                "Verification → Synthesis..."
            ):

                state = run_lexverify_pipeline(
                    submitted_query,
                    client,
                )

            execution_time = (
                time.perf_counter()
                - start_time
            )

            st.session_state.pipeline_state = state

            st.session_state.execution_time = (
                execution_time
            )

            st.session_state.submitted_query = (
                submitted_query
            )

        except Exception as exc:

            execution_time = (
                time.perf_counter()
                - start_time
            )

            st.session_state.execution_time = (
                execution_time
            )

            st.session_state.pipeline_state = None

            st.error(
                "LexVerify pipeline encountered an error."
            )

            st.exception(exc)


# =========================================================
# DISPLAY RESULTS
# =========================================================

state = st.session_state.pipeline_state


if state is not None:

    st.divider()

    # =====================================================
    # EXECUTION TIME
    # =====================================================

    render_execution_time(
        st.session_state.execution_time
    )

    # =====================================================
    # AGENT WORKFLOW STATUS
    # =====================================================

    status = {
        "research": "completed",
        "retrieval": "completed",
        "verification": "completed",
        "synthesis": "completed",
    }

    pipeline_status = state.get(
        "status",
        "",
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

    st.divider()

    # =====================================================
    # DATA
    # =====================================================

    verified_citations = state.get(
        "verified_citations",
        [],
    )

    rejected_citations = state.get(
        "rejected_citations",
        [],
    )

    retrieved_chunks = state.get(
        "retrieved_chunks",
        [],
    )

    # =====================================================
    # VERIFICATION SUMMARY
    # =====================================================

    render_verification_summary(
        verified_count=len(
            verified_citations
        ),
        rejected_count=len(
            rejected_citations
        ),
        evidence_count=len(
            retrieved_chunks
        ),
    )

    st.divider()

    # =====================================================
    # VERIFIED CITATIONS
    # =====================================================

    if verified_citations:

        st.markdown(
            '<div class="section-title">✅ Verified Citations</div>',
            unsafe_allow_html=True,
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
                item.get(
                    "title",
                    "Unknown case",
                ),
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

                    <div class="verified-title">
                        ✓ {escape(str(citation))}
                    </div>

                    <br>

                    <b>Case:</b>
                    {escape(str(case_name))}

                    <br>

                    <b>Court:</b>
                    {escape(str(court))}

                    <br>

                    <b>Year:</b>
                    {escape(str(year))}

                </div>
                """,
                unsafe_allow_html=True,
            )

    # =====================================================
    # REJECTED CITATIONS
    # =====================================================

    if rejected_citations:

        st.markdown(
            '<div class="section-title">❌ Rejected / Unverified Citations</div>',
            unsafe_allow_html=True,
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

                    <div class="rejected-title">
                        ✗ {escape(str(citation))}
                    </div>

                    <br>

                    {escape(str(reason))}

                </div>
                """,
                unsafe_allow_html=True,
            )

    # =====================================================
    # RESPONSE PANEL
    # =====================================================

    st.divider()

    render_response_panel(
        state
    )

    # =====================================================
    # RETRIEVED EVIDENCE
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">📚 Retrieved Evidence</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="evidence-intro">
            Evidence retrieved from the Pakistani legal
            judgment corpus and used by the verification/
            synthesis pipeline.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if retrieved_chunks:

        for index, chunk in enumerate(
            retrieved_chunks,
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
                f"📄 Evidence {index} — {source_file}"
            ):

                st.markdown(
                    str(text)
                )

    else:

        st.info(
            "No evidence chunks were retrieved."
        )

    # =====================================================
    # EXPORT REPORT
    # =====================================================

    st.divider()

    st.markdown(
        '<div class="section-title">📄 Export Report</div>',
        unsafe_allow_html=True,
    )

    final_answer = state.get(
        "final_answer",
        "",
    )

    if final_answer and final_answer.strip():

        execution_time = (
            st.session_state.execution_time
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

    else:

        st.info(
            "PDF export will be available when a "
            "final research response is generated."
        )


# =========================================================
# EMPTY STATE
# =========================================================

else:

    st.info(
        "Enter a Pakistani legal research question "
        "or select a demo scenario to begin."
    )

    st.markdown(
        '<div class="section-title">💡 How LexVerify AI Works</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-description">
            LexVerify AI uses a four-stage citation-grounded
            legal research workflow.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.markdown(
            """
            **🔎 1. Research Agent**

            Extracts useful legal search terms
            from the user's question.
            """
        )

    with col2:

        st.markdown(
            """
            **📚 2. Retrieval Agent**

            Searches the Pakistani judgment
            corpus using FAISS.
            """
        )

    with col3:

        st.markdown(
            """
            **🔐 3. Verification Agent**

            Checks citation candidates against
            the deterministic Truth Registry.
            """
        )

    with col4:

        st.markdown(
            """
            **🧠 4. Synthesis Agent**

            Generates the response using
            verified citations and evidence.
            """
        )


# =========================================================
# FOOTER
# =========================================================

render_footer()
```
