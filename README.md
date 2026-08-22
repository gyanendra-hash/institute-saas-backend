# Coaching / Institute Management SaaS

Multi-tenant Django + DRF backend for coaching institute management —
students, batches, attendance, fees (Razorpay), exams/results, and
async notifications (Celery).

## Architecture

- **Backend:** Django 5 + Django REST Framework, JWT auth
- **Multi-tenancy:** Shared DB + `tenant_id`, resolved per-request via subdomain
  (`apps/tenants/middleware.py`) and enforced automatically through a
  tenant-scoped model manager (`apps/tenants/managers.py`) — no query can
  accidentally leak cross-tenant data.
- **Async:** Celery + Redis for notifications, payment receipts, fee reminders
- **DB:** PostgreSQL
- **Admin:** Enhanced Django admin — tenant-scoped querysets, autocomplete,
  inlines (Batch→Students, Exam→Results), CSV export, revenue summary

## Local setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt

# Start Postgres + Redis (or use docker-compose below)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Or with Docker (full stack: web + db + redis + celery)

```bash
docker compose -f docker/docker-compose.yml up --build
```

App: http://localhost:8000 · Admin: http://localhost:8000/admin/

## Environment variables

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | PostgreSQL connection |
| `REDIS_URL` | Redis (cache + Celery broker) |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Payment gateway |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |

`config.settings.prod` expects the discrete `DB_*` vars above. The free-tier
deployment path (`config.settings.free_tier`, see below) instead takes a
single `DATABASE_URL` (Neon) and `REDIS_URL` (Render/Upstash) connection
string — see `Coaching_SaaS_Deployment_Guide.docx` for the full walkthrough.

## Deployment

- **Free tier (Render + Neon + Upstash):** `render.yaml` in this repo is a
  Render Blueprint — connect the repo on Render, it provisions the web
  service, two Celery workers (worker + beat), and a free Redis instance.
  Set `DATABASE_URL` (from Neon) and the Razorpay/CORS vars in the Render
  dashboard, then run `python manage.py migrate` from the Render Shell tab.
  Full steps: `Coaching_SaaS_Deployment_Guide.docx`.
- **Self-hosted / Docker (paid infra):** use `config.settings.prod` +
  `docker/` (Dockerfile, docker-compose, nginx) as the reverse-proxy path.

## Branching strategy

- `dev` — active development, all feature work merges here first
- `stage` — pre-production integration/testing, merged from `dev`
- `main` — production-ready, merged from `stage`; tagged per milestone
  (e.g. `v0.1.0-m1`)

## Local tenant testing (no real DNS needed)

Add to `/etc/hosts`:
```
127.0.0.1 abc.localhost
```
Then create a `Tenant` with `slug="abc"` via admin/shell, and hit
`http://abc.localhost:8000/api/...` — the middleware resolves the tenant
from the subdomain automatically.

## API overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/login/` | POST | JWT login (tenant + role embedded in token) |
| `/api/auth/login/refresh/` | POST | Refresh access token |
| `/api/auth/me/` | GET/PATCH | Current user profile |
| `/api/students/` | GET/POST | List/create students (filter, search, paginate) |
| `/api/attendance/` | GET/POST | Attendance records |
| `/api/attendance/bulk-mark/` | POST | Mark attendance for a whole batch in one call |

## Project structure

```
coaching_saas/
├── config/            # settings (base/dev/prod), urls, celery, wsgi/asgi
├── apps/
│   ├── tenants/        # multi-tenancy core
│   ├── accounts/        # custom User, JWT auth, admin
│   ├── batches/          # course/batch model
│   ├── students/          # student CRUD API
│   ├── attendance/         # attendance + bulk-mark API
│   ├── fees/                # fee structures, Razorpay payments
│   ├── exams/                 # exams + results
│   └── notifications/          # Celery async tasks
├── common/             # shared permissions, pagination
├── docker/             # Dockerfile, docker-compose, nginx
└── requirements/       # base/dev/prod pip requirements
```

## Milestones

See the accompanying **SRS document** (`Coaching_SaaS_SRS.docx`) — Section 7
for the full week-by-week milestone plan (M1–M9), and Section 6 for the ER
diagram.

### M1 — Foundation (this scaffold) — DONE

- Django 5 project layout: `config/` (settings per env), `apps/` (one app
  per domain), `common/` (shared permissions + pagination)
- `Tenant` model + `TenantMiddleware` resolving tenant from subdomain
  (`apps/tenants/`)
- Tenant-scoped default manager (`TenantManager`) — every tenant-aware
  model is isolated at the query level automatically (FR-1.2)
- Custom `User` model with `role` (admin/teacher/student/parent) + JWT
  login embedding `tenant_id`/`role` in the token (FR-1.3, FR-1.5)
- Docker (web + Postgres + Redis + Celery worker/beat) for local dev
- Free-tier deployment path (`render.yaml`, `config/settings/free_tier.py`)
  per the Deployment Guide, so M1 can go live on Render/Neon at ₹0 cost

### Next up — M2: Student & Batch Management

- Student/Batch CRUD, CSV bulk import, RBAC-scoped list/search APIs

## Next steps (not yet in this scaffold)

- React/Next.js frontend (auth flow + dashboards)
- Test suite (pytest-django)
- CI/CD pipeline (GitHub Actions)
- Read-replica routing for scale phase (see SRS §5)
