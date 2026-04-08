"""Thin Lambda handler shim.

Phase 4 Task 1 of the 2026-04-08-audit-float plan split the 750+ line god
object that used to live here into domain-focused modules:

- :mod:`.summary_handler` -- sentiment analysis pathway
- :mod:`.meditation_handler` -- async meditation generation pathway
- :mod:`.job_handler` -- job status and download pathways
- :mod:`.router` -- dispatch table and top-level ``lambda_handler`` entry

This module now does three things:

1. Constructs the :class:`LambdaHandler` facade that wires services to the
   sub-handlers and preserves the public method surface used by existing
   tests and by :mod:`backend.lambda_function`.
2. Re-imports provider and service symbols at module scope so that
   ``unittest.mock.patch('src.handlers.lambda_handler.GeminiTTSProvider')``
   and friends continue to intercept construction in tests.
3. Re-exports the route helpers and the top-level ``lambda_handler`` entry
   point so existing tests that patch
   ``src.handlers.lambda_handler._handle_job_status_request`` etc. still
   reach the dispatch path.
"""

from typing import Any, Dict, List, Optional, Union

import boto3  # type: ignore[import-untyped]

from ..config.constants import (
    ENABLE_HLS_STREAMING,
    GEMINI_LIVE_WS_ENDPOINT,
    MAX_GENERATION_ATTEMPTS,
    MUSIC_TRAILING_BUFFER_SECONDS,
    TOKEN_MARKER_TTL_SECONDS,
    TTS_WORDS_PER_MINUTE,
)
from ..config.settings import settings
from ..models.requests import MeditationRequestModel, SummaryRequestModel, parse_request_body
from ..providers.gemini_tts import GeminiTTSProvider
from ..providers.openai_tts import OpenAITTSProvider
from ..services.ai_service import AIService
from ..services.download_service import DownloadService
from ..services.ffmpeg_audio_service import FFmpegAudioService
from ..services.hls_service import HLSService
from ..services.job_service import JobService
from ..services.s3_storage_service import S3StorageService
from ..utils.logging_utils import get_logger
from .job_handler import JobHandler
from .meditation_handler import MeditationHandler
from .middleware import (
    apply_middleware,
    cors_middleware,
    create_error_response,
    create_success_response,
    error_handling_middleware,
    json_middleware,
    method_validation_middleware,
    request_size_validation_middleware,
)
from .router import (
    _ROUTES,
    _authorize_job_access,
    _handle_download_request,
    _handle_job_status_request,
    _handle_token_request,
    _match_route,
    _validate_user_id_or_400,
    _with_cors,
    lambda_handler,
)
from .summary_handler import SummaryHandler

logger = get_logger(__name__)

# Cached boto3 Lambda client at module scope so it is reused across warm
# invocations. ``boto3.client`` is thread-safe and the connection pool
# benefits from reuse.
_lambda_client: Any = None


def _get_lambda_client() -> Any:
    """Return a cached boto3 Lambda client, creating it on first use."""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda")
    return _lambda_client


