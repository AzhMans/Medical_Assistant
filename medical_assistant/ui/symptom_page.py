"""
ui/symptom_page.py
Streamlit page for the interactive symptom assessment.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from engine.recommender import Recommender


def get_recommender():
    if "recommender" not in st.session_state:
        with st.spinner("Loading AI model... (first load only)"):
            st.session_state.recommender = Recommender()
    return st.session_state.recommender


def render():
    st.header("🩺 Symptom Assessment")
    st.write("Select all symptoms you are currently experiencing.")

    rec = get_recommender()
    engine = rec.symptom_engine

    gender = st.radio("Your biological sex:", ["general", "male", "female"], horizontal=True)
    st.session_state["gender"] = gender

    st.divider()

    # All symptoms in clean non-overlapping categories
    categories = {
        "General": [
            "fatigue", "severe_fatigue", "fever", "mild_fever", "high_fever",
            "chills", "weight_loss", "weight_gain", "loss_of_appetite",
            "slow_healing", "post_exertional_malaise",
        ],
        "Head & Neurological": [
            "headache", "severe_headache", "dizziness", "aura",
            "light_sensitivity", "sound_sensitivity", "memory_problems",
            "concentration_problems", "cognitive_changes", "cognitive_impairment",
            "tremors", "balance_problems", "numbness", "tingling",
            "seizures", "temporary_confusion", "staring_spells",
            "loss_of_consciousness", "uncontrolled_movements",
            "slowed_movement", "rigid_muscles", "coordination_problems",
            "speech_changes", "writing_changes",
        ],
        "Face & Eyes": [
            "blurred_vision", "vision_problems", "itchy_eyes", "watery_eyes",
            "facial_drooping", "sensitivity_to_light",
        ],
        "Chest & Heart": [
            "chest_pain", "chest_discomfort", "chest_tightness",
            "palpitations", "rapid_heartbeat", "shortness_of_breath",
            "difficulty_breathing", "wheezing",
        ],
        "Respiratory": [
            "cough", "mucus", "runny_nose", "sneezing",
            "nasal_congestion", "sore_throat", "loss_of_smell", "loss_of_taste",
        ],
        "Digestive": [
            "nausea", "vomiting", "stomach_pain", "abdominal_pain",
            "severe_abdominal_pain", "upper_right_abdominal_pain",
            "severe_upper_abdominal_pain", "bloating", "indigestion",
            "heartburn", "acid_reflux", "regurgitation",
            "diarrhea", "constipation", "cramping", "mucus_in_stool",
            "rebound_tenderness", "jaundice", "dark_urine",
            "difficulty_swallowing",
        ],
        "Urinary": [
            "frequent_urination", "painful_urination", "urgency",
            "cloudy_urine", "blood_in_urine", "pelvic_pain",
            "weak_urine_stream", "nocturia", "incomplete_bladder_emptying",
        ],
        "Musculoskeletal": [
            "joint_pain", "joint_swelling", "morning_stiffness", "stiffness",
            "back_pain", "severe_back_pain", "side_pain",
            "muscle_weakness", "muscle_pain", "muscle_tension", "body_aches",
            "bone_pain", "sudden_joint_pain", "reduced_range_of_motion",
            "limited_range_of_motion", "crepitus", "tenderness",
            "warmth", "redness", "swollen_legs", "fragile_bones",
            "bone_fractures", "stooped_posture", "height_loss",
        ],
        "Skin & Hair": [
            "dry_skin", "itching", "red_rash", "red_patches", "hives",
            "swelling", "oozing", "cracked_skin", "burning",
            "thickened_nails", "brittle_nails", "pale_skin",
            "butterfly_rash", "rash", "acne", "hair_loss", "excess_hair",
        ],
        "Mental & Sleep": [
            "sadness", "hopelessness", "loss_of_interest",
            "excessive_worry", "restlessness", "anxiety", "depression",
            "mood_changes", "sleep_changes", "sleep_problems",
            "difficulty_concentrating", "irritability",
            "daytime_sleepiness", "gasping_during_sleep",
            "loud_snoring", "morning_headache",
        ],
        "Other / Systemic": [
            "cold_intolerance", "heat_intolerance", "sweating", "cold_hands",
            "nosebleed", "fainting", "irregular_periods", "painful_periods",
            "pain_during_sex", "heavy_bleeding", "speech_difficulty",
            "sudden_weakness",
        ],
    }

    # Build label map from engine
    all_labels = engine.get_all_symptom_labels()
    label_map = {k: v for k, v in all_labels}

    selected_symptoms = []

    with st.expander("📋 Select your symptoms (click to expand)", expanded=True):
        for category, symptom_keys in categories.items():
            st.markdown(f"**{category}**")
            cols = st.columns(3)
            for i, key in enumerate(symptom_keys):
                label = label_map.get(key, key.replace("_", " ").capitalize())
                # Use category name in key to guarantee uniqueness
                unique_key = f"sym_{category}_{key}"
                if cols[i % 3].checkbox(label, key=unique_key):
                    selected_symptoms.append(key)

    st.divider()

    if selected_symptoms:
        st.info(f"✅ {len(selected_symptoms)} symptom(s) selected: "
                f"{', '.join([label_map.get(s, s) for s in selected_symptoms])}")
    else:
        st.warning("Please select at least one symptom above.")

    if st.button("🔍 Analyse Symptoms", type="primary", disabled=len(selected_symptoms) == 0):
        with st.spinner("Analysing..."):
            report = rec.recommend_from_symptoms(selected_symptoms, top_n=5)

        st.divider()

        if report["type"] == "emergency":
            st.error(report["message"])
        elif report["type"] == "symptom":
            _render_symptom_results(report, label_map)
        else:
            st.warning(report["message"])

        st.warning(report["disclaimer"])


def _render_symptom_results(report, label_map):
    severity_color = {"mild": "🟢", "moderate": "🟡", "severe": "🔴"}.get(report["severity"], "⚪")
    st.subheader("📊 Analysis Results")

    col1, col2, col3 = st.columns(3)
    col1.metric("Top Match", report["top_condition"])
    col2.metric("Confidence", f"{report['confidence']}%")
    col3.metric("Severity", f"{severity_color} {report['severity'].capitalize()}")

    st.divider()
    st.subheader("🏥 Possible Conditions")

    for i, pred in enumerate(report["predictions"]):
        sev = {"mild": "🟢", "moderate": "🟡", "severe": "🔴"}.get(pred["severity"], "⚪")
        with st.expander(f"{i+1}. {pred['name']} — {pred['confidence']}% {sev}"):
            col_a, col_b = st.columns(2)
            col_a.markdown(f"**Specialist:** {pred['specialist']}")
            col_b.markdown(f"**Severity:** {pred['severity'].capitalize()}")
            matched = [label_map.get(s, s) for s in pred["matched_symptoms"]]
            st.markdown(f"**Matching symptoms:** {', '.join(matched) if matched else 'None'}")
            if pred["tests"]:
                st.markdown(f"**Recommended tests:** {', '.join(pred['tests'])}")

    st.divider()
    st.subheader("👨‍⚕️ Recommended Specialists")
    for specialist in report["specialists"]:
        st.markdown(f"- {specialist}")

    if report["tests"]:
        st.subheader("🧪 Recommended Tests")
        test_cols = st.columns(3)
        for i, test in enumerate(report["tests"]):
            test_cols[i % 3].markdown(f"- {test}")

    if report.get("otc"):
        st.divider()
        st.subheader("💊 General Self-Care Suggestion")
        st.info(report["otc"])