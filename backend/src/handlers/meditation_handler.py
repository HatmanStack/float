"""Meditation request handler.

Extracted from :mod:`lambda_handler` as part of Phase 4 Task 1 of the
2026-04-08-audit-float plan. Owns the synchronous create-job fan-out,
the async processing entry, the base64 and HLS generation paths, and
the retry-loop bookkeeping.
"""

import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from ..config.constants import (
    ENABLE_HLS_STREAMING,
    MAX_GENERATION_ATTEMPTS,
    MUSIC_TRAILING_BUFFER_SECONDS,
    TTS_WORDS_PER_MINUTE,
)
from ..config.settings import settings
from ..exceptions import (
    AudioProcessingError,
    CircuitBreakerOpenError,
    ErrorCode,
    ExternalServiceError,
    TTSError,
)
from ..models.requests import MeditationRequestModel
from ..models.responses import create_meditation_response
from ..services.ai_service import AIService
from ..services.ffmpeg_audio_service import FFmpegAudioService
from ..services.hls_service import HLSService
from ..services.job_service import JobService, JobStatus
from ..services.s3_storage_service import S3StorageService
from ..utils.audio_utils import (
    cleanup_temp_file,
    encode_audio_to_base64,
)
from ..utils.file_utils import generate_request_id, generate_timestamp
from ..utils.logging_utils import get_logger

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
        """Invoke this Lambda asynchronously to process meditation."""
        lambda_client = self._lambda_client_provider()
        function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")

        async_payload = {
            "_async_meditation": True,
            "job_id": job_id,
            "request": request.to_dict(),
        }

        logger.info("Invoking async meditation", extra={"data": {"job_id": job_id}})
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="Event",
            Payload=json.dumps(async_payload),
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
        voice_path = None
        combined_path = None
        try:
            self.job_service.update_job_status(request.user_id, job_id, JobStatus.PROCESSING)

            input_data = self._ensure_input_data_is_dict(request.input_data)
            meditation_text = self.ai_service.generate_meditation(
                input_data,
                duration_minutes=request.duration_minutes,
                qa_transcript=[item.model_dump() for item in request.qa_transcript]
                if request.qa_transcript
                else None,
            )
            logger.info(
                "Meditation text generated",
                extra={
                    "data": {
                        "length": len(meditation_text),
                        "duration_minutes": request.duration_minutes,
                    }
                },
            )
            timestamp = generate_timestamp()

            voice_path, combined_path = self._generate_meditation_audio(meditation_text, timestamp)
            new_music_list = self.audio_service.combine_voice_and_music(
                voice_path=voice_path,
                music_list=request.music_list,
                timestamp=timestamp,
                output_path=combined_path,
            )
            logger.debug("Audio combination completed")
            base64_audio = encode_audio_to_base64(combined_path)
            if not base64_audio:
                raise AudioProcessingError(
                    "Failed to encode combined audio",
                    details=f"job_id={job_id}",
                )

            request_id = generate_request_id()
            response = create_meditation_response(
                request_id=request_id,
                user_id=request.user_id,
                music_list=new_music_list,
                base64_audio=base64_audio,
            )
            self._store_meditation_results(request, response)

            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.COMPLETED, result=response.to_dict()
            )
            logger.info("Job completed successfully", extra={"data": {"job_id": job_id}})

        except Exception as e:
            logger.error(
                "Error processing meditation job",
                extra={"data": {"job_id": job_id}},
                exc_info=True,
            )
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.FAILED, error=str(e)
            )
        finally:
            if voice_path:
                cleanup_temp_file(voice_path)
            if combined_path:
                cleanup_temp_file(combined_path)

    def _process_hls(self, job_id: str, request: MeditationRequestModel) -> None:
        """Process meditation with HLS streaming output."""
        voice_path = None
        try:
            self.job_service.update_job_status(request.user_id, job_id, JobStatus.PROCESSING)

            job_data = self.job_service.get_job(request.user_id, job_id)
            generation_attempt = job_data.get("generation_attempt", 1) if job_data else 1

            timestamp = generate_timestamp()
            voice_path = f"{settings.TEMP_DIR}/voice_{timestamp}.mp3"

            playlist_url = self.hls_service.generate_playlist_url(request.user_id, job_id)

            if self.hls_service.tts_cache_exists(request.user_id, job_id):
                logger.info(
                    "Using cached TTS audio (batch mode)",
                    extra={"data": {"job_id": job_id, "attempt": generation_attempt}},
                )
                if not self.hls_service.download_tts_cache(request.user_id, job_id, voice_path):
                    raise ExternalServiceError(
                        "Failed to download cached TTS audio",
                        ErrorCode.STORAGE_FAILURE,
                        details=f"job_id={job_id}",
                    )

                self.job_service.mark_streaming_started(request.user_id, job_id, playlist_url)

                def progress_callback(
                    segments_completed: int, segments_total: Optional[int]
                ) -> None:
                    self.job_service.update_streaming_progress(
                        request.user_id,
                        job_id,
                        segments_completed=segments_completed,
                        segments_total=segments_total,
                        playlist_url=playlist_url,
                    )

                _, total_segments, _ = self.audio_service.combine_voice_and_music_hls(
                    voice_path=voice_path,
                    music_list=request.music_list,
                    timestamp=timestamp,
                    user_id=request.user_id,
                    job_id=job_id,
                    progress_callback=progress_callback,
                )
            else:
                input_data = self._ensure_input_data_is_dict(request.input_data)
                meditation_text = self.ai_service.generate_meditation(
                    input_data,
                    duration_minutes=request.duration_minutes,
                    qa_transcript=[item.model_dump() for item in request.qa_transcript]
                    if request.qa_transcript
                    else None,
                )
                logger.info(
                    "Meditation text generated",
                    extra={
                        "data": {
                            "length": len(meditation_text),
                            "duration_minutes": request.duration_minutes,
                            "preview": meditation_text[:200],
                            "ending": meditation_text[-200:]
                            if len(meditation_text) > 200
                            else meditation_text,
                        }
                    },
                )

                word_count = len(meditation_text.split())
                estimated_tts_duration = (word_count / TTS_WORDS_PER_MINUTE) * 60
                music_duration = estimated_tts_duration + MUSIC_TRAILING_BUFFER_SECONDS

                music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
                self.audio_service.select_background_music(
                    request.music_list, music_duration, music_path
                )
                logger.debug(
                    "Music selected based on estimated TTS duration",
                    extra={"data": {"words": word_count, "est_duration": estimated_tts_duration}},
                )

                tts_provider = self.get_tts_provider()
                try:
                    voice_generator = tts_provider.stream_speech(meditation_text)
                except (TTSError, CircuitBreakerOpenError):
                    logger.warning("Primary TTS streaming failed, trying fallback provider")
                    voice_generator = self.fallback_tts_provider.stream_speech(meditation_text)

                streaming_started = False

                def progress_callback(
                    segments_completed: int, segments_total: Optional[int]
                ) -> None:
                    nonlocal streaming_started
                    if not streaming_started:
                        self.job_service.mark_streaming_started(
                            request.user_id, job_id, playlist_url
                        )
                        streaming_started = True
                        logger.info(
                            "First segment ready, marked as streaming",
                            extra={"data": {"job_id": job_id, "playlist_url": playlist_url}},
                        )
                    self.job_service.update_streaming_progress(
                        request.user_id,
                        job_id,
                        segments_completed=segments_completed,
                        segments_total=segments_total,
                        playlist_url=playlist_url,
                    )

                total_segments, segment_durations = self.audio_service.process_stream_to_hls(
                    voice_generator=voice_generator,
                    music_path=music_path,
                    user_id=request.user_id,
                    job_id=job_id,
                    progress_callback=progress_callback,
                    estimated_voice_duration=estimated_tts_duration,
                )

                if os.path.exists(music_path):
                    os.remove(music_path)

            self.job_service.mark_streaming_complete(request.user_id, job_id, total_segments)

            logger.info(
                "HLS job completed successfully",
                extra={"data": {"job_id": job_id, "segments": total_segments}},
            )

        except Exception as e:
            logger.error(
                "Error processing HLS meditation job",
                extra={"data": {"job_id": job_id}},
                exc_info=True,
            )

            job_data = self.job_service.get_job(request.user_id, job_id)
            current_attempt = job_data.get("generation_attempt", 1) if job_data else 1

            if current_attempt >= MAX_GENERATION_ATTEMPTS:
                self._mark_job_failed(request, job_id, e, MAX_GENERATION_ATTEMPTS)
                return

            try:
                self.job_service.increment_generation_attempt(request.user_id, job_id)
            except Exception as inc_error:
                logger.error(
                    "Failed to increment generation attempt; not retrying",
                    extra={"data": {"job_id": job_id, "error": str(inc_error)}},
                )
                self._mark_job_failed(request, job_id, e, current_attempt)
                return

            logger.info(
                "Retrying HLS generation",
                extra={"data": {"job_id": job_id, "attempt": current_attempt + 1}},
            )
            try:
                # Call through the parent facade so tests that do
                # ``patch.object(handler, "_invoke_async_meditation")`` still
                # observe the retry invocation.
                self._parent._invoke_async_meditation(request, job_id)
            except Exception as invoke_error:
                logger.error(
                    "Failed to invoke retry; marking failed",
                    extra={"data": {"job_id": job_id, "error": str(invoke_error)}},
                )
                self._mark_job_failed(request, job_id, e, current_attempt + 1)
        finally:
            if voice_path:
                cleanup_temp_file(voice_path)

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
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        object_key = f"{request.user_id}/meditation/{timestamp}.json"
        self.storage_service.upload_json(
            bucket=settings.AWS_S3_BUCKET, key=object_key, data=response.to_dict()
        )
