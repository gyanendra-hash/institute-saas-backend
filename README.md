# Institute SaaS Backend

Multi-tenant Django + DRF backend for coaching / institute management —
students, batches, attendance, fees (Razorpay), exams & results, and
async notifications (Email/SMS/WhatsApp via Celery). One codebase, many
institutes, each fully data-isolated.

Full requirements: [`docs/Coaching_SaaS_SRS.docx`](docs/Coaching_SaaS_SRS.docx) ·
Deployment walkthrough: [`docs/Coaching_SaaS_Deployment_Guide.docx`](docs/Coaching_SaaS_Deployment_Guide.docx)

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 5.x, Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`), tenant- and role-aware |
| Database | PostgreSQL 15+ |
| Cache / broker | Redis |
| Async tasks | Celery (worker + beat) |
| Payments | Razorpay |
| Frontend (planned, M8) | React / Next.js |
| Free-tier hosting | Render + Neon + Upstash |
| Paid / self-hosted | Docker + Nginx + Gunicorn |

## Architecture

- **Multi-tenancy:** shared DB + `tenant_id`, resolved per-request from the
  subdomain (`apps/tenants/middleware.py`) and enforced automatically
  through a tenant-scoped default model manager (`apps/tenants/managers.py`)
  — no query can accidentally leak cross-tenant data.
- **Auth:** custom `User` model with `role` (admin / teacher / student /
  parent). Login returns a JWT with `tenant_id` and `role` embedded, so the
  frontend and every permission check work off the token alone.
- **Async:** Celery + Redis for notifications, payment receipts, and
  fee-due reminders — dispatched off the request/response cycle.
- **Admin:** enhanced Django admin — tenant-scoped querysets, autocomplete,
  inlines (Batch→Students, Exam→Results), CSV export, revenue summary.

## Project structure

```
institute-saas-backend/
├── config/                  # settings (base/dev/prod/free_tier), urls, celery, wsgi/asgi
│   └── settings/
│       ├── base.py          # shared across every environment
│       ├── dev.py           # local development
│       ├── prod.py          # self-hosted / Docker, discrete DB_* env vars
│       └── free_tier.py     # Render + Neon + Upstash, single DATABASE_URL/REDIS_URL
├── apps/
│   ├── tenants/              # Tenant model, subdomain middleware, tenant-scoped manager
│   ├── accounts/              # custom User, JWT auth, tenant-aware auth backend
│   ├── batches/                 # course/batch model
│   ├── students/                  # student CRUD API
│   ├── attendance/                  # attendance + bulk-mark API
│   ├── fees/                          # fee structures, Razorpay payments
│   ├── exams/                           # exams + results
│   └── notifications/                     # Celery async tasks (email/SMS/WhatsApp)
├── common/                  # shared DRF permissions, pagination
├── docker/                  # Dockerfile, docker-compose, nginx.conf
├── docs/                    # source SRS + Deployment Guide
├── requirements/            # base / dev / prod / free_tier pip requirements
└── render.yaml              # Render Blueprint (free-tier deploy)
```

## Local setup

```bash
git clone https://github.com/gyanendra-hash/institute-saas-backend.git
cd institute-saas-backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt

# Start Postgres + Redis (or use docker-compose below), then:
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
| `DJANGO_SETTINGS_MODULE` | Which settings file to load (`config.settings.dev` / `.prod` / `.free_tier`) |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | PostgreSQL connection — used by `config.settings.prod` |
| `DATABASE_URL` | Single Postgres connection string (Neon) — used by `config.settings.free_tier` |
| `REDIS_URL` | Redis — cache + Celery broker |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Payment gateway |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames |

## Deployment

**Live (free tier):** https://institute-saas-web.onrender.com — web
service on Render (free plan) + Neon Postgres, migrated and running.
`/admin/` and JWT login (`/api/auth/login/`) verified working.

- Celery worker/beat are **not deployed yet** — Render's free plan only
  covers Web Services; background workers need the Starter plan
  (~$7/mo each). Notifications/reminders queue in the DB but won't be
  dispatched until a worker is added (Render dashboard → New → Background
  Worker, same repo/build command as `render.yaml`, plan `starter`).
- Render's default `*.onrender.com` host has no tenant subdomain (no
  wildcard DNS on the free plan), so `TenantMiddleware` treats it as
  platform-level, same as `localhost` — real per-tenant subdomains need a
  custom domain (Deployment Guide §3.6).
- Render's current default Python (3.14) has no ABI-compatible
  `psycopg2-binary` wheel — pinned to 3.12 via `.python-version` (also
  matches the SRS-specified runtime).
- `render.yaml` is the Blueprint reference for a from-scratch dashboard
  deploy (connect repo → New → Blueprint) — the live instance above was
  provisioned directly via the Render API instead.
- **Self-hosted / paid infra:** `config.settings.prod` + `docker/`
  (Dockerfile, docker-compose, nginx) as the reverse-proxy path.