class LambdaHandler:
    """Thin facade that constructs services and delegates to domain handlers."""

    def __init__(
        self, ai_service: Optional[AIService] = None, validate_config: bool = True
    ) -> None:
        self.ai_service = ai_service or self._create_ai_service()
        self.storage_service = S3StorageService()
        self.hls_service = HLSService(self.storage_service)
        self.download_service = DownloadService(self.storage_service, self.hls_service)
        self.audio_service = FFmpegAudioService(self.storage_service, hls_service=self.hls_service)
        if validate_config:
            settings.validate_keys()
        self.tts_provider = GeminiTTSProvider()
        self.fallback_tts_provider = OpenAITTSProvider()
        self.job_service = JobService(self.storage_service)

        self.summary = SummaryHandler(self)
        self.meditation = MeditationHandler(self, lambda_client_provider=_get_lambda_client)
        self.jobs = JobHandler(self)

    @staticmethod
    def _create_ai_service() -> AIService:
        from ..services.gemini_service import GeminiAIService

        return GeminiAIService()

    # ------------------------------------------------------------------
    # Legacy public surface. Each method delegates to a domain handler so
    # existing tests and call sites continue to work unchanged.
    # ------------------------------------------------------------------
    def get_tts_provider(self) -> Any:
        return self.meditation.get_tts_provider()

    def handle_summary_request(self, request: SummaryRequestModel) -> Dict[str, Any]:
        return self.summary.handle(request)

    def handle_meditation_request(self, request: MeditationRequestModel) -> Dict[str, Any]:
        return self.meditation.handle(request)

    def process_meditation_async(self, job_id: str, request_dict: Dict[str, Any]) -> None:
        self.meditation.process_async(job_id, request_dict)

    def handle_job_status(self, user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.handle_status(user_id, job_id)

    def handle_download_request(
        self,
        user_id: str,
        job_id: str,
        job_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        return self.jobs.handle_download(user_id, job_id, job_data)

    # Internal helpers kept for back-compat with existing tests that exercise
    # them directly. New code should call the domain handlers instead.
    def _ensure_input_data_is_dict(
        self, input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        return self.meditation._ensure_input_data_is_dict(input_data)

    def _generate_meditation_audio(self, meditation_text: str, timestamp: str) -> tuple[str, str]:
        return self.meditation._generate_meditation_audio(meditation_text, timestamp)

    def _invoke_async_meditation(self, request: MeditationRequestModel, job_id: str) -> None:
        self.meditation._invoke_async_meditation(request, job_id)

    def _process_meditation_base64(self, job_id: str, request: MeditationRequestModel) -> None:
        self.meditation._process_base64(job_id, request)

    def _process_meditation_hls(self, job_id: str, request: MeditationRequestModel) -> None:
        self.meditation._process_hls(job_id, request)

    def _mark_job_failed(
        self,
        request: MeditationRequestModel,
        job_id: str,
        error: BaseException,
        attempts: int,
    ) -> None:
        self.meditation._mark_job_failed(request, job_id, error, attempts)

    def _store_summary_results(
        self, request: SummaryRequestModel, response: Any, has_audio: bool
    ) -> None:
        self.summary._store_summary_results(request, response, has_audio)

    def _store_meditation_results(self, request: MeditationRequestModel, response: Any) -> None:
        self.meditation._store_meditation_results(request, response)

    @apply_middleware(
        cors_middleware,
        json_middleware,
        method_validation_middleware(["POST"]),
        # request_validation_middleware removed in Phase 4 Task 3: Pydantic
        # ``parse_request_body`` now owns ``user_id`` / ``inference_type``
        # presence checks end-to-end, collapsing the dual validation path
        # called out by the audit. The function is retained in
        # :mod:`.middleware` for back-compat with unit tests that exercise
        # it directly; it is no longer wired into the request chain.
        request_size_validation_middleware,
        error_handling_middleware,
    )
    def handle_request(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            parsed_body = event.get("parsed_body", {})
            request = parse_request_body(parsed_body)
            if isinstance(request, SummaryRequestModel):
                result = self.handle_summary_request(request)
            elif isinstance(request, MeditationRequestModel):
                result = self.handle_meditation_request(request)
            else:
                from ..config.constants import HTTP_BAD_REQUEST

                return create_error_response(
                    HTTP_BAD_REQUEST, f"Unsupported request type: {type(request)}"
                )
            return create_success_response(result)
        except Exception:
            logger.error("Error in handle_request", exc_info=True)
            raise


_handler: Optional[LambdaHandler] = None


def _get_handler() -> LambdaHandler:
    global _handler
    if _handler is None:
        _handler = LambdaHandler()
    return _handler


__all__ = [
    "ENABLE_HLS_STREAMING",
    "GEMINI_LIVE_WS_ENDPOINT",
    "GeminiTTSProvider",
    "JobHandler",
    "LambdaHandler",
    "MAX_GENERATION_ATTEMPTS",
    "MUSIC_TRAILING_BUFFER_SECONDS",
    "MeditationHandler",
    "OpenAITTSProvider",
    "S3StorageService",
    "SummaryHandler",
    "TOKEN_MARKER_TTL_SECONDS",
    "TTS_WORDS_PER_MINUTE",
    "_ROUTES",
    "_authorize_job_access",
    "_get_handler",
    "_get_lambda_client",
    "_handle_download_request",
    "_handle_job_status_request",
    "_handle_token_request",
    "_handler",
    "_lambda_client",
    "_match_route",
    "_validate_user_id_or_400",
    "_with_cors",
    "boto3",
    "lambda_handler",
]
