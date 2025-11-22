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
    pass
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        if method == "OPTIONS":
            return {
                "statusCode": HTTP_OK,
                "headers": CORS_HEADERS,
                "body": "",
            }
        response: Dict[str, Any] = handler(event, context)
        if "headers" not in response:
            response["headers"] = {}
        response["headers"].update(CORS_HEADERS)
        return response
    return wrapper
def json_middleware(handler: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
    pass
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                event["parsed_body"] = {}
                return handler(event, context)
            print(f"[JSON_MIDDLEWARE] Raw event: {event}")
            print(f"[JSON_MIDDLEWARE] Event keys: {list(event.keys())}")
            if "body" in event and event["body"]:
                try:
                    event["parsed_body"] = json.loads(event["body"])
                    print(f"[JSON_MIDDLEWARE] Parsed from body: {event['parsed_body']}")
                except json.JSONDecodeError as e:
                    print(f"[JSON_MIDDLEWARE] JSON decode error: {e}")
                    return create_error_response(HTTP_BAD_REQUEST, f"Invalid JSON: {str(e)}")
            elif any(key in event for key in ["user_id", "inference_type"]):
                event["parsed_body"] = {
                    k: v
                    for k, v in event.items()
                    if k
                    not in ["requestContext", "headers", "pathParameters", "queryStringParameters"]
                }
                print(
                    f"[JSON_MIDDLEWARE] Direct invocation, using event data: {event['parsed_body']}"
                )
            else:
                print("[JSON_MIDDLEWARE] No body or direct data found in event")
                event["parsed_body"] = {}
            return handler(event, context)
        except Exception as e:
            print(f"Unexpected error in json_middleware: {e}")
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                f"Internal server error: {str(e)}",
            )
    return wrapper
def method_validation_middleware(
    allowed_methods: list,
) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:
    pass
    def decorator(handler: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if not event.get("requestContext"):
                print("[METHOD_VALIDATION] Direct Lambda invocation - skipping method validation")
                return handler(event, context)
            if method not in allowed_methods and method != "OPTIONS":
                print(
                    f"[METHOD_VALIDATION] Method {method} not allowed. Allowed: {allowed_methods}"
                )
                return create_error_response(
                    HTTP_METHOD_NOT_ALLOWED,
                    f"Method {method} not allowed. Allowed methods: {', '.join(allowed_methods)}",
                )
            print(f"[METHOD_VALIDATION] Method {method} allowed")
            return handler(event, context)
        return wrapper
    return decorator
def request_validation_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:
    pass
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                return handler(event, context)
            parsed_body = event.get("parsed_body", {})
            print(f"[REQUEST_VALIDATION] Event keys: {list(event.keys())}")
            print(f"[REQUEST_VALIDATION] Parsed body: {parsed_body}")
            print(f"[REQUEST_VALIDATION] user_id in parsed_body: {parsed_body.get('user_id')}")
            if not parsed_body.get("user_id"):
                print("[REQUEST_VALIDATION] FAILED - user_id not found in parsed_body")
                return create_error_response(HTTP_BAD_REQUEST, "Missing required field: user_id")
            if not parsed_body.get("inference_type"):
                return create_error_response(
                    HTTP_BAD_REQUEST, "Missing required field: inference_type"
                )
            return handler(event, context)
        except Exception as e:
            print(f"Error in request validation: {e}")
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                f"Request validation error: {str(e)}",
            )
    return wrapper
def error_handling_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:
    pass
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return handler(event, context)
        except ValueError as e:
            print(f"ValueError in handler: {e}")
            return create_error_response(HTTP_BAD_REQUEST, str(e))
        except Exception as e:
            print(f"Unexpected error in handler: {e}")
            return create_error_response(HTTP_INTERNAL_SERVER_ERROR, "An unexpected error occurred")
    return wrapper
def create_error_response(
    status_code: int, error_message: str, details: Optional[str] = None
) -> Dict[str, Any]:
    pass
    error_response = ErrorResponse(error=error_message, details=details)
    return {"statusCode": status_code, "headers": CORS_HEADERS, "body": error_response.to_json()}
def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    pass
    return {"statusCode": HTTP_OK, "headers": CORS_HEADERS, "body": json.dumps(data)}
def apply_middleware(*middleware_functions):
    pass
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, event, context, *args, **kwargs):
            print(
                f"[APPLY_MIDDLEWARE] Starting middleware chain with {len(middleware_functions)} middleware"
            )
            def bound_handler(evt, ctx):
                print("[APPLY_MIDDLEWARE] Calling final handler")
                return func(self, evt, ctx, *args, **kwargs)
            wrapped = bound_handler
            for i, middleware in enumerate(reversed(middleware_functions)):
                middleware_name = getattr(middleware, "__name__", str(middleware))
                print(f"[APPLY_MIDDLEWARE] Applying middleware {i+1}: {middleware_name}")
                wrapped = middleware(wrapped)
            print("[APPLY_MIDDLEWARE] Executing middleware chain")
            return wrapped(event, context)
        return wrapper
    return decorator
