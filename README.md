# ⚡ FinFlow — Personal Finance Management System

> A production-ready, full-stack fintech web application built with Flask, PostgreSQL, and modern frontend tooling. Features JWT authentication, AI-powered insights, receipt OCR scanning, PDF/Excel export, budget management, financial goals tracking, and a full REST API.

---

## 🖼️ Screenshots

> Dashboard
> <img width="960" height="540" alt="dashboard" src="https://github.com/user-attachments/assets/8e9a712c-f056-46cb-9f7c-063b660d9d8d" />
<img width="960" height="540" alt="dashboard-dark" src="https://github.com/user-attachments/assets/0c6deeec-b6cf-46e4-a3fe-31e3ec828186" />
· Transactions <img width="960" height="540" alt="transactions" src="https://github.com/user-attachments/assets/f3ed72fa-0889-4c47-88d8-bde6a6f8626f" />
<img width="960" height="540" alt="add-transaction" src="https://github.com/user-attachments/assets/afc2a5fa-b9e1-4c39-8bbc-ce197ba9df41" />
> · Budgets <img width="960" height="540" alt="add-transaction" src="https://github.com/user-attachments/assets/3faaac75-80c4-4ab9-92fd-73cf7ec616c6" />
> · Goals <img width="960" height="540" alt="add-transaction" src="https://github.com/user-attachments/assets/de223160-b67c-484d-8e2e-c71fbd09b326" />
> · Export Reports <img width="960" height="540" alt="reports" src="https://github.com/user-attachments/assets/5dcd189a-a999-4fdc-be65-3dfc033921b1" />

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Auth | JWT + session auth, bcrypt hashing, remember-me, CSRF |
| 📊 Dashboard | Balance, income/expense cards, charts, recent transactions |
| 💳 Transactions | Add / edit / delete / search / filter / paginate |
| 📁 Categories | Default + custom income/expense categories with icons |
| 📈 Analytics | Line charts, doughnut charts, savings rate trend |
| 💰 Budgets | Monthly budgets, progress bars, auto alerts at threshold |
| 🎯 Goals | Financial goals with progress tracking and deadline |
| 🧠 AI Insights | Rule-based smart insights: savings rate, overspending, trends |
| 📄 PDF Export | Branded PDF reports using ReportLab |
| 📊 Excel Export | Multi-sheet XLSX with transactions + summary |
| 📋 CSV Export | Raw CSV for external analysis |
| 🧾 OCR Scanning | Tesseract + OpenCV receipt scanning (extracts amount/date) |
| 📧 Email Alerts | Monthly reports + budget alerts via Flask-Mail |
| 💱 Multi-currency | INR / USD / EUR / GBP with live exchange rates |
| 🌙 Dark Mode | Full dark mode toggle, persisted in localStorage |
| 🔌 REST API | Full JWT-protected API for all resources |
| 🐳 Docker | Dockerfile + Docker Compose + Nginx |
| 🚀 CI/CD | GitHub Actions: test → lint → Docker build → deploy |
| ✅ Tests | pytest unit + integration + API tests |

---

## 🗂️ Project Structure

```
finflow/
├── app/
│   ├── __init__.py           # App factory, extensions
│   ├── models/
│   │   └── __init__.py       # User, Transaction, Budget, Goal, Category, Notification
│   ├── auth/
│   │   └── __init__.py       # Signup, login, logout, profile
│   ├── routes/
│   │   ├── dashboard.py      # Main dashboard
│   │   ├── transactions.py   # CRUD + OCR receipt scan
│   │   ├── budgets.py        # Budget management
│   │   ├── goals.py          # Financial goals
│   │   └── reports.py        # PDF / Excel / CSV export
│   ├── api/
│   │   └── routes.py         # Full REST API (/api/v1/)
│   ├── services/
│   │   ├── analytics.py      # Charts, summaries, AI insights
│   │   ├── export.py         # PDF, Excel, CSV generation
│   │   ├── ocr.py            # Tesseract receipt scanning
│   │   └── email_service.py  # Transactional emails
│   ├── utils/
│   │   └── currency.py       # Live exchange rate conversion
│   └── templates/
│       ├── base.html          # Sidebar layout + dark mode
│       ├── auth/              # login, signup, profile
│       ├── dashboard/         # Main dashboard
│       ├── transactions/      # List + add/edit form
│       ├── budgets/           # Budget tracker
│       ├── goals/             # Goals tracker
│       └── reports/           # Export UI
├── tests/
│   └── test_app.py            # 20+ unit + API tests
├── docker/
│   └── nginx.conf             # Nginx reverse proxy
├── .github/
│   └── workflows/ci.yml       # GitHub Actions CI/CD
├── config.py                  # Dev / Prod / Test configs
├── run.py                     # App entry point + CLI commands
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 🗃️ Database Schema

```
users            transactions          categories
────────         ─────────────         ──────────
id               id                    id
name             user_id (FK)          name
email            category_id (FK)      icon
password_hash    amount                color
role             type                  type (income|expense)
currency         description           is_default
created_at       date                  user_id (FK)
last_login       currency
                 receipt_url
                 tags
