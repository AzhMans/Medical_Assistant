import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="AI Medical Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)
def _render_home():
    st.title("🏥 AI Medical Assistant")
    st.subheader("Your intelligent preliminary health screening tool")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
### 🩺 Symptom Assessment
- Select your symptoms from a comprehensive list
- AI analyses patterns using a trained Random Forest model
- Get a ranked list of possible conditions with confidence scores
- Receive specialist and test recommendations instantly
""")

    with col2:
        st.markdown("""
### 🧪 Lab Results Interpreter
- Enter your lab test values manually
- Compared against validated reference ranges
- Flags abnormal values with possible concerns
- Recommends follow-up specialists and tests
""")

    st.divider()

    st.error("""
⚠️ IMPORTANT DISCLAIMER

This tool is designed for preliminary screening purposes only.
It is NOT a replacement for professional medical advice, diagnosis, or treatment.

- Always consult a qualified doctor for any health concerns
- Do not delay seeking medical help based on this tool's output
- In case of emergency, call your local emergency number (112 / 911) immediately
""")

    st.divider()
    st.markdown("""
### About this project
This AI Medical Assistant was developed as a Bachelor's Project at Caucasus University.
It demonstrates practical application of machine learning (Random Forest classifier),
natural language processing, and ethical AI development principles.

**Technologies:** Python 3.11 · scikit-learn · Streamlit · SQLite · pandas · NumPy
""")


# ── Sidebar navigation ──
with st.sidebar:
    st.title("🏥 AI Medical Assistant")
    st.caption("Preliminary screening tool — not a substitute for medical advice.")
    st.divider()

    page = st.radio(
        "Navigate to:",
        ["🏠 Home", "🩺 Symptom Assessment", "🧪 Lab Results"],
        index=0,
    )

    st.divider()
    st.markdown("""
**How to use:**
1. Go to **Symptom Assessment** to check your symptoms
2. Go to **Lab Results** to interpret your test values
3. Follow the specialist recommendations
4. Always consult a real doctor
""")
    st.divider()
    st.caption("Built with Python · scikit-learn · Streamlit")
    st.caption("Bachelor's Project — Caucasus University")


# ── Page routing ──
if page == "🏠 Home":
    _render_home()
elif page == "🩺 Symptom Assessment":
    from ui.symptom_page import render
    render()
elif page == "🧪 Lab Results":
    from ui.lab_page import render
    render()