- Upgrading from free → paid later is a **plan change, not a rewrite** —
  same `DATABASE_URL` / `REDIS_URL` format throughout (see Deployment
  Guide §6).

## Branching strategy

| Branch | Purpose |
|---|---|
| `dev` | active development — all feature/milestone work merges here first |
| `stage` | pre-production integration & QA testing, merged from `dev` |
| `main` | production-ready, merged from `stage`; tagged per milestone (e.g. `v0.1.0-m1`) |

Flow: feature branch → PR into `dev` → PR `dev` → `stage` (QA sign-off) →
PR `stage` → `main` (deploy to production) → tag the release.

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
| `/api/students/` | GET/POST | List/create students (filter by batch/status, search by name/roll no, paginate) |
| `/api/students/{id}/` | GET/PATCH/DELETE | Retrieve/update/remove a student |
| `/api/students/{id}/deactivate/` | POST | Deactivate a student profile (admin only) |
| `/api/students/bulk-import/` | POST | Bulk-create students from a CSV upload (admin only) |
| `/api/batches/` | GET/POST | List/create batches (filter by course/status, search) |
| `/api/batches/{id}/` | GET/PATCH/DELETE | Retrieve/update/remove a batch |
| `/api/batches/{id}/assign-students/` | POST | Assign a list of existing students to this batch (admin only) |
| `/api/attendance/` | GET/POST | Attendance records (duplicate student/date rejected with a 400) |
| `/api/attendance/bulk-mark/` | POST | Mark attendance for a whole batch in one call |
| `/api/attendance/report/?student_id=` | GET | Attendance % for one student, optional `?from=&to=` date range |
| `/api/attendance/report/?batch_id=` | GET | Per-student breakdown + batch-average attendance % |
| `/api/fees/structures/` | GET/POST | List/create fee structures (installments) per batch — admin write, everyone else read-only |
| `/api/fees/structures/{id}/` | GET/PATCH/DELETE | Retrieve/update/remove a fee structure |
| `/api/fees/payments/` | GET | List payments (admin/teacher), filter by student/fee_structure/status |
| `/api/fees/payments/initiate/` | POST | Create a pending Payment + Razorpay order for one fee-structure installment |
| `/api/fees/payments/{id}/verify/` | POST | Verify the Razorpay signature, mark the payment successful, queue the PDF receipt |
| `/api/fees/payments/outstanding/?batch_id=` | GET | Outstanding dues across all students, optionally scoped to one batch (admin only) |

## Milestones

Full week-by-week plan: SRS §7. Status:

| Milestone | Scope | Status |
|---|---|---|
| **M1** | Foundation: Django setup, Tenant model + middleware, custom User + JWT auth, Docker, free-tier deploy config | ✅ Done |
| **M2** | Student & Batch management (CRUD, RBAC, filters) | ✅ Done |
| **M3** | Attendance module (bulk marking, reports) | ✅ Done |
| **M4** | Fee management (Razorpay, receipts, reminders) | ✅ Done |
| M5 | Exam/Result module + analytics | Next |
| M6 | Notifications (Celery + Email/SMS/WhatsApp) | Planned |
| M7 | Admin dashboard & reporting APIs | Planned |
| M8 | Frontend integration (React) | Planned |
| M9 | Production readiness: CI/CD, monitoring, load testing | Planned |

### M1 — what's in this scaffold

- Django 5 project layout: `config/` (settings per env), `apps/` (one app
  per domain), `common/` (shared permissions + pagination)
- `Tenant` model + `TenantMiddleware` resolving tenant from subdomain
  (`apps/tenants/`) — FR-1.1
- Tenant-scoped default manager (`TenantManager`) — every tenant-aware
  model is isolated at the query level automatically — FR-1.2
- Custom `User` model with `role` (admin/teacher/student/parent) + JWT
  login embedding `tenant_id`/`role` in the token — FR-1.3, FR-1.5
- Docker (web + Postgres + Redis + Celery worker/beat) for local dev
- Free-tier deployment path (`render.yaml`, `config/settings/free_tier.py`)
  so M1 can go live on Render/Neon at ₹0 cost

### M2 — what's new

- `Batch` CRUD API (`apps/batches/`) — was model + admin only in M1, now
  has a full `BatchViewSet` (search/filter by course & status) — FR-2.2
- `assign_students` action — assign many existing students to a batch in
  one call, instead of one PATCH per student — FR-2.2
- Auto-generated per-tenant roll numbers (`STU-0001`, ...) — filled in on
  create when left blank, computed in `apps/students/services.py` with a
  tenant-row lock to stay unique under concurrent creates — FR-2.3
- CSV bulk student import (`apps/students/services.py:bulk_import_students`)
  — creates the `User` + `Student` per row, skips bad rows individually
  with a per-row error instead of failing the whole file — FR-2.4
- `deactivate` action on `StudentViewSet` — explicit soft-delete matching
  the SRS wording, instead of overloading the DELETE endpoint — FR-2.1
