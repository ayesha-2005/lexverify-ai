import streamlit as st


# =========================================================
# CUSTOM CSS
# =========================================================

def load_custom_css():

    st.markdown(
        """
        <style>

        /* =========================
           MAIN APP
        ========================= */

        .stApp {
            background-color: #f7f9fc;
        }

        .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }


        /* =========================
           HERO
        ========================= */

        .hero {
            background: linear-gradient(
                135deg,
                #102a43 0%,
                #1f4e79 100%
            );

            padding: 2rem 2.2rem;
            border-radius: 18px;
            margin-bottom: 1.5rem;

            color: white;

            box-shadow:
                0 8px 25px rgba(16, 42, 67, 0.15);
        }

        .hero-title {
            font-size: 2.25rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            font-size: 1rem;
            opacity: 0.9;
            margin: 0;
            line-height: 1.5;
        }


        /* =========================
           SECTION TITLES
        ========================= */

        .section-title {
            font-size: 1.35rem;
            font-weight: 750;
            color: #102a43;

            margin-top: 1.4rem;
            margin-bottom: 0.8rem;
        }

        .section-description {
            color: #66788a;
            font-size: 0.85rem;

            margin-top: -0.4rem;
            margin-bottom: 1rem;
        }


        /* =========================
           QUERY CARD
        ========================= */

        .query-card {
            background: white;

            padding: 1.3rem;

            border-radius: 16px;

            border: 1px solid #e3e8ef;

            box-shadow:
                0 4px 15px rgba(16, 42, 67, 0.06);

            margin-bottom: 1rem;
        }


        /* =========================
           WORKFLOW CARDS
        ========================= */

        .workflow-card {
            background: white;

            border: 1px solid #e1e7ef;

            border-radius: 14px;

            padding: 1rem;

            text-align: center;

            min-height: 120px;

            box-shadow:
                0 3px 12px rgba(16, 42, 67, 0.05);
        }

        .workflow-icon {
            font-size: 1.5rem;
            margin-bottom: 0.35rem;
        }

        .workflow-name {
            font-weight: 700;
            color: #102a43;
            font-size: 0.95rem;
        }

        .workflow-status {
            margin-top: 0.45rem;
            font-size: 0.82rem;
            font-weight: 650;
        }

        .status-pending {
            color: #667085;
        }

        .status-running {
            color: #b7791f;
        }

        .status-completed {
            color: #16803c;
        }

        .status-failed {
            color: #c53030;
        }


        /* =========================
           ANSWER CARD
        ========================= */

        .answer-card {
            background: #ffffff;
            border: 1px solid #dce4ed;
            border-left: 5px solid #1f6feb;
            border-radius: 12px;
            padding: 1.5rem 1.8rem;
            box-shadow: 0 4px 15px rgba(16, 42, 67, 0.05);
            line-height: 1.8;
            font-size: 1rem;
            color: #1e293b;
            margin-bottom: 1.5rem;
        }
        
        .answer-card p {
            margin-bottom: 1rem;
        }
        
        .answer-card ul, .answer-card ol {
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }


        /* =========================
           CITATION CARDS
        ========================= */

        .citation-card {
            background: white;

            border-radius: 12px;

            padding: 1rem 1.2rem;

            border: 1px solid #dce4ed;

            margin-bottom: 0.7rem;
        }

        .verified-card {
            border-left: 5px solid #2e9d5b;
            background: #f8fffa;
        }

        .rejected-card {
            border-left: 5px solid #d64545;
            background: #fff8f8;
        }

        .citation-status {
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.4px;
        }

        .verified-status {
            color: #19713d;
        }

        .rejected-status {
            color: #b42318;
        }

        .citation-main {
            margin-top: 0.35rem;

            font-weight: 700;

            color: #102a43;
        }

        .citation-meta {
            margin-top: 0.25rem;

            color: #66788a;

            font-size: 0.8rem;
        }


        /* =========================
           SUMMARY CARDS
        ========================= */

        .summary-card {
            background: white;

            border: 1px solid #e1e7ef;

            border-radius: 14px;

            padding: 1rem;

            text-align: center;

            box-shadow:
                0 3px 12px rgba(16, 42, 67, 0.04);
        }

        .summary-number {
            font-size: 1.5rem;

            font-weight: 800;

            color: #102a43;
        }

        .summary-label {
            font-size: 0.8rem;

            color: #66788a;

            margin-top: 0.2rem;
        }


        /* =========================
           EXECUTION TIMER
        ========================= */

        .execution-card {
            background: #eef6ff;

            border: 1px solid #c7ddf7;

            border-radius: 12px;

            padding: 0.75rem 1rem;

            margin: 1rem 0;

            text-align: center;

            color: #174a7c;

            font-weight: 700;
        }


        /* =========================
           SIDEBAR
        ========================= */

        .sidebar-title {
            font-size: 1.25rem;

            font-weight: 800;

            color: #102a43;

            margin-bottom: 0.2rem;
        }

        .sidebar-subtitle {
            font-size: 0.75rem;

            color: #718096;

            margin-bottom: 1rem;
        }

        .engine-card {
            background: white;

            border: 1px solid #e1e7ef;

            border-radius: 12px;

            padding: 0.8rem;

            margin-bottom: 0.7rem;

            box-shadow:
                0 2px 8px rgba(16, 42, 67, 0.04);
        }

        .engine-label {
            font-size: 0.7rem;

            color: #667085;

            font-weight: 600;

            letter-spacing: 0.3px;
        }

        .engine-value {
            font-size: 0.95rem;

            font-weight: 750;

            color: #102a43;

            margin-top: 0.2rem;
        }

        .engine-small {
            font-size: 0.72rem;

            color: #718096;

            margin-top: 0.15rem;
        }


        /* =========================
           BUTTONS
        ========================= */

        .stButton > button {
            border-radius: 10px;

            font-weight: 600;

            min-height: 2.5rem;
        }

        div[data-testid="stButton"] > button[kind="primary"] {
            border-radius: 10px;

            font-weight: 700;

            min-height: 2.8rem;
        }


        /* =========================
           FOOTER
        ========================= */

        .footer {
            text-align: center;

            color: #718096;

            font-size: 0.8rem;

            margin-top: 2.5rem;

            padding-top: 1rem;

            border-top: 1px solid #e1e7ef;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# HERO HEADER
# =========================================================

def render_header():

    st.html(
        """
        <div class="hero">

            <div class="hero-title">
                ⚖️ LexVerify AI
            </div>

            <p class="hero-subtitle">
                AI-powered legal research with retrieval,
                citation verification, and evidence-grounded answers.
            </p>

        </div>
        """
    )


# =========================================================
# SECTION TITLE
# =========================================================

def render_section_title(title, icon=""):

    st.html(
        f"""
        <div class="section-title">
            {icon} {title}
        </div>
        """
    )


def render_section_description(text):

    st.html(
        f"""
        <div class="section-description">
            {text}
        </div>
        """
    )


# =========================================================
# AGENT WORKFLOW
# =========================================================

def render_agent_status(status_dict):

    render_section_title(
        "Agent Workflow",
        "⚙️"
    )

    agents = [
        ("research", "🔎", "Research"),
        ("retrieval", "📚", "Retrieval"),
        ("verification", "✓", "Verification"),
        ("synthesis", "📝", "Synthesis"),
    ]

    status_info = {

        "pending": (
            "⚪",
            "Pending",
            "status-pending"
        ),

        "running": (
            "🟡",
            "Running",
            "status-running"
        ),

        "completed": (
            "🟢",
            "Completed",
            "status-completed"
        ),

        "failed": (
            "🔴",
            "Failed",
            "status-failed"
        ),
    }

    columns = st.columns(4)

    for column, (key, icon, name) in zip(
        columns,
        agents
    ):

        status = status_dict.get(
            key,
            "pending"
        )

        status_icon, status_text, status_class = status_info.get(
            status,
            status_info["pending"]
        )

        with column:

            st.html(
                f"""
                <div class="workflow-card">

                    <div class="workflow-icon">
                        {icon}
                    </div>

                    <div class="workflow-name">
                        {name}
                    </div>

                    <div class="workflow-status {status_class}">
                        {status_icon} {status_text}
                    </div>

                </div>
                """
            )


# =========================================================
# VERIFICATION SUMMARY
# =========================================================

def render_verification_summary(
    verified_count,
    rejected_count,
    evidence_count
):

    render_section_title(
        "Verification Summary",
        "📊"
    )

    columns = st.columns(3)

    summary_data = [
        (
            columns[0],
            verified_count,
            "🟢 Verified Citations"
        ),
        (
            columns[1],
            rejected_count,
            "🔴 Rejected Citations"
        ),
        (
            columns[2],
            evidence_count,
            "📚 Evidence Chunks"
        ),
    ]

    for column, number, label in summary_data:

        with column:

            st.html(
                f"""
                <div class="summary-card">

                    <div class="summary-number">
                        {number}
                    </div>

                    <div class="summary-label">
                        {label}
                    </div>

                </div>
                """
            )


# =========================================================
# RESPONSE PANEL
# =========================================================

def render_response_panel(response_data):
    # -----------------------------------------------------
    # FINAL ANSWER
    # -----------------------------------------------------

    render_section_title(
        "Final Answer",
        "📝"
    )

    answer = response_data.get(
        "final_answer",
        ""
    )

    if answer and answer.strip():
        # Clean HTML escaping and line breaks for proper card embedding
        formatted_content = answer.replace("\n", "<br>")
        st.markdown(
            f"""
            <div class="answer-card">
                {formatted_content}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info(
            "No final answer was generated from "
            "the available legal evidence."
        )

    # -----------------------------------------------------
    # VERIFIED CITATIONS
    # -----------------------------------------------------
    verified_citations = response_data.get(
        "verified_citations",
        []
    )

    if verified_citations:
        render_section_title(
            "Verified Citations",
            "🟢"
        )

        for citation in verified_citations:
            if isinstance(citation, dict):
                citation_text = citation.get("citation", "Unknown citation")
                title = citation.get("title", citation.get("case_name", "Unknown Case"))
                court = citation.get("court", "Unknown Court")
                year = citation.get("year", "N/A")

                st.html(
                    f"""
                    <div class="citation-card verified-card">
                        <div class="citation-status verified-status">
                            ✓ VERIFIED
                        </div>
                        <div class="citation-main">
                            {citation_text}
                        </div>
                        <div class="citation-meta">
                            {title} &nbsp; • &nbsp; {court} &nbsp; • &nbsp; {year}
                        </div>
                    </div>
                    """
                )
            else:
                st.success(f"✓ VERIFIED — {citation}")

    # -----------------------------------------------------
    # REJECTED CITATIONS
    # -----------------------------------------------------
    rejected_citations = response_data.get(
        "rejected_citations",
        []
    )

    if rejected_citations:
        render_section_title(
            "Rejected Citations",
            "🔴"
        )

        for citation in rejected_citations:
            st.html(
                f"""
                <div class="citation-card rejected-card">
                    <div class="citation-status rejected-status">
                        ✗ REJECTED
                    </div>
                    <div class="citation-main">
                        {citation}
                    </div>
                    <div class="citation-meta">
                        This citation was not found in the verified truth registry.
                    </div>
                </div>
                """
            )

    # -----------------------------------------------------
    # EVIDENCE DRAWER
    # -----------------------------------------------------
    retrieved_chunks = response_data.get(
        "retrieved_chunks",
        []
    )

    if retrieved_chunks:
        render_section_title(
            "Evidence",
            "📚"
        )

        render_section_description(
            "Open the drawer below to inspect retrieved legal evidence."
        )

        with st.expander(
            "🔍 View Retrieved Evidence",
            expanded=False
        ):
            for index, chunk in enumerate(
                retrieved_chunks,
                start=1
            ):
                if isinstance(chunk, dict):
                    source = chunk.get(
                        "source_file",
                        chunk.get("source_doc", "Unknown source")
                    )
                    text = chunk.get("text", "No evidence text available.")

                    st.markdown(f"**Evidence {index}**")
                    st.markdown(f"**Source:** `{source}`")
                    st.write(text)
                else:
                    st.write(chunk)

                if index < len(retrieved_chunks):
                    st.divider()

# =========================================================
# SIDEBAR ENGINE METRICS
# =========================================================

def render_engine_metrics():

    st.sidebar.html(
        """
        <div class="sidebar-title">
            ⚙️ Engine Metrics
        </div>

        <div class="sidebar-subtitle">
            LexVerify AI system information
        </div>
        """
    )


    # System Status

    st.sidebar.html(
        """
        <div class="engine-card">

            <div class="engine-label">
                SYSTEM STATUS
            </div>

            <div class="engine-value"
                 style="color:#16803c;">
                🟢 Online
            </div>

        </div>
        """
    )


    # LLM Engine

    st.sidebar.html(
        """
        <div class="engine-card">

            <div class="engine-label">
                LLM ENGINE
            </div>

            <div class="engine-value">
                Groq
            </div>

            <div class="engine-small">
                GPT-OSS 120B
            </div>

        </div>
        """
    )


    # Vector Store

    st.sidebar.html(
        """
        <div class="engine-card">

            <div class="engine-label">
                VECTOR STORE
            </div>

            <div class="engine-value">
                175 chunks
            </div>

            <div class="engine-small">
                Indexed legal evidence
            </div>

        </div>
        """
    )


    # Reporter Index Scope

    st.sidebar.html(
        """
        <div class="engine-card">

            <div class="engine-label">
                REPORTER INDEX SCOPE
            </div>

            <div class="engine-value">
                Pakistani Case Law
            </div>

            <div class="engine-small">
                PLD • SCMR • CLC • PCrLJ • YLR
            </div>

        </div>
        """
    )


# =========================================================
# EXECUTION TIMER
# =========================================================

def render_execution_time(execution_time):

    st.html(
        f"""
        <div class="execution-card">
            ⚡ Pipeline executed in
            {execution_time:.2f}s
        </div>
        """
    )


# =========================================================
# FOOTER
# =========================================================

def render_footer():

    st.html(
        """
        <div class="footer">

            <strong>LexVerify AI</strong>
            &nbsp;•&nbsp;
            Research. Retrieve. Verify. Respond.

            <br>

            AI-assisted legal research with
            evidence-grounded citation verification.

        </div>
        """
    )