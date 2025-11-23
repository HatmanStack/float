"""Unit tests for middleware functions."""

import json

import pytest

from src.config.constants import (
    CORS_HEADERS,
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_METHOD_NOT_ALLOWED,
    HTTP_OK,
)
from src.handlers.middleware import (
    cors_middleware,
    create_error_response,
    create_success_response,
    error_handling_middleware,
    json_middleware,
    method_validation_middleware,
    request_validation_middleware,
)


@pytest.mark.unit
class TestCORSMiddleware:
    """Test CORS middleware functionality."""

    def test_cors_headers_added_to_successful_responses(self):
        """Test CORS headers are added to successful responses."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = cors_middleware(mock_handler)
        result = wrapped({}, {})

        assert "headers" in result
        assert result["headers"] == CORS_HEADERS

    def test_cors_headers_added_to_error_responses(self):
        """Test CORS headers are added to error responses."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_BAD_REQUEST, "body": "Error"}

        wrapped = cors_middleware(mock_handler)
        result = wrapped({}, {})

        assert "headers" in result
        assert result["headers"] == CORS_HEADERS

    def test_preflight_options_requests_handled_correctly(self):
        """Test preflight OPTIONS requests handled correctly."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Should not reach here"}

        wrapped = cors_middleware(mock_handler)

        event = {
            "requestContext": {
                "http": {"method": "OPTIONS"}
            }
        }

        result = wrapped(event, {})

        assert result["statusCode"] == HTTP_OK
        assert result["headers"] == CORS_HEADERS
        assert result["body"] == ""

    def test_cors_headers_merge_with_existing_headers(self):
        """Test CORS headers merge with existing headers."""
        def mock_handler(event, context):
            return {
                "statusCode": HTTP_OK,
                "headers": {"Custom-Header": "value"},
                "body": "Success"
            }

        wrapped = cors_middleware(mock_handler)
        result = wrapped({}, {})

        assert "headers" in result
        assert result["headers"]["Custom-Header"] == "value"
        for key, value in CORS_HEADERS.items():
            assert result["headers"][key] == value


@pytest.mark.unit
class TestJSONMiddleware:
    """Test JSON parsing and handling middleware."""

    def test_valid_json_body_parsed_correctly(self):
        """Test valid JSON body parsed correctly."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": json.dumps(event["parsed_body"])}

        wrapped = json_middleware(mock_handler)

        event = {
            "body": json.dumps({"user_id": "test-123", "inference_type": "summary"}),
            "requestContext": {"http": {"method": "POST"}}
        }

        wrapped(event, {})

        assert "parsed_body" in event
        assert event["parsed_body"]["user_id"] == "test-123"

    def test_invalid_json_returns_400_error(self):
        """Test invalid JSON returns 400 error."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = json_middleware(mock_handler)

        event = {
            "body": "invalid json {{{",
            "requestContext": {"http": {"method": "POST"}}
        }

        result = wrapped(event, {})

        assert result["statusCode"] == HTTP_BAD_REQUEST
        assert "Invalid JSON" in result["body"]

    def test_missing_body_handled_appropriately(self):
        """Test missing body handled appropriately."""
        def mock_handler(event, context):
            assert "parsed_body" in event
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = json_middleware(mock_handler)

        event = {
            "requestContext": {"http": {"method": "POST"}}
        }

        wrapped(event, {})

        assert "parsed_body" in event
        assert event["parsed_body"] == {}

    def test_empty_body_handled_appropriately(self):
        """Test empty body handled appropriately."""
        def mock_handler(event, context):
            assert "parsed_body" in event
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = json_middleware(mock_handler)

        event = {
            "body": "",
            "requestContext": {"http": {"method": "POST"}}
        }

        wrapped(event, {})

        assert "parsed_body" in event

    def test_direct_lambda_invocation_data_extracted(self):
        """Test direct Lambda invocation (data at root level) extracted correctly."""
        def mock_handler(event, context):
            assert "parsed_body" in event
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = json_middleware(mock_handler)

        event = {
            "user_id": "test-123",
            "inference_type": "summary",
            "prompt": "Test"
        }

        wrapped(event, {})

        assert "parsed_body" in event
        assert event["parsed_body"]["user_id"] == "test-123"
        assert event["parsed_body"]["inference_type"] == "summary"

    def test_options_request_skips_json_parsing(self):
        """Test OPTIONS request skips JSON parsing."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": ""}

        wrapped = json_middleware(mock_handler)

        event = {
            "requestContext": {"http": {"method": "OPTIONS"}}
        }

        wrapped(event, {})

        assert "parsed_body" in event
        assert event["parsed_body"] == {}