- Search/filter by batch, active status, and name was already in place
  from the M1 scaffold and needed no changes — FR-2.5
- Fixed a latent M1 bug: `User.objects` was a plain `TenantManager`, which
  has no `create_user`/`create_superuser` — this silently broke
  `manage.py createsuperuser`. Now `TenantUserManager` combines Django's
  `UserManager` with the tenant-scoping `TenantManager`.
- **Generated the initial migration files** (`0001_initial.py`) for every
  app — the M1 scaffold shipped models but no migrations, so
  `manage.py migrate` created zero tables. Verified end-to-end against a
  throwaway SQLite DB (see M3 notes below).

### M3 — what's new

- `report` action on `AttendanceViewSet` — attendance % per student
  (`?student_id=`) or aggregated per batch (`?batch_id=`), with an
  optional `?from=&to=` date range — FR-3.3
- `validate()` on `AttendanceSerializer` rejects a duplicate student/date
  with a clean 400 instead of an unhandled `IntegrityError` — the DB's
  `unique_together` includes `tenant`, which isn't a serializer field, so
  DRF's automatic `UniqueTogetherValidator` couldn't see the constraint —
  this covers it explicitly — FR-3.2
- `check_low_attendance` Celery Beat task (`apps/notifications/tasks.py`,
  runs daily) — flags students under 75% attendance over the trailing 30
  days and queues an email alert — FR-3.4
- Bulk marking (FR-3.1) was already in place from the M1 scaffold — its
  `update_or_create` upsert also means it never collides with FR-3.2
- **Fixed another latent M1 bug:** `config/__init__.py` was empty, so the
  Celery app was never wired up via Django settings — every `.delay()`
  call would have tried the default `amqp://guest@localhost//` broker
  instead of the configured Redis, in every environment. Added the
  standard `from .celery import app as celery_app` wiring.
- Verified all of the above (roll numbers, bulk import, duplicate
  rejection, report math, the low-attendance task end-to-end through an
  eager Celery run) with a scripted functional test against a throwaway
  SQLite DB — not committed, but every check passed before this was
  pushed.

### M4 — what's new

- `FeeStructureViewSet` (`apps/fees/`) — full CRUD over fee structures,
  admin-write / everyone-read via `IsAdminOrReadOnly`, filterable by
  `batch` — FR-4.1. An installment plan is modeled as several
  `FeeStructure` rows sharing a batch (e.g. "Term 1", "Term 2") rather
  than a separate plan entity — the model already supported this from the
  M1/M3 scaffold, so M4 only needed to expose it over the API.
- `PaymentViewSet.initiate` — creates a pending `Payment` and a matching
  Razorpay order for one fee-structure installment; a student caller
  always pays for themselves (`student_id` in the body is ignored for
  student-role users, only honored for admin/teacher paying on a
  student's behalf) — FR-4.2.
- `PaymentViewSet.verify` — verifies the Razorpay signature from the
  client-side callback via `RazorpayService.verify_and_mark_paid`, 403s a
  student trying to verify someone else's payment, 400s an
  already-verified payment, and marks the payment `FAILED` (not just a
  bare error) on a bad signature — FR-4.2.
- `generate_receipt_pdf` (`apps/fees/services/receipts.py`, reportlab) —
  actually renders the receipt PDF that was previously just a comment
  ("PDF generation would happen here") in the M1/M3 scaffold's
  `send_payment_receipt` task; now attached to the async email — FR-4.3.
- `PaymentViewSet.outstanding` — admin-only, aggregates unpaid
  installments per student across all fee structures (optionally scoped
  to one batch via `?batch_id=`), returns each row plus a running total —
  FR-4.5.
- Fee-due reminders (FR-4.4) were already in place from the M1/M3
  scaffold (`send_fee_due_reminders`, wired into `CELERY_BEAT_SCHEDULE`)
  and needed no changes.
- **Fixed a latent dependency bug that M4 was the first milestone to
  actually exercise:** `razorpay==1.4.2` imports `pkg_resources` at
  import time, which `setuptools` stopped shipping — the `apps.fees`
  models/service/tasks existed since the M1/M3 scaffold but were never
  reachable from a URL, so nothing had imported the package yet. Bumped
  to `razorpay==2.0.1` (same `client.order` / `client.utility` API, no
  code changes needed) so `pip install -r requirements/base.txt` doesn't
  break on current setuptools.
- Verified the full pay → verify → receipt → outstanding-dues flow
  (including a mocked Razorpay client, bad-signature handling, and
  cross-tenant/cross-student permission checks) with a scripted
  functional test against a throwaway SQLite DB — not committed, same as
  M2/M3, but every check passed before this was pushed.

### Not yet in this scaffold

- React/Next.js frontend (auth flow + dashboards) — M8
- Test suite (pytest-django)
- CI/CD pipeline (GitHub Actions)
- Read-replica routing for scale phase (see SRS §5)
