# Basira — Ramadan Program Management Platform

**المنصة الرمضانية (بصيرة)** — منصة رقمية متكاملة لإدارة ومتابعة المشاركين في البرنامج الرمضاني.

Full-stack web application for managing Ramadan daily tracking programs. Participants fill a daily scorecard (11 categories, max 110 points), supervisors monitor their circles (halqas), and admins manage the entire program with analytics, bulk operations, and data import/export.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+ / FastAPI / SQLAlchemy ORM |
| **Database** | PostgreSQL 14+ |
| **Frontend** | React 18 / React Router v6 / Axios |
| **Auth** | JWT (python-jose) / bcrypt |
| **UI** | Custom CSS (RTL Arabic) / Lucide React icons |
| **Reports** | OpenPyXL (Excel) / CSV export & import |

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 14+

---

## Getting Started 

### 1. Clone the repository

```bash
git clone <repo-url>
cd ramadan-program-management-basira
```

### 2. Database Setup

```bash
# Connect to PostgreSQL
sudo -u postgres psql   # Linux/Mac
# or: psql -U postgres  # Windows

# Create database and user
CREATE DATABASE ramadan_db;
CREATE USER ramadan_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ramadan_db TO ramadan_user;
\q
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database URL, JWT secret, email settings, and super admin credentials
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 5. Run the Application

**Start the backend** (from `backend/` directory):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: `http://localhost:8000`
API docs (Swagger): `http://localhost:8000/docs`

**Start the frontend** (from `frontend/` directory):

```bash
npm start
```

Frontend runs at: `http://localhost:3000`

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://ramadan_user:your_password@localhost:5432/ramadan_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
JWT_ACCESS_TOKEN_EXPIRES=2592000    # 30 days in seconds

# Mail (for email notifications & password reset)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Super Admin (auto-created on first startup)
SUPER_ADMIN_EMAIL=admin@example.com
SUPER_ADMIN_PASSWORD=Admin@123456

