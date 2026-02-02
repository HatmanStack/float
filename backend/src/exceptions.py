"""Domain-specific exception hierarchy for Float backend.

This module provides a structured exception hierarchy that enables:
- Type-safe error handling with discriminated error codes
- Automatic retry decisions via the `retriable` flag
- Consistent error responses across all API endpoints
- Structured logging with error context
"""

from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    """Standardized error codes for categorization and client handling."""

    # Validation errors (4xx - client should fix request)
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_INFERENCE_TYPE = "INVALID_INFERENCE_TYPE"
    AUDIO_TOO_LARGE = "AUDIO_TOO_LARGE"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    MUSIC_LIST_TOO_LARGE = "MUSIC_LIST_TOO_LARGE"
    INVALID_DURATION = "INVALID_DURATION"

    # External service errors (5xx but retriable)
    TTS_FAILURE = "TTS_FAILURE"
    AI_SERVICE_FAILURE = "AI_SERVICE_FAILURE"
    STORAGE_FAILURE = "STORAGE_FAILURE"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"

    # Internal errors (5xx - not retriable without code fix)
    FFMPEG_FAILURE = "FFMPEG_FAILURE"
    ENCODING_FAILURE = "ENCODING_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Job errors
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_NOT_COMPLETED = "JOB_NOT_COMPLETED"
    JOB_ACCESS_DENIED = "JOB_ACCESS_DENIED"


class FloatException(Exception):
    """Base exception for all Float domain errors.

    Attributes:
        message: Human-readable error description
        code: Machine-readable error code for client handling
        retriable: Whether the client should retry the request
        details: Additional context for debugging (not exposed to client)
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        retriable: bool = False,
        details: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retriable = retriable
        self.details = details

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": self.message,
            "code": self.code.value,
            "retriable": self.retriable,
        }


class ValidationError(FloatException):
    """Raised for request validation failures (4xx errors).

    These errors indicate the client sent an invalid request and should
    fix it before retrying.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_REQUEST,
        details: Optional[str] = None,
    ):
        super().__init__(message, code, retriable=False, details=details)


class ExternalServiceError(FloatException):
    """Raised when external APIs fail (5xx errors, retriable).

    These errors indicate a temporary failure in an external service
    (OpenAI TTS, Gemini AI, S3) that may succeed on retry.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        details: Optional[str] = None,
    ):
        super().__init__(message, code, retriable=True, details=details)


class TTSError(ExternalServiceError):
    """Raised when text-to-speech synthesis fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, ErrorCode.TTS_FAILURE, details=details)


class AIServiceError(ExternalServiceError):
    """Raised when AI service (Gemini) fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, ErrorCode.AI_SERVICE_FAILURE, details=details)


class StorageError(ExternalServiceError):
    """Raised when storage operations (S3) fail."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, ErrorCode.STORAGE_FAILURE, details=details)


class CircuitBreakerOpenError(ExternalServiceError):
    """Raised when circuit breaker is open and rejecting requests."""

    def __init__(self, service_name: str, details: Optional[str] = None):
        super().__init__(
            f"Service {service_name} is temporarily unavailable",
            ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
            details=details,
        )
        self.service_name = service_name


class AudioProcessingError(FloatException):
    """Raised when FFmpeg or audio encoding fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message, ErrorCode.FFMPEG_FAILURE, retriable=False, details=details
        )


class EncodingError(FloatException):
    """Raised when audio encoding/decoding fails."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message, ErrorCode.ENCODING_FAILURE, retriable=False, details=details
        )


class JobError(FloatException):
    """Base class for job-related errors."""

    pass


class JobNotFoundError(JobError):
    """Raised when a job cannot be found."""

    def __init__(self, job_id: str, details: Optional[str] = None):
        super().__init__(
            f"Job {job_id} not found",
            ErrorCode.JOB_NOT_FOUND,
            retriable=False,
            details=details,
        )
        self.job_id = job_id


class JobNotCompletedError(JobError):
    """Raised when an operation requires a completed job."""

    def __init__(self, job_id: str, current_status: str, details: Optional[str] = None):
        super().__init__(
            f"Job {job_id} is not completed (status: {current_status})",
            ErrorCode.JOB_NOT_COMPLETED,
            retriable=True,  # Client can poll and retry
            details=details,
        )
        self.job_id = job_id
        self.current_status = current_status


class JobAccessDeniedError(JobError):
    """Raised when user attempts to access another user's job."""

    def __init__(self, job_id: str, details: Optional[str] = None):
        super().__init__(
            f"Access denied: you do not own job {job_id}",
            ErrorCode.JOB_ACCESS_DENIED,
            retriable=False,
            details=details,
        )
        self.job_id = job_id
