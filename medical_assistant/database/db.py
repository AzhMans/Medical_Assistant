"""
database/db.py
Loads conditions.json and lab_ranges.json into SQLite.
Uses a fresh connection per call to avoid threading issues with Streamlit.
"""

import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONDITIONS_PATH = os.path.join(BASE_DIR, "data", "conditions.json")
LAB_RANGES_PATH = os.path.join(BASE_DIR, "data", "lab_ranges.json")


def get_connection():
    """Create and return a new SQLite in-memory connection with data loaded."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    _load_data(conn)
    return conn


def _create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conditions (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            specialist  TEXT NOT NULL,
            severity    TEXT NOT NULL,
            tests       TEXT NOT NULL,
            symptoms    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS lab_tests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            unit            TEXT NOT NULL,
            ranges          TEXT NOT NULL,
            low_concern     TEXT NOT NULL,
            high_concern    TEXT NOT NULL
        );
    """)
    conn.commit()


def _load_data(conn):
    with open(CONDITIONS_PATH, "r", encoding="utf-8") as f:
        conditions = json.load(f)["conditions"]

    conn.executemany(
        "INSERT INTO conditions (id, name, specialist, severity, tests, symptoms) VALUES (:id, :name, :specialist, :severity, :tests, :symptoms)",
        [{"id": c["id"], "name": c["name"], "specialist": c["specialist"],
          "severity": c["severity"], "tests": json.dumps(c["tests"]), "symptoms": json.dumps(c["symptoms"])}
         for c in conditions],
    )

    with open(LAB_RANGES_PATH, "r", encoding="utf-8") as f:
        lab_tests = json.load(f)["lab_tests"]

    conn.executemany(
        "INSERT INTO lab_tests (name, unit, ranges, low_concern, high_concern) VALUES (:name, :unit, :ranges, :low_concern, :high_concern)",
        [{"name": lt["name"], "unit": lt["unit"], "ranges": json.dumps(lt["ranges"]),
          "low_concern": lt["low_concern"], "high_concern": lt["high_concern"]}
         for lt in lab_tests],
    )
    conn.commit()


def get_all_conditions(conn):
    rows = conn.execute("SELECT * FROM conditions").fetchall()
    return [_parse_condition(row) for row in rows]


def get_condition_by_id(conn, condition_id):
    row = conn.execute("SELECT * FROM conditions WHERE id = ?", (condition_id,)).fetchone()
    return _parse_condition(row) if row else None


def get_all_symptoms(conn):
    rows = conn.execute("SELECT symptoms FROM conditions").fetchall()
    symptom_set = set()
    for row in rows:
        symptom_set.update(json.loads(row["symptoms"]))
    return sorted(symptom_set)


def get_lab_test(conn, name):
    row = conn.execute("SELECT * FROM lab_tests WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
    return _parse_lab_test(row) if row else None


def get_all_lab_tests(conn):
    rows = conn.execute("SELECT * FROM lab_tests").fetchall()
    return [_parse_lab_test(row) for row in rows]


def _parse_condition(row):
    return {"id": row["id"], "name": row["name"], "specialist": row["specialist"],
            "severity": row["severity"], "tests": json.loads(row["tests"]), "symptoms": json.loads(row["symptoms"])}


def _parse_lab_test(row):
    return {"name": row["name"], "unit": row["unit"], "ranges": json.loads(row["ranges"]),
            "low_concern": row["low_concern"], "high_concern": row["high_concern"]}


if __name__ == "__main__":
    conn = get_connection()
    conditions = get_all_conditions(conn)
    print(f"Loaded {len(conditions)} conditions")
    lab_tests = get_all_lab_tests(conn)
    print(f"Loaded {len(lab_tests)} lab tests")
    print("Database module working correctly!")
