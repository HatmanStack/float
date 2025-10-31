"""Unit tests for Lambda handler."""

import pytest
import json
from unittest.mock import MagicMock, patch, call
from src.handlers.lambda_handler import LambdaHandler, lambda_handler
from src.models.requests import SummaryRequest, MeditationRequest
from tests.mocks.external_apis import (
    create_sentiment_analysis_response,
    create_meditation_transcript
)
from tests.fixtures.sample_data import (
    SAMPLE_SUMMARY_REQUEST,
    SAMPLE_MEDITATION_REQUEST,
    EMPTY_PROMPT_REQUEST,
    VERY_LONG_PROMPT_REQUEST
)


class TestLambdaHandlerInitialization:
    """Test Lambda handler initialization and configuration."""

    def test_handler_initializes_with_default_ai_service(self):
        """Test handler initializes with default AI service."""
        with patch('src.handlers.lambda_handler.LambdaHandler._create_ai_service') as mock_create:
            mock_create.return_value = MagicMock()
            handler = LambdaHandler(validate_config=False)
            assert handler.ai_service is not None
            assert handler.storage_service is not None
            assert handler.audio_service is not None
            assert handler.tts_provider is not None

    def test_handler_accepts_injected_ai_service(self, mock_ai_service):
        """Test handler accepts dependency injected AI service."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        assert handler.ai_service == mock_ai_service

    def test_get_tts_provider_returns_openai(self):
        """Test get_tts_provider returns OpenAI provider."""
        with patch('src.handlers.lambda_handler.LambdaHandler._create_ai_service') as mock_create:
            mock_create.return_value = MagicMock()
            handler = LambdaHandler(validate_config=False)
            provider = handler.get_tts_provider()
            assert provider is not None


class TestSummaryRequestHandling:
    """Test handling of summary inference requests."""

    def test_summary_happy_path(self, mock_ai_service, mock_storage_service):
        """Test summary request with valid data."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        summary_request = SummaryRequest(
            type="summary",
            user_id="test-user-123",
            prompt="I had a difficult day at work",
            audio="NotAvailable"
        )

        result = handler.handle_summary_request(summary_request)

        # Verify response structure
        assert "request_id" in result
        assert "user_id" in result
        assert result["user_id"] == "test-user-123"
        assert "sentiment_label" in result
        assert result["status"] == "success"

        # Verify storage was called
        mock_storage_service.upload_json.assert_called()

    def test_summary_with_audio_file(self, mock_ai_service, mock_storage_service):
        """Test summary request with audio file."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        summary_request = SummaryRequest(
            type="summary",
            user_id="test-user-123",
            prompt="NotAvailable",
            audio="fake_base64_audio_data"
        )

        # Mock audio decoding and cleanup
        with patch('src.handlers.lambda_handler.decode_audio_base64') as mock_decode, \
             patch('src.handlers.lambda_handler.cleanup_temp_file') as mock_cleanup:

            mock_decode.return_value = "/tmp/audio.mp3"

            result = handler.handle_summary_request(summary_request)

            # Verify result
            assert result["status"] == "success"
            mock_decode.assert_called_once()
            mock_cleanup.assert_called_once()

    def test_summary_error_in_ai_service(self, mock_ai_service, mock_storage_service):
        """Test summary request when AI service fails."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        # Configure mock to raise exception
        mock_ai_service.analyze_sentiment.side_effect = Exception("AI service error")

        summary_request = SummaryRequest(
            type="summary",
            user_id="test-user-123",
            prompt="I had a difficult day",
            audio="NotAvailable"
        )

        # Should raise exception
        with pytest.raises(Exception):
            handler.handle_summary_request(summary_request)


