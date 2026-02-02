"""Unit tests for the domain exception hierarchy."""

import pytest

from src.exceptions import (
    AIServiceError,
    AudioProcessingError,
    CircuitBreakerOpenError,
    EncodingError,
    ErrorCode,
    ExternalServiceError,
    FloatException,
    JobAccessDeniedError,
    JobError,
    JobNotCompletedError,
    JobNotFoundError,
    StorageError,
    TTSError,
    ValidationError,
)


@pytest.mark.unit
class TestErrorCode:
    """Test ErrorCode enum."""

    def test_validation_error_codes_exist(self):
        """Verify validation error codes are defined."""
        assert ErrorCode.INVALID_REQUEST.value == "INVALID_REQUEST"
        assert ErrorCode.MISSING_FIELD.value == "MISSING_FIELD"
        assert ErrorCode.AUDIO_TOO_LARGE.value == "AUDIO_TOO_LARGE"
        assert ErrorCode.TEXT_TOO_LONG.value == "TEXT_TOO_LONG"

    def test_external_service_error_codes_exist(self):
        """Verify external service error codes are defined."""
        assert ErrorCode.TTS_FAILURE.value == "TTS_FAILURE"
        assert ErrorCode.AI_SERVICE_FAILURE.value == "AI_SERVICE_FAILURE"
        assert ErrorCode.STORAGE_FAILURE.value == "STORAGE_FAILURE"

    def test_internal_error_codes_exist(self):
        """Verify internal error codes are defined."""
        assert ErrorCode.FFMPEG_FAILURE.value == "FFMPEG_FAILURE"
        assert ErrorCode.ENCODING_FAILURE.value == "ENCODING_FAILURE"


@pytest.mark.unit
class TestFloatException:
    """Test base FloatException class."""

    def test_create_with_all_fields(self):
        """Test creating exception with all fields."""
        exc = FloatException(
            message="Test error",
            code=ErrorCode.INTERNAL_ERROR,
            retriable=True,
            details="Additional context",
        )

        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.code == ErrorCode.INTERNAL_ERROR
        assert exc.retriable is True
        assert exc.details == "Additional context"

    def test_to_dict(self):
        """Test converting exception to dictionary."""
        exc = FloatException(
            message="Test error",
            code=ErrorCode.INVALID_REQUEST,
            retriable=False,
        )

        result = exc.to_dict()

        assert result == {
            "error": "Test error",
            "code": "INVALID_REQUEST",
            "retriable": False,
        }

    def test_default_retriable_is_false(self):
        """Test default retriable value."""
        exc = FloatException("Error", ErrorCode.INTERNAL_ERROR)
        assert exc.retriable is False


@pytest.mark.unit
class TestValidationError:
    """Test ValidationError class."""

    def test_is_not_retriable(self):
        """Validation errors should not be retriable."""
        exc = ValidationError("Invalid input")
        assert exc.retriable is False

    def test_default_code(self):
        """Test default error code."""
        exc = ValidationError("Invalid input")
        assert exc.code == ErrorCode.INVALID_REQUEST

    def test_custom_code(self):
        """Test custom error code."""
        exc = ValidationError("Audio too large", code=ErrorCode.AUDIO_TOO_LARGE)
        assert exc.code == ErrorCode.AUDIO_TOO_LARGE

    def test_inherits_from_float_exception(self):
        """Verify inheritance hierarchy."""
        exc = ValidationError("Test")
        assert isinstance(exc, FloatException)
        assert isinstance(exc, Exception)


@pytest.mark.unit
class TestExternalServiceError:
    """Test ExternalServiceError class."""

    def test_is_retriable(self):
        """External service errors should be retriable."""
        exc = ExternalServiceError("Service failed", ErrorCode.TTS_FAILURE)
        assert exc.retriable is True

    def test_inherits_from_float_exception(self):
        """Verify inheritance hierarchy."""
        exc = ExternalServiceError("Test", ErrorCode.AI_SERVICE_FAILURE)
        assert isinstance(exc, FloatException)


