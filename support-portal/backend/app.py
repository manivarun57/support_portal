import os
from dataclasses import asdict

from chalice import BadRequestError, Chalice, Response, CORSConfig

from chalicelib.auth import resolve_user_id
from chalicelib.db import CommentRepository, TicketRepository
from chalicelib.logger import log_error, log_info
from chalicelib.schemas import CreateTicketPayload, parse_ticket_payload
from chalicelib.storage import StorageClient

cors_config = CORSConfig(
    allow_origin="*",
    allow_headers=["Content-Type", "X-User-Id"],
    max_age=600,
)

app = Chalice(app_name="support-portal-api")
app.debug = True

ticket_repo = TicketRepository()
comment_repo = CommentRepository()
storage_client = StorageClient()
OFFLINE_MODE = os.getenv("AWS_OFFLINE", "true").lower() == "true"


def _response(payload, status_code: int = 200) -> Response:
    return Response(
        body=payload,
        status_code=status_code,
        headers={"Content-Type": "application/json"},
    )


@app.route("/health", methods=["GET"], cors=cors_config)
def health() -> Response:
    log_info("Health check requested")
    return _response({"status": "ok"})


@app.route("/tickets", methods=["POST"], cors=cors_config)
def create_ticket() -> Response:
    request = app.current_request
    log_info("Received create ticket request")
    try:
        payload: CreateTicketPayload = parse_ticket_payload(request)
        user_id = resolve_user_id(request)

        attachment_url = None
        if payload.attachment and payload.attachment_name:
            attachment_url, _ = storage_client.store_base64_blob(
                payload.attachment,
                payload.attachment_name,
                payload.attachment_type,
            )
            log_info("Attachment handled for ticket", attachment_url=attachment_url)

        record = ticket_repo.create_ticket(
            subject=payload.subject,
            priority=payload.priority,
            category=payload.category,
            description=payload.description,
            user_id=user_id,
            attachment_url=attachment_url,
        )

        if attachment_url:
            ticket_repo.save_ticket_file(
                ticket_id=record.id,
                file_url=attachment_url,
                file_name=payload.attachment_name or "attachment",
            )

        if OFFLINE_MODE:
            comment_repo.seed_demo_comment(record.id, user_id)
            log_info("Seeded demo comment for ticket", ticket_id=record.id)

        log_info("Ticket created successfully", ticket_id=record.id, user_id=user_id)
        return _response({"ticket": asdict(record)}, status_code=201)
    except BadRequestError as exc:
        log_error("Create ticket validation failed", error=str(exc))
        raise
    except Exception as exc:  # pragma: no cover - defensive
        log_error("Create ticket failed unexpectedly", error=str(exc))
        raise


@app.route("/tickets/my", methods=["GET"], cors=cors_config)
def get_my_tickets() -> Response:
    try:
        user_id = resolve_user_id(app.current_request)
        tickets = ticket_repo.list_by_user(user_id)
        log_info("Returning ticket list", user_id=user_id, count=len(tickets))
        return _response({"tickets": tickets})
    except BadRequestError:
        raise
    except Exception as exc:  # pragma: no cover
        log_error("Failed to fetch tickets", error=str(exc))
        raise


@app.route("/tickets/{ticket_id}", methods=["GET"], cors=cors_config)
def get_ticket(ticket_id: str) -> Response:
    try:
        user_id = resolve_user_id(app.current_request)
        record = ticket_repo.get_ticket(ticket_id, user_id)
        if not record:
            log_error("Ticket not found", ticket_id=ticket_id, user_id=user_id)
            raise BadRequestError("Ticket not found")
        log_info("Returning ticket details", ticket_id=ticket_id)
        return _response({"ticket": record})
    except BadRequestError:
        raise
    except Exception as exc:  # pragma: no cover
        log_error("Failed to fetch ticket", error=str(exc), ticket_id=ticket_id)
        raise


@app.route("/tickets/{ticket_id}/comments", methods=["GET"], cors=cors_config)
def get_ticket_comments(ticket_id: str) -> Response:
    try:
        comments = comment_repo.list_for_ticket(ticket_id)
        log_info("Returning comments", ticket_id=ticket_id, count=len(comments))
        return _response({"comments": comments})
    except Exception as exc:  # pragma: no cover
        log_error("Failed to fetch comments", error=str(exc), ticket_id=ticket_id)
        raise


@app.route("/dashboard/metrics", methods=["GET"], cors=cors_config)
def dashboard_metrics() -> Response:
    try:
        user_id = resolve_user_id(app.current_request)
        metrics = ticket_repo.get_metrics(user_id)
        log_info("Returning dashboard metrics", user_id=user_id, **metrics)
        return _response({"metrics": metrics})
    except BadRequestError:
        raise
    except Exception as exc:  # pragma: no cover
        log_error("Failed to fetch metrics", error=str(exc))
        raise

