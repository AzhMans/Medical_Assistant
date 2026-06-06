# AI Medical Assistant

A machine learning-powered preliminary health screening tool built as a Bachelor's Project at Caucasus University, Computer Science Program.

**Disclaimer:** This tool is for preliminary screening purposes only and is NOT a substitute for professional medical advice. Always consult a qualified doctor.

---

## Project Overview

The AI Medical Assistant is a web-based application that helps users identify possible medical conditions based on their symptoms and interpret their lab test results. It uses a trained Random Forest classifier to analyse symptom patterns across 50 conditions and compares lab values against validated reference ranges.

---

## Features

- **Symptom Assessment** — Select symptoms from a categorised list; the AI ranks possible conditions with confidence scores and recommends the appropriate specialist and tests
- **Lab Results Interpreter** — Enter lab test values and get instant interpretation against standard reference ranges with flagged abnormalities
- **Emergency Detection** — Automatically detects life-threatening symptom combinations and triggers an emergency alert
- **Specialist Recommendations** — Directs users to the right medical specialist based on their symptoms or abnormal lab results
- **Self-Care Suggestions** — Provides basic OTC guidance for mild, self-resolving conditions

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.11 | Core language |
| scikit-learn | Random Forest ML classifier |
| Streamlit | Web UI framework |
| SQLite (in-memory) | Knowledge base storage |
| pandas and NumPy | Data processing |
| pytest | Unit testing |

---

## Project Structure

```
medical_assistant/
│
├── app.py                  # Main Streamlit entry point
├── requirements.txt        # Dependencies
├── README.md
│
├── data/
│   ├── conditions.json     # 50 medical conditions with symptoms
│   └── lab_ranges.json     # 22 lab tests with reference ranges
│
├── database/
│   └── db.py               # SQLite setup and query helpers
│
├── engine/
│   ├── symptom_engine.py   # Random Forest classifier and question logic
│   ├── lab_engine.py       # Lab result interpreter
│   └── recommender.py      # Specialist and test recommender
│
├── ui/
│   ├── symptom_page.py     # Streamlit symptom assessment page
│   └── lab_page.py         # Streamlit lab results page
│
└── tests/
    └── test_engines.py     # pytest unit tests
```

---

## Installation and Setup

### Prerequisites
- Python 3.9 or higher
- pip

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/medical_assistant.git
cd medical_assistant
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the application**
```bash
streamlit run app.py
```
On Windows:
```bash
python -m streamlit run app.py
```

**4. Open in browser**

Navigate to `http://localhost:8501`

---

## How the AI Works

The symptom engine uses a Random Forest Classifier trained on a knowledge base of 50 medical conditions. Each condition is represented as a binary feature vector where each dimension corresponds to a possible symptom (present = 1, absent = 0).

**Training data generation:**
For each condition, multiple synthetic training samples are created by systematically removing symptoms one at a time, teaching the model to recognise partial symptom patterns. This results in a robust classifier that handles real-world scenarios where patients only report some of their symptoms.

**Prediction:**
User-selected symptoms are encoded into the same binary vector format. The model returns probability scores for all 50 conditions, ranked by confidence and enriched with specialist and test recommendations.

---

## Running Tests

```bash
pytest tests/test_engines.py -v
```

---

## Knowledge Base

- 50 medical conditions across 15 specialties including Cardiology, Neurology, and Endocrinology
- 22 lab tests with gender-specific reference ranges where applicable
- Over 100 unique symptoms used as ML features

---

## Ethical Considerations

- The application displays a clear medical disclaimer on every result page
- Emergency symptoms such as stroke signs and seizures trigger an immediate emergency alert
- No user data is stored — all processing is done in memory per session
- Built in compliance with responsible AI development principles

---

## Author

Bachelor's Program — Computer Science
Caucasus University
2026

---

## License

This project is submitted as an academic Bachelor's Project. All code is original work by the author.
