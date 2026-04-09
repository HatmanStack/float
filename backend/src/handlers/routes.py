"""Per-route dispatch handlers extracted from :mod:`router`.

Phase 4 revision (iteration 2) moves the three per-route helpers
(``_handle_job_status_request``, ``_handle_download_request``,
``_handle_token_request``) and the small HTTP helper utilities that
support them out of :mod:`router` so that module can become a
dispatch-only shim under the Phase 4 Task 1 <200-line target.
"""

import hashlib
from typing import Any, Dict, Optional

from ..config.constants import CORS_HEADERS, HTTP_BAD_REQUEST, HTTP_FORBIDDEN, HTTP_NOT_FOUND
from ..utils.logging_utils import get_logger
from ..utils.validation import is_valid_user_id
from .middleware import create_error_response, create_success_response

logger = get_logger(__name__)


def _mask_id(value: str) -> str:
    """Return a deterministic short hash of ``value`` for log linkage.

    Used so that ``user_id`` and ``job_id`` can appear in warnings without
    exposing the raw identifier in logs.
    """
    if not value:
        return "<missing>"
    return "id:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _with_cors(response: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure ``response`` carries the canonical CORS headers."""
    if "headers" not in response:
        response["headers"] = {}
    response["headers"].update(CORS_HEADERS)
    return response


def _validate_user_id_or_400(user_id: str) -> Optional[Dict[str, Any]]:
    """Return a 400 error response if ``user_id`` is invalid, else ``None``."""
    if not user_id:
        return create_error_response(HTTP_BAD_REQUEST, "Missing user_id parameter")
    if not is_valid_user_id(user_id):
        return create_error_response(HTTP_BAD_REQUEST, "Invalid user_id parameter")
    return None


def _authorize_job_access(
    job_data: Dict[str, Any], user_id: str, job_id: str
) -> Optional[Dict[str, Any]]:
    """Return a 403 error response if ``user_id`` does not own the job."""
    job_owner = job_data.get("user_id", "")
    if not job_owner or job_owner != user_id:
        logger.warning(
            "Mismatched or missing user_id on job access",
            extra={
                "data": {
                    "job_id": _mask_id(job_id),
                    "requested_by": _mask_id(user_id),
                    "owner": _mask_id(job_owner),
                }
            },
        )
        return create_error_response(HTTP_FORBIDDEN, "Access denied: you do not own this job")
    return None


def _handle_job_status_request(handler: Any, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /job/{job_id} requests with user authorization."""
    path_params = event.get("pathParameters") or {}
    job_id = path_params.get("job_id") or ""

    query_params = event.get("queryStringParameters", {}) or {}
    user_id = query_params.get("user_id", "")

    if not job_id:
        return _with_cors(create_error_response(HTTP_BAD_REQUEST, "Missing job_id parameter"))

    bad_user = _validate_user_id_or_400(user_id)
    if bad_user is not None:
        return _with_cors(bad_user)

    job_data = handler.handle_job_status(user_id, job_id)
    if not job_data:
        return _with_cors(create_error_response(HTTP_NOT_FOUND, f"Job {job_id} not found"))

    forbidden = _authorize_job_access(job_data, user_id, job_id)
    if forbidden is not None:
        return _with_cors(forbidden)

    return _with_cors(create_success_response(job_data))


def _handle_download_request(handler: Any, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /job/{job_id}/download requests."""
    path_params = event.get("pathParameters") or {}
    job_id = path_params.get("job_id") or ""

    query_params = event.get("queryStringParameters", {}) or {}
    user_id = query_params.get("user_id", "")

    if not job_id:
        return _with_cors(create_error_response(HTTP_BAD_REQUEST, "Missing job_id parameter"))

    bad_user = _validate_user_id_or_400(user_id)
    if bad_user is not None:
        return _with_cors(bad_user)

    job_data = handler.job_service.get_job(user_id, job_id)
    if not job_data:
        return _with_cors(create_error_response(HTTP_NOT_FOUND, f"Job {job_id} not found"))

    forbidden = _authorize_job_access(job_data, user_id, job_id)
    if forbidden is not None:
        return _with_cors(forbidden)

    result = handler.handle_download_request(user_id, job_id, job_data)
    if result is None:
        return _with_cors(create_error_response(HTTP_NOT_FOUND, f"Job {job_id} not found"))

    if "error" in result:
        message = result["error"].get("message", "Download failed")
        return _with_cors(create_error_response(HTTP_BAD_REQUEST, message))

    return _with_cors(create_success_response(result))


def _handle_token_request(handler: Any, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /token requests for Gemini Live API authentication."""
    from ..config.constants import GEMINI_LIVE_WS_ENDPOINT, TOKEN_MARKER_TTL_SECONDS
    from ..utils.security import derive_token_marker

    query_params = event.get("queryStringParameters", {}) or {}
    user_id = query_params.get("user_id", "")

    bad_user = _validate_user_id_or_400(user_id)
    if bad_user is not None:
        return _with_cors(bad_user)

    logger.info("Token request received", extra={"data": {"user_id": _mask_id(user_id)}})

    token_marker = derive_token_marker(user_id)
    token_response = create_success_response(
        {
            "token": token_marker,
            "expires_in": TOKEN_MARKER_TTL_SECONDS,
            "endpoint": GEMINI_LIVE_WS_ENDPOINT,
        }
    )
    return _with_cors(token_response)
