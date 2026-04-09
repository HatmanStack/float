"""Thin Lambda handler shim.

Construction of services and the singleton facade lives here so that
``unittest.mock.patch('src.handlers.lambda_handler.GeminiTTSProvider')`` and
the other symbol-level patches in the test suite continue to intercept the
concrete classes at construction time. The legacy delegation methods and
the ``handle_request`` entry point are inherited from
:class:`LambdaHandlerFacade` in :mod:`handler_facade`.
"""

from typing import Any, Optional

import boto3  # type: ignore[import-untyped]

from ..config.constants import ENABLE_HLS_STREAMING  # noqa: F401 -- test imports
from ..config.settings import settings
from ..providers.gemini_tts import GeminiTTSProvider
from ..providers.openai_tts import OpenAITTSProvider
from ..services.ai_service import AIService
from ..services.download_service import DownloadService
from ..services.ffmpeg_audio_service import FFmpegAudioService
from ..services.hls_service import HLSService
from ..services.job_service import JobService
from ..services.s3_storage_service import S3StorageService
from ..utils.logging_utils import get_logger
from .handler_facade import LambdaHandlerFacade
from .job_handler import JobHandler
from .meditation_handler import MeditationHandler
from .router import (  # noqa: F401 -- re-exports for test patching
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

_lambda_client: Any = None


def _get_lambda_client() -> Any:
    """Return a cached boto3 Lambda client, creating it on first use."""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda")
    return _lambda_client


class LambdaHandler(LambdaHandlerFacade):
    """Facade that constructs services and delegates to domain handlers."""

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


_handler: Optional[LambdaHandler] = None


def _get_handler() -> LambdaHandler:
    global _handler
    if _handler is None:
        _handler = LambdaHandler()
    return _handler
