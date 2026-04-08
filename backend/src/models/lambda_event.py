"""TypedDict for the subset of the AWS Lambda Function URL event we read.

Phase 4 Task 3 introduced this shape so the ``rawPath`` / method /
query-string access patterns in :mod:`router` and :mod:`lambda_handler`
can be checked structurally instead of hiding behind
``Dict[str, Any]``.

Only the fields actually consumed by the handler code are modelled.
``total=False`` so unknown keys do not break consumers.
"""

from typing import Any, Dict, List, Optional, TypedDict


class _HttpContext(TypedDict, total=False):
    method: str
    path: str


class _RequestContext(TypedDict, total=False):
    http: _HttpContext


class LambdaEvent(TypedDict, total=False):
    """Subset of the Lambda Function URL / API Gateway event shape."""

    rawPath: str
    body: Optional[str]
    isBase64Encoded: bool
    queryStringParameters: Optional[Dict[str, str]]
    pathParameters: Optional[Dict[str, str]]
    requestContext: _RequestContext
    headers: Optional[Dict[str, str]]
    # Self-invoked async meditation payload fields
    _async_meditation: bool
    job_id: str
    request: Dict[str, Any]
    # Enriched at request parse time
    parsed_body: Dict[str, Any]
    # Frequently-used nested-access shortcut for middlewares that stash
    # pre-parsed content
    stages: List[str]
