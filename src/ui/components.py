import streamlit as st


def render_agent_status(status_dict):
    """
    Display the status of the four LexVerify AI agents.
    """

    st.subheader("Agent Workflow")

    agents = [
        ("research", "🔎 Research"),
        ("retrieval", "📚 Retrieval"),
        ("verification", "✓ Verification"),
        ("synthesis", "📝 Synthesis"),
    ]

    col1, col2, col3, col4 = st.columns(4)

    columns = [col1, col2, col3, col4]

    status_labels = {
        "pending": "⚪ Pending",
        "running": "🟡 Running",
        "completed": "🟢 Completed",
        "failed": "🔴 Failed",
    }

    for column, (key, name) in zip(columns, agents):
        status = status_dict.get(key, "pending")

        with column:
            st.markdown(f"**{name}**")
            st.info(status_labels.get(status, "⚪ Pending"))


def render_response_panel(response_data):
    """
    Display the final answer, citations, and evidence.
    """

    st.subheader("LexVerify Response")

    # Final answer
    answer = response_data.get("answer", "No answer available.")
    st.markdown("### Answer")
    st.write(answer)

    # Citations
    citations = response_data.get("citations", [])

    if citations:
        st.markdown("### Citations")

        for citation in citations:
            citation_text = citation.get("citation", "Unknown citation")
            status = citation.get("status", "UNKNOWN")

            if status == "VERIFIED":
                st.success(f"✓ VERIFIED — {citation_text}")

            elif status == "REJECTED":
                st.error(f"✗ REJECTED — {citation_text}")

    # Evidence
    evidence = response_data.get("evidence", [])

    if evidence:
        st.markdown("### Evidence")

        for item in evidence:
            citation_text = item.get("citation", "Evidence")
            snippet = item.get("snippet", "No evidence available.")

            with st.expander(f"View Evidence — {citation_text}"):
                st.write(snippet)