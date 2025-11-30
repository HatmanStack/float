import functools
import json
from typing import Any, Callable, Dict, Optional

from ..config.constants import (
    CORS_HEADERS,
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_METHOD_NOT_ALLOWED,
    HTTP_OK,
)
from ..models.responses import ErrorResponse
def cors_middleware(handler: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
    """Middleware to handle CORS headers."""

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Handle CORS preflight
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        if method == "OPTIONS":
            return {
                "statusCode": HTTP_OK,
                "headers": CORS_HEADERS,
                "body": "",
            }

        # Process request
        response: Dict[str, Any] = handler(event, context)

        # Ensure CORS headers are included
        if "headers" not in response:
            response["headers"] = {}
        response["headers"].update(CORS_HEADERS)

        return response

    return wrapper
def json_middleware(handler: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
    """Middleware to handle JSON parsing and error responses."""

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            # Skip JSON parsing for OPTIONS requests (CORS preflight)
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                event["parsed_body"] = {}
                return handler(event, context)

            # Debug logging

            # Handle direct Lambda invocation (data in event root) vs API Gateway (data in body)
            if "body" in event and event["body"]:
                # API Gateway format - parse JSON from body
                try:
                    event["parsed_body"] = json.loads(event["body"])
except json.JSONDecodeError as e:
return create_error_response(HTTP_BAD_REQUEST, f"Invalid JSON: {str(e)}")
            elif any(key in event for key in ["user_id", "inference_type"]):
                # Direct Lambda invocation - data already at root level
                event["parsed_body"] = {
                    k: v
                    for k, v in event.items()
                    if k
                    not in ["requestContext", "headers", "pathParameters", "queryStringParameters"]
                }
else:
event["parsed_body"] = {}

            return handler(event, context)

        except Exception as e:
return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                f"Internal server error: {str(e)}",
            )

    return wrapper
def method_validation_middleware(
    allowed_methods: list,
) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:
    """Middleware to validate HTTP methods."""

    def decorator(handler: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")

            # Skip method validation for direct Lambda invocations (no requestContext)
            if not event.get("requestContext"):
return handler(event, context)

            if method not in allowed_methods and method != "OPTIONS":
return create_error_response(
                    HTTP_METHOD_NOT_ALLOWED,
                    f"Method {method} not allowed. Allowed methods: {', '.join(allowed_methods)}",
                )
return handler(event, context)

        return wrapper

    return decorator
def request_validation_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:
    """Middleware to validate request structure."""

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            # Skip validation for OPTIONS requests (CORS preflight)
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                return handler(event, context)

            parsed_body = event.get("parsed_body", {})

            # Debug logging for validation
)}")

            # Check for required fields
            if not parsed_body.get("user_id"):
return create_error_response(HTTP_BAD_REQUEST, "Missing required field: user_id")

            if not parsed_body.get("inference_type"):
                return create_error_response(
                    HTTP_BAD_REQUEST, "Missing required field: inference_type"
                )

            return handler(event, context)

        except Exception as e:
return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                f"Request validation error: {str(e)}",
            )

    return wrapper
def error_handling_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:
    """Middleware for global error handling."""

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return handler(event, context)
        except ValueError as e:
return create_error_response(HTTP_BAD_REQUEST, str(e))
        except Exception as e:
return create_error_response(HTTP_INTERNAL_SERVER_ERROR, "An unexpected error occurred")

    return wrapper
def create_error_response(
    status_code: int, error_message: str, details: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized error response."""
    error_response = ErrorResponse(error=error_message, details=details)

    return {"statusCode": status_code, "headers": CORS_HEADERS, "body": error_response.to_json()}
def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized success response."""
    return {"statusCode": HTTP_OK, "headers": CORS_HEADERS, "body": json.dumps(data)}
def apply_middleware(*middleware_functions):
    """Apply multiple middleware functions to a handler."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, event, context, *args, **kwargs):
} middleware"
            )

            # Create a bound method wrapper that middleware can call
            def bound_handler(evt, ctx):
return func(self, evt, ctx, *args, **kwargs)

            # Apply middlewares in order
            wrapped = bound_handler
            for i, middleware in enumerate(reversed(middleware_functions)):
                middleware_name = getattr(middleware, "__name__", str(middleware))
wrapped = middleware(wrapped)
return wrapped(event, context)

        return wrapper

    return decorator
