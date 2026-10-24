"""Simple web UI for the HKU Student Service Navigator (Streamlit).

Run:
    streamlit run ui.py

This wraps src.pipeline.answer() — the same core workflow behind app.py.
It is NOT a substitute for the live pipeline; it calls the real retrieval +
generation + refusal guard on every question.
"""
import os

import streamlit as st

from src import pipeline as pipeline_mod
from src import index as index_mod
import config

st.set_page_config(page_title="HKU Student Service Navigator", page_icon="🎓")

# ----- Persistent disclaimer bar (proposal must-have) -----
DISCLAIMER = (
    "This tool only points you to official HKU student-service information. "
    "It does not give medical, mental-health, legal, or emergency advice. "
    "In an emergency call 999; for urgent wellbeing support call UHS "
    "(Mental Health) 24h at +852 3917 2889."
)


EXAMPLES = [
    "How do I book a study room in the Main Library?",
    "What are the opening hours for CEDARS?",
    "Where can I get a replacement student card?",
    "How do I connect to the HKU Wi-Fi on my phone?",
]

with st.sidebar:
    st.title("🎓 Navigator Guide")
    st.markdown(
        "Ask questions about **Libraries, CEDARS, UHS, IT, Careers, Cards, Registry,** and **Moodle**."
    )
    
    st.markdown("### 💡 Try asking:")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            # We store the button click in the session state to process it in the main loop
            st.session_state.pending_prompt = ex

    st.divider()
    
    # Persistent disclaimer in the sidebar
    st.warning(DISCLAIMER)
# Build index on first load if it does not exist yet.
if not os.path.exists(config.INDEX_PATH):
    try:
        index_mod.build_index()
    except Exception as e:  # noqa: BLE001
        st.warning(f"Could not build the index automatically: {e}. "
                   "Run `python ingest.py` once, then reload.")

st.title("🎓 HKU Student Service Navigator")
st.caption("Ask about libraries, CEDARS, UHS, IT, Careers, Cards, Registry, Moodle…")

q = st.text_input(
    "Your question",
    placeholder="Type a question and press Enter",
    key="main_input",
)

if q and q.strip():
    with st.spinner("Searching HKU service info…"):
        result = pipeline_mod.answer(q.strip())

    if result.get("refused"):
        st.error("⚠️ This question is outside the tool's scope.")
        st.markdown(result["answer"])
        st.caption("Refusal categories: " + ", ".join(result["categories"]))
    else:
        st.markdown(result["answer"])
        if result.get("sources"):
            st.markdown("---")
            st.markdown("**Sources**")
            for s in result["sources"]:
                st.markdown(f"- [{s['title']}]({s['url']})")

st.markdown("---")
st.info(DISCLAIMER)
