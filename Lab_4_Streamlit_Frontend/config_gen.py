"""config_gen.py — intent → SR Linux config, with human-in-the-loop review.

This is the Lab 4 "Going Further" alternative app. Instead of querying the
network, generate configs from natural-language intent. The human is the
safety gate — the 'approve' button deliberately does nothing destructive.
"""
import streamlit as st
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="SR Linux Config Generator", page_icon="🛠️")
st.title("🛠️ SR Linux Config Generator")
st.caption("Describe what you want; review the generated config before applying.")

intent = st.text_area(
    "What do you want to configure?",
    placeholder=(
        "e.g., Add an eBGP neighbor 10.0.99.1 in AS 65010 with permit-all "
        "import and export policies on r1."
    ),
)

if "generated_config" not in st.session_state:
    st.session_state.generated_config = None

if st.button("Generate config", type="primary"):
    if not intent.strip():
        st.error("Describe what you want to configure first.")
    else:
        with st.spinner("Generating..."):
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            prompt = (
                "You are an SR Linux configuration expert. Generate config "
                "for the following intent. Use 'set / ...' syntax. Output "
                "ONLY the configuration commands, one per line, no commentary "
                "or markdown.\n\n"
                f"Intent: {intent}"
            )
            response = llm.invoke(prompt)
            st.session_state.generated_config = response.content

if st.session_state.generated_config:
    st.markdown("### Review the generated config")
    st.code(st.session_state.generated_config, language="bash")

    col_left, col_right = st.columns(2)
    with col_left:
        if st.button("✅ Approve & copy"):
            st.success(
                "Approved. In production, this would be the point at which "
                "the config is pushed to the device. For safety, this demo "
                "stops here — copy the commands above and review on the box."
            )
    with col_right:
        if st.button("❌ Reject"):
            st.session_state.generated_config = None
            st.rerun()
