"""Meditation request handler.

Extracted from :mod:`lambda_handler` as part of Phase 4 Task 1 of the
2026-04-08-audit-float plan. Owns the synchronous create-job fan-out,
the async processing entry, the base64 and HLS generation paths, and
the retry-loop bookkeeping.
"""

import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Union

from ..config.constants import ENABLE_HLS_STREAMING
from ..config.settings import settings
from ..exceptions import ErrorCode, ExternalServiceError, TTSError
from ..models.requests import MeditationRequestModel
from ..services.ai_service import AIService
from ..services.ffmpeg_audio_service import FFmpegAudioService
from ..services.hls_service import HLSService
from ..services.job_service import JobService, JobStatus
from ..services.s3_storage_service import S3StorageService
from ..utils.logging_utils import get_logger
from . import meditation_pipeline

logger = get_logger(__name__)


class MeditationHandler:
    """Handle meditation generation requests."""

    def __init__(
        self,
        parent: Any,
        lambda_client_provider: Callable[[], Any],
    ) -> None:
        # ``parent`` is the :class:`LambdaHandler` facade. All service and
        # provider access goes through the parent so that tests which
        # reassign ``handler.tts_provider`` / ``handler.job_service`` after
        # construction transparently affect this handler too.
        self._parent = parent
        self._lambda_client_provider = lambda_client_provider

    @property
    def ai_service(self) -> AIService:
        return self._parent.ai_service

    @property
    def storage_service(self) -> S3StorageService:
        return self._parent.storage_service

    @property
    def hls_service(self) -> HLSService:
        return self._parent.hls_service

    @property
    def audio_service(self) -> FFmpegAudioService:
        return self._parent.audio_service

    @property
    def job_service(self) -> JobService:
        return self._parent.job_service

    @property
    def tts_provider(self) -> Any:
        return self._parent.tts_provider

    @property
    def fallback_tts_provider(self) -> Any:
        return self._parent.fallback_tts_provider

    def get_tts_provider(self) -> Any:
        return self.tts_provider

    def _ensure_input_data_is_dict(
        self, input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        return input_data if isinstance(input_data, dict) else {"floats": input_data}

    def _generate_meditation_audio(self, meditation_text: str, timestamp: str) -> tuple[str, str]:
        voice_path = f"{settings.TEMP_DIR}/voice_{timestamp}.mp3"
        combined_path = f"{settings.TEMP_DIR}/combined_{timestamp}.mp3"
        tts_provider = self.get_tts_provider()
        success = tts_provider.synthesize_speech(meditation_text, voice_path)
        if not success:
            logger.warning("Primary TTS provider failed, trying fallback")
            success = self.fallback_tts_provider.synthesize_speech(meditation_text, voice_path)
            if not success:
                raise TTSError("Failed to generate speech audio with both primary and fallback TTS")
        logger.debug("Voice generation completed")
        return voice_path, combined_path

    def handle(self, request: MeditationRequestModel) -> Dict[str, Any]:
        """Create job and invoke async processing, return job_id immediately."""
        logger.info(
            "Processing meditation request",
            extra={
                "data": {"user_id": request.user_id, "duration_minutes": request.duration_minutes}
            },
        )

        job_id = self.job_service.create_job(
            request.user_id, "meditation", enable_streaming=ENABLE_HLS_STREAMING
        )
        logger.info(
            "Created meditation job",
            extra={"data": {"job_id": job_id, "hls_enabled": ENABLE_HLS_STREAMING}},
        )

        # Route through the parent facade so tests that do
        # ``patch.object(handler, "_invoke_async_meditation")`` see the call.
        self._parent._invoke_async_meditation(request, job_id)

        response: Dict[str, Any] = {
            "job_id": job_id,
            "status": "pending",
            "message": "Meditation generation started. Poll /job/{job_id} for status.",
        }

        if ENABLE_HLS_STREAMING:
            response["streaming"] = {
                "enabled": True,
                "playlist_url": None,
            }

        return response

    def _invoke_async_meditation(self, request: MeditationRequestModel, job_id: str) -> None:
        """Invoke this Lambda asynchronously to process meditation.

        Marks the job as FAILED if the AWS SDK call raises or the response
        StatusCode is not 202 so callers do not see a job stuck in PENDING.
        """
        lambda_client = self._lambda_client_provider()
        function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")

        async_payload = {
            "_async_meditation": True,
            "job_id": job_id,
            "request": request.to_dict(),
        }

        logger.info("Invoking async meditation", extra={"data": {"job_id": job_id}})
        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="Event",
                Payload=json.dumps(async_payload),
            )
        except Exception as exc:
            logger.error(
                "Async Lambda invoke raised; marking job failed",
                extra={"data": {"job_id": job_id, "error": str(exc)}},
                exc_info=True,
            )
            self.job_service.update_job_status(
                request.user_id,
                job_id,
                JobStatus.FAILED,
                error=f"Async invoke failed: {exc}",
            )
            raise ExternalServiceError(
                "Failed to dispatch async meditation",
                ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
                details=f"job_id={job_id}",
            ) from exc

        status_code = response.get("StatusCode") if isinstance(response, dict) else None
        if status_code != 202:
            logger.error(
                "Async Lambda invoke returned non-202",
                extra={"data": {"job_id": job_id, "status_code": status_code}},
            )
            self.job_service.update_job_status(
                request.user_id,
                job_id,
                JobStatus.FAILED,
                error=f"Async invoke returned status {status_code}",
            )
            raise ExternalServiceError(
                "Async meditation dispatch returned non-202",
                ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
                details=f"job_id={job_id}, status={status_code}",
            )

    def process_async(self, job_id: str, request_dict: Dict[str, Any]) -> None:
        """Process meditation in async Lambda invocation."""
        request = MeditationRequestModel.model_validate(request_dict)
        logger.info(
            "Processing async meditation",
            extra={"data": {"job_id": job_id, "user_id": request.user_id}},
        )

        job_data = self.job_service.get_job(request.user_id, job_id)
        use_hls = (
            ENABLE_HLS_STREAMING
            and job_data
            and job_data.get("streaming", {}).get("enabled", False)
        )

        if use_hls:
            self._process_hls(job_id, request)
        else:
            self._process_base64(job_id, request)

    def _process_base64(self, job_id: str, request: MeditationRequestModel) -> None:
        """Process meditation with base64 output (legacy mode)."""
        meditation_pipeline.process_base64(self, job_id, request)

    def _process_hls(self, job_id: str, request: MeditationRequestModel) -> None:
        """Process meditation with HLS streaming output."""
        meditation_pipeline.process_hls(self, job_id, request)

    def _trigger_retry(self, request: MeditationRequestModel, job_id: str) -> None:
        """Re-invoke async meditation processing for a retry attempt.

        Routed through the parent facade so tests that
        ``patch.object(handler, "_invoke_async_meditation")`` see the call.
        Centralizing the indirection here keeps :mod:`meditation_pipeline`
        from reaching into ``handler._parent`` directly.
        """
        self._parent._invoke_async_meditation(request, job_id)

    def _mark_job_failed(
        self,
        request: MeditationRequestModel,
        job_id: str,
        error: BaseException,
        attempts: int,
    ) -> None:
        """Mark an HLS meditation job as failed."""
        self.job_service.update_job_status(
            request.user_id,
            job_id,
            JobStatus.FAILED,
            error=f"Failed after {attempts} attempts: {str(error)}",
        )

    def _store_meditation_results(self, request: MeditationRequestModel, response: Any) -> None:
        # Microsecond UTC + random suffix prevents key collisions for
        # concurrent meditations from the same user.
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        suffix = secrets.token_hex(4)
        object_key = f"{request.user_id}/meditation/{timestamp}-{suffix}.json"
        self.storage_service.upload_json(
            bucket=settings.AWS_S3_BUCKET, key=object_key, data=response.to_dict()
        )
