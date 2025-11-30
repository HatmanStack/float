"""Unit tests for Lambda handler."""

import shutil
from unittest.mock import MagicMock

import pytest

from src.config.constants import InferenceType
from src.handlers.lambda_handler import LambdaHandler
from src.models.requests import MeditationRequest, SummaryRequest

# Check if ffmpeg is available for tests that need audio processing
FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


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


@pytest.mark.unit
class TestSummaryRequestRouting:
    """Test Lambda handler routing for summary requests."""

    def test_summary_request_routes_to_handle_summary_request(
        self, mock_ai_service, mock_storage_service, mock_tts_provider, monkeypatch
    ):
        """Test summary request routes to handle_summary_request."""
        from unittest.mock import patch

        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)

        # Mock services
        handler.storage_service = mock_storage_service
        handler.tts_provider = mock_tts_provider

        # Mock handle_summary_request method
        with patch.object(handler, 'handle_summary_request') as mock_handle_summary:
            mock_handle_summary.return_value = {"request_id": "test-123"}

            event = {
                "parsed_body": {
                    "user_id": "user-123",
                    "inference_type": "summary",
                    "prompt": "I had a bad day",
                    "audio": "NotAvailable"
                }
            }

            # Call handle_request directly without middleware
            handler.handle_request.__wrapped__(handler, event, {})

            # Verify handle_summary_request was called
            assert mock_handle_summary.called

    def test_summary_request_with_audio_processes_correctly(
        self, mock_ai_service, mock_storage_service, mock_tts_provider
    ):
        """Test summary request with audio data processes correctly."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.tts_provider = mock_tts_provider

        request = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="NotAvailable",
            audio="dGVzdCBhdWRpbyBkYXRh"  # base64 encoded test data
        )

        result = handler.handle_summary_request(request)

        assert result is not None
        assert "request_id" in result
        assert mock_ai_service.analyze_sentiment.called

    def test_summary_request_without_audio_processes_correctly(
        self, mock_ai_service, mock_storage_service
    ):
        """Test summary request without audio data processes correctly."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        request = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="I had a difficult day",
            audio="NotAvailable"
        )

        result = handler.handle_summary_request(request)

        assert result is not None
        assert "request_id" in result
        assert mock_ai_service.analyze_sentiment.called
        # Verify it was called with None for audio_file
        call_args = mock_ai_service.analyze_sentiment.call_args
        assert call_args.kwargs['audio_file'] is None

    def test_invalid_summary_request_raises_error(self):
        """Test invalid summary request raises appropriate error."""
        from src.models.requests import parse_request_body

        invalid_body = {
            "user_id": "user-123",
            "inference_type": "summary",
            "prompt": "NotAvailable",
            "audio": "NotAvailable"  # Both are NotAvailable - invalid
        }

        with pytest.raises(ValueError, match="Invalid request data"):
            parse_request_body(invalid_body)


@pytest.mark.unit
class TestMeditationRequestRouting:
    """Test Lambda handler routing for meditation requests."""

    def test_meditation_request_routes_to_handle_meditation_request(
        self, mock_ai_service, mock_storage_service, mock_audio_service, mock_tts_provider
    ):
        """Test meditation request routes to handle_meditation_request."""
        from unittest.mock import patch

        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service
        handler.tts_provider = mock_tts_provider

        with patch.object(handler, 'handle_meditation_request') as mock_handle_meditation:
            mock_handle_meditation.return_value = {"request_id": "test-456"}

            event = {
                "parsed_body": {
                    "user_id": "user-123",
                    "inference_type": "meditation",
                    "input_data": {"sentiment_label": ["Happy"]},
                    "music_list": []
                }
            }

            handler.handle_request.__wrapped__(handler, event, {})

            assert mock_handle_meditation.called

    @pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg not available")
    def test_meditation_request_with_all_required_fields(
        self, mock_ai_service, mock_storage_service, mock_audio_service, mock_tts_provider
    ):
        """Test meditation request with all required input_data fields."""
        from unittest.mock import MagicMock

        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service
        handler.tts_provider = mock_tts_provider

        # Mock the audio file operations
        handler.tts_provider.synthesize_speech = MagicMock(return_value=True)

        request = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
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

        # Mock file operations to avoid actual file I/O
        from unittest.mock import patch
        with patch('src.handlers.lambda_handler.encode_audio_to_base64') as mock_encode:
            mock_encode.return_value = "base64_encoded_audio"
            result = handler.handle_meditation_request(request)

        assert result is not None
        assert "request_id" in result
        assert mock_ai_service.generate_meditation.called

    @pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg not available")
    def test_meditation_request_with_music_list_processes_correctly(
        self, mock_ai_service, mock_storage_service, mock_audio_service, mock_tts_provider
    ):
        """Test meditation request with music list processes correctly."""
        from unittest.mock import MagicMock, patch

        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service
        handler.tts_provider = mock_tts_provider

        handler.tts_provider.synthesize_speech = MagicMock(return_value=True)

        request = MeditationRequest(
            user_id="user-123",
            inference_type=InferenceType.MEDITATION,
            input_data={"sentiment_label": ["Happy"]},
            music_list=["Ambient-Peaceful_300.wav", "Nature-Birds_180.wav"]
        )

        with patch('src.handlers.lambda_handler.encode_audio_to_base64') as mock_encode:
            mock_encode.return_value = "base64_encoded_audio"
            result = handler.handle_meditation_request(request)

        assert result is not None
        assert mock_audio_service.combine_voice_and_music.called
        call_args = mock_audio_service.combine_voice_and_music.call_args
        assert len(call_args.kwargs['music_list']) == 2

    def test_invalid_meditation_request_raises_error(self):
        """Test invalid meditation request raises appropriate error."""
        from src.models.requests import parse_request_body

        invalid_body = {
            "user_id": "user-123",
            "inference_type": "meditation",
            "input_data": {},  # Empty input_data - invalid
            "music_list": []
        }

        with pytest.raises(ValueError, match="Invalid request data"):
            parse_request_body(invalid_body)


