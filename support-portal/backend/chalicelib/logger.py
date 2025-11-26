from datetime import datetime
from typing import Any


def _serialize_context(context: dict[str, Any]) -> str:
    if not context:
        return ""
    return " ".join(f"{key}={value}" for key, value in context.items())


def _log(level: str, message: str, **context: Any) -> None:
    """
    Print structured logs with a consistent prefix.
    """
    timestamp = datetime.utcnow().isoformat()
    context_blob = _serialize_context(context)
    print(f"[{timestamp}] [{level}] {message} {context_blob}".strip())


def log_info(message: str, **context: Any) -> None:
    _log("INFO", message, **context)


def log_error(message: str, **context: Any) -> None:
    _log("ERROR", message, **context)

