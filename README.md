# Institute SaaS Backend

Multi-tenant Django + DRF backend for coaching / institute management —
students, batches, attendance, fees (Razorpay), exams & results, and
async notifications (Email/SMS/WhatsApp via Celery). One codebase, many
institutes, each fully data-isolated.

Full requirements: [`docs/Coaching_SaaS_SRS.docx`](docs/Coaching_SaaS_SRS.docx) ·
Deployment walkthrough: [`docs/Coaching_SaaS_Deployment_Guide.docx`](docs/Coaching_SaaS_Deployment_Guide.docx)

**Live:**

| | URL |
|---|---|
| Frontend | https://coaching-saas-frontend.onrender.com |
| Backend API | https://institute-saas-web.onrender.com/api/ |
| Django admin | https://institute-saas-web.onrender.com/admin/ |

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 5.x, Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`), tenant- and role-aware |
| Database | PostgreSQL 15+ |
| Cache / broker | Redis |
| Async tasks | Celery (worker + beat) |
| Payments | Razorpay |
| Frontend | React + Vite + TypeScript + Tailwind CSS (`frontend/`) |
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
│   ├── notifications/                     # Celery async tasks (email/SMS/WhatsApp)
│   └── dashboard/                           # admin/teacher summary reporting API
├── common/                  # shared DRF permissions, pagination, CSV export admin mixin
├── docker/                  # Dockerfile, docker-compose, nginx.conf
├── docs/                    # source SRS + Deployment Guide
├── requirements/            # base / dev / prod / free_tier pip requirements
├── frontend/                # React + Vite + TS + Tailwind SPA (M8) — see frontend/README.md
└── render.yaml              # Render Blueprint (backend API + Celery + Redis + frontend static site)
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
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_FROM_NUMBER` / `TWILIO_WHATSAPP_FROM` | SMS/WhatsApp — left blank, notifications log instead of sending until configured |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames |

## Deployment

**Live (free tier):**
- Backend — https://institute-saas-web.onrender.com (web service, Render
  free plan + Neon Postgres). `/admin/`, JWT login (`/api/auth/login/`),
  and every M1-M8 endpoint verified reachable on this URL.
- Frontend — https://coaching-saas-frontend.onrender.com (static site,
  Render free plan, built from `frontend/`). CORS on the backend
  (`CORS_ALLOWED_ORIGINS`) includes this origin.
- Both services were provisioned directly via the Render API rather than
  a Blueprint sync — `render.yaml` is kept as the from-scratch reference
  (connect repo → New → Blueprint) in case either needs to be rebuilt.

- **`autoDeploy: yes` does not mean every push actually redeploys** —
  the backend service sat on an M1-era commit through M2-M7 despite
  every milestone being pushed to `main`; nothing had re-triggered a
  build in the interim. If a live URL looks stale after a push, trigger
  a manual deploy from the Render dashboard (or `POST
  /v1/services/{id}/deploys` via the API) rather than assuming the push
  alone was enough — don't take "it's on `main`" as proof it's live.
- Celery worker/beat are **not deployed yet** — Render's free plan only
  covers Web Services; background workers need the Starter plan
  (~$7/mo each). Notifications/reminders queue in the DB but won't be
  dispatched until a worker is added (Render dashboard → New → Background
  Worker, same repo/build command as `render.yaml`, plan `starter`).
- Render's default `*.onrender.com` host has no tenant subdomain (no
  wildcard DNS on the free plan), so `TenantMiddleware` treats it as
  platform-level, same as `localhost` — real per-tenant subdomains need a
  custom domain (Deployment Guide §3.6). This also means the live
  frontend can't exercise a real tenant login until a custom domain is
  attached; local dev (`abc.localhost`) is the only way to test tenant
  resolution today.
- Render's current default Python (3.14) has no ABI-compatible
  `psycopg2-binary` wheel — pinned to 3.12 via `.python-version` (also
  matches the SRS-specified runtime).
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
| `/api/exams/` | GET/POST | List/create exams (filter by batch) — admin/teacher only |
| `/api/exams/{id}/` | GET/PATCH/DELETE | Retrieve/update/remove an exam |
| `/api/exams/{id}/enter-marks/` | POST | Enter/update marks for many students against this exam in one call |
| `/api/exams/{id}/report/` | GET | Rank, average, and pass/fail status for every student in this exam |
| `/api/exams/my-results/?student_id=` | GET | A student's own results + performance trend; admin/teacher can pass `?student_id=` for another student |
| `/api/notifications/` | GET | Delivery-status history — admins/teachers see the whole tenant, everyone else sees only their own |
| `/api/notifications/{id}/` | GET | Retrieve one notification |
| `/api/dashboard/summary/` | GET | Revenue collected, active students, outstanding dues, attendance % over a trailing window (`?days=`, default 30) — admin/teacher only |

