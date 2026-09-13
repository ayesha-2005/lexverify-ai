import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from src.orchestrator import run_lexverify_pipeline
from src.ui.components import render_agent_status

load_dotenv()

# Cache client initialization to prevent app freeze during Streamlit reruns
@st.cache_resource
def get_groq_client():
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )

client = get_groq_client()

# Page setup
st.set_page_config(
    page_title="LexVerify AI",
    layout="wide"
)

st.title("LexVerify AI")
st.subheader("Research. Retrieve. Verify. Respond.")

# Initialize query state BEFORE UI components load
if "user_query" not in st.session_state:
    st.session_state.user_query = ""

# Sample query shortcuts
st.write("### Try a sample query")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Bail Standards"):
        st.session_state.user_query = "What is the bail standard in non-bailable offenses?"

with col2:
    if st.button("Fake Citation Test"):
        st.session_state.user_query = "Check precedent PLD 2025 SC 999"

with col3:
    if st.button("Out of Corpus Query"):
        st.session_state.user_query = "What are foreign maritime tax rates?"

# Query text input bound to session state
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

        # 1. Render Agent Workflow Status Cards
        status = {
            "research": "completed",
            "retrieval": "completed",
            "verification": "completed",
            "synthesis": "completed",
        }
        render_agent_status(status)

        # 2. Render Final Answer with Fallback for Empty / Out-of-Corpus Outputs
        st.markdown("## Final Answer")
        final_text = state.get("final_answer", "")
        if final_text and final_text.strip():
            st.markdown(final_text)
        else:
            st.warning("⚠️ No relevant Pakistani legal precedents found in the verified corpus to answer this query.")

        # 3. Citation Truth Gate Status Badges
        verified_citations = state.get("verified_citations", [])
        rejected_citations = state.get("rejected_citations", [])

        if verified_citations:
            st.markdown("## Verified Citations")
            for citation in verified_citations:
                st.success(f"✓ VERIFIED — {citation}")

        if rejected_citations:
            st.markdown("## Rejected Citations")
            for citation in rejected_citations:
                st.error(f"✗ REJECTED — {citation}")

        if not verified_citations and not rejected_citations:
            st.info("No explicit legal citations detected in this analysis.")

        # 4. Evidence Drawer
        retrieved_chunks = state.get("retrieved_chunks", [])
        if retrieved_chunks:
            st.markdown("## Evidence")
            with st.expander("View Retrieved Evidence Chunks"):
                for chunk in retrieved_chunks:
                    if isinstance(chunk, dict):
                        st.json(chunk)
                    else:
                        st.write(chunk)

        # 5. Legal Disclaimer Footer
        st.markdown("---")
        st.caption("Disclaimer: LexVerify AI is an AI-assisted legal research engine for Pakistani Case Law. Results are generated for analytical purposes and do not constitute formal legal advice.")
    else:
        st.warning("Please enter a legal question.")