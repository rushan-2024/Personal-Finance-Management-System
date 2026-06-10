# ⚡ FinFlow — Personal Finance Management System

> A production-ready, full-stack fintech web application built with Flask, PostgreSQL, and modern frontend tooling. Features JWT authentication, AI-powered insights, receipt OCR scanning, PDF/Excel export, budget management, financial goals tracking, and a full REST API.

---

## 🖼️ Screenshots

### Dashboard
<img width="960" height="540" alt="dashboard" src="https://github.com/user-attachments/assets/8e9a712c-f056-46cb-9f7c-063b660d9d8d" />
<img width="960" height="540" alt="dashboard-dark" src="https://github.com/user-attachments/assets/0c6deeec-b6cf-46e4-a3fe-31e3ec828186" />

### Transactions
<img width="960" height="540" alt="transactions" src="https://github.com/user-attachments/assets/f3ed72fa-0889-4c47-88d8-bde6a6f8626f" />
<img width="960" height="540" alt="add-transaction" src="https://github.com/user-attachments/assets/afc2a5fa-b9e1-4c39-8bbc-ce197ba9df41" />

### Budgets & Goals
| Budgets | Goals |
|---|---|
| <img width="954" height="540" alt="budgets" src="https://github.com/user-attachments/assets/36a690c8-9de3-406c-b9ea-da3abeace0db" /> | <img width="960" height="540" alt="goals" src="https://github.com/user-attachments/assets/557b9fe8-8d8f-4035-9fdc-8b83617acbf3" /> |

### Export Reports
<img width="960" height="540" alt="reports" src="https://github.com/user-attachments/assets/5dcd189a-a999-4fdc-be65-3dfc033921b1" />

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Auth | JWT + session auth, bcrypt hashing, remember-me, CSRF protection |
| 📊 Dashboard | Balance, income/expense cards, 6-month charts, recent transactions |
| 💳 Transactions | Add / edit / delete / search / filter / paginate |
| 📁 Categories | Default + custom income/expense categories with icons and colors |
| 📈 Analytics | Line charts, doughnut charts, savings rate trend |
| 💰 Budgets | Monthly budgets, progress bars, auto alerts at custom threshold |
| 🎯 Goals | Financial goals with progress tracking and deadline |
| 🧠 AI Insights | Rule-based smart insights: savings rate, overspending, trends |
| 📄 PDF Export | Branded PDF reports using ReportLab |
| 📊 Excel Export | Multi-sheet XLSX with transactions + summary |
| 📋 CSV Export | Raw CSV for external analysis |
| 🧾 OCR Scanning | Tesseract + OpenCV receipt scanning (extracts amount, date, merchant) |
| 📧 Email Alerts | Monthly reports + budget alerts via Flask-Mail |
| 💱 Multi-currency | INR / USD / EUR / GBP with live exchange rates |
| 🌙 Dark Mode | Full dark mode toggle, persisted in localStorage |
| 🔌 REST API | Full JWT-protected API for all resources |
| 🐳 Docker | Dockerfile + Docker Compose + Nginx reverse proxy |
| 🚀 CI/CD | GitHub Actions: test → lint → Docker build → deploy |
| ✅ Tests | pytest unit + integration + API tests (20+) |

---

## 🗂️ Project Structure

```
Personal-Finance-Management-System/
│
├── app/
│   ├── __init__.py                  # App factory, all extensions
│   │
│   ├── models/
│   │   └── __init__.py              # User, Transaction, Category, Budget, Goal, Notification
│   │
│   ├── auth/
│   │   └── __init__.py              # Signup, login, logout, profile, category seeding
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py             # Main dashboard view
│   │   ├── transactions.py          # CRUD + OCR receipt upload
│   │   ├── budgets.py               # Budget management
│   │   ├── goals.py                 # Financial goals
│   │   └── reports.py               # PDF / Excel / CSV export
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                # Full REST API (/api/v1/) — 25+ endpoints
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analytics.py             # Charts, summaries, AI insights engine
│   │   ├── export.py                # PDF (ReportLab), Excel (openpyxl), CSV
│   │   ├── ocr.py                   # Tesseract + OpenCV receipt scanner
│   │   └── email_service.py         # Transactional email templates + sender
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── currency.py              # Live exchange rate fetching + conversion
│   │
│   └── templates/
│       ├── base.html                # Sidebar layout, dark mode, nav
│       ├── auth/
│       │   ├── login.html
│       │   ├── signup.html
│       │   └── profile.html
│       ├── dashboard/
│       │   └── index.html           # Charts, metrics, insights
│       ├── transactions/
│       │   ├── index.html           # Filterable, paginated list
│       │   └── form.html            # Add / edit + OCR upload
│       ├── budgets/
│       │   └── index.html
│       ├── goals/
│       │   └── index.html
│       └── reports/
│           └── index.html
│
├── tests/
│   ├── __init__.py
│   └── test_app.py                  # 20+ unit, model, and API tests
│
├── docker/
│   └── nginx.conf                   # Nginx reverse proxy config
│
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions CI/CD pipeline
│
├── config.py                        # DevelopmentConfig, ProductionConfig, TestingConfig
├── run.py                           # Entry point + flask seed-demo CLI command
├── requirements.txt                 # All Python dependencies
├── Dockerfile                       # Multi-stage Docker build
├── docker-compose.yml               # App + PostgreSQL + Nginx
├── .env.example                     # Environment variable template
└── .gitignore
```

---

## 🗃️ Database Schema