# Settings
ENABLE_EMAIL_NOTIFICATIONS=True
```

> **Important:** The email set in `SUPER_ADMIN_EMAIL` is automatically created as a super admin on first startup. If you register with this email, it will be auto-promoted to super admin upon login.

---

## User Roles & Permissions

| Role | Permissions |
|------|------------|
| **Participant** (مشارك) | Fill daily card, view own stats, see leaderboard |
| **Supervisor** (مشرف) | All participant permissions + manage halqa members, view/edit member cards, daily tracking with WhatsApp reminders, export reports |
| **Super Admin** (سوبر آدمن) | All permissions + manage users, halqas, supervisors, approve/reject registrations, analytics dashboard, bulk operations, import/export |

---

## Features

### Participants
- Daily Ramadan scorecard (11 categories x 10 points = 110 max per day)
- Edit cards for past days (within Ramadan period)
- Personal statistics: today's score, overall percentage, total cards
- General leaderboard
- Profile management & password change

### Supervisors
- All participant features
- View halqa members and their cards
- Create/edit/delete cards for any member
- Daily tracking: see who submitted and who didn't
- WhatsApp reminder links for non-submitters (individual + group)
- Period summary with date range filters
- Weekly summary
- Leaderboard (filtered by halqa)
- Export halqa data to Excel/CSV

### Super Admin
- All supervisor features across all halqas
- Registration approval/rejection workflow
- User management: edit, activate, withdraw, change roles
- Halqa management: create, edit, assign supervisors and members
- Supervisor conflict detection (warns when reassigning a supervisor)
- Advanced analytics dashboard with filters (gender, halqa, date range, percentage range, name search)
- Sorting by percentage, score, or name
- Bulk operations: approve, reject, activate, withdraw, assign halqa
- Import users from Excel template
- Export analytics & user data (CSV/XLSX)
- Email notification settings

---

## Daily Card Categories

| # | Category (Arabic) | Category (English) |
|---|-------------------|-------------------|
| 1 | وِرد القرآن | Quran recitation |
| 2 | الأدعية | Duas (supplications) |
| 3 | صلاة التراويح | Taraweeh prayer |
| 4 | التهجد والوتر | Tahajjud & Witr |
| 5 | صلاة الضحى | Duha prayer |
| 6 | السنن الرواتب | Rawatib (Sunnah prayers) |
| 7 | المقطع الأساسي | Main lesson |
| 8 | المقطع الواجب | Required lesson |
| 9 | المقطع الإثرائي | Enrichment lesson |
| 10 | عبادة متعدية | Charity/community worship |
| 11 | أعمال إضافية | Extra deeds |

Each category is scored 0–10. Maximum daily score: **110 points**.

---

## Project Structure

```
ramadan-program-management-basira/
├── README.md
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment template
│   └── app/
│       ├── config.py               # Settings (from .env)
│       ├── database.py             # SQLAlchemy engine & session
│       ├── dependencies.py         # Auth: JWT decode, role checker
│       ├── models/
│       │   ├── user.py             # User model
│       │   ├── daily_card.py       # Daily card model (11 score fields)
│       │   ├── halqa.py            # Halqa (circle) model
│       │   └── site_settings.py    # Site settings model
│       ├── routes/
│       │   ├── auth.py             # Register, login, password reset
│       │   ├── participant.py      # Card submission, stats
│       │   ├── supervisor.py       # Halqa management, summaries, export
│       │   ├── admin.py            # User/halqa CRUD, analytics, bulk ops
│       │   └── settings.py         # Site settings
│       ├── schemas/
│       │   ├── user.py             # User request/response schemas
│       │   ├── daily_card.py       # Card schemas
│       │   ├── halqa.py            # Halqa schemas
│       │   └── settings.py         # Settings schemas
│       └── utils/
│           └── email.py            # Email sending utilities
└── frontend/
    ├── package.json
    └── src/
        ├── App.js                  # Router & route definitions
        ├── index.js                # Entry point
        ├── context/
        │   └── AuthContext.js      # Auth state & token management
        ├── components/
        │   ├── layout/
        │   │   └── Layout.js       # Sidebar, header, navigation
        │   └── Pagination.js       # Reusable pagination component
        ├── pages/
        │   ├── HomePage.js         # Landing page
        │   ├── LoginPage.js        # Login
        │   ├── RegisterPage.js     # Registration
        │   ├── ForgotPasswordPage.js
        │   ├── DashboardPage.js    # Role-based dashboard
        │   ├── DailyCardPage.js    # Daily card form
        │   ├── LeaderboardPage.js  # Leaderboard
        │   ├── ProfilePage.js      # Profile settings
        │   ├── SupervisorPage.js   # Supervisor panel (4 tabs)
        │   ├── AdminUsersPage.js   # User management
        │   ├── AdminHalqasPage.js  # Halqa management
        │   ├── AdminAnalyticsPage.js # Analytics dashboard
        │   └── AdminSettingsPage.js  # Site settings
        ├── utils/
        │   └── api.js              # Axios instance with JWT interceptor
        └── styles/
            └── global.css          # Global styles (RTL, dark theme vars)
```

---

## API Endpoints

### Auth (`/api/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new participant |
| POST | `/login` | Login (returns JWT token) |
| GET | `/me` | Get current user + refresh token |
| PUT | `/profile` | Update profile |
| POST | `/change-password` | Change password |
| POST | `/forgot-password` | Request reset code via email |
| POST | `/reset-password` | Reset password with code |

### Participant (`/api/participant`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/card` | Submit/update daily card |
| GET | `/card/{date}` | Get card for specific date |
| GET | `/cards` | Get all cards (optional date filter) |
| GET | `/stats` | Get personal statistics |
| GET | `/leaderboard` | Get general leaderboard |

### Supervisor (`/api/supervisor`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/halqas` | Get available halqas |
| GET | `/members` | Get halqa members |
| GET | `/member/{id}/cards` | Get member's cards |
| GET | `/member/{id}/card/{date}` | Get specific member card |
| PUT | `/member/{id}/card/{date}` | Create/update member card |
| DELETE | `/member/{id}/card/{date}` | Delete member card |
| GET | `/leaderboard` | Halqa leaderboard |
| GET | `/daily-summary` | Daily submission summary |
| GET | `/weekly-summary` | Weekly summary |
| GET | `/range-summary` | Custom date range summary |
| GET | `/export` | Export cards (CSV/XLSX) |