budgets          goals                 notifications
───────          ─────                 ─────────────
id               id                    id
user_id (FK)     user_id (FK)          user_id (FK)
category_id (FK) name                  title
name             description           message
amount           target_amount         type
month            saved_amount          is_read
year             deadline              created_at
alert_threshold  icon / color
                 is_completed
```

---

## 🚀 Quick Start (Local)

### 1. Clone & setup

```bash
git clone https://github.com/yourusername/finflow.git
cd finflow

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your SECRET_KEY, MAIL settings, etc.
```

### 3. Initialize database

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

### 4. (Optional) Seed demo data

```bash
flask seed-demo
# Demo credentials: demo@finflow.app / password123
```

### 5. Run

```bash
python run.py
# Open http://localhost:5000
```

---

## 🐳 Docker Deployment

```bash
# 1. Copy and configure environment
cp .env.example .env

# 2. Start all services (app + postgres + nginx)
docker compose up -d --build

# 3. Apply migrations
docker compose exec web flask db upgrade

# 4. Seed demo data (optional)
docker compose exec web flask seed-demo

# App available at http://localhost
```

---

## ☁️ Render / Railway Deployment

### Render

1. Connect your GitHub repo at https://render.com
2. Create a **Web Service** with:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `flask db upgrade && gunicorn run:app`
3. Add a **PostgreSQL** database and copy the `DATABASE_URL` to environment variables
4. Set all required env vars from `.env.example`

### Railway

```bash
railway login
railway init
railway add postgresql
railway up
railway run flask db upgrade
```

---

## 🔌 REST API Reference

**Base URL:** `/api/v1/`  
**Authentication:** `Authorization: Bearer <jwt_token>`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, get tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/transactions` | List (paginated, filterable) |
| POST | `/transactions` | Create |
| PUT | `/transactions/:id` | Update |
| DELETE | `/transactions/:id` | Delete |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/summary` | Monthly income/expense/balance |
| GET | `/analytics/monthly?months=6` | Chart data |
| GET | `/analytics/categories` | Expense breakdown |
| GET | `/analytics/insights` | AI insights |

### Budgets & Goals
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/budgets` | List / create budgets |
| DELETE | `/budgets/:id` | Remove budget |
| GET/POST | `/goals` | List / create goals |
| PATCH | `/goals/:id/contribute` | Add funds to goal |
| DELETE | `/goals/:id` | Remove goal |

### Example request

```bash
# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpass"}'

# Create a transaction
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount":5000,"type":"expense","description":"Groceries","date":"2026-05-15","category_id":6}'
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
| Backend | Python 3.11, Flask 3.0, SQLAlchemy |
| Auth | Flask-Login, Flask-JWT-Extended, bcrypt |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Frontend | Jinja2, Tabler Icons, Chart.js |
| PDF | ReportLab |
| Excel | openpyxl, pandas |
| OCR | Tesseract, OpenCV, pytesseract |
| Email | Flask-Mail |
| Security | CSRF (Flask-WTF), rate limiting (Flask-Limiter), CORS |
| DevOps | Docker, Docker Compose, Nginx, GitHub Actions |
| Testing | pytest, pytest-flask |

---

## 🗺️ Implementation Roadmap

- [x] **Phase 1** — Core backend, models, auth (JWT + session)
- [x] **Phase 2** — Transactions CRUD, dashboard, budget management
- [x] **Phase 3** — Analytics, AI insights, financial goals
- [x] **Phase 4** — OCR receipt scanner, PDF/Excel/CSV export, email notifications
- [x] **Phase 5** — REST API, Docker, CI/CD, tests, deployment guide
- [ ] **Phase 6** *(future)* — OpenAI GPT insights, mobile app, two-factor auth, admin panel

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

> Built with ❤️ using Flask + PostgreSQL. Star ⭐ the repo if it helped you!
