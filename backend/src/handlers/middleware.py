import functools
import json
from typing import Any, Callable, Dict, Optional

from ..config.constants import (
    CORS_HEADERS,
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_METHOD_NOT_ALLOWED,
    HTTP_OK,
    MAX_AUDIO_PAYLOAD_BYTES,
    MAX_INPUT_DATA_ITEMS,
    MAX_MUSIC_LIST_SIZE,
    MAX_TEXT_INPUT_LENGTH,
)
from ..models.responses import ErrorResponse
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def cors_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:

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


def json_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                event["parsed_body"] = {}
                return handler(event, context)

            if "body" in event and event["body"]:
                try:
                    event["parsed_body"] = json.loads(event["body"])
                    logger.debug("Parsed JSON body successfully")
                except json.JSONDecodeError as e:
                    logger.warning("JSON decode error", extra={"data": {"error": str(e)}})
                    return create_error_response(
                        HTTP_BAD_REQUEST, f"Invalid JSON: {str(e)}"
                    )
            elif any(key in event for key in ["user_id", "inference_type"]):
                event["parsed_body"] = {
                    k: v
                    for k, v in event.items()
                    if k
                    not in [
                        "requestContext",
                        "headers",
                        "pathParameters",
                        "queryStringParameters",
                    ]
                }
                logger.debug("Direct Lambda invocation detected")
            else:
                event["parsed_body"] = {}
            return handler(event, context)
        except Exception:
            logger.error("Unexpected error in json_middleware", exc_info=True)
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                "Internal server error",
            )

    return wrapper


def method_validation_middleware(
    allowed_methods: list,
) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:

    def decorator(
        handler: Callable[..., Dict[str, Any]],
    ) -> Callable[..., Dict[str, Any]]:
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if not event.get("requestContext"):
                # Direct Lambda invocation - skip method validation
                return handler(event, context)
            if method not in allowed_methods and method != "OPTIONS":
                logger.info(
                    "Method not allowed",
                    extra={"data": {"method": method, "allowed": allowed_methods}}
                )
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

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            method = event.get("requestContext", {}).get("http", {}).get("method", "")
            if method == "OPTIONS":
                return handler(event, context)
            parsed_body = event.get("parsed_body", {})

            if not parsed_body.get("user_id"):
                logger.info("Request validation failed: missing user_id")
                return create_error_response(
                    HTTP_BAD_REQUEST, "Missing required field: user_id"
                )
            if not parsed_body.get("inference_type"):
                logger.info("Request validation failed: missing inference_type")
                return create_error_response(
                    HTTP_BAD_REQUEST, "Missing required field: inference_type"
                )
            return handler(event, context)
        except Exception:
            logger.error("Request validation error", exc_info=True)
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                "Request validation error",
            )

    return wrapper


