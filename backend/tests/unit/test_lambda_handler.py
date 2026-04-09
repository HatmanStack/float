"""Unit tests for Lambda handler."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.exceptions import CircuitBreakerOpenError, TTSError, ValidationError
from src.handlers.lambda_handler import LambdaHandler
from src.models.requests import MeditationRequestModel, SummaryRequestModel


@pytest.fixture(autouse=True)
def _patch_tts_providers():
    """Patch TTS providers to avoid API key validation during handler init."""
    with (
        patch("src.handlers.lambda_handler.GeminiTTSProvider") as mock_gemini,
        patch("src.handlers.lambda_handler.OpenAITTSProvider") as mock_openai,
    ):
        mock_gemini.return_value.get_provider_name.return_value = "gemini"
        mock_gemini.return_value.synthesize_speech.return_value = True
        mock_gemini.return_value.stream_speech.return_value = iter([b"audio"])
        mock_openai.return_value.get_provider_name.return_value = "openai"
        mock_openai.return_value.synthesize_speech.return_value = True
        mock_openai.return_value.stream_speech.return_value = iter([b"audio"])
        yield


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
        self,
        mock_ai_service,
        mock_storage_service,
        mock_audio_service,
        mock_tts_provider,
        monkeypatch,
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
        pytest.importorskip("google.genai")
        # When no AI service is injected, handler should create a default one
        with patch("src.services.gemini_service.genai.Client"):
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


@pytest.mark.unit
class TestTTSProviderConfiguration:
    """Test TTS provider configuration and fallback logic."""

    def test_default_tts_provider_is_gemini(self, mock_ai_service):
        """Test that the default TTS provider is Gemini."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider") as mock_gemini,
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            mock_gemini.return_value.get_provider_name.return_value = "gemini"
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            assert handler.tts_provider.get_provider_name() == "gemini"

    def test_fallback_tts_provider_is_openai(self, mock_ai_service):
        """Test that the fallback TTS provider is OpenAI."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider") as mock_openai,
        ):
            mock_openai.return_value.get_provider_name.return_value = "openai"
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            assert handler.fallback_tts_provider.get_provider_name() == "openai"

    def test_tts_fallback_on_gemini_failure(self, mock_ai_service):
        """Test that OpenAI is used as fallback when Gemini TTS fails."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        mock_gemini = MagicMock()
        mock_openai = MagicMock()
        handler.tts_provider = mock_gemini
        handler.fallback_tts_provider = mock_openai

        mock_gemini.synthesize_speech.return_value = False
        mock_openai.synthesize_speech.return_value = True

        voice_path, combined_path = handler._generate_meditation_audio(
            "Test meditation text", "20240101120000"
        )
        mock_openai.synthesize_speech.assert_called_once()

    def test_tts_fallback_on_circuit_breaker_open(self, mock_ai_service):
        """Test fallback when Gemini circuit breaker is open in streaming mode."""
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        mock_gemini = MagicMock()
        mock_openai = MagicMock()
        handler.tts_provider = mock_gemini
        handler.fallback_tts_provider = mock_openai

        mock_gemini.stream_speech.side_effect = CircuitBreakerOpenError("gemini_tts")
        mock_openai.stream_speech.return_value = iter([b"audio_data"])

        tts_provider = handler.get_tts_provider()
        try:
            list(tts_provider.stream_speech("test"))
            fallback_used = False
        except (TTSError, CircuitBreakerOpenError):
            list(handler.fallback_tts_provider.stream_speech("test"))
            fallback_used = True

        assert fallback_used
        mock_openai.stream_speech.assert_called_once()


