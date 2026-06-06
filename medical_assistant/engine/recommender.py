"""
engine/recommender.py
Combines symptom predictions and lab results into a final
recommendation: which specialist to see and which tests to take.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.symptom_engine import SymptomEngine
from engine.lab_engine import LabEngine

DISCLAIMER = """
⚠️  IMPORTANT DISCLAIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This tool is NOT a substitute for professional medical advice.
It is a preliminary screening aid only.
Always consult a qualified doctor for diagnosis and treatment.
In case of emergency, call your local emergency number immediately.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# Conditions where we allow a basic OTC suggestion (mild, self-resolving)
OTC_SUGGESTIONS = {
    "Common Cold": "Rest, fluids, and over-the-counter decongestants (e.g. paracetamol for fever). Consult a doctor if symptoms worsen or last more than 10 days.",
    "Tension Headache": "Rest in a quiet dark room, stay hydrated, over-the-counter pain relievers (e.g. ibuprofen or paracetamol) may help. See a doctor if headaches are frequent.",
    "Allergic Rhinitis": "Over-the-counter antihistamines (e.g. cetirizine) may relieve symptoms. Avoid known allergens. See an Allergist for persistent symptoms.",
}

# Emergency symptoms that require immediate action
EMERGENCY_SYMPTOMS = {
    "facial_drooping", "sudden_weakness", "speech_difficulty",
    "loss_of_consciousness", "seizures", "severe_chest_pain",
    "difficulty_breathing", "uncontrolled_movements"
}


class Recommender:
    def __init__(self):
        self.symptom_engine = SymptomEngine()
        self.lab_engine     = LabEngine()

    # ──────────────────────────────────────────
    # Main recommendation entry points
    # ──────────────────────────────────────────

    def recommend_from_symptoms(self, symptoms, top_n=3):
        """
        Given a list of symptom keys, return a full recommendation report.
        """
        # Emergency check first
        emergency = self._check_emergency(symptoms)
        if emergency:
            return self._emergency_report(emergency)

        predictions = self.symptom_engine.predict(symptoms, top_n=top_n)
        if not predictions:
            return {"type": "no_match", "message": "Could not identify a condition. Please consult a General Practitioner.", "disclaimer": DISCLAIMER}

        top = predictions[0]
        specialists = self._collect_specialists(predictions)
        tests       = self._collect_tests(predictions)
        otc         = OTC_SUGGESTIONS.get(top["name"])

        return {
            "type":         "symptom",
            "top_condition": top["name"],
            "confidence":   top["confidence"],
            "severity":     top["severity"],
            "predictions":  predictions,
            "specialists":  specialists,
            "tests":        tests,
            "otc":          otc,
            "disclaimer":   DISCLAIMER,
        }

    def recommend_from_labs(self, entries, gender="general"):
        """
        Given lab entries [(test_name, value), ...], return a recommendation report.
        """
        report    = self.lab_engine.interpret_multiple(entries, gender)
        abnormal  = report["abnormal"]

        specialists = []
        tests       = []

        # Map abnormal lab tests → likely conditions → specialists
        for item in abnormal:
            mapped = self._map_lab_to_conditions(item["test"])
            for condition in mapped:
                if condition["specialist"] not in specialists:
                    specialists.append(condition["specialist"])
                for t in condition["tests"]:
                    if t not in tests:
                        tests.append(t)

        if not specialists:
            specialists = ["General Practitioner"]

        return {
            "type":        "lab",
            "lab_report":  report,
            "specialists": specialists,
            "follow_up_tests": tests[:6],  # limit to top 6
            "disclaimer":  DISCLAIMER,
        }

    def recommend_combined(self, symptoms, lab_entries, gender="general"):
        """
        Combine symptom + lab analysis into one unified report.
        """
        emergency = self._check_emergency(symptoms)
        if emergency:
            return self._emergency_report(emergency)

        symptom_report = self.recommend_from_symptoms(symptoms)
        lab_report     = self.recommend_from_labs(lab_entries, gender)

        # Merge specialist lists (preserve order, no duplicates)
        all_specialists = list(dict.fromkeys(
            symptom_report.get("specialists", []) +
            lab_report.get("specialists", [])
        ))

        all_tests = list(dict.fromkeys(
            symptom_report.get("tests", []) +
            lab_report.get("follow_up_tests", [])
        ))

        return {
            "type":            "combined",
            "symptom_section": symptom_report,
            "lab_section":     lab_report,
            "specialists":     all_specialists,
            "tests":           all_tests[:8],
            "disclaimer":      DISCLAIMER,
        }

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _check_emergency(self, symptoms):
        """Return list of emergency symptoms found, or empty list."""
        return [s for s in symptoms if s in EMERGENCY_SYMPTOMS]

    def _emergency_report(self, emergency_symptoms):
        labels = [self.symptom_engine.format_symptom_label(s) for s in emergency_symptoms]
        return {
            "type":      "emergency",
            "message":   (
                "🚨 EMERGENCY: The following symptoms may indicate a life-threatening condition: "
                + ", ".join(labels) +
                ". Please call emergency services (112 / 911) immediately."
            ),
            "disclaimer": DISCLAIMER,
        }

    def _collect_specialists(self, predictions):
        """Deduplicated list of specialists from predictions."""
        seen = []
        for p in predictions:
            if p["specialist"] not in seen:
                seen.append(p["specialist"])
        return seen

    def _collect_tests(self, predictions):
        """Deduplicated list of recommended tests from predictions."""
        seen = []
        for p in predictions:
            for t in p["tests"]:
                if t not in seen:
                    seen.append(t)
        return seen[:8]  # cap at 8

    def _map_lab_to_conditions(self, test_name):
        """
        Return conditions that commonly involve this lab test.
        Simple keyword matching against condition test lists.
        """
        all_conditions = self.symptom_engine.conditions
        matched = []
        test_lower = test_name.lower()
        for c in all_conditions:
            for t in c["tests"]:
                if test_lower in t.lower() or t.lower() in test_lower:
                    matched.append(c)
                    break
        return matched[:3]  # top 3 relevant conditions


# ──────────────────────────────────────────────
# Quick self-test  (run: python engine/recommender.py)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("Initialising recommender (training model)...")
    rec = Recommender()
    print("✅ Recommender ready\n")

    # Test 1: symptom-based recommendation
    symptoms = ["high_fever", "cough", "fatigue", "body_aches", "chills"]
    report = rec.recommend_from_symptoms(symptoms)
    print("── Symptom Report ──────────────────────────")
    print(f"Top condition : {report['top_condition']} ({report['confidence']}%)")
    print(f"Severity      : {report['severity']}")
    print(f"See           : {', '.join(report['specialists'])}")
    print(f"Tests         : {', '.join(report['tests'][:3]) if report['tests'] else 'None'}")

    # Test 2: lab-based recommendation
    print("\n── Lab Report ──────────────────────────────")
    lab_entries = [("Hemoglobin", 9.5), ("Ferritin", 8), ("Vitamin D (25-OH)", 15)]
    lab_report = rec.recommend_from_labs(lab_entries, gender="female")
    print(f"Abnormal tests : {lab_report['lab_report']['abnormal_count']}/{lab_report['lab_report']['total']}")
    print(f"See            : {', '.join(lab_report['specialists'])}")
    print(f"Summary        : {lab_report['lab_report']['summary']}")

    # Test 3: emergency detection
    print("\n── Emergency Test ──────────────────────────")
    emerg = rec.recommend_from_symptoms(["facial_drooping", "sudden_weakness", "speech_difficulty"])
    print(emerg["message"])

    print("\n✅ Recommender working correctly!")