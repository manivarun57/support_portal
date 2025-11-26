# Support Portal API (Chalice)

## Quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp env.example .env
chalice local
```

The service listens on `http://localhost:8000`. The default `DEFAULT_USER_ID` is `demo-user`.

## Ticket workflow

1. **Create ticket (`POST /tickets`)**
   - Request body: `subject`, `priority`, `category`, `description`, plus optional Base64 `attachment`.
   - Backend uploads the attachment to S3 (or `tmp/s3` when `AWS_OFFLINE=true`), stores the public URL in `ticket_files`, and inserts the ticket row into **PostgreSQL**.
2. **List tickets (`GET /tickets/my`)**
   - Uses the `X-User-Id` header to scope queries to the logged-in user.
3. **Ticket details + comments**
   - `GET /tickets/{id}` returns the record, `GET /tickets/{id}/comments` returns the threaded discussion.
4. **Dashboard metrics (`GET /dashboard/metrics`)**
   - Aggregates Total/Open/Resolved counts directly in SQL for the same user ID.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | **Required for PostgreSQL/RDS.** Populate these to target your RDS instance. When `DB_HOST` is empty the service falls back to a local SQLite file purely for development. |
| `AWS_REGION` | AWS region used by the Chalice app and S3 uploads. |
| `S3_BUCKET_NAME` | Destination bucket for ticket attachments. |
| `AWS_OFFLINE` | When `"true"` files are saved under `tmp/s3` instead of calling S3. |
| `DEFAULT_USER_ID` | Used when an auth layer is not in place. |

Copy `env.example` to `.env`, fill in the values, and Chalice will load them via `python-dotenv`.

## API surface

- `GET /health` – readiness probe
- `POST /tickets` – create tickets (accepts JSON with optional Base64 attachment)
- `GET /tickets/my` – fetch tickets scoped to the requesting user
- `GET /tickets/{ticket_id}` – fetch a single ticket
- `GET /tickets/{ticket_id}/comments` – fetch comments for a ticket
- `GET /dashboard/metrics` – aggregate KPI cards for the dashboard

Send the `X-User-Id` header to impersonate a specific user. The front-end uses `demo-user` by default.

## AWS deployment

The repo already follows Chalice conventions so promoting to AWS later is straightforward:

1. Configure AWS credentials locally (`aws configure` or environment variables).
2. Provision PostgreSQL on Amazon RDS and an S3 bucket for attachments.
3. Update `.chalice/config.json` with IAM role information or let Chalice manage it.
4. Set the `.env` variables (or use Secrets Manager/Parameter Store) with the RDS + S3 settings.
5. Run `chalice deploy --stage prod`.

Reminder: in AWS you should disable `AWS_OFFLINE`, ensure the Lambda IAM role has `s3:PutObject` permissions for the bucket, and allow outbound networking to the RDS instance (security groups/subnets).