def request_size_validation_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:
    """Validate request payload sizes before processing.

    This middleware protects against oversized payloads that could:
    - Exhaust Lambda memory (128MB-3GB depending on config)
    - Cause excessive processing time
    - Result in API Gateway 10MB payload limit errors

    Validates:
    - Audio payload size (base64 encoded)
    - Text input length
    - Music list size
    - Input data array size
    """

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        if method == "OPTIONS":
            return handler(event, context)

        parsed_body = event.get("parsed_body", {})

        # Validate audio payload size
        audio = parsed_body.get("audio", "")
        if audio and audio != "NotAvailable":
            audio_size = len(audio) if isinstance(audio, str) else 0
            if audio_size > MAX_AUDIO_PAYLOAD_BYTES:
                logger.warning(
                    "Audio payload too large",
                    extra={"data": {"size": audio_size, "max": MAX_AUDIO_PAYLOAD_BYTES}},
                )
                return create_error_response(
                    HTTP_BAD_REQUEST,
                    f"Audio payload exceeds maximum size of {MAX_AUDIO_PAYLOAD_BYTES // (1024 * 1024)}MB",
                )

        # Validate text input length
        prompt = parsed_body.get("prompt", "")
        if prompt and prompt != "NotAvailable":
            prompt_length = len(prompt) if isinstance(prompt, str) else 0
            if prompt_length > MAX_TEXT_INPUT_LENGTH:
                logger.warning(
                    "Text input too long",
                    extra={"data": {"length": prompt_length, "max": MAX_TEXT_INPUT_LENGTH}},
                )
                return create_error_response(
                    HTTP_BAD_REQUEST,
                    f"Text input exceeds maximum length of {MAX_TEXT_INPUT_LENGTH} characters",
                )

        # Validate music list size
        music_list = parsed_body.get("music_list", [])
        if isinstance(music_list, list) and len(music_list) > MAX_MUSIC_LIST_SIZE:
            logger.warning(
                "Music list too large",
                extra={"data": {"size": len(music_list), "max": MAX_MUSIC_LIST_SIZE}},
            )
            return create_error_response(
                HTTP_BAD_REQUEST,
                f"Music list exceeds maximum size of {MAX_MUSIC_LIST_SIZE} items",
            )

        # Validate input_data array size (for meditation requests)
        input_data = parsed_body.get("input_data", {})
        if isinstance(input_data, list) and len(input_data) > MAX_INPUT_DATA_ITEMS:
            logger.warning(
                "Input data too large",
                extra={"data": {"size": len(input_data), "max": MAX_INPUT_DATA_ITEMS}},
            )
            return create_error_response(
                HTTP_BAD_REQUEST,
                f"Input data exceeds maximum of {MAX_INPUT_DATA_ITEMS} items",
            )

        return handler(event, context)

    return wrapper


def error_handling_middleware(
    handler: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:
    """Handle exceptions and convert them to appropriate HTTP responses.

    Exception handling priority:
    1. FloatException hierarchy - use code, message, retriable from exception
    2. ValueError - treat as bad request (4xx)
    3. All other exceptions - internal server error (5xx)
    """
    from ..exceptions import ExternalServiceError, FloatException, ValidationError

    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return handler(event, context)
        except ValidationError as e:
            logger.warning(
                "Validation error",
                extra={"data": {"error": str(e), "code": e.code.value}}
            )
            return create_error_response(HTTP_BAD_REQUEST, e.message)
        except ExternalServiceError as e:
            logger.error(
                "External service error",
                extra={"data": {"error": str(e), "code": e.code.value, "retriable": e.retriable}},
                exc_info=True
            )
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR,
                e.message,
                details=f"retriable={e.retriable}"
            )
        except FloatException as e:
            logger.error(
                "Domain error",
                extra={"data": {"error": str(e), "code": e.code.value}},
                exc_info=True
            )
            status_code = HTTP_BAD_REQUEST if not e.retriable else HTTP_INTERNAL_SERVER_ERROR
            return create_error_response(status_code, e.message)
        except ValueError as e:
            logger.warning("ValueError in handler", extra={"data": {"error": str(e)}})
            return create_error_response(HTTP_BAD_REQUEST, str(e))
        except Exception:
            logger.error("Unexpected error in handler", exc_info=True)
            return create_error_response(
                HTTP_INTERNAL_SERVER_ERROR, "An unexpected error occurred"
            )

    return wrapper


def create_error_response(
    status_code: int,
    error_message: str,
    details: Optional[str] = None,
) -> Dict[str, Any]:
    error_response = ErrorResponse(error=error_message, details=details)
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": error_response.to_json(),
    }


def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": HTTP_OK,
        "headers": CORS_HEADERS,
        "body": json.dumps(data),
    }


def apply_middleware(*middleware_functions):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, event, context, *args, **kwargs):
            def bound_handler(evt, ctx):
                return func(self, evt, ctx, *args, **kwargs)

            wrapped = bound_handler
            for middleware in reversed(middleware_functions):
                wrapped = middleware(wrapped)
            return wrapped(event, context)

        return wrapper

    return decorator