```
┌─────────────────────┐     ┌──────────────────────────┐     ┌─────────────────────┐
│        users        │     │       transactions        │     │      categories     │
├─────────────────────┤     ├──────────────────────────┤     ├─────────────────────┤
│ id (PK)             │──┐  │ id (PK)                  │  ┌──│ id (PK)             │
│ name                │  │  │ user_id (FK → users)     │◄─┘  │ name                │
│ email (unique)      │  └─►│ category_id (FK → cats)  │◄────│ icon                │
│ password_hash       │     │ amount                   │     │ color               │
│ role                │     │ type (income|expense)    │     │ type (income|expense│
│ currency            │     │ description              │     │ is_default          │
│ is_active           │     │ date                     │     │ user_id (FK)        │
│ email_notifications │     │ currency                 │     └─────────────────────┘
│ created_at          │     │ receipt_url              │
│ last_login          │     │ tags                     │
└─────────────────────┘     │ created_at               │
          │                 │ updated_at               │
          │                 └──────────────────────────┘
          │
          │    ┌──────────────────────────┐     ┌─────────────────────────┐
          │    │         budgets          │     │          goals          │
          │    ├──────────────────────────┤     ├─────────────────────────┤
          ├───►│ id (PK)                  │     │ id (PK)                 │
          │    │ user_id (FK → users)     │  ┌─►│ user_id (FK → users)   │
          │    │ category_id (FK → cats)  │  │  │ name                   │
          │    │ name                     │  │  │ description             │
          │    │ amount                   │  │  │ target_amount           │
          │    │ month                    │  │  │ saved_amount            │
          │    │ year                     │  │  │ deadline                │
          │    │ alert_threshold          │  │  │ icon / color            │
          │    │ created_at               │  │  │ is_completed            │
          │    └──────────────────────────┘  │  │ created_at              │
          │                                  │  └─────────────────────────┘
          │    ┌──────────────────────────┐  │
          │    │      notifications       │  │
          │    ├──────────────────────────┤  │
          └───►│ id (PK)                  │◄─┘
               │ user_id (FK → users)     │
               │ title                    │
               │ message                  │
               │ type (info|warning|...)  │
               │ is_read                  │
               │ created_at               │
               └──────────────────────────┘
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.10+
- pip
- Git

### 1. Clone the repository

```bash
git clone https://github.com/rushan-2024/Personal-Finance-Management-System.git
cd Personal-Finance-Management-System
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and set at minimum:
```env
SECRET_KEY=any-long-random-string
JWT_SECRET_KEY=another-long-random-string
FLASK_ENV=development
```

### 5. Initialize the database

```bash
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

### 6. (Optional) Load demo data

```bash
flask seed-demo
```
This creates a ready-to-use demo account:
- **Email:** `demo@finflow.app`
- **Password:** `password123`

### 7. Run the application

```bash
python run.py
```

Open your browser at **http://localhost:5000** 🚀

---

## 🔌 REST API Reference

**Base URL:** `/api/v1/`
**Authentication:** `Authorization: Bearer <jwt_token>`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create new account |
| POST | `/auth/login` | Login, returns access + refresh tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/transactions` | List all (paginated, filterable by type/category) |
| POST | `/transactions` | Create transaction |
| PUT | `/transactions/:id` | Update transaction |
| DELETE | `/transactions/:id` | Delete transaction |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/summary` | Monthly income / expense / balance / savings rate |
| GET | `/analytics/monthly?months=6` | Chart data for last N months |
| GET | `/analytics/categories` | Expense breakdown by category |
| GET | `/analytics/insights` | AI-powered spending insights |

### Budgets & Goals
| Method | Endpoint | Description |
|---|---|---|
| GET | `/budgets` | List budgets with spent % |
| POST | `/budgets` | Create budget |
| DELETE | `/budgets/:id` | Delete budget |
| GET | `/goals` | List all goals |
| POST | `/goals` | Create goal |
| PATCH | `/goals/:id/contribute` | Add funds to a goal |
| DELETE | `/goals/:id` | Delete goal |

### Categories
| Method | Endpoint | Description |
|---|---|---|
| GET | `/categories` | List all categories for current user |

### Example

```bash
# 1. Login and get token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@finflow.app","password":"password123"}'

# 2. Create a transaction
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"amount":5000,"type":"expense","description":"Groceries","date":"2026-05-15"}'
```

---

## 🧪 Running Tests

```bash
pip install pytest pytest-flask pytest-cov
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask 3.0, SQLAlchemy 2.0 |
| Auth | Flask-Login, Flask-JWT-Extended, bcrypt |
| Database | PostgreSQL (production) / SQLite (development) |
| Frontend | Jinja2, Tabler Icons, Chart.js |
| PDF Reports | ReportLab |
| Excel Reports | openpyxl, pandas |
| OCR | Tesseract, OpenCV, pytesseract |
| Email | Flask-Mail |
| Security | Flask-WTF (CSRF), Flask-Limiter (rate limiting), Flask-CORS |
| DevOps | Docker, Docker Compose, Nginx, GitHub Actions |
| Testing | pytest, pytest-flask |

---

## 🗺️ Roadmap

- [x] **Phase 1** — Core backend, models, JWT + session authentication
- [x] **Phase 2** — Transactions CRUD, dashboard, budget management
- [x] **Phase 3** — Analytics, AI insights, financial goals
- [x] **Phase 4** — OCR receipt scanner, PDF/Excel/CSV export, email notifications
- [x] **Phase 5** — REST API, Docker, CI/CD, pytest test suite
- [ ] **Phase 6** *(planned)* — OpenAI GPT insights, two-factor auth, admin panel, mobile app

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

> Built with ❤️ using Flask + PostgreSQL. Star ⭐ the repo if it helped you!
