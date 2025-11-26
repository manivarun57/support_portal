import os
from chalice import BadRequestError

from chalicelib.logger import log_error, log_info


def resolve_user_id(request) -> str:
    """
    Extract the logged-in user's ID from the incoming request.

    Falls back to DEFAULT_USER_ID so the API can run locally without
    an auth service. In production, wire this up to Cognito, IAM, etc.
    """
    try:
        user_id = request.headers.get("X-User-Id") if request else None
        user_id = user_id or os.getenv("DEFAULT_USER_ID")
        if not user_id:
            raise BadRequestError("Missing X-User-Id header or DEFAULT_USER_ID env var")
        log_info("Resolved user ID", user_id=user_id)
        return user_id
    except BadRequestError:
        log_error("Failed to resolve user ID - header and DEFAULT_USER_ID missing")
        raise

