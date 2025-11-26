import base64
from dataclasses import dataclass
from typing import Optional

from chalice import BadRequestError

from chalicelib.logger import log_error, log_info

REQUIRED_FIELDS = ("subject", "priority", "category", "description")
ALLOWED_PRIORITIES = {"low", "medium", "high"}


@dataclass
class CreateTicketPayload:
    subject: str
    priority: str
    category: str
    description: str
    attachment: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None


def parse_ticket_payload(request) -> CreateTicketPayload:
    """
    Validate and normalize the incoming JSON body for ticket creation.
    """
    try:
        body = request.json_body if request else None
        if not isinstance(body, dict):
            raise BadRequestError("Request body must be JSON")

        missing = [field for field in REQUIRED_FIELDS if not body.get(field)]
        if missing:
            raise BadRequestError(f"Missing required field(s): {', '.join(missing)}")

        priority = str(body["priority"]).lower()
        if priority not in ALLOWED_PRIORITIES:
            raise BadRequestError(
                f"Invalid priority '{priority}'. Allowed: {', '.join(sorted(ALLOWED_PRIORITIES))}"
            )

        attachment = body.get("attachment")
        attachment_name = body.get("attachment_name")
        attachment_type = body.get("attachment_type")

        if attachment and not attachment_name:
            raise BadRequestError(
                "attachment_name is required when attachment is supplied"
            )

        if attachment:
            _validate_base64_blob(attachment)

        payload = CreateTicketPayload(
            subject=body["subject"],
            priority=priority,
            category=body["category"],
            description=body["description"],
            attachment=attachment,
            attachment_name=attachment_name,
            attachment_type=attachment_type,
        )
        log_info(
            "Validated create ticket payload",
            has_attachment=bool(attachment),
            priority=priority,
        )
        return payload
    except BadRequestError as exc:
        log_error("Payload validation failed", error=str(exc))
        raise


def _validate_base64_blob(blob: str) -> None:
    try:
        base64.b64decode(blob.split(",")[-1])
        log_info("Validated Base64 attachment payload")
    except Exception as exc:  # pragma: no cover - sanity check
        log_error("Attachment payload invalid", error=str(exc))
        raise BadRequestError("attachment must be Base64 encoded") from exc

