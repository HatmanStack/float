import json
import functools
from typing import Dict, Any, Callable, Tuple, Optional
from ..config.constants import CORS_HEADERS, HTTP_OK, HTTP_BAD_REQUEST, HTTP_METHOD_NOT_ALLOWED, HTTP_INTERNAL_SERVER_ERROR
from ..models.responses import ErrorResponse

def cors_middleware(handler: Callable) -> Callable:
    """Middleware to handle CORS headers."""
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Handle CORS preflight
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        if method == "OPTIONS":
            return {
                "statusCode": HTTP_OK,
                "headers": CORS_HEADERS,
                "body": ""
            }
        
        # Process request
        response = handler(event, context)
        
        # Ensure CORS headers are included
        if "headers" not in response:
            response["headers"] = {}
        response["headers"].update(CORS_HEADERS)
        
        return response
    
    return wrapper

def json_middleware(handler: Callable) -> Callable:
    """Middleware to handle JSON parsing and error responses."""
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            # Skip JSON parsing for OPTIONS requests (CORS preflight)
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                event["parsed_body"] = {}
                return handler(event, context)
            
            # Debug logging
            print(f"[JSON_MIDDLEWARE] Raw event: {event}")
            print(f"[JSON_MIDDLEWARE] Event keys: {list(event.keys())}")
            
            # Handle direct Lambda invocation (data in event root) vs API Gateway (data in body)
            if "body" in event and event["body"]:
                # API Gateway format - parse JSON from body
                try:
                    event["parsed_body"] = json.loads(event["body"])
                    print(f"[JSON_MIDDLEWARE] Parsed from body: {event['parsed_body']}")
                except json.JSONDecodeError as e:
                    print(f"[JSON_MIDDLEWARE] JSON decode error: {e}")
                    return create_error_response(
                        HTTP_BAD_REQUEST,
                        f"Invalid JSON: {str(e)}"
                    )
            elif any(key in event for key in ["user_id", "inference_type"]):
                # Direct Lambda invocation - data already at root level
                event["parsed_body"] = {k: v for k, v in event.items() 
                                      if k not in ["requestContext", "headers", "pathParameters", "queryStringParameters"]}
                print(f"[JSON_MIDDLEWARE] Direct invocation, using event data: {event['parsed_body']}")
            else:
                print("[JSON_MIDDLEWARE] No body or direct data found in event")
                event["parsed_body"] = {}
            
            return handler(event, context)
            
        except Exception as e:
            print(f"Unexpected error in json_middleware: {e}")
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                f"Internal server error: {str(e)}"
            )
    
    return wrapper

def method_validation_middleware(allowed_methods: list) -> Callable:
    """Middleware to validate HTTP methods."""
    def decorator(handler: Callable) -> Callable:
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            
            # Skip method validation for direct Lambda invocations (no requestContext)
            if not event.get("requestContext"):
                print(f"[METHOD_VALIDATION] Direct Lambda invocation - skipping method validation")
                return handler(event, context)
            
            if method not in allowed_methods and method != "OPTIONS":
                print(f"[METHOD_VALIDATION] Method {method} not allowed. Allowed: {allowed_methods}")
                return create_error_response(
                    HTTP_METHOD_NOT_ALLOWED,
                    f"Method {method} not allowed. Allowed methods: {', '.join(allowed_methods)}"
                )
            
            print(f"[METHOD_VALIDATION] Method {method} allowed")
            return handler(event, context)
        
        return wrapper
    return decorator

def request_validation_middleware(handler: Callable) -> Callable:
    """Middleware to validate request structure."""
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            # Skip validation for OPTIONS requests (CORS preflight)
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                return handler(event, context)
            
            parsed_body = event.get("parsed_body", {})
            
            # Debug logging for validation
            print(f"[REQUEST_VALIDATION] Event keys: {list(event.keys())}")
            print(f"[REQUEST_VALIDATION] Parsed body: {parsed_body}")
            print(f"[REQUEST_VALIDATION] user_id in parsed_body: {parsed_body.get('user_id')}")
            
            # Check for required fields
            if not parsed_body.get("user_id"):
                print(f"[REQUEST_VALIDATION] FAILED - user_id not found in parsed_body")
                return create_error_response(
                    HTTP_BAD_REQUEST,
                    "Missing required field: user_id"
                )
            
            if not parsed_body.get("inference_type"):
                return create_error_response(
                    HTTP_BAD_REQUEST,
                    "Missing required field: inference_type"
                )
            
            return handler(event, context)
            
        except Exception as e:
            print(f"Error in request validation: {e}")
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                f"Request validation error: {str(e)}"
            )
    
    return wrapper

def error_handling_middleware(handler: Callable) -> Callable:
    """Middleware for global error handling."""
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return handler(event, context)
        except ValueError as e:
            print(f"ValueError in handler: {e}")
            return create_error_response(HTTP_BAD_REQUEST, str(e))
        except Exception as e:
            print(f"Unexpected error in handler: {e}")
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                "An unexpected error occurred"
            )
    
    return wrapper

def create_error_response(status_code: int, error_message: str, details: Optional[str] = None) -> Dict[str, Any]:
    """Create standardized error response."""
    error_response = ErrorResponse(error=error_message, details=details)
    
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": error_response.to_json()
    }

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized success response."""
    return {
        "statusCode": HTTP_OK,
        "headers": CORS_HEADERS,
        "body": json.dumps(data)
    }

def apply_middleware(*middleware_functions):
    """Apply multiple middleware functions to a handler."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, event, context, *args, **kwargs):
            print(f"[APPLY_MIDDLEWARE] Starting middleware chain with {len(middleware_functions)} middleware")
            
            # Create a bound method wrapper that middleware can call
            def bound_handler(evt, ctx):
                print(f"[APPLY_MIDDLEWARE] Calling final handler")
                return func(self, evt, ctx, *args, **kwargs)
            
            # Apply middlewares in order
            wrapped = bound_handler
            for i, middleware in enumerate(reversed(middleware_functions)):
                middleware_name = getattr(middleware, '__name__', str(middleware))
                print(f"[APPLY_MIDDLEWARE] Applying middleware {i+1}: {middleware_name}")
                wrapped = middleware(wrapped)
            
            print(f"[APPLY_MIDDLEWARE] Executing middleware chain")
            return wrapped(event, context)
        return wrapper
    return decorator