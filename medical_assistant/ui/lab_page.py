"""
ui/lab_page.py
Streamlit page for lab results interpretation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from engine.lab_engine import LabEngine
from engine.recommender import Recommender


def get_lab_engine():
    if "lab_engine" not in st.session_state:
        st.session_state.lab_engine = LabEngine()
    return st.session_state.lab_engine


def get_recommender():
    if "recommender" not in st.session_state:
        with st.spinner("🔄 Loading AI model..."):
            st.session_state.recommender = Recommender()
    return st.session_state.recommender


def render():
    st.header("🧪 Lab Results Interpreter")
    st.write("Enter your lab test values below. The assistant will compare them against standard reference ranges and flag any abnormalities.")

    lab = get_lab_engine()
    rec = get_recommender()

    gender = st.session_state.get("gender", "general")
    st.caption(f"Using reference ranges for: **{gender}**. Change this on the Symptom Assessment page.")

    st.divider()

    test_names = lab.get_test_names()

    # ── Dynamic test entry table ──
    st.subheader("Enter your test results")
    st.caption("Select a test, enter the value, then click Add. You can add as many as you like.")

    # Store entries in session state
    if "lab_entries" not in st.session_state:
        st.session_state.lab_entries = []

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        selected_test = st.selectbox("Test name", test_names, key="lab_test_select")
    with col2:
        unit = lab.get_test_unit(selected_test)
        low, high = lab.get_reference_range(selected_test, gender)
        ref_str = f"{low}–{high} {unit}" if low is not None else unit
        value_input = st.number_input(f"Value ({unit})", min_value=0.0, step=0.1, format="%.2f", key="lab_value_input")
        st.caption(f"Normal range: {ref_str}")
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add"):
            entry = (selected_test, value_input)
            # Avoid duplicate test names
            existing_tests = [e[0] for e in st.session_state.lab_entries]
            if selected_test in existing_tests:
                idx = existing_tests.index(selected_test)
                st.session_state.lab_entries[idx] = entry
                st.toast(f"Updated {selected_test}")
            else:
                st.session_state.lab_entries.append(entry)
                st.toast(f"Added {selected_test}")

    # ── Show current entries ──
    if st.session_state.lab_entries:
        st.divider()
        st.subheader("Your entries")

        to_remove = None
        for i, (name, val) in enumerate(st.session_state.lab_entries):
            unit = lab.get_test_unit(name)
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.markdown(f"**{name}**")
            c2.markdown(f"`{val} {unit}`")
            if c3.button("🗑️", key=f"remove_{i}"):
                to_remove = i

        if to_remove is not None:
            st.session_state.lab_entries.pop(to_remove)
            st.rerun()

        if st.button("🗑️ Clear all", type="secondary"):
            st.session_state.lab_entries = []
            st.rerun()

        st.divider()

        # ── Analyse button ──
        if st.button("🔍 Interpret Results", type="primary"):
            with st.spinner("Interpreting..."):
                report = rec.recommend_from_labs(st.session_state.lab_entries, gender)

            _render_lab_results(report, lab)
            st.warning(report["disclaimer"])

    else:
        st.info("No tests added yet. Use the form above to add your results.")


def _render_lab_results(report, lab):
    """Render the lab interpretation results."""
    lab_report = report["lab_report"]

    # Summary metrics
    st.subheader("📊 Results Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tests", lab_report["total"])
    col2.metric("Normal", lab_report["normal_count"])
    col3.metric("Abnormal", lab_report["abnormal_count"],
                delta=f"{lab_report['abnormal_count']} flagged" if lab_report["abnormal_count"] > 0 else None,
                delta_color="inverse")

    if lab_report["abnormal_count"] > 0:
        st.error(f"⚠️ {lab_report['summary']}")
    else:
        st.success(f"✅ {lab_report['summary']}")

    st.divider()

    # Individual test results
    st.subheader("🔬 Detailed Results")
    for result in lab_report["results"]:
        if "error" in result:
            st.error(result["error"])
            continue

        emoji = lab.status_emoji(result["status"])
        status_color = {"normal": "normal", "low": "off", "high": "inverse"}.get(result["status"], "normal")

        with st.expander(f"{emoji} {result['test']} — {result['status'].upper()}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Your Value", f"{result['value']} {result['unit']}")
            c2.metric("Normal Low", result["low"])
            c3.metric("Normal High", result["high"] if result["high"] < 999 else "—")

            st.markdown(f"**{result['message']}**")

            if result["concern"]:
                st.warning(f"💡 Possible concern: {result['concern']}")

    st.divider()

    # Specialist recommendations
    if report["specialists"]:
        st.subheader("👨‍⚕️ Recommended Specialists")
        for s in report["specialists"]:
            st.markdown(f"- {s}")

    if report["follow_up_tests"]:
        st.subheader("🧪 Suggested Follow-up Tests")
        cols = st.columns(3)
        for i, t in enumerate(report["follow_up_tests"]):
            cols[i % 3].markdown(f"- {t}")