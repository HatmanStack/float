"""Unit tests for request size validation middleware."""

import pytest

from src.config.constants import (
    MAX_AUDIO_PAYLOAD_BYTES,
    MAX_INPUT_DATA_ITEMS,
    MAX_MUSIC_LIST_SIZE,
    MAX_TEXT_INPUT_LENGTH,
)
from src.handlers.middleware import request_size_validation_middleware


def create_mock_handler():
    """Create a mock handler that returns success."""
    def handler(event, context):
        return {"statusCode": 200, "body": "success"}
    return handler


def create_event(parsed_body, method="POST"):
    """Create a mock Lambda event."""
    return {
        "requestContext": {"http": {"method": method}},
        "parsed_body": parsed_body,
    }


@pytest.mark.unit
class TestRequestSizeValidationMiddleware:
    """Test request_size_validation_middleware."""

    def test_allows_valid_request(self):
        """Valid request should pass through."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "prompt": "This is a valid prompt",
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_allows_options_request(self):
        """OPTIONS requests should pass through without validation."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        event = create_event({}, method="OPTIONS")

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_rejects_oversized_audio(self):
        """Request with audio exceeding limit should be rejected."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        # Create audio payload larger than limit
        oversized_audio = "x" * (MAX_AUDIO_PAYLOAD_BYTES + 1)

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "audio": oversized_audio,
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 400
        assert "Audio payload" in result["body"]

    def test_allows_audio_at_limit(self):
        """Request with audio at exactly the limit should pass."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        # Create audio payload at exactly the limit
        max_audio = "x" * MAX_AUDIO_PAYLOAD_BYTES

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "audio": max_audio,
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_allows_not_available_audio(self):
        """Audio set to 'NotAvailable' should be ignored."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "audio": "NotAvailable",
            "prompt": "valid prompt",
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_rejects_oversized_text(self):
        """Request with text exceeding limit should be rejected."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        oversized_text = "x" * (MAX_TEXT_INPUT_LENGTH + 1)

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "prompt": oversized_text,
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 400
        assert "Text input" in result["body"]

    def test_allows_text_at_limit(self):
        """Request with text at exactly the limit should pass."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        max_text = "x" * MAX_TEXT_INPUT_LENGTH

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "prompt": max_text,
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_allows_not_available_text(self):
        """Prompt set to 'NotAvailable' should be ignored."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "prompt": "NotAvailable",
            "audio": "validbase64audio",
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_rejects_oversized_music_list(self):
        """Request with music_list exceeding limit should be rejected."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        oversized_music_list = [f"track{i}.mp3" for i in range(MAX_MUSIC_LIST_SIZE + 1)]

        event = create_event({
            "user_id": "user123",
            "inference_type": "meditation",
            "input_data": {"sentiment_label": ["Happy"]},
            "music_list": oversized_music_list,
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 400
        assert "Music list" in result["body"]

    def test_allows_music_list_at_limit(self):
        """Request with music_list at exactly the limit should pass."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        max_music_list = [f"track{i}.mp3" for i in range(MAX_MUSIC_LIST_SIZE)]

        event = create_event({
            "user_id": "user123",
            "inference_type": "meditation",
            "input_data": {"sentiment_label": ["Happy"]},
            "music_list": max_music_list,
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_rejects_oversized_input_data(self):
        """Request with input_data array exceeding limit should be rejected."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        oversized_input = [{"sentiment_label": "Happy"} for _ in range(MAX_INPUT_DATA_ITEMS + 1)]

        event = create_event({
            "user_id": "user123",
            "inference_type": "meditation",
            "input_data": oversized_input,
            "music_list": [],
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 400
        assert "Input data" in result["body"]

    def test_allows_input_data_at_limit(self):
        """Request with input_data at exactly the limit should pass."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        max_input = [{"sentiment_label": "Happy"} for _ in range(MAX_INPUT_DATA_ITEMS)]

        event = create_event({
            "user_id": "user123",
            "inference_type": "meditation",
            "input_data": max_input,
            "music_list": [],
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_allows_dict_input_data(self):
        """Dictionary input_data should not be subject to array size limit."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        # Dict with many keys is fine
        dict_input = {f"key{i}": f"value{i}" for i in range(100)}

        event = create_event({
            "user_id": "user123",
            "inference_type": "meditation",
            "input_data": dict_input,
            "music_list": [],
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_handles_empty_parsed_body(self):
        """Empty parsed_body should pass size validation."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        event = create_event({})

        result = wrapped(event, None)
        assert result["statusCode"] == 200

    def test_handles_non_string_audio(self):
        """Non-string audio should not cause error."""
        handler = create_mock_handler()
        wrapped = request_size_validation_middleware(handler)

        event = create_event({
            "user_id": "user123",
            "inference_type": "summary",
            "audio": 12345,  # Invalid type
        })

        result = wrapped(event, None)
        assert result["statusCode"] == 200  # Passes size check, may fail later validation


@pytest.mark.unit
class TestSizeLimitConstants:
    """Test that size limit constants are reasonable."""

    def test_audio_limit_is_10mb(self):
        """Audio limit should be 10MB."""
        assert MAX_AUDIO_PAYLOAD_BYTES == 10 * 1024 * 1024

    def test_text_limit_is_10k_chars(self):
        """Text limit should be 10,000 characters."""
        assert MAX_TEXT_INPUT_LENGTH == 10000

    def test_music_list_limit_is_20(self):
        """Music list limit should be 20 items."""
        assert MAX_MUSIC_LIST_SIZE == 20

    def test_input_data_limit_is_50(self):
        """Input data array limit should be 50 items."""
        assert MAX_INPUT_DATA_ITEMS == 50
