# Support Portal

End-to-end sample that pairs a Python Chalice backend with a Next.js frontend
to demonstrate a create-ticket workflow, ticket list, and dashboard metrics.

```
support-portal/
├── backend/   # Chalice API: tickets, comments, dashboard metrics
└── frontend/  # Next.js app router UI
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- AWS credentials (optional for real S3 uploads/RDS connectivity)

## Workflow overview

1. **Create Ticket** – Frontend posts subject/priority/category/description plus an optional Base64 file blob to the Chalice `POST /tickets` endpoint. The backend stores ticket metadata in PostgreSQL (RDS in AWS, SQLite fallback only when `DB_HOST` is empty) and ships attachments to S3 (or a local `tmp/s3` folder when offline).
2. **My Tickets** – UI reads `GET /tickets/my`, scoped by the `X-User-Id` header, and renders a sortable table. Selecting a ticket calls `GET /tickets/{id}` + `/comments` to hydrate the details pane.
3. **Dashboard Metrics** – KPI cards pull from `GET /dashboard/metrics`, which aggregates Total/Open/Resolved counts server-side for the active user.

> **Production note:** The database layer is built for PostgreSQL on Amazon RDS. SQLite only exists for local prototyping; supply `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `DB_PORT` to run against Postgres.

## Getting started

### Backend (Chalice)

```bash
cd support-portal/backend
python -m venv .venv
.venv\Scripts\activate  # or source .venv/bin/activate
pip install -r requirements.txt
copy env.example .env   # remember to populate the RDS + S3 secrets
chalice local
```

Key endpoints:

- `POST /tickets` – create ticket + optional attachment (Base64) pushed to S3/local folder
- `GET /tickets/my` – tickets for the caller (`X-User-Id` header, defaults to `demo-user`)
- `GET /tickets/{id}` & `/tickets/{id}/comments`
- `GET /dashboard/metrics` – KPI counts

### Frontend (Next.js)

```bash
cd support-portal/frontend
cp example.env.local .env.local  # adjust API base URL if needed
npm install
npm run dev
```

Pages:

- `/` Dashboard KPIs
- `/tickets` My tickets list with drill-in to `/tickets/:id`
- `/tickets/create` Ticket submission form (subject/priority/category/description/file)

The UI talks to the Chalice API via `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`).

## Environment configuration

| Path | File | Purpose |
| --- | --- | --- |
| `support-portal/backend/env.example` | Backend `.env` template covering AWS region, S3 bucket, `DEFAULT_USER_ID`, and **PostgreSQL** credentials (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`). Copy to `.env`, edit values, then Chalice picks them up automatically. |
| `support-portal/frontend/example.env.local` | Frontend `.env.local` template. Set `NEXT_PUBLIC_API_BASE_URL` to your Chalice URL (e.g., `http://localhost:8000` or your API Gateway invoke URL) and optionally override `NEXT_PUBLIC_DEFAULT_USER_ID`. |

### S3 uploads

- Local: When `AWS_OFFLINE=true` (default), attachments are written to `support-portal/backend/tmp/s3/...` so you can inspect outputs without AWS credentials.
- AWS: Set `AWS_OFFLINE=false`, provide `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (or use an instance profile), and ensure `S3_BUCKET_NAME` points to an existing bucket. The API responds with the public object URL, which the frontend links to in ticket details.

### PostgreSQL / RDS

- **RDS-ready configuration:** Populate `DB_HOST=<rds-endpoint>` plus other credentials. The repositories use `psycopg2` to connect and run standard SQL. Schema creation/migrations can be managed externally; for quick starts, the same SQL executed for SQLite will run on PostgreSQL, but in production you should manage DDL via migration tooling (Flyway, Alembic, etc.).
- **Local fallback:** If `DB_HOST` is blank, the app spins up `support-portal/backend/chalicelib/support-portal.db` (SQLite) to mimic the schema. This is intended only for laptop development to keep dependencies light.

## Local vs. AWS flow

- **Local development**
  - Backend: `chalice local` (serves on `http://localhost:8000`)
  - Frontend: `npm run dev` (Next.js dev server with hot reload)
  - Storage: SQLite + filesystem-backed uploads, seeded demo comments for each ticket
- **AWS-ready deployment**
  1. Provision infrastructure: Amazon RDS for PostgreSQL, S3 bucket, and IAM roles/credentials.
  2. Update `.chalice/config.json` or IAM roles to permit S3 + RDS access.
  3. Set backend `.env` with production secrets (via AWS Secrets Manager/SM Parameter Store in real deployments).
  4. Run `chalice deploy --stage prod` to publish the API Gateway + Lambda stack.
  5. Point the frontend `NEXT_PUBLIC_API_BASE_URL` at the API Gateway invoke URL, then build/deploy (`npm run build`, `next build && next start`, or host on Vercel/S3+CloudFront).

## AWS readiness

- Chalice directory structure is deployment-ready (`chalice deploy`)
- S3 uploads switch automatically from local disk to AWS when `AWS_OFFLINE=false`
- Database layer expects PostgreSQL via standard `DB_HOST/DB_NAME/...` environment variables (SQLite only when these are absent)