@pytest.mark.unit
class TestTokenEndpoint:
    """Test token exchange endpoint for Gemini Live API."""

    def _make_token_event(self, user_id=None):
        """Create a mock API Gateway event for POST /token."""
        query_params = {"user_id": user_id} if user_id else {}
        return {
            "rawPath": "/production/token",
            "requestContext": {"http": {"method": "POST"}},
            "queryStringParameters": query_params,
        }

    @patch("src.handlers.lambda_handler._get_handler")
    def test_token_request_returns_token(self, mock_get_handler, mock_ai_service):
        """Test POST /token returns token payload with opaque marker."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
            patch("src.handlers.lambda_handler.settings") as mock_settings,
        ):
            mock_settings.GEMINI_API_KEY = "test-gemini-key"
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_token_event(user_id="test-user")
            response = lambda_handler(event, None)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert "token" in body
            assert "endpoint" in body
            assert "expires_in" in body

    @patch("src.handlers.lambda_handler._get_handler")
    def test_token_endpoint_does_not_leak_api_key(self, mock_get_handler, mock_ai_service):
        """The /token response MUST NOT contain settings.GEMINI_API_KEY verbatim."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
            patch("src.handlers.lambda_handler.settings") as mock_settings,
        ):
            mock_settings.GEMINI_API_KEY = "super-secret-gemini-api-key-xyz"
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_token_event(user_id="test-user")
            response = lambda_handler(event, None)

            # Regardless of status code, the plaintext key must not appear
            assert "super-secret-gemini-api-key-xyz" not in response["body"]
            body = json.loads(response["body"])
            assert body.get("token") != "super-secret-gemini-api-key-xyz"

    @patch("src.handlers.lambda_handler._get_handler")
    def test_token_endpoint_returns_opaque_marker(self, mock_get_handler, mock_ai_service):
        """The token field should be an HMAC-derived hex string."""
        import re as _re

        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
            patch("src.handlers.lambda_handler.settings") as mock_settings,
        ):
            mock_settings.GEMINI_API_KEY = "test-gemini-key"
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_token_event(user_id="test-user")
            response = lambda_handler(event, None)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            token = body["token"]
            # HMAC-SHA256 hexdigest (truncated) - must be hex characters only
            assert isinstance(token, str)
            assert _re.fullmatch(r"[0-9a-f]+", token) is not None
            assert token != mock_settings.GEMINI_API_KEY

    @patch("src.handlers.lambda_handler._get_handler")
    def test_token_request_missing_user_id(self, mock_get_handler, mock_ai_service):
        """Test POST /token without user_id returns 400."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_token_event()
            response = lambda_handler(event, None)

            assert response["statusCode"] == 400

    @patch("src.handlers.lambda_handler._get_handler")
    def test_token_request_cors_headers(self, mock_get_handler, mock_ai_service):
        """Test POST /token response includes CORS headers."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
            patch("src.handlers.lambda_handler.settings") as mock_settings,
        ):
            mock_settings.GEMINI_API_KEY = "test-gemini-key"
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_token_event(user_id="test-user")
            response = lambda_handler(event, None)

            assert "Access-Control-Allow-Origin" in response.get("headers", {})

    @patch("src.handlers.lambda_handler._get_handler")
    def test_token_request_rejects_invalid_user_id(self, mock_get_handler, mock_ai_service):
        """POST /token with a path-traversal user_id must return 400."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
            patch("src.handlers.lambda_handler.settings") as mock_settings,
        ):
            mock_settings.GEMINI_API_KEY = "test-gemini-key"
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_token_event(user_id="../etc/passwd")
            response = lambda_handler(event, None)

            assert response["statusCode"] == 400


@pytest.mark.unit
class TestUserIdValidationInHandlers:
    """Test that route helpers reject invalid user_id values with 400."""

    def _make_job_status_event(self, user_id, job_id="abc"):
        return {
            "rawPath": f"/production/job/{job_id}",
            "requestContext": {"http": {"method": "GET"}},
            "queryStringParameters": {"user_id": user_id},
        }

    def _make_download_event(self, user_id, job_id="abc"):
        return {
            "rawPath": f"/production/job/{job_id}/download",
            "requestContext": {"http": {"method": "POST"}},
            "queryStringParameters": {"user_id": user_id},
        }

    @patch("src.handlers.lambda_handler._get_handler")
    def test_handle_job_status_rejects_invalid_user_id(self, mock_get_handler, mock_ai_service):
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_job_status_event(user_id="../etc/passwd")
            response = lambda_handler(event, None)

            assert response["statusCode"] == 400

    @patch("src.handlers.lambda_handler._get_handler")
    def test_handle_download_rejects_invalid_user_id(self, mock_get_handler, mock_ai_service):
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_download_event(user_id="a/b")
            response = lambda_handler(event, None)

            assert response["statusCode"] == 400

    @patch("src.handlers.lambda_handler._get_handler")
    def test_handle_job_status_rejects_slash_user_id(self, mock_get_handler, mock_ai_service):
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            from src.handlers.lambda_handler import lambda_handler

            event = self._make_job_status_event(user_id="user/evil")
            response = lambda_handler(event, None)

            assert response["statusCode"] == 400


@pytest.mark.unit
class TestRouteHandlerNameValidation:
    """Validate that every handler name in the _ROUTES table resolves
    against the lambda_handler module at import time.

    A typo (e.g., ``_handle_dowload_request``) would otherwise surface as
    a runtime ``AttributeError`` only at request-dispatch time.
    """

    def test_all_route_handler_names_resolve(self):
        """Every handler_name in _ROUTES must be a callable attribute
        of the lambda_handler module."""
        from src.handlers.router import _ROUTES, _resolve_handler

        for method, pattern, handler_name in _ROUTES:
            handler = _resolve_handler(handler_name)
            assert callable(handler), (
                f"Route ({method}, {pattern.pattern}) maps to "
                f"{handler_name!r} which is not callable"
            )


@pytest.mark.unit
class TestRoutingDispatchTable:
    """Test the dispatch-table routing in lambda_handler."""

    def _event(self, method, raw_path, user_id="user-abc"):
        return {
            "rawPath": raw_path,
            "requestContext": {"http": {"method": method}},
            "queryStringParameters": {"user_id": user_id},
        }

    @patch("src.handlers.lambda_handler._handle_job_status_request")
    @patch("src.handlers.lambda_handler._handle_download_request")
    @patch("src.handlers.lambda_handler._handle_token_request")
    @patch("src.handlers.lambda_handler._get_handler")
    def test_get_job_matches_job_status_route(
        self,
        mock_get_handler,
        mock_token,
        mock_download,
        mock_job_status,
        mock_ai_service,
    ):
        """GET /job/abc routes to the job-status handler only."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler
            mock_job_status.return_value = {"statusCode": 200, "body": "{}"}

            from src.handlers.lambda_handler import lambda_handler

            lambda_handler(self._event("GET", "/job/abc"), None)

            assert mock_job_status.called
            assert not mock_download.called
            assert not mock_token.called

    @patch("src.handlers.lambda_handler._handle_job_status_request")
    @patch("src.handlers.lambda_handler._handle_download_request")
    @patch("src.handlers.lambda_handler._handle_token_request")
    @patch("src.handlers.lambda_handler._get_handler")
    def test_get_production_prefix_job_matches_job_status_route(
        self,
        mock_get_handler,
        mock_token,
        mock_download,
        mock_job_status,
        mock_ai_service,
    ):
        """GET /production/job/abc (stage prefix) still matches."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler
            mock_job_status.return_value = {"statusCode": 200, "body": "{}"}

            from src.handlers.lambda_handler import lambda_handler

            lambda_handler(self._event("GET", "/production/job/abc"), None)

            assert mock_job_status.called
            assert not mock_download.called
            assert not mock_token.called

    @patch("src.handlers.lambda_handler._handle_job_status_request")
    @patch("src.handlers.lambda_handler._handle_download_request")
    @patch("src.handlers.lambda_handler._handle_token_request")
    @patch("src.handlers.lambda_handler._get_handler")
    def test_post_job_download_matches_download_only(
        self,
        mock_get_handler,
        mock_token,
        mock_download,
        mock_job_status,
        mock_ai_service,
    ):
        """POST /job/abc/download matches the download route, NOT job-status."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler
            mock_download.return_value = {"statusCode": 200, "body": "{}"}

            from src.handlers.lambda_handler import lambda_handler

            lambda_handler(self._event("POST", "/job/abc/download"), None)

            assert mock_download.called
            assert not mock_job_status.called
            assert not mock_token.called

    @patch("src.handlers.lambda_handler._handle_job_status_request")
    @patch("src.handlers.lambda_handler._handle_download_request")
    @patch("src.handlers.lambda_handler._handle_token_request")
    @patch("src.handlers.lambda_handler._get_handler")
    def test_post_token_matches_token_route(
        self,
        mock_get_handler,
        mock_token,
        mock_download,
        mock_job_status,
        mock_ai_service,
    ):
        """POST /token matches the token route only."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler
            mock_token.return_value = {"statusCode": 200, "body": "{}"}

            from src.handlers.lambda_handler import lambda_handler

            lambda_handler(self._event("POST", "/token"), None)

            assert mock_token.called
            assert not mock_download.called
            assert not mock_job_status.called

    @patch("src.handlers.lambda_handler._get_handler")
    def test_post_root_falls_through_to_main_handler(self, mock_get_handler, mock_ai_service):
        """POST / falls through to handler.handle_request (main inference path)."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler

            # Mock the main handler path
            with patch.object(handler, "handle_request") as mock_handle_request:
                mock_handle_request.return_value = {"statusCode": 200, "body": "{}"}

                from src.handlers.lambda_handler import lambda_handler

                event = {
                    "rawPath": "/",
                    "requestContext": {"http": {"method": "POST"}},
                    "body": "{}",
                }
                lambda_handler(event, None)

                assert mock_handle_request.called

    @patch("src.handlers.lambda_handler._handle_job_status_request")
    @patch("src.handlers.lambda_handler._handle_download_request")
    @patch("src.handlers.lambda_handler._handle_token_request")
    @patch("src.handlers.lambda_handler._get_handler")
    def test_download_job_x_does_not_double_match_job_status(
        self,
        mock_get_handler,
        mock_token,
        mock_download,
        mock_job_status,
        mock_ai_service,
    ):
        """The historical ambiguous path /job/abc/download must NOT match job-status."""
        with (
            patch("src.handlers.lambda_handler.GeminiTTSProvider"),
            patch("src.handlers.lambda_handler.OpenAITTSProvider"),
        ):
            handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
            mock_get_handler.return_value = handler
            mock_download.return_value = {"statusCode": 200, "body": "{}"}

            from src.handlers.lambda_handler import lambda_handler

            lambda_handler(self._event("POST", "/production/job/abc/download"), None)

            assert mock_download.called
            assert not mock_job_status.called


@pytest.mark.unit
class TestHLSRetryLoop:
    """Phase 3 Task 4 -- tightened HLS retry self-invoke loop."""

    def _make_request(self) -> MeditationRequestModel:
        return MeditationRequestModel(
            user_id="user-123",
            inference_type="meditation",
            input_data={"sentiment_label": ["Sad"]},
            music_list=[],
        )

    def _make_handler(self, mock_ai_service):
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
        # Force the HLS branch in process_meditation_async via patched job data
        handler.job_service = MagicMock()
        handler.hls_service = MagicMock()
        handler.audio_service = MagicMock()
        return handler

    def _trigger_retry_path(self, handler, boom: Exception, current_attempt: int):
        """Drive _process_meditation_hls into its exception handler."""
        request = self._make_request()
        handler.job_service.get_job.return_value = {"generation_attempt": current_attempt}
        handler.job_service.update_job_status.return_value = None
        # Make the first service call inside _process_meditation_hls raise.
        handler.job_service.update_job_status.side_effect = [boom]
        # update_job_status is called to set PROCESSING; after that raises,
        # the except Exception block runs and re-fetches the job.
        handler._process_meditation_hls("job-1", request)
        return request

    def test_retry_fires_when_counter_and_invoke_succeed(self, mock_ai_service):
        handler = self._make_handler(mock_ai_service)
        with patch.object(handler, "_invoke_async_meditation") as mock_invoke:
            # Second get_job call (inside except) returns attempt=1
            handler.job_service.get_job.return_value = {"generation_attempt": 1}
            # First update_job_status (PROCESSING) blows up to enter the except
            handler.job_service.update_job_status.side_effect = [RuntimeError("boom"), None]
            request = self._make_request()
            handler._process_meditation_hls("job-1", request)
            handler.job_service.increment_generation_attempt.assert_called_once_with(
                "user-123", "job-1"
            )
            mock_invoke.assert_called_once()

    def test_retry_does_not_fire_on_increment_failure(self, mock_ai_service):
        handler = self._make_handler(mock_ai_service)
        with patch.object(handler, "_invoke_async_meditation") as mock_invoke:
            handler.job_service.get_job.return_value = {"generation_attempt": 1}
            handler.job_service.update_job_status.side_effect = [RuntimeError("boom"), None]
            handler.job_service.increment_generation_attempt.side_effect = RuntimeError(
                "counter write failed"
            )
            request = self._make_request()
            handler._process_meditation_hls("job-1", request)
            mock_invoke.assert_not_called()
            # Second update_job_status call marks the job failed
            assert handler.job_service.update_job_status.call_count == 2

    def test_retry_marks_failed_on_invoke_failure(self, mock_ai_service):
        handler = self._make_handler(mock_ai_service)
        with patch.object(handler, "_invoke_async_meditation") as mock_invoke:
            handler.job_service.get_job.return_value = {"generation_attempt": 1}
            handler.job_service.update_job_status.side_effect = [RuntimeError("boom"), None]
            mock_invoke.side_effect = RuntimeError("lambda invoke failed")
            request = self._make_request()
            handler._process_meditation_hls("job-1", request)
            handler.job_service.increment_generation_attempt.assert_called_once()
            mock_invoke.assert_called_once()
            # Mark-failed should still run
            assert handler.job_service.update_job_status.call_count == 2

    def test_no_retry_when_attempts_exhausted(self, mock_ai_service):
        handler = self._make_handler(mock_ai_service)
        with patch.object(handler, "_invoke_async_meditation") as mock_invoke:
            handler.job_service.get_job.return_value = {"generation_attempt": 3}
            handler.job_service.update_job_status.side_effect = [RuntimeError("boom"), None]
            request = self._make_request()
            handler._process_meditation_hls("job-1", request)
            handler.job_service.increment_generation_attempt.assert_not_called()
            mock_invoke.assert_not_called()