@pytest.mark.unit
class TestTTSError:
    """Test TTSError class."""

    def test_has_correct_code(self):
        """TTS errors should have TTS_FAILURE code."""
        exc = TTSError("Speech synthesis failed")
        assert exc.code == ErrorCode.TTS_FAILURE

    def test_is_retriable(self):
        """TTS errors should be retriable."""
        exc = TTSError("Speech synthesis failed")
        assert exc.retriable is True

    def test_inherits_from_external_service_error(self):
        """Verify inheritance hierarchy."""
        exc = TTSError("Test")
        assert isinstance(exc, ExternalServiceError)
        assert isinstance(exc, FloatException)


@pytest.mark.unit
class TestAIServiceError:
    """Test AIServiceError class."""

    def test_has_correct_code(self):
        """AI service errors should have AI_SERVICE_FAILURE code."""
        exc = AIServiceError("Generation failed")
        assert exc.code == ErrorCode.AI_SERVICE_FAILURE

    def test_is_retriable(self):
        """AI service errors should be retriable."""
        exc = AIServiceError("Generation failed")
        assert exc.retriable is True


@pytest.mark.unit
class TestCircuitBreakerOpenError:
    """Test CircuitBreakerOpenError class."""

    def test_message_includes_service_name(self):
        """Error message should include service name."""
        exc = CircuitBreakerOpenError("openai_tts")
        assert "openai_tts" in str(exc)
        assert exc.service_name == "openai_tts"

    def test_has_correct_code(self):
        """Circuit breaker errors should have EXTERNAL_SERVICE_UNAVAILABLE code."""
        exc = CircuitBreakerOpenError("test_service")
        assert exc.code == ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE

    def test_is_retriable(self):
        """Circuit breaker errors should be retriable (after timeout)."""
        exc = CircuitBreakerOpenError("test_service")
        assert exc.retriable is True


@pytest.mark.unit
class TestAudioProcessingError:
    """Test AudioProcessingError class."""

    def test_has_correct_code(self):
        """Audio processing errors should have FFMPEG_FAILURE code."""
        exc = AudioProcessingError("FFmpeg failed")
        assert exc.code == ErrorCode.FFMPEG_FAILURE

    def test_is_not_retriable(self):
        """Audio processing errors should not be retriable."""
        exc = AudioProcessingError("FFmpeg failed")
        assert exc.retriable is False


@pytest.mark.unit
class TestJobErrors:
    """Test job-related exception classes."""

    def test_job_not_found_error(self):
        """Test JobNotFoundError."""
        exc = JobNotFoundError("abc-123")
        assert "abc-123" in str(exc)
        assert exc.job_id == "abc-123"
        assert exc.code == ErrorCode.JOB_NOT_FOUND
        assert exc.retriable is False

    def test_job_not_completed_error(self):
        """Test JobNotCompletedError."""
        exc = JobNotCompletedError("abc-123", "processing")
        assert "abc-123" in str(exc)
        assert "processing" in str(exc)
        assert exc.job_id == "abc-123"
        assert exc.current_status == "processing"
        assert exc.code == ErrorCode.JOB_NOT_COMPLETED
        assert exc.retriable is True  # Client can poll and retry

    def test_job_access_denied_error(self):
        """Test JobAccessDeniedError."""
        exc = JobAccessDeniedError("abc-123")
        assert "abc-123" in str(exc)
        assert exc.job_id == "abc-123"
        assert exc.code == ErrorCode.JOB_ACCESS_DENIED
        assert exc.retriable is False

    def test_job_errors_inherit_from_job_error(self):
        """Verify job errors inherit from JobError."""
        assert isinstance(JobNotFoundError("x"), JobError)
        assert isinstance(JobNotCompletedError("x", "y"), JobError)
        assert isinstance(JobAccessDeniedError("x"), JobError)