### Admin (`/api/admin`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List users (with filters) |
| GET | `/user/{id}` | Get user details |
| PUT | `/user/{id}` | Update user |
| POST | `/user/{id}/reset-password` | Reset user password |
| POST | `/user/{id}/set-role` | Change user role |
| POST | `/user/{id}/withdraw` | Withdraw user |
| POST | `/user/{id}/activate` | Activate user |
| POST | `/user/{id}/assign-halqa` | Assign user to halqa |
| GET | `/registrations` | Get pending registrations |
| POST | `/registration/{id}/approve` | Approve registration |
| POST | `/registration/{id}/reject` | Reject registration |
| GET | `/halqas` | List all halqas |
| POST | `/halqa` | Create halqa |
| PUT | `/halqa/{id}` | Update halqa |
| POST | `/halqa/{id}/assign-members` | Assign members to halqa |
| GET | `/analytics` | Analytics dashboard data |
| GET | `/user/{id}/cards` | Get user cards (admin) |
| GET | `/export` | Export analytics (CSV/XLSX) |
| GET | `/export-users` | Export users list |
| GET | `/import-template` | Download import template |
| POST | `/import` | Import users from Excel |
| POST | `/bulk/approve` | Bulk approve |
| POST | `/bulk/reject` | Bulk reject |
| POST | `/bulk/activate` | Bulk activate |
| POST | `/bulk/withdraw` | Bulk withdraw |
| POST | `/bulk/assign-halqa` | Bulk assign halqa |

### Settings (`/api/settings`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get site settings |
| PUT | `/` | Update site settings |

---

## Frontend Routes

| Path | Page | Access |
|------|------|--------|
| `/` | Home/Landing | Public |
| `/login` | Login | Public |
| `/register` | Registration | Public |
| `/forgot-password` | Password Reset | Public |
| `/dashboard` | Dashboard | All authenticated |
| `/daily-card` | Daily Card Form | All authenticated |
| `/profile` | Profile Settings | All authenticated |
| `/leaderboard` | Leaderboard | Supervisor, Admin |
| `/supervisor` | Supervisor Panel | Supervisor, Admin |
| `/admin/users` | User Management | Admin only |
| `/admin/halqas` | Halqa Management | Admin only |
| `/admin/analytics` | Analytics | Admin only |
| `/admin/settings` | Site Settings | Admin only |

---

## Database Schema

### Users
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| member_id | Integer (unique) | Custom member number (starts at 1000) |
| full_name | String | Full name |
| gender | String | `male` or `female` |
| age | Integer | Age |
| phone | String | Phone number |
| email | String (unique) | Email address |
| password_hash | String | bcrypt hash |
| country | String | Country |
| referral_source | String | How they heard about the program |
| status | String | `pending`, `active`, `rejected`, `withdrawn` |
| role | String | `participant`, `supervisor`, `super_admin` |
| rejection_note | String | Note when rejected |
| halqa_id | Integer (FK) | Assigned halqa |
| created_at | DateTime | Registration date |
| updated_at | DateTime | Last update |

### Daily Cards
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| user_id | Integer (FK) | Card owner |
| date | Date (unique with user_id) | Card date |
| quran | Float (0-10) | Quran recitation score |
| duas | Float (0-10) | Duas score |
| taraweeh | Float (0-10) | Taraweeh prayer score |
| tahajjud | Float (0-10) | Tahajjud & Witr score |
| duha | Float (0-10) | Duha prayer score |
| rawatib | Float (0-10) | Sunnah prayers score |
| main_lesson | Float (0-10) | Main lesson score |
| required_lesson | Float (0-10) | Required lesson score |
| enrichment_lesson | Float (0-10) | Enrichment lesson score |
| charity_worship | Float (0-10) | Community worship score |
| extra_work | Float (0-10) | Extra deeds score |
| extra_work_description | Text | Description of extra deeds |

### Halqas
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| name | String (unique) | Halqa name |
| supervisor_id | Integer (FK) | Assigned supervisor |
| created_at | DateTime | Creation date |
| updated_at | DateTime | Last update |

---

## Ramadan Period

The application is configured for **Ramadan 2026**:
- Start: **February 19, 2026**
- End: **March 19, 2026**

To change the dates, update `RAMADAN_START` and `RAMADAN_END` in:
- `backend/app/routes/supervisor.py`
- `backend/app/routes/participant.py`

---

## License

This project is private and proprietary.
