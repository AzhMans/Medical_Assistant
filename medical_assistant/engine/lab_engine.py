"""
engine/lab_engine.py
Interprets user-entered lab results against standard reference ranges.
Creates a fresh DB connection per call to avoid SQLite threading issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_connection, get_all_lab_tests, get_lab_test


class LabEngine:
    def __init__(self):
        # Only used for test name listing — fresh conn each time for queries
        conn = get_connection()
        self.all_tests = get_all_lab_tests(conn)
        conn.close()

    def _conn(self):
        """Always return a fresh connection (thread-safe for Streamlit)."""
        return get_connection()

    # ──────────────────────────────────────────
    # Main interpreter
    # ──────────────────────────────────────────

    def interpret(self, test_name, value, gender="general"):
        conn = self._conn()
        lab = get_lab_test(conn, test_name)
        conn.close()

        if lab is None:
            return {"error": f"Test '{test_name}' not found in database."}

        ranges = lab["ranges"]
        if gender in ranges:
            ref = ranges[gender]
        elif "general" in ranges:
            ref = ranges["general"]
        else:
            ref = list(ranges.values())[0]

        low  = ref["low"]
        high = ref["high"]

        if value < low:
            status    = "low"
            deviation = round((low - value) / low * 100, 1) if low > 0 else 0
            concern   = lab["low_concern"]
            message   = (f"{test_name} is LOW ({value} {lab['unit']}). "
                         f"Normal range: {low}–{high} {lab['unit']}. "
                         f"It is {deviation}% below the lower limit.")
        elif value > high and high < 999:
            status    = "high"
            deviation = round((value - high) / high * 100, 1) if high > 0 else 0
            concern   = lab["high_concern"]
            message   = (f"{test_name} is HIGH ({value} {lab['unit']}). "
                         f"Normal range: {low}–{high} {lab['unit']}. "
                         f"It is {deviation}% above the upper limit.")
        else:
            status    = "normal"
            deviation = 0.0
            concern   = ""
            message   = (f"{test_name} is NORMAL ({value} {lab['unit']}). "
                         f"Normal range: {low}–{high} {lab['unit']}.")

        return {"test": test_name, "value": value, "unit": lab["unit"],
                "status": status, "low": low, "high": high,
                "deviation": deviation, "concern": concern, "message": message}

    def interpret_multiple(self, entries, gender="general"):
        results  = []
        abnormal = []

        for test_name, value in entries:
            try:
                value = float(value)
            except (ValueError, TypeError):
                results.append({"error": f"Invalid value for {test_name}: {value}"})
                continue

            result = self.interpret(test_name, value, gender)
            results.append(result)
            if "status" in result and result["status"] != "normal":
                abnormal.append(result)

        if len(abnormal) >= 3:
            overall = "Multiple abnormalities detected — please consult a doctor promptly."
        elif len(abnormal) >= 1:
            overall = "Some values are outside normal range — medical review recommended."
        else:
            overall = "All values within normal range."

        return {"results": results, "abnormal": abnormal, "summary": overall,
                "total": len(results), "normal_count": len(results) - len(abnormal),
                "abnormal_count": len(abnormal)}

    # ──────────────────────────────────────────
    # Helpers for the UI
    # ──────────────────────────────────────────

    def get_test_names(self):
        return sorted([t["name"] for t in self.all_tests])

    def get_test_unit(self, test_name):
        conn = self._conn()
        lab = get_lab_test(conn, test_name)
        conn.close()
        return lab["unit"] if lab else ""

    def get_reference_range(self, test_name, gender="general"):
        conn = self._conn()
        lab = get_lab_test(conn, test_name)
        conn.close()
        if not lab:
            return None, None
        ranges = lab["ranges"]
        ref = ranges.get(gender) or ranges.get("general") or list(ranges.values())[0]
        return ref["low"], ref["high"]

    def status_emoji(self, status):
        return {"normal": "✅", "low": "🔵", "high": "🔴"}.get(status, "❓")


if __name__ == "__main__":
    engine = LabEngine()
    print("✅ Lab engine initialised")
    r = engine.interpret("Hemoglobin", 10.2, gender="female")
    print(f"{engine.status_emoji(r['status'])} {r['message']}")
    print("✅ Lab engine working correctly!")