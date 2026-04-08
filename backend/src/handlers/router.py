"""Dispatch table and routing helpers for the Lambda entry point.

Extracted from :mod:`lambda_handler` as part of Phase 4 Task 1 of the
2026-04-08-audit-float plan. The top-level ``lambda_handler`` entry point
is defined here and re-exported from :mod:`lambda_handler` for backward
compatibility with the SAM template and downstream importers.

Route handlers are resolved by name from :mod:`lambda_handler`'s module
globals so that ``unittest.mock.patch('...lambda_handler._handle_xxx_request')``
continues to intercept dispatch during tests.
"""

import importlib
import re
from typing import Any, Callable, Dict, Optional, Tuple

from ..config.constants import (
    CORS_HEADERS,
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
)
from ..utils.logging_utils import get_logger
from ..utils.validation import is_valid_user_id
from .middleware import create_error_response, create_success_response

logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Shared HTTP helpers
# -----------------------------------------------------------------------------
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
    if job_owner and job_owner != user_id:
        logger.warning(
            "Mismatched user_id on job access",
            extra={
                "data": {
                    "job_id": job_id,
                    "requested_by": user_id,
                    "owner": job_owner,
                }
            },
        )
        return create_error_response(HTTP_FORBIDDEN, "Access denied: you do not own this job")
    return None


# -----------------------------------------------------------------------------
# Per-route handlers
# -----------------------------------------------------------------------------
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
        return _with_cors(create_error_response(HTTP_BAD_REQUEST, result["error"]["message"]))

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

    logger.info("Token request received", extra={"data": {"user_id": user_id}})

    token_marker = derive_token_marker(user_id)
    token_response = create_success_response(
        {
            "token": token_marker,
            "expires_in": TOKEN_MARKER_TTL_SECONDS,
            "user_id": user_id,
            "endpoint": GEMINI_LIVE_WS_ENDPOINT,
        }
    )
    return _with_cors(token_response)


# -----------------------------------------------------------------------------
# Dispatch table
# -----------------------------------------------------------------------------
# The Lambda function URL / API Gateway stage prefix is not stripped before
# ``rawPath`` reaches us, so every pattern tolerates an optional leading stage
# segment. Handlers are stored by NAME (not by reference) so patches applied
# via ``unittest.mock.patch`` at the :mod:`lambda_handler` module level
# correctly redirect dispatch during tests.
_ROUTES: Tuple[Tuple[str, re.Pattern, str], ...] = (
    (
        "POST",
        re.compile(r"^/?(?:[^/]+/)*job/(?P<job_id>[^/]+)/download/?$"),
        "_handle_download_request",
    ),
    (
        "POST",
        re.compile(r"^/?(?:[^/]+/)*token/?$"),
        "_handle_token_request",
    ),
    (
        "GET",
        re.compile(r"^/?(?:[^/]+/)*job/(?P<job_id>[^/]+)/?$"),
        "_handle_job_status_request",
    ),
)


def _resolve_handler(handler_name: str) -> Callable[..., Dict[str, Any]]:
    """Resolve a route handler by name against :mod:`lambda_handler`.

    The indirection via ``importlib`` (rather than a module-level import)
    keeps the patch contract: tests that do
    ``@patch("src.handlers.lambda_handler._handle_job_status_request")`` need
    dispatch to read the CURRENT value of the attribute on every call, not
    a bound reference captured at import time.
    """
    module = importlib.import_module("src.handlers.lambda_handler")
    return getattr(module, handler_name)


def _match_route(method: str, raw_path: str) -> Optional[Tuple[Callable[..., Any], Dict[str, str]]]:
    """Return ``(handler, path_params)`` for the first matching route, or None."""
    for route_method, pattern, handler_name in _ROUTES:
        if route_method != method:
            continue
        match = pattern.match(raw_path)
        if match is None:
            continue
        return _resolve_handler(handler_name), match.groupdict()
    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Top-level AWS Lambda entry point.

    Re-exported from :mod:`lambda_handler` for backward compatibility with
    the SAM template's ``Handler: lambda_function.lambda_handler`` wiring.
    """
    # Deferred import avoids a module-import cycle: ``lambda_handler``
    # imports ``router`` for the ``lambda_handler`` symbol, and we import
    # ``lambda_handler._get_handler`` lazily here.
    from .lambda_handler import _get_handler

    logger.debug("Lambda handler invoked")
    try:
        handler = _get_handler()

        # Check for async meditation processing (self-invoked)
        if event.get("_async_meditation"):
            logger.info(
                "Processing async meditation job",
                extra={"data": {"job_id": event.get("job_id")}},
            )
            handler.process_meditation_async(event["job_id"], event["request"])
            return {"status": "async_completed"}

        raw_path = event.get("rawPath", "")
        http_method = event.get("requestContext", {}).get("http", {}).get("method", "")
        matched = _match_route(http_method, raw_path)
        if matched is not None:
            route_handler, path_params = matched
            if path_params:
                existing_params = event.get("pathParameters") or {}
                event["pathParameters"] = {**existing_params, **path_params}
            return route_handler(handler, event)

        result: Dict[str, Any] = handler.handle_request(event, context)
        return result
    except Exception:
        logger.error("Lambda handler exception", exc_info=True)
        raise