@pytest.mark.unit
class TestRequestTypeDetection:
    """Test request type detection and routing logic."""

    def test_request_with_missing_type_field(self):
        """Test request with missing inference_type field."""
        from src.models.requests import parse_request_body

        body = {
            "user_id": "user-123",
            "prompt": "Test prompt"
        }

        with pytest.raises(ValueError, match="inference_type is required"):
            parse_request_body(body)

    def test_request_with_invalid_type_value(self):
        """Test request with invalid inference_type value."""
        from src.models.requests import parse_request_body

        body = {
            "user_id": "user-123",
            "inference_type": "invalid_type",
            "prompt": "Test prompt"
        }

        with pytest.raises(ValueError, match="Invalid inference_type"):
            parse_request_body(body)

    def test_request_with_missing_user_id(self):
        """Test request with missing user_id field."""
        from src.models.requests import parse_request_body

        body = {
            "inference_type": "summary",
            "prompt": "Test prompt"
        }

        with pytest.raises(ValueError, match="user_id is required"):
            parse_request_body(body)


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in Lambda handler."""

    def test_handler_catches_and_formats_exceptions(
        self, mock_ai_service, mock_storage_service
    ):
        """Test handler catches and formats exceptions properly."""

        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        # Make AI service raise an exception
        mock_ai_service.analyze_sentiment.side_effect = Exception("AI service error")

        request = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="Test",
            audio="NotAvailable"
        )

        with pytest.raises(Exception, match="AI service error"):
            handler.handle_summary_request(request)

    def test_validation_error_handling(self, mock_ai_service):
        """Test validation errors are handled appropriately."""
        from src.models.requests import parse_request_body

        # Test with invalid data
        body = {
            "user_id": "user-123",
            "inference_type": "summary",
            "prompt": "NotAvailable",
            "audio": "NotAvailable"
        }

        with pytest.raises(ValueError):
            parse_request_body(body)

    def test_unsupported_request_type_raises_error(self):
        """Test unsupported request type raises ValueError during parsing."""
        from src.models.requests import parse_request_body

        # An invalid inference_type should raise ValueError during parsing
        body = {"user_id": "test", "inference_type": "unsupported"}
        with pytest.raises(ValueError, match="Invalid inference_type"):
            parse_request_body(body)


@pytest.mark.unit
class TestDependencyInjection:
    """Test dependency injection in Lambda handler."""

    def test_handler_accepts_injected_services(self, mock_ai_service):
        """Test handler accepts all injected services."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)

        assert handler.ai_service == mock_ai_service
        assert handler.storage_service is not None
        assert handler.audio_service is not None
        assert handler.tts_provider is not None

    def test_handler_uses_injected_ai_service(
        self, mock_ai_service, mock_storage_service
    ):
        """Test handler uses injected AI service in request processing."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        request = SummaryRequest(
            user_id="user-123",
            inference_type=InferenceType.SUMMARY,
            prompt="Test prompt",
            audio="NotAvailable"
        )

        handler.handle_summary_request(request)

        # Verify the injected service was used
        assert mock_ai_service.analyze_sentiment.called

    def test_handler_uses_default_ai_service_when_not_injected(self):
        """Test handler creates default AI service when not injected."""
        pytest.importorskip("google.generativeai")
        # When no AI service is injected, handler should create a default one
        handler = LambdaHandler(ai_service=None, validate_config=False)

        # Default AI service should be created
        assert handler.ai_service is not None
