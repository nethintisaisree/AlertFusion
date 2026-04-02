# ALERTFUSION - Intelligent Emergency Alert Prioritization System

A final year project for Bachelor of Computer Applications.

An AI + ML + Rule-based hybrid system that receives emergency reports from users, evaluates them through a multi-layer pipeline, and assigns one of five escalation decisions — all while detecting and soft-preventing misuse without permanently blocking users.

---

## 🚨 What It Does

Users submit emergency reports with their name, phone number, location, emergency type, and a description. The system processes each report through:

- **ML Classifier** — TF-IDF + Logistic Regression trained on emergency messages.
- **AI Semantic Engine** — spaCy NLP similarity and concept scoring.
- **Risk Engine** — keyword severity analysis.
- **Scoring Engine** — priority, credibility, and Emergency Credibility Score (ECS).
- **Trust Engine** — user behavioral history and soft-prevention layer.
- **Misuse Detection** — flags pranks and fake reports without blocking users.
- **Decision Engine** — combines all signals into a final escalation decision.
- **Explainability Engine** — generates a human-readable breakdown of every decision.

---

## 📋 Five Decision Categories

| Decision | Meaning |
|---|---|
| `IMMEDIATE_ESCALATION` | Critical emergency — immediate response required |
| `CONDITIONAL_ESCALATION` | Potential danger — escalate with verification |
| `REVIEW_REQUIRED` | Ambiguous situation — human review needed |
| `LOG_AND_MONITOR` | Low risk — logged for monitoring |
| `SUSPECTED_MISUSE` | Suspicious behavior — flagged, user not blocked |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask |
| Database | MySQL |
| ML Model | scikit-learn (TF-IDF + Logistic Regression) |
| AI Semantic Engine | spaCy (en_core_web_md) |
| Templating | Jinja2 (HTML templates) |
| Environment Config | python-dotenv |

---

## ⚙️ Requirements

- Python **3.11.x** (recommended — tested on 3.11.8)
- MySQL Server (5.7+ or 8.0+)
- Git

---

## 🚀 Setup Instructions

### 1. Clone the project

```bash
git clone <your-repo-url>
cd intelligent_emergency_alert_system
```

### 2. Create and activate virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> This installs all packages including the spaCy `en_core_web_md` model automatically.

### 4. Create your `.env` file

Create a file called `.env` in the project root (same folder as `run.py`) with the following contents:

```
SECRET_KEY=your-random-secret-key-here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=emergency_alert_db
DB_PORT=3306
FLASK_DEBUG=true
```

> `.env` is listed in `.gitignore` and will never be committed. Each person running the project creates their own.

### 5. Set up the database

Open MySQL and run:

```sql
CREATE DATABASE emergency_alert_db;
USE emergency_alert_db;
SOURCE path/to/app/database/schema.sql;
```

Or from terminal:

```bash
mysql -u root -p emergency_alert_db < app/database/schema.sql
```

### 6. Train the ML model

```bash
python train_model.py
```

This generates `model/emergency_model.pkl` and `model/vectorizer.pkl`.
You will see a classification report printed — check the accuracy before running the app.

### 7. Run the application

```bash
python run.py
```

Open your browser and go to:
```
http://localhost:5000
```

---

## 📁 Project Structure

```
intelligent_emergency_alert_system/
├── app/
│   ├── database/
│   │   └── schema.sql              — MySQL table definitions
│   ├── db/
│   │   └── db_handler.py           — Database read/write operations
│   ├── services/
│   │   ├── ai_engine.py            — spaCy semantic scoring
│   │   ├── decision_engine.py      — Final escalation logic
│   │   ├── explainability.py       — Human-readable decision breakdown
│   │   ├── misuse_detection.py     — Soft-prevention layer
│   │   ├── ml_engine.py            — ML model classification
│   │   ├── pipeline.py             — Central processing pipeline
│   │   ├── risk_engine.py          — Keyword + AI risk scoring
│   │   ├── scoring_engine.py       — Priority, credibility, ECS
│   │   └── trust_engine.py         — User trust management
│   ├── templates/
│   │   ├── base.html               — Shared layout and CSS
│   │   ├── report.html             — Emergency report form
│   │   ├── result.html             — Decision result page
│   │   ├── admin_alerts.html       — Admin alerts dashboard
│   │   ├── admin_audit.html        — Full audit log
│   │   └── ethics.html             — Ethics and governance page
│   ├── __init__.py                 — Flask app factory
│   ├── config.py                   — Environment-based configuration
│   ├── models.py                   — Database connection manager
│   └── routes.py                   — Flask route handlers
├── dataset/
│   └── emergency_dataset.csv       — Training data for ML model
├── model/
│   ├── emergency_model.pkl         — Trained ML model (generated)
│   └── vectorizer.pkl              — TF-IDF vectorizer (generated)
├── venv
├── .env                            — Local credentials (not committed)
├── .gitignore
├── README.md
├── requirements.txt
├── run.py                          — Application entry point
└── train_model.py                  — ML model training script
```

---

## 🌐 Pages

| URL | Description |
|---|---|
| `http://localhost:5000/` | Home — redirects to report form |
| `http://localhost:5000/report` | Submit an emergency report |
| `http://localhost:5000/admin/alerts` | Admin dashboard — all alerts |
| `http://localhost:5000/admin/audit` | Full audit log with scores |
| `http://localhost:5000/ethics` | Ethics and AI governance page |

---

## 🧪 Quick Test

After setup, submit this test report:

- **Name:** Test User
- **Phone:** 9876543210
- **Location:** Hyderabad, Block C
- **Emergency Type:** Fire
- **Message:** There is a fire on the third floor, people are trapped and not breathing

Expected result: `IMMEDIATE_ESCALATION` with high risk and priority scores.

---

## 🔒 Security Notes

- Database credentials are stored in `.env` — never committed to version control
- `misuse_count` is fetched from the database only — cannot be manipulated via the form
- Users flagged for misuse are never permanently blocked — trust scores are reduced and recoverable
- All decisions are logged in the audit table for full traceability

---

## 👨‍💻 Author
Nethinti Saisree.

**Bachelor of Computer Applications — Final Year Project**
Intelligent Emergency Alert Prioritization System