@pytest.mark.unit
class TestMethodValidationMiddleware:
    """Test HTTP method validation middleware."""

    def test_post_method_allowed(self):
        """Test POST method allowed."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        middleware = method_validation_middleware(["POST"])
        wrapped = middleware(mock_handler)

        event = {
            "requestContext": {"http": {"method": "POST"}}
        }

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_OK

    def test_get_method_returns_405_error(self):
        """Test GET method returns 405 error."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        middleware = method_validation_middleware(["POST"])
        wrapped = middleware(mock_handler)

        event = {
            "requestContext": {"http": {"method": "GET"}}
        }

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_METHOD_NOT_ALLOWED
        assert "not allowed" in result["body"].lower()

    def test_put_delete_methods_return_405_error(self):
        """Test PUT/DELETE methods return 405 error."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        middleware = method_validation_middleware(["POST"])
        wrapped = middleware(mock_handler)

        for method in ["PUT", "DELETE", "PATCH"]:
            event = {
                "requestContext": {"http": {"method": method}}
            }
            result = wrapped(event, {})
            assert result["statusCode"] == HTTP_METHOD_NOT_ALLOWED

    def test_options_method_bypasses_validation(self):
        """Test OPTIONS method bypasses validation (for CORS)."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": ""}

        middleware = method_validation_middleware(["POST"])
        wrapped = middleware(mock_handler)

        event = {
            "requestContext": {"http": {"method": "OPTIONS"}}
        }

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_OK

    def test_direct_lambda_invocation_skips_method_validation(self):
        """Test direct Lambda invocation skips method validation."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        middleware = method_validation_middleware(["POST"])
        wrapped = middleware(mock_handler)

        event = {}  # No requestContext for direct invocation

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_OK


@pytest.mark.unit
class TestRequestValidationMiddleware:
    """Test request validation middleware."""

    def test_valid_request_data_passes_through(self):
        """Test valid request data passes through."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = request_validation_middleware(mock_handler)

        event = {
            "parsed_body": {
                "user_id": "test-123",
                "inference_type": "summary"
            },
            "requestContext": {"http": {"method": "POST"}}
        }

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_OK

    def test_missing_user_id_returns_400(self):
        """Test missing user_id returns 400 error."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = request_validation_middleware(mock_handler)

        event = {
            "parsed_body": {
                "inference_type": "summary"
            },
            "requestContext": {"http": {"method": "POST"}}
        }

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_BAD_REQUEST
        assert "user_id" in result["body"].lower()

    def test_missing_inference_type_returns_400(self):
        """Test missing inference_type returns 400 error."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = request_validation_middleware(mock_handler)

        event = {
            "parsed_body": {
                "user_id": "test-123"
            },
            "requestContext": {"http": {"method": "POST"}}
        }

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_BAD_REQUEST
        assert "inference_type" in result["body"].lower()

    def test_options_request_skips_validation(self):
        """Test OPTIONS request skips validation."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": ""}

        wrapped = request_validation_middleware(mock_handler)

        event = {
            "parsed_body": {},
            "requestContext": {"http": {"method": "OPTIONS"}}
        }

        result = wrapped(event, {})
        assert result["statusCode"] == HTTP_OK


@pytest.mark.unit
class TestErrorHandlingMiddleware:
    """Test error handling middleware."""

    def test_exceptions_caught_and_formatted_properly(self):
        """Test exceptions caught and formatted properly."""
        def mock_handler(event, context):
            raise Exception("Unexpected error")

        wrapped = error_handling_middleware(mock_handler)

        result = wrapped({}, {})
        assert result["statusCode"] == HTTP_INTERNAL_SERVER_ERROR
        assert "unexpected" in result["body"].lower()

    def test_value_error_returns_400_status(self):
        """Test ValueError returns 400 status code."""
        def mock_handler(event, context):
            raise ValueError("Invalid input")

        wrapped = error_handling_middleware(mock_handler)

        result = wrapped({}, {})
        assert result["statusCode"] == HTTP_BAD_REQUEST
        assert "Invalid input" in result["body"]

    def test_successful_response_passes_through(self):
        """Test successful response passes through unchanged."""
        def mock_handler(event, context):
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = error_handling_middleware(mock_handler)

        result = wrapped({}, {})
        assert result["statusCode"] == HTTP_OK
        assert result["body"] == "Success"


@pytest.mark.unit
class TestMiddlewareChainExecution:
    """Test middleware chain execution order and integration."""

    def test_middleware_executes_in_correct_order(self):
        """Test middleware executes in correct order."""
        execution_order = []

        def tracking_middleware(name):
            def middleware(handler):
                def wrapper(event, context):
                    execution_order.append(f"{name}_before")
                    result = handler(event, context)
                    execution_order.append(f"{name}_after")
                    return result
                return wrapper
            return middleware

        def mock_handler(event, context):
            execution_order.append("handler")
            return {"statusCode": HTTP_OK, "body": "Success"}

        # Apply middlewares (they apply in reverse order)
        wrapped = tracking_middleware("first")(mock_handler)
        wrapped = tracking_middleware("second")(wrapped)
        wrapped = tracking_middleware("third")(wrapped)

        wrapped({}, {})

        # Middlewares should execute: third -> second -> first -> handler -> first -> second -> third
        assert execution_order[0] == "third_before"
        assert execution_order[1] == "second_before"
        assert execution_order[2] == "first_before"
        assert execution_order[3] == "handler"
        assert execution_order[4] == "first_after"
        assert execution_order[5] == "second_after"
        assert execution_order[6] == "third_after"

    def test_early_middleware_can_short_circuit_chain(self):
        """Test early middleware can short-circuit chain."""
        def blocking_middleware(handler):
            def wrapper(event, context):
                # Short-circuit - don't call handler
                return {"statusCode": HTTP_BAD_REQUEST, "body": "Blocked"}
            return wrapper

        def mock_handler(event, context):
            # Should not be reached
            return {"statusCode": HTTP_OK, "body": "Success"}

        wrapped = blocking_middleware(mock_handler)
        result = wrapped({}, {})

        assert result["statusCode"] == HTTP_BAD_REQUEST
        assert result["body"] == "Blocked"


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions for creating responses."""

    def test_create_error_response_structure(self):
        """Test create_error_response creates proper structure."""
        result = create_error_response(HTTP_BAD_REQUEST, "Test error", "Details here")

        assert result["statusCode"] == HTTP_BAD_REQUEST
        assert "headers" in result
        assert result["headers"] == CORS_HEADERS
        assert "body" in result

        # Body should be JSON
        body = json.loads(result["body"])
        assert body["error"] == "Test error"
        assert body["details"] == "Details here"

    def test_create_error_response_without_details(self):
        """Test create_error_response without details."""
        result = create_error_response(HTTP_INTERNAL_SERVER_ERROR, "Server error")

        assert result["statusCode"] == HTTP_INTERNAL_SERVER_ERROR
        body = json.loads(result["body"])
        assert body["error"] == "Server error"

    def test_create_success_response_structure(self):
        """Test create_success_response creates proper structure."""
        data = {"request_id": "123", "result": "success"}
        result = create_success_response(data)

        assert result["statusCode"] == HTTP_OK
        assert result["headers"] == CORS_HEADERS
        assert "body" in result

        # Body should be JSON
        body = json.loads(result["body"])
        assert body["request_id"] == "123"
        assert body["result"] == "success"

    def test_create_success_response_with_complex_data(self):
        """Test create_success_response with complex data."""
        data = {
            "request_id": "123",
            "data": {
                "nested": "value",
                "list": [1, 2, 3]
            }
        }
        result = create_success_response(data)

        body = json.loads(result["body"])
        assert body["request_id"] == "123"
        assert body["data"]["nested"] == "value"
        assert body["data"]["list"] == [1, 2, 3]
