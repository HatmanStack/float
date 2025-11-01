"""Unit tests for Lambda handler."""

import pytest

from src.config.constants import InferenceType
from src.handlers.lambda_handler import LambdaHandler
from src.models.requests import MeditationRequest, SummaryRequest


@pytest.mark.unit
class TestLambdaHandlerInitialization:
    """Test Lambda handler initialization."""

    def test_handler_accepts_injected_ai_service(self, mock_ai_service):
        """Test handler accepts dependency injected AI service."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        assert handler.ai_service == mock_ai_service
        assert handler.storage_service is not None
        assert handler.audio_service is not None
        assert handler.tts_provider is not None

    def test_handler_get_tts_provider(self, mock_ai_service):
        """Test get_tts_provider returns TTS provider."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        provider = handler.get_tts_provider()
        assert provider is not None


@pytest.mark.unit
class TestSummaryRequest:
    """Test summary request handling."""

    def test_summary_request_valid(self):
        """Test creating valid summary request."""
        req = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="I had a bad day",
            audio="NotAvailable",
        )
        assert req.user_id == "user-123"
        assert req.prompt == "I had a bad day"
        assert req.inference_type == InferenceType.SUMMARY

    def test_summary_request_validation(self):
        """Test summary request validation."""
        req = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="I had a bad day",
            audio="NotAvailable",
        )
        assert req.validate() is True


@pytest.mark.unit
class TestMeditationRequest:
    """Test meditation request handling."""

    def test_meditation_request_valid(self):
        """Test creating valid meditation request."""
        req = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
            input_data={
                "sentiment_label": ["Sad"],
                "intensity": [4],
                "speech_to_text": ["NotAvailable"],
                "added_text": ["Difficult day"],
                "summary": ["Work stress"],
                "user_summary": ["Had a bad day"],
                "user_short_summary": ["Bad day"],
            },
            music_list=[],
        )
        assert req.user_id == "user-123"
        assert req.inference_type == InferenceType.MEDITATION
        assert "sentiment_label" in req.input_data


@pytest.mark.unit
class TestHandlerConfigValidation:
    """Test configuration validation behavior."""

    def test_validate_config_false_skips_validation(self, mock_ai_service):
        """Test that validate_config=False skips environment validation."""
        # This should not raise even without env vars
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        assert handler is not None

    def test_settings_validate_with_flag(self):
        """Test settings validation can be skipped."""
        from src.config.settings import settings

        # Should not raise when require_keys=False
        result = settings.validate(require_keys=False)
        assert result is True
