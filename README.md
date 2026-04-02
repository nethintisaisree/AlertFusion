# AlertFusion — Intelligent Emergency Alert Prioritization System

A final year project for Bachelor of Computer Applications.

An AI + ML + Rule-based hybrid system that receives emergency reports from users, evaluates them through a multi-layer pipeline, and assigns one of five escalation decisions — all while detecting and soft-preventing misuse without permanently blocking users.

---

## 🚨 What It Does

Users submit emergency reports with their name, phone number, location, emergency type, and a description. The system processes each report through:

- **ML Classifier** — TF-IDF + Logistic Regression trained on 390 balanced emergency messages
- **AI Semantic Engine** — spaCy NLP similarity and concept scoring
- **Risk Engine** — keyword severity analysis with per-category score capping
- **Scoring Engine** — priority, credibility, and Emergency Credibility Score (ECS)
- **Trust Engine** — user behavioral history and soft-prevention layer
- **Misuse Detection** — flags pranks and fake reports without permanently blocking users
- **Decision Engine** — combines all signals into a final escalation decision
- **Explainability Engine** — generates a human-readable breakdown of every decision

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
| Admin Security | Flask session-based login |

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
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
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
│   │   ├── ai_engine.py            — spaCy semantic scoring + analyze_with_ai()
│   │   ├── decision_engine.py      — Final escalation logic
│   │   ├── explainability.py       — Human-readable decision breakdown
│   │   ├── misuse_detection.py     — Soft-prevention layer
│   │   ├── ml_engine.py            — ML model classification (safe loading)
│   │   ├── pipeline.py             — Central processing pipeline
│   │   ├── risk_engine.py          — Keyword + AI risk scoring
│   │   ├── scoring_engine.py       — Priority, credibility, ECS
│   │   └── trust_engine.py         — User trust management
│   ├── templates/
│   │   ├── base.html               — Shared layout, CSS and navbar
│   │   ├── report.html             — Emergency report form
│   │   ├── result.html             — Decision result page with ECS + confirmation
│   │   ├── admin_login.html        — Admin login page (secure access)
│   │   ├── admin_alerts.html       — Admin alerts dashboard (login required)
│   │   ├── admin_audit.html        — Full audit log (login required)
│   │   └── ethics.html             — Ethics and AI governance page
│   ├── __init__.py                 — Flask app factory
│   ├── config.py                   — Environment-based configuration
│   ├── models.py                   — Database connection manager
│   └── routes.py                   — Flask route handlers + admin auth
├── dataset/
│   └── emergency_dataset.csv       — 390-row balanced training dataset
├── model/
│   ├── emergency_model.pkl         — Trained ML model (generated)
│   └── vectorizer.pkl              — TF-IDF vectorizer (generated)
├── .env                            — Local credentials (not committed)
├── .gitignore
├── README.md
├── requirements.txt
├── run.py                          — Application entry point
└── train_model.py                  — ML model training script
```

---

## 🌐 Pages

| URL | Access | Description |
|---|---|---|
| `http://localhost:5000/` | Public | Home — redirects to report form |
| `http://localhost:5000/report` | Public | Submit an emergency report |
| `http://localhost:5000/ethics` | Public | Ethics and AI governance page |
| `http://localhost:5000/admin/login` | Public | Admin login page |
| `http://localhost:5000/admin/alerts` | Admin only | All alerts dashboard |
| `http://localhost:5000/admin/audit` | Admin only | Full audit log with scores |
| `http://localhost:5000/admin/logout` | Admin only | Logs out and returns to login |

---

## 🔐 Admin Access

The admin dashboard and audit log are protected by session-based login.

- Navigate to `http://localhost:5000/admin/login`
- Enter the credentials set in your `.env` file (`ADMIN_USERNAME` and `ADMIN_PASSWORD`)
- After login, Dashboard and Audit links appear in the navbar
- Direct URL access to `/admin/alerts` or `/admin/audit` without login redirects to the login page

---

## 🧪 Quick Test

After setup, submit these test reports to verify all 5 decision categories:

| Name | Phone | Location | Type | Message | Expected |
|---|---|---|---|---|---|
| Ravi Kumar | 9876543210 | Hyderabad, Block C | Fire | There is a fire on the third floor, people are trapped and not breathing | `IMMEDIATE_ESCALATION` |
| Priya Sharma | 9123456780 | Secunderabad | Crime | Someone is following me and acting suspicious near my house | `CONDITIONAL_ESCALATION` |
| Sneha Patel | 9988776655 | Banjara Hills | Other | There is a pothole on the road near my house causing minor inconvenience | `LOG_AND_MONITOR` |
| Test User | 1234567890 | Nowhere | Other | lol this is just a fake prank not a real emergency just testing | `SUSPECTED_MISUSE` |

---

## 🔒 Security Notes

- Database credentials stored in `.env` — never committed to version control
- Admin credentials (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) stored in `.env` — never hardcoded
- Admin routes protected by Flask session — direct URL access redirects to login page
- `misuse_count` fetched from database only — cannot be manipulated via the form
- Users flagged for misuse are never permanently blocked — trust scores are reduced and recoverable
- All decisions are logged in the audit table for full traceability

---

## 👩‍💻 Author

**Nethinti Saisree**
Bachelor of Computer Applications — Final Year Project
St. Paul's Degree & PG College, Department of Computer Science
Affiliated with Osmania University, Hyderabad