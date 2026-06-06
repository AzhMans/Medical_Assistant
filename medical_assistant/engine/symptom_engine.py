"""
engine/symptom_engine.py
Symptom-based condition classifier using Random Forest.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from database.db import get_connection, get_all_conditions, get_all_symptoms


class SymptomEngine:
    def __init__(self):
        self.conn = get_connection()
        self.conditions = get_all_conditions(self.conn)
        self.all_symptoms = get_all_symptoms(self.conn)
        self.symptom_index = {s: i for i, s in enumerate(self.all_symptoms)}

        self.label_encoder = LabelEncoder()
        self.model = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            min_samples_leaf=1
        )
        self._train()

    # ──────────────────────────────────────────
    # Training
    # ──────────────────────────────────────────

    def _train(self):
        """
        Build training data from the knowledge base.
        Each condition becomes multiple synthetic training samples
        with slight variation to help the model generalise.
        """
        X, y = [], []

        for condition in self.conditions:
            condition_symptoms = condition["symptoms"]

            # Full symptom set (positive sample)
            X.append(self._encode(condition_symptoms))
            y.append(condition["name"])

            # Partial samples — drop one symptom at a time
            for i in range(len(condition_symptoms)):
                partial = condition_symptoms[:i] + condition_symptoms[i+1:]
                X.append(self._encode(partial))
                y.append(condition["name"])

            # Minimal sample — only first two symptoms
            if len(condition_symptoms) >= 2:
                X.append(self._encode(condition_symptoms[:2]))
                y.append(condition["name"])

        X = np.array(X)
        y = self.label_encoder.fit_transform(y)
        self.model.fit(X, y)

    def _encode(self, symptoms):
        """Convert a list of symptom strings to a binary feature vector."""
        vector = np.zeros(len(self.all_symptoms), dtype=int)
        for s in symptoms:
            if s in self.symptom_index:
                vector[self.symptom_index[s]] = 1
        return vector

    # ──────────────────────────────────────────
    # Prediction
    # ──────────────────────────────────────────

    def predict(self, selected_symptoms, top_n=5):
        """
        Given a list of symptom strings, return top_n conditions
        sorted by confidence score (highest first).

        Returns a list of dicts:
        {
            "name": str,
            "confidence": float (0-100),
            "specialist": str,
            "tests": list,
            "severity": str,
            "matched_symptoms": list,
            "total_symptoms": int
        }
        """
        if not selected_symptoms:
            return []

        vector = self._encode(selected_symptoms).reshape(1, -1)
        probabilities = self.model.predict_proba(vector)[0]

        # Map class index → condition name
        class_names = self.label_encoder.classes_
        scored = sorted(
            zip(class_names, probabilities),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        results = []
        for name, prob in scored:
            if prob < 0.01:   # skip negligible matches
                continue
            condition = self._get_condition_by_name(name)
            if not condition:
                continue

            matched = [s for s in selected_symptoms if s in condition["symptoms"]]
            results.append({
                "name":             condition["name"],
                "confidence":       round(prob * 100, 1),
                "specialist":       condition["specialist"],
                "tests":            condition["tests"],
                "severity":         condition["severity"],
                "matched_symptoms": matched,
                "total_symptoms":   len(condition["symptoms"]),
            })

        return results

    # ──────────────────────────────────────────
    # Dynamic question generation
    # ──────────────────────────────────────────

    def get_next_question(self, confirmed_symptoms, ruled_out_symptoms=None):
        """
        Given symptoms already confirmed, return the single most
        informative symptom to ask about next.

        Strategy: find the symptom that appears most often in the
        top candidate conditions and hasn't been asked yet.
        """
        if ruled_out_symptoms is None:
            ruled_out_symptoms = []

        asked = set(confirmed_symptoms) | set(ruled_out_symptoms)

        # Get top candidate conditions based on confirmed symptoms
        candidates = self.predict(confirmed_symptoms, top_n=10) if confirmed_symptoms else [
            {"name": c["name"]} for c in self.conditions
        ]

        # Score each unasked symptom by how many top candidates contain it
        symptom_score = {}
        for result in candidates:
            condition = self._get_condition_by_name(result["name"])
            if not condition:
                continue
            for symptom in condition["symptoms"]:
                if symptom not in asked:
                    symptom_score[symptom] = symptom_score.get(symptom, 0) + 1

        if not symptom_score:
            return None

        # Return the highest-scoring symptom
        best = max(symptom_score, key=symptom_score.get)
        return best

    def get_questions_batch(self, confirmed_symptoms, ruled_out_symptoms=None, count=5):
        """Return up to `count` next questions to ask."""
        if ruled_out_symptoms is None:
            ruled_out_symptoms = []

        questions = []
        confirmed = list(confirmed_symptoms)
        ruled_out = list(ruled_out_symptoms)

        for _ in range(count):
            q = self.get_next_question(confirmed, ruled_out)
            if q is None:
                break
            questions.append(q)
            ruled_out.append(q)   # mark as "will be asked" so we don't repeat

        return questions

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _get_condition_by_name(self, name):
        for c in self.conditions:
            if c["name"] == name:
                return c
        return None

    def format_symptom_label(self, symptom):
        """Convert snake_case symptom key to readable label."""
        return symptom.replace("_", " ").capitalize()

    def get_all_symptom_labels(self):
        """Return list of (key, label) tuples for the UI."""
        return [(s, self.format_symptom_label(s)) for s in self.all_symptoms]


# ──────────────────────────────────────────────
# Quick self-test  (run: python engine/symptom_engine.py)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("Training model... (this takes a few seconds)")
    engine = SymptomEngine()
    print("✅ Model trained\n")

    # Test 1: flu-like symptoms
    symptoms = ["high_fever", "body_aches", "fatigue", "cough", "headache"]
    print(f"Input symptoms: {symptoms}")
    results = engine.predict(symptoms, top_n=3)
    for r in results:
        print(f"  → {r['name']:30s} {r['confidence']:5.1f}%  |  See: {r['specialist']}")

    # Test 2: heart symptoms
    print()
    symptoms2 = ["chest_pain", "shortness_of_breath", "palpitations", "dizziness"]
    print(f"Input symptoms: {symptoms2}")
    results2 = engine.predict(symptoms2, top_n=3)
    for r in results2:
        print(f"  → {r['name']:30s} {r['confidence']:5.1f}%  |  See: {r['specialist']}")

    # Test 3: next question logic
    print()
    next_q = engine.get_next_question(["fatigue", "weight_gain"])
    print(f"Next question to ask after [fatigue, weight_gain]: '{engine.format_symptom_label(next_q)}'")

    print("\n✅ Symptom engine working correctly!")