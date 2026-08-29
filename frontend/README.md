# Institute SaaS — Frontend (M8)

React SPA consuming the [Django/DRF API](../README.md) in this repo. No new
backend endpoints — every page is a thin client over what already exists.

## Stack

Vite + React 19 + TypeScript + Tailwind CSS v4 + React Router + Axios.

## Local development

```bash
npm install
cp .env.example .env   # point VITE_API_BASE_URL at your backend
npm run dev
```

`VITE_API_BASE_URL` must point at a **tenant subdomain**, not bare
`localhost` — `TenantMiddleware` treats bare `localhost`/`127.0.0.1` as a
platform host with no tenant (see the backend README's "Local dev" section
on adding `abc.localhost` to `/etc/hosts`). For example:

```
VITE_API_BASE_URL=http://demo.localhost:8000
```

## Structure

```
src/
├── api/          # axios client (JWT + silent refresh), shared TS types
├── auth/         # AuthContext, RequireAuth route guard
├── components/   # Layout (role-aware nav), shared UI primitives
├── pages/        # one file per module (Dashboard, Students, Batches, …)
└── razorpay.ts   # lazy-loads Razorpay Checkout only when a student pays
```

## Role-gated routing

Routes mirror each endpoint's actual DRF `permission_classes` rather than
assuming access:

| Role | Sees |
|---|---|
| admin | Dashboard, Students (full CRUD), Batches, Attendance, Fees (structures/payments/outstanding), Exams, Notifications |
| teacher | Same as admin minus student creation/deactivation and outstanding dues (both `IsInstituteAdmin`-only on the backend) |
| student | Students/Batches (read-only), Fees (pay own dues), My Results, Notifications (own only) |
| parent | Students/Batches (read-only), Fees, Notifications — `my-results` and attendance reports aren't available; the backend has no Parent→Student link yet (see main README) |

## Known gaps (carried over from the API, not papered over)

- Students can't view their own payment history — `PaymentViewSet` list
  action is admin/teacher-only; only `initiate`/`verify` are open to a
  student caller. The self-service Fees page only lists fee structures +
  a "Pay now" button.
- Parent role has no linked student anywhere in the schema, so most
  self-service pages are effectively read-only for parents.

## Verifying changes

There's no committed frontend test suite yet. Before pushing UI changes,
run it against a real backend and click through the golden paths for at
least an admin and a student login — `npm run build` only catches
type/compile errors, not broken data flows.

## Deployment

Deployed as a static site — see `render.yaml` at the repo root
(`coaching-saas-frontend` service, `runtime: static`, `rootDir: frontend`).
Set `VITE_API_BASE_URL` on that service to the backend web service's URL,
and add the frontend's resulting `.onrender.com` URL to the backend's
`CORS_ALLOWED_ORIGINS` env var.