## Milestones

Full week-by-week plan: SRS §7. Status:

| Milestone | Scope | Status |
|---|---|---|
| **M1** | Foundation: Django setup, Tenant model + middleware, custom User + JWT auth, Docker, free-tier deploy config | ✅ Done |
| **M2** | Student & Batch management (CRUD, RBAC, filters) | ✅ Done |
| **M3** | Attendance module (bulk marking, reports) | ✅ Done |
| **M4** | Fee management (Razorpay, receipts, reminders) | ✅ Done |
| **M5** | Exam/Result module + analytics | ✅ Done |
| **M6** | Notifications (Celery + Email/SMS/WhatsApp) | ✅ Done |
| **M7** | Admin dashboard & reporting APIs | ✅ Done |
| **M8** | Frontend integration (React) | ✅ Done |
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

### M5 — what's new

- `ExamViewSet` (`apps/exams/`) — full CRUD over exams, admin/teacher-only
  via `IsTeacherOrAdmin`, filterable by `batch` — FR-5.1.
- Added `Exam.passing_marks` (default 35, migration `0002`) — the model
  only had `max_marks` from the M1/M3 scaffold, so there was no threshold
  to compute a pass/fail status against. `ExamSerializer.validate()`
  rejects `passing_marks > max_marks`.
- `ExamViewSet.enter_marks` — bulk-upserts marks for many students against
  one exam in a single call, mirroring attendance's `bulk_mark` action.
  Rejects the whole request (with a per-row detail) if any entry names a
  student outside the exam's tenant or exceeds `max_marks`, rather than
  silently skipping or clamping bad rows — FR-5.2.
- `ExamViewSet.report` — rank (competition ranking: ties share a rank,
  the next rank skips ahead), class average, and pass/fail status per
  student for one exam. Admin/teacher only, same as the attendance
  report — FR-5.3.
- `ExamViewSet.my_results` — a student's own results and percentage trend
  across every exam they've sat, or (for admin/teacher oversight)
  another student's via `?student_id=`. **Known gap:** there's no
  Parent→Student link anywhere in the schema (`Student` only stores
  free-text `guardian_name`/`guardian_phone`), so FR-5.4's "Parent shall
  be able to view results" isn't implementable yet without a schema
  change — a parent-role caller gets a 403 with an explanatory message
  instead of being silently allowed to pull up any student by guessing
  an id.
- Verified the full schedule → enter-marks → rank/report → student
  self-view flow (including tie-ranking, cross-tenant student-id
  smuggling, and permission boundaries per role) with a scripted
  functional test against a throwaway SQLite DB — not committed, same as
  M2-M4, but every check passed before this was pushed.

### M6 — what's new

- `apps/notifications/services.py` — `send_sms`/`send_whatsapp` via Twilio
  when `TWILIO_ACCOUNT_SID`/`TWILIO_AUTH_TOKEN` are set; otherwise they log
  and still report success instead of raising, the same trade-off `dev.py`'s
  console `EMAIL_BACKEND` already makes — FR-6.1.
- `send_notification` (`apps/notifications/tasks.py`) now actually branches
  into `send_sms`/`send_whatsapp` for those channels — the M1/M3 scaffold
  only implemented the `EMAIL` branch, the other two were a comment.
- `NotificationViewSet` (read-only) — admins/teachers see every notification
  for the tenant, everyone else only their own — FR-6.3.
- **Normalized `send_fee_due_reminders`** to queue a `Notification` row (like
  `check_low_attendance` already did) instead of calling `send_mail`
  directly — the M4 version of this task sent mail with no delivery-status
  record at all, inconsistent with FR-6.3 and with the low-attendance task
  sitting right next to it in the same file.
- Verified log-fallback SMS/WhatsApp, the email send path, the
  now-audited fee-reminder flow (including that an already-paid student is
  correctly skipped on the next run), and admin-vs-self notification
  scoping with a scripted functional test against a throwaway SQLite DB —
  not committed, same discipline as M2-M5.

### M7 — what's new

- **`apps/dashboard/`** (new app) — `GET /api/dashboard/summary/`
  (`DashboardSummaryView`), admin/teacher only (FR-7.3): active student
  count, revenue collected (`Payment` success sum), outstanding dues
  (same per-fee-structure unpaid calculation as
  `PaymentViewSet.outstanding`, kept consistent rather than
  reimplemented), and attendance % over a trailing window (`?days=`,
  default 30).
- **`common/admin.py::CSVExportMixin`** (new, FR-7.4) — a generic "export
  selected as CSV" admin action that reads each `ModelAdmin`'s own
  `list_display` as the column set, so any list view gets CSV export for
  free. Replaces the one-off `export_as_csv` that `StudentAdmin` had
  hand-rolled, and is now applied to every tenant-scoped admin
  (`Student`, `Batch`, `Attendance`, `FeeStructure`, `Payment`, `Exam`,
  `Result`, `Notification`, `User`).
- FR-7.1 (tenant-scoped list views with search/filter/pagination), FR-7.2
  (inline editing — `StudentInline` on `Batch`, `ResultInline` on `Exam`),
  and FR-7.5 (admin actions scoped to tenant via each `get_queryset()`)
  were already satisfied by the M1-M6 scaffold — no new work needed there.
- Verified the dashboard numbers (revenue/outstanding/attendance %) against
  hand-computed expected values, tenant isolation (a second tenant's data
  never leaks into the summary), the admin/teacher-only permission
  boundary, and CSV export on both a model with custom `list_display`
  methods (`Student.full_name`) and one with only plain fields
  (`Notification`) — scripted functional test against a throwaway SQLite
  DB, not committed, same discipline as M2-M6.

### M8 — what's new

- **`frontend/`** (new, React + Vite + TypeScript + Tailwind CSS) — a
  single-page app consuming the existing REST API, no new backend
  endpoints. See [`frontend/README.md`](frontend/README.md) for setup.
- JWT auth (login, silent access-token refresh via `login/refresh/` on a
  401, logout) — `src/auth/AuthContext.tsx`.
- Role-aware routing/nav (`src/App.tsx`, `src/components/Layout.tsx`):
  admin/teacher get Dashboard, Attendance, and Exam management; students
  get My Results and a self-service Pay Now flow; every role gets
  Students/Batches (read-only unless admin) and Notifications — matching
  each endpoint's actual DRF permission class rather than assuming access.
- Pages per module: Dashboard (FR-7.3 widgets), Students (search/filter,
  create, deactivate, bulk CSV import), Batches (create, assign students),
  Attendance (bulk-mark a batch, batch/student reports), Fees (staff:
  structures/payments/outstanding; student: pay via Razorpay Checkout,
  loaded lazily from `src/razorpay.ts`), Exams (schedule, enter marks,
  rank report), My Results, Notifications.
- Known gap carried over from the API rather than papered over: there's no
  endpoint that lets a student list their own payment history (`PaymentViewSet`
  is admin/teacher-only apart from `initiate`/`verify`), so the student Fees
  page doesn't show past payments — see `SelfServiceFeesView` in
  `frontend/src/pages/FeesPage.tsx`.
- Verified with a real Chromium session (Playwright, not committed) against
  the Django dev server on a throwaway SQLite DB: admin login → dashboard →
  students → exam report; logout; student login → My Results with the
  correct computed percentage; role-gated nav; every staff/self-service
  page render for Attendance, Batches, Fees, and Notifications — same
  "verify before pushing" discipline as the backend milestones, extended to
  the browser since this is UI work.
- Deployed as a Render static site (`coaching-saas-frontend`) alongside
  the backend web service — see the live URLs at the top of this README
  and the "Deployment" section for the CORS/tenant-subdomain caveats that
  apply to the hosted instance.

### Not yet in this scaffold

- Test suite (pytest-django, plus a frontend test runner)
- CI/CD pipeline (GitHub Actions)
- Read-replica routing for scale phase (see SRS §5)
- Parent→Student linking — `Student` only stores free-text
  `guardian_name`/`guardian_phone`, so a parent role can't be securely
  scoped to "their" student(s) yet (see M5 notes above); FR-5.4's
  parent-facing result view is blocked on this