class TestMeditationRequestHandling:
    """Test handling of meditation generation requests."""

    def test_meditation_happy_path(self, mock_ai_service, mock_audio_service, mock_storage_service):
        """Test meditation request with valid data."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service

        meditation_request = MeditationRequest(
            type="meditation",
            user_id="test-user-123",
            input_data={
                "sentiment_label": ["Sad"],
                "intensity": [4],
                "speech_to_text": ["NotAvailable"],
                "added_text": ["Difficult day"],
                "summary": ["Work stress"],
                "user_summary": ["Had a bad day"],
                "user_short_summary": ["Bad day"]
            },
            music_list=[{"name": "ambient", "path": "s3://bucket/ambient.mp3", "volume": 0.3}]
        )

        # Mock TTS and audio encoding
        with patch('src.handlers.lambda_handler.encode_audio_to_base64') as mock_encode, \
             patch('src.handlers.lambda_handler.cleanup_temp_file'):

            mock_encode.return_value = "base64_encoded_audio"

            result = handler.handle_meditation_request(meditation_request)

            # Verify response structure
            assert "request_id" in result
            assert "user_id" in result
            assert result["user_id"] == "test-user-123"
            assert "audio" in result
            assert result["status"] == "success"

    def test_meditation_tts_failure(self, mock_ai_service, mock_audio_service, mock_storage_service):
        """Test meditation request when TTS fails."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service

        # Configure TTS to fail
        handler.tts_provider.synthesize_speech.return_value = False

        meditation_request = MeditationRequest(
            type="meditation",
            user_id="test-user-123",
            input_data={
                "sentiment_label": ["Sad"],
                "intensity": [4],
                "speech_to_text": ["NotAvailable"],
                "added_text": ["Difficult day"],
                "summary": ["Work stress"],
                "user_summary": ["Had a bad day"],
                "user_short_summary": ["Bad day"]
            },
            music_list=[]
        )

        # Should raise exception due to TTS failure
        with pytest.raises(Exception):
            handler.handle_meditation_request(meditation_request)

    def test_meditation_audio_combination_failure(self, mock_ai_service, mock_audio_service, mock_storage_service):
        """Test meditation request when audio combination fails."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service

        # Configure audio service to fail
        mock_audio_service.combine_voice_and_music.side_effect = Exception("Audio combination failed")

        meditation_request = MeditationRequest(
            type="meditation",
            user_id="test-user-123",
            input_data={
                "sentiment_label": ["Sad"],
                "intensity": [4],
                "speech_to_text": ["NotAvailable"],
                "added_text": ["Difficult day"],
                "summary": ["Work stress"],
                "user_summary": ["Had a bad day"],
                "user_short_summary": ["Bad day"]
            },
            music_list=[]
        )

        # Should raise exception
        with pytest.raises(Exception):
            handler.handle_meditation_request(meditation_request)


class TestRequestRouting:
    """Test main request routing logic."""

    def test_handle_request_routes_to_summary(self, mock_ai_service, mock_storage_service):
        """Test request router directs summary requests correctly."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        event = {
            "parsed_body": SAMPLE_SUMMARY_REQUEST
        }

        with patch.object(handler, 'handle_summary_request', return_value={"status": "success"}) as mock_summary:
            result = handler.handle_request(event, MagicMock())
            mock_summary.assert_called_once()

    def test_handle_request_routes_to_meditation(self, mock_ai_service, mock_audio_service, mock_storage_service):
        """Test request router directs meditation requests correctly."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service

        event = {
            "parsed_body": SAMPLE_MEDITATION_REQUEST
        }

        with patch.object(handler, 'handle_meditation_request', return_value={"status": "success"}) as mock_meditation:
            result = handler.handle_request(event, MagicMock())
            mock_meditation.assert_called_once()

    def test_handle_request_invalid_type(self, mock_ai_service):
        """Test request router rejects unknown request types."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)

        event = {
            "parsed_body": {
                "type": "unknown_type",
                "user_id": "test-user",
                "data": "some data"
            }
        }

        result = handler.handle_request(event, MagicMock())

        # Should return error response
        assert result["statusCode"] == 400 or "error" in result


class TestLambdaEntryPoint:
    """Test Lambda function entry point."""

    def test_lambda_handler_calls_handler(self, mock_ai_service, mock_storage_service):
        """Test lambda_handler entry point."""
        with patch('src.handlers.lambda_handler.LambdaHandler') as mock_handler_class:
            mock_instance = MagicMock()
            mock_handler_class.return_value = mock_instance
            mock_instance.handle_request.return_value = {"statusCode": 200, "body": "success"}

            event = {"parsed_body": SAMPLE_SUMMARY_REQUEST}
            context = MagicMock()

            result = lambda_handler(event, context)

            # Verify handler was called
            mock_instance.handle_request.assert_called_once()


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in Lambda handler."""

    def test_empty_prompt_handling(self, mock_ai_service, mock_storage_service):
        """Test handler with empty prompt."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        summary_request = SummaryRequest(
            type="summary",
            user_id="test-user-123",
            prompt="",
            audio="NotAvailable"
        )

        # Handler should still process empty prompts (AI service decides handling)
        result = handler.handle_summary_request(summary_request)
        assert result["status"] == "success"

    def test_very_long_prompt_handling(self, mock_ai_service, mock_storage_service):
        """Test handler with very long prompt."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        long_prompt = "This is a test. " * 1000
        summary_request = SummaryRequest(
            type="summary",
            user_id="test-user-123",
            prompt=long_prompt,
            audio="NotAvailable"
        )

        # Handler should accept long prompts
        result = handler.handle_summary_request(summary_request)
        assert result["status"] == "success"
