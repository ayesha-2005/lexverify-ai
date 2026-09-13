import re
import streamlit as st

def clean_html(text):
    """Strips raw HTML tags if the LLM outputted literal HTML tags."""
    if not isinstance(text, str):
        return text
    clean = re.sub(r'<[^>]*>', '', text)
    return clean.strip()

def render_response_panel(response_data):
    # -----------------------------------------------------
    # RESEARCH RESPONSE (FINAL ANSWER)
    # -----------------------------------------------------
    render_section_title("Research Response", "🧠")

    answer = response_data.get("final_answer", "")

    if answer and answer.strip():
        # Strip any accidental st.code or markdown block wrappers
        clean_answer = answer.strip()
        with st.container(border=True):
            st.markdown(clean_answer)
    else:
        st.info("No final answer was generated from the available legal evidence.")

    # -----------------------------------------------------
    # VERIFIED CITATIONS
    # -----------------------------------------------------
    verified_citations = response_data.get("verified_citations", [])

    if verified_citations:
        render_section_title("Verified Citations", "✅")

        for citation in verified_citations:
            if isinstance(citation, dict):
                cit_text = clean_html(citation.get("citation", "Unknown citation"))
                title = clean_html(citation.get("title", citation.get("case_name", "Unknown Case")))
                court = clean_html(citation.get("court", "Unknown Court"))
                year = clean_html(citation.get("year", "N/A"))

                st.markdown(
                    f"""
                    <div style="background-color: #f0fdf4; border-left: 5px solid #22c55e; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; color: #15803d;">
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 6px;">
                            ✓ {cit_text}
                        </div>
                        <div style="color: #166534; font-size: 14px;">
                            <strong>Case:</strong> {title}<br>
                            <strong>Court:</strong> {court}<br>
                            <strong>Year:</strong> {year}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                cit_clean = clean_html(str(citation))
                st.success(f"✓ VERIFIED — {cit_clean}")

    # -----------------------------------------------------
    # REJECTED CITATIONS
    # -----------------------------------------------------
    rejected_citations = response_data.get("rejected_citations", [])

    if rejected_citations:
        render_section_title("Rejected Citations", "🔴")

        for citation in rejected_citations:
            cit_display = clean_html(citation.get("citation", str(citation)) if isinstance(citation, dict) else str(citation))
            st.markdown(
                f"""
                <div style="background-color: #fef2f2; border-left: 5px solid #ef4444; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; color: #991b1b;">
                    <div style="font-weight: bold; font-size: 15px;">
                        ✗ REJECTED — {cit_display}
                    </div>
                    <div style="font-size: 13px; color: #7f1d1d; margin-top: 4px;">
                        This citation was not found in the verified truth registry.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )