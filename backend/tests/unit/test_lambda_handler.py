"""Unit tests for Lambda handler."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.exceptions import ValidationError
from src.handlers.lambda_handler import LambdaHandler
from src.models.requests import MeditationRequestModel, SummaryRequestModel


@pytest.fixture
def mock_audio_service():
    """Mock audio service for testing."""
    service = MagicMock()
    service.combine_voice_and_music.return_value = ["Ambient-Peaceful-Meditation_300.wav"]
    return service


@pytest.fixture
def mock_tts_provider():
    """Mock TTS provider for testing."""
    provider = MagicMock()
    provider.synthesize_speech.return_value = True
    provider.get_provider_name.return_value = "openai"
    return provider


@pytest.fixture
def mock_lambda_context():
    """Mock Lambda context object."""
    context = MagicMock()
    context.function_name = "float-meditation"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:float-meditation"
    context.memory_limit_in_mb = 512
    context.aws_request_id = "test-request-id-12345"
    context.log_group_name = "/aws/lambda/float-meditation"
    context.log_stream_name = "2024/10/31/[$LATEST]abc123def456"
    context.get_remaining_time_in_millis = MagicMock(return_value=30000)
    return context


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
        req = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="I had a bad day",
            audio="NotAvailable",
        )
        assert req.user_id == "user-123"
        assert req.prompt == "I had a bad day"
        assert req.inference_type == "summary"

    def test_summary_request_construction_validates(self):
        """Test summary request validates on construction (Pydantic)."""
        # Valid request should not raise
        req = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="I had a bad day",
            audio="NotAvailable",
        )
        assert req.user_id == "user-123"


@pytest.mark.unit
class TestMeditationRequest:
    """Test meditation request handling."""

    def test_meditation_request_valid(self):
        """Test creating valid meditation request."""
        req = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
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
        assert req.inference_type == "meditation"
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
        result = settings.validate_keys(require_keys=False)
        assert result is True


@pytest.mark.unit
class TestSummaryRequestRouting:
    """Test Lambda handler routing for summary requests."""

    def test_summary_request_routes_to_handle_summary_request(
        self, mock_ai_service, mock_storage_service, mock_tts_provider, monkeypatch
    ):
        """Test summary request routes to handle_summary_request."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)

        # Mock services
        handler.storage_service = mock_storage_service
        handler.tts_provider = mock_tts_provider

        # Mock handle_summary_request method
        with patch.object(handler, "handle_summary_request") as mock_handle_summary:
            mock_handle_summary.return_value = {"request_id": "test-123"}

            event = {
                "parsed_body": {
                    "user_id": "user-123",
                    "inference_type": "summary",
                    "prompt": "I had a bad day",
                    "audio": "NotAvailable",
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

        request = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="NotAvailable",
            audio="dGVzdCBhdWRpbyBkYXRh",  # base64 encoded test data
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

        request = SummaryRequestModel(
            user_id="user-123",
            inference_type="summary",
            prompt="I had a difficult day",
            audio="NotAvailable",
        )

        result = handler.handle_summary_request(request)

        assert result is not None
        assert "request_id" in result
        assert mock_ai_service.analyze_sentiment.called
        # Verify it was called with None for audio_file
        call_args = mock_ai_service.analyze_sentiment.call_args
        assert call_args.kwargs["audio_file"] is None

    def test_invalid_summary_request_raises_error(self):
        """Test invalid summary request raises appropriate error."""
        from src.models.requests import parse_request_body

        invalid_body = {
            "user_id": "user-123",
            "inference_type": "summary",
            "prompt": "NotAvailable",
            "audio": "NotAvailable",  # Both are NotAvailable - invalid
        }

        with pytest.raises(ValidationError):
            parse_request_body(invalid_body)


@pytest.mark.unit
class TestMeditationRequestRouting:
    """Test Lambda handler routing for meditation requests."""

    def test_meditation_request_routes_to_handle_meditation_request(
        self, mock_ai_service, mock_storage_service, mock_audio_service, mock_tts_provider
    ):
        """Test meditation request routes to handle_meditation_request."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service
        handler.tts_provider = mock_tts_provider

        with patch.object(handler, "handle_meditation_request") as mock_handle_meditation:
            mock_handle_meditation.return_value = {"request_id": "test-456"}

            event = {
                "parsed_body": {
                    "user_id": "user-123",
                    "inference_type": "meditation",
                    "input_data": {"sentiment_label": ["Happy"]},
                    "music_list": [],
                }
            }

            handler.handle_request.__wrapped__(handler, event, {})

            assert mock_handle_meditation.called

    def test_meditation_request_with_all_required_fields(
        self, mock_ai_service, mock_storage_service, mock_audio_service, mock_tts_provider, monkeypatch
    ):
        """Test meditation request with all required input_data fields."""
        monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "float-meditation")
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.job_service.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service
        handler.tts_provider = mock_tts_provider

        # Mock the audio file operations
        handler.tts_provider.synthesize_speech = MagicMock(return_value=True)

        request = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
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

        # Mock the async Lambda invocation method directly
        with patch.object(handler, "_invoke_async_meditation") as mock_invoke:
            result = handler.handle_meditation_request(request)

        assert result is not None
        assert "job_id" in result
        assert result["status"] == "pending"
        assert mock_invoke.called

    def test_meditation_request_with_music_list_processes_correctly(
        self, mock_ai_service, mock_storage_service, mock_audio_service, mock_tts_provider
    ):
        """Test meditation request with music list creates async job correctly."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service
        handler.job_service.storage_service = mock_storage_service
        handler.audio_service = mock_audio_service
        handler.tts_provider = mock_tts_provider

        handler.tts_provider.synthesize_speech = MagicMock(return_value=True)

        request = MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment_label": ["Happy"]},
            music_list=["Ambient-Peaceful_300.wav", "Nature-Birds_180.wav"],
        )

        # Mock the async Lambda invocation method directly
        with patch.object(handler, "_invoke_async_meditation") as mock_invoke:
            result = handler.handle_meditation_request(request)

        assert result is not None
        assert "job_id" in result
        assert result["status"] == "pending"
        assert mock_invoke.called
        # Verify it was called with the request and a job_id
        call_args = mock_invoke.call_args
        assert call_args[0][0] == request  # first positional arg is the request

    def test_invalid_meditation_request_raises_error(self):
        """Test invalid meditation request raises appropriate error."""
        from src.models.requests import parse_request_body

        invalid_body = {
            "user_id": "user-123",
            "inference_type": "meditation",
            "input_data": {},  # Empty input_data - invalid
            "music_list": [],
        }

        with pytest.raises(ValidationError):
            parse_request_body(invalid_body)


@pytest.mark.unit
class TestRequestTypeDetection:
    """Test request type detection and routing logic."""

    def test_request_with_missing_type_field(self):
        """Test request with missing inference_type field."""
        from src.models.requests import parse_request_body

        body = {"user_id": "user-123", "prompt": "Test prompt"}

        with pytest.raises(ValidationError, match="inference_type is required"):
            parse_request_body(body)

    def test_request_with_invalid_type_value(self):
        """Test request with invalid inference_type value."""
        from src.models.requests import parse_request_body

        body = {"user_id": "user-123", "inference_type": "invalid_type", "prompt": "Test prompt"}

        with pytest.raises(ValidationError, match="Invalid inference_type"):
            parse_request_body(body)

    def test_request_with_missing_user_id(self):
        """Test request with missing user_id field."""
        from src.models.requests import parse_request_body

        body = {"inference_type": "summary", "prompt": "Test prompt"}

        with pytest.raises(ValidationError, match="user_id is required"):
            parse_request_body(body)


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in Lambda handler."""

    def test_handler_catches_and_formats_exceptions(self, mock_ai_service, mock_storage_service):
        """Test handler catches and formats exceptions properly."""

        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        # Make AI service raise an exception
        mock_ai_service.analyze_sentiment.side_effect = Exception("AI service error")

        request = SummaryRequestModel(
            user_id="user-123", inference_type="summary", prompt="Test", audio="NotAvailable"
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
            "audio": "NotAvailable",
        }

        with pytest.raises(ValidationError):
            parse_request_body(body)

    def test_unsupported_request_type_raises_error(self):
        """Test unsupported request type raises ValueError during parsing."""
        from src.models.requests import parse_request_body

        # An invalid inference_type should raise ValueError during parsing
        body = {"user_id": "test", "inference_type": "unsupported"}
        with pytest.raises(ValidationError, match="Invalid inference_type"):
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

    def test_handler_uses_injected_ai_service(self, mock_ai_service, mock_storage_service):
        """Test handler uses injected AI service in request processing."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = mock_storage_service

        request = SummaryRequestModel(
            user_id="user-123", inference_type="summary", prompt="Test prompt", audio="NotAvailable"
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


@pytest.mark.unit
class TestEndToEndSummaryFlow:
    """Test the full handle_request -> middleware -> handler path.

    Unlike other tests that mock handle_summary_request, these tests
    mock only external services (AI, storage) and let the full
    request flow execute.
    """

    @pytest.fixture
    def handler_with_mock_services(self, mock_ai_service):
        """Create handler with mocked external services but real routing."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        handler.storage_service = MagicMock()
        handler.storage_service.upload_json.return_value = True
        return handler

    def test_summary_request_full_flow(self, handler_with_mock_services, mock_lambda_context):
        """Exercise the full handle_request path for a summary request."""
        event = {
            "httpMethod": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Origin": "https://float-app.fun",
            },
            "body": json.dumps(
                {
                    "inference_type": "summary",
                    "user_id": "test-user-e2e",
                    "prompt": "I had a stressful day",
                    "audio": "NotAvailable",
                }
            ),
        }

        response = handler_with_mock_services.handle_request(event, mock_lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "sentiment_label" in body
        assert "intensity" in body
        # Verify AI service was actually called (not mocked at handler level)
        handler_with_mock_services.ai_service.analyze_sentiment.assert_called_once()
