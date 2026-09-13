import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from src.orchestrator import run_lexverify_pipeline
from src.ui.components import render_agent_status

load_dotenv()

# Groq client
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# Page setup
st.set_page_config(
    page_title="LexVerify AI",
    layout="wide"
)

st.title("LexVerify AI")
st.subheader("Research. Retrieve. Verify. Respond.")

# Sample queries
st.write("### Try a sample query")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Bail Standards"):
        st.session_state.user_query = (
            "What is the bail standard in non-bailable offenses?"
        )

with col2:
    if st.button("Fake Citation Test"):
        st.session_state.user_query = (
            "Check precedent PLD 2025 SC 999"
        )

with col3:
    if st.button("Out of Corpus Query"):
        st.session_state.user_query = (
            "What are foreign maritime tax rates?"
        )

# Initialize query
if "user_query" not in st.session_state:
    st.session_state.user_query = ""

# Input
user_question = st.text_input(
    "Enter your legal query:",
    key="user_query"
)

# Run pipeline
if st.button("Search"):
    if user_question.strip():

        with st.spinner("Running LexVerify AI pipeline..."):

            state = run_lexverify_pipeline(
                user_question,
                client
            )

        # Agent workflow status
        status = {
            "research": "completed",
            "retrieval": "completed",
            "verification": "completed",
            "synthesis": "completed",
        }

        render_agent_status(status)

        # Final answer
        st.markdown("## Final Answer")
        st.markdown(state["final_answer"])

        # Verified citations
        if state["verified_citations"]:
            st.markdown("## Verified Citations")

            for citation in state["verified_citations"]:
                st.success(f"✓ VERIFIED — {citation}")

        # Rejected citations
        if state["rejected_citations"]:
            st.markdown("## Rejected Citations")

            for citation in state["rejected_citations"]:
                st.error(f"✗ REJECTED — {citation}")

        # Evidence
        if state["retrieved_chunks"]:
            st.markdown("## Evidence")

            with st.expander("View Retrieved Evidence Chunks"):

                for chunk in state["retrieved_chunks"]:
                    st.write(chunk)

    else:
        st.warning("Please enter a legal question.")
