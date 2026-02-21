# 🌙 المنصة الرمضانية — منصة إدارة ومتابعة البرنامج الرمضاني

منصة رقمية متكاملة لإدارة ومتابعة المشاركين في البرنامج الرمضاني.

---

## 📋 المتطلبات

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 14+

---

## 🚀 التثبيت والتشغيل

### 1. قاعدة البيانات

```bash
# إنشاء قاعدة البيانات
sudo -u postgres psql
CREATE DATABASE ramadan_db;
CREATE USER ramadan_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ramadan_db TO ramadan_user;
\q
```

### 2. الباك إند (Backend)

```bash
cd backend

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# تثبيت المكتبات
pip install -r requirements.txt

# إعداد ملف البيئة
cp .env .env.local
# عدّل .env بإعدادات قاعدة البيانات والبريد

# تشغيل السيرفر
python run.py
```

السيرفر يعمل على: `http://localhost:8000`

### 3. الفرونت إند (Frontend)

```bash
cd frontend

# تثبيت المكتبات
npm install

# تشغيل التطبيق
npm start
```

التطبيق يعمل على: `http://localhost:3000`

---

## ⚙️ إعداد ملف .env

```env
DATABASE_URL=postgresql://ramadan_user:your_password@localhost:5432/ramadan_db
JWT_SECRET_KEY=your-super-secret-key
SUPER_ADMIN_EMAIL=admin@example.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ENABLE_EMAIL_NOTIFICATIONS=True
```

> **مهم:** البريد المحدد في `SUPER_ADMIN_EMAIL` هو السوبر آدمن الأساسي. سجّل حساباً بهذا البريد ثم سيتم تفعيله تلقائياً كسوبر آدمن عند تسجيل الدخول.

---

## 👤 الفئات والصلاحيات

| الفئة | الصلاحيات |
|-------|-----------|
| **مشارك** | تعبئة البطاقة، عرض الإحصائيات، الترتيب العام |
| **مشرف** | كل صلاحيات المشارك + متابعة أعضاء الحلقة |
| **سوبر آدمن** | كل الصلاحيات + إدارة المستخدمين والحلقات والتحليلات |

---

## 📱 الميزات

### للمشاركين
- البطاقة الرمضانية اليومية (11 قسم × 10 نقاط)
- تعديل بطاقات الأيام السابقة
- إحصائيات يومية/أسبوعية/كلية
- الترتيب العام (Leaderboard)

### للمشرفين
- ملخص يومي (من سلّم / لم يسلّم)
- ملخص أسبوعي
- عرض بطاقات كل مشارك

### للسوبر آدمن
- قبول/رفض طلبات التسجيل
- إدارة الحلقات والمشرفين
- تحليلات متقدمة مع فلاتر
- تصدير/استيراد Excel وCSV
- إعدادات إشعارات البريد

---

## 🏗 هيكل المشروع

```
ramadan-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask App Factory
│   │   ├── config.py            # Configuration
│   │   ├── models/              # Database Models
│   │   │   ├── user.py
│   │   │   ├── daily_card.py
│   │   │   ├── halqa.py
│   │   │   └── site_settings.py
│   │   ├── routes/              # API Endpoints
│   │   │   ├── auth.py
│   │   │   ├── participant.py
│   │   │   ├── supervisor.py
│   │   │   ├── admin.py
│   │   │   └── settings.py
│   │   └── utils/               # Helpers
│   │       ├── decorators.py
│   │       └── email.py
│   ├── .env
│   ├── requirements.txt
│   └── run.py
└── frontend/
    └── src/
        ├── App.js
        ├── context/AuthContext.js
        ├── utils/api.js
        ├── styles/global.css
        ├── components/layout/Layout.js
        └── pages/
            ├── LoginPage.js
            ├── RegisterPage.js
            ├── DashboardPage.js
            ├── DailyCardPage.js
            ├── LeaderboardPage.js
            ├── ProfilePage.js
            ├── SupervisorPage.js
            ├── AdminUsersPage.js
            ├── AdminHalqasPage.js
            ├── AdminAnalyticsPage.js
            └── AdminSettingsPage.js
```

---

## 🔌 API Endpoints

### المصادقة (Auth)
| Method | Endpoint | الوصف |
|--------|----------|-------|
| POST | `/api/auth/register` | تسجيل جديد |
| POST | `/api/auth/login` | تسجيل دخول |
| GET | `/api/auth/me` | بيانات المستخدم |
| PUT | `/api/auth/profile` | تعديل الملف |
| POST | `/api/auth/change-password` | تغيير كلمة المرور |
| POST | `/api/auth/forgot-password` | طلب إعادة تعيين |
| POST | `/api/auth/reset-password` | تعيين كلمة جديدة |

### المشارك (Participant)
| Method | Endpoint | الوصف |
|--------|----------|-------|
| POST | `/api/participant/card` | حفظ/تعديل بطاقة |
| GET | `/api/participant/card/:date` | بطاقة يوم محدد |
| GET | `/api/participant/cards` | كل البطاقات |
| GET | `/api/participant/stats` | الإحصائيات |
| GET | `/api/participant/leaderboard` | الترتيب العام |

### المشرف (Supervisor)
| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/api/supervisor/members` | أعضاء الحلقة |
| GET | `/api/supervisor/member/:id/cards` | بطاقات عضو |
| GET | `/api/supervisor/daily-summary` | ملخص يومي |
| GET | `/api/supervisor/weekly-summary` | ملخص أسبوعي |

### السوبر آدمن (Admin)
| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/api/admin/users` | قائمة المستخدمين |
| POST | `/api/admin/registration/:id/approve` | قبول طلب |
| POST | `/api/admin/registration/:id/reject` | رفض طلب |
| POST | `/api/admin/user/:id/set-role` | تغيير صلاحية |
| POST/GET | `/api/admin/halqa(s)` | إدارة الحلقات |
| GET | `/api/admin/analytics` | التحليلات |
| GET | `/api/admin/export` | تصدير البيانات |
| POST | `/api/admin/import` | استيراد من Excel |