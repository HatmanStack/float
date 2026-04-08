"""Dispatch table and Lambda entry point.

Phase 4 revision (iteration 2) moved the per-route handlers and the
helper utilities to :mod:`routes` so this module holds only the dispatch
table and the top-level ``lambda_handler`` entry point. Route handlers
are resolved by name against :mod:`lambda_handler` on every dispatch so
``unittest.mock.patch('...lambda_handler._handle_xxx_request')`` still
redirects dispatch during tests.
"""

import importlib
import re
from typing import Any, Callable, Dict, Optional, Tuple

from ..utils.logging_utils import get_logger
from .routes import (  # noqa: F401 -- re-exported for test patching shim
    _authorize_job_access,
    _handle_download_request,
    _handle_job_status_request,
    _handle_token_request,
    _validate_user_id_or_400,
    _with_cors,
)

logger = get_logger(__name__)


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
    """Resolve a route handler by name against :mod:`lambda_handler`."""
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
    """Top-level AWS Lambda entry point."""
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
