"""Meditation generation pipelines extracted from :class:`MeditationHandler`.

Phase 4 revision (iteration 2) extracted the two processing pipelines
(``_process_base64`` for legacy base64 responses and ``_process_hls`` for
streaming HLS) and the retry bookkeeping into this module so the
meditation handler class itself can stay under the 400-line phase ceiling.

Each pipeline is a plain module-level function that takes the
:class:`MeditationHandler` as its first argument so attribute access
(``handler.audio_service``, ``handler.hls_service`` etc.) matches the
original method bodies verbatim.
"""

import os
from typing import TYPE_CHECKING, Optional

from ..config.constants import (
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
from ..services.job_service import JobStatus
from ..utils.audio_utils import cleanup_temp_file, encode_audio_to_base64
from ..utils.file_utils import generate_request_id, generate_timestamp
from ..utils.logging_utils import get_logger

if TYPE_CHECKING:
    from .meditation_handler import MeditationHandler

logger = get_logger(__name__)


def process_base64(
    handler: "MeditationHandler", job_id: str, request: MeditationRequestModel
) -> None:
    """Process meditation with base64 output (legacy mode)."""
    voice_path: Optional[str] = None
    combined_path: Optional[str] = None
    try:
        handler.job_service.update_job_status(request.user_id, job_id, JobStatus.PROCESSING)

        input_data = handler._ensure_input_data_is_dict(request.input_data)
        meditation_text = handler.ai_service.generate_meditation(
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

        voice_path, combined_path = handler._generate_meditation_audio(meditation_text, timestamp)
        new_music_list = handler.audio_service.combine_voice_and_music(
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
        handler._store_meditation_results(request, response)

        handler.job_service.update_job_status(
            request.user_id, job_id, JobStatus.COMPLETED, result=response.to_dict()
        )
        logger.info("Job completed successfully", extra={"data": {"job_id": job_id}})

    except Exception as e:
        logger.error(
            "Error processing meditation job",
            extra={"data": {"job_id": job_id}},
            exc_info=True,
        )
        handler.job_service.update_job_status(
            request.user_id, job_id, JobStatus.FAILED, error=str(e)
        )
    finally:
        if voice_path:
            cleanup_temp_file(voice_path)
        if combined_path:
            cleanup_temp_file(combined_path)


def _generate_hls_audio(
    handler: "MeditationHandler",
    request: MeditationRequestModel,
    job_id: str,
    voice_path: str,
    playlist_url: str,
    timestamp: str,
) -> int:
    """Run the TTS + mixing pipeline and return total_segments."""
    if handler.hls_service.tts_cache_exists(request.user_id, job_id):
        job_data = handler.job_service.get_job(request.user_id, job_id)
        generation_attempt = job_data.get("generation_attempt", 1) if job_data else 1
        logger.info(
            "Using cached TTS audio (batch mode)",
            extra={"data": {"job_id": job_id, "attempt": generation_attempt}},
        )
        if not handler.hls_service.download_tts_cache(request.user_id, job_id, voice_path):
            raise ExternalServiceError(
                "Failed to download cached TTS audio",
                ErrorCode.STORAGE_FAILURE,
                details=f"job_id={job_id}",
            )

        handler.job_service.mark_streaming_started(request.user_id, job_id, playlist_url)

        def progress_callback(segments_completed: int, segments_total: Optional[int]) -> None:
            handler.job_service.update_streaming_progress(
                request.user_id,
                job_id,
                segments_completed=segments_completed,
                segments_total=segments_total,
                playlist_url=playlist_url,
            )

        _, total_segments, _ = handler.audio_service.combine_voice_and_music_hls(
            voice_path=voice_path,
            music_list=request.music_list,
            timestamp=timestamp,
            user_id=request.user_id,
            job_id=job_id,
            progress_callback=progress_callback,
        )
        return total_segments

    input_data = handler._ensure_input_data_is_dict(request.input_data)
    meditation_text = handler.ai_service.generate_meditation(
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

    word_count = len(meditation_text.split())
    estimated_tts_duration = (word_count / TTS_WORDS_PER_MINUTE) * 60
    music_duration = estimated_tts_duration + MUSIC_TRAILING_BUFFER_SECONDS

    music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
    handler.audio_service.select_background_music(request.music_list, music_duration, music_path)
    logger.debug(
        "Music selected based on estimated TTS duration",
        extra={"data": {"words": word_count, "est_duration": estimated_tts_duration}},
    )

    tts_provider = handler.get_tts_provider()
    try:
        voice_generator = tts_provider.stream_speech(meditation_text)
    except (TTSError, CircuitBreakerOpenError):
        logger.warning("Primary TTS streaming failed, trying fallback provider")
        voice_generator = handler.fallback_tts_provider.stream_speech(meditation_text)

    streaming_started = False

    def progress_callback(segments_completed: int, segments_total: Optional[int]) -> None:
        nonlocal streaming_started
        if not streaming_started:
            handler.job_service.mark_streaming_started(request.user_id, job_id, playlist_url)
            streaming_started = True
            logger.info(
                "First segment ready, marked as streaming",
                extra={"data": {"job_id": job_id, "playlist_url": playlist_url}},
            )
        handler.job_service.update_streaming_progress(
            request.user_id,
            job_id,
            segments_completed=segments_completed,
            segments_total=segments_total,
            playlist_url=playlist_url,
        )

    total_segments, _ = handler.audio_service.process_stream_to_hls(
        voice_generator=voice_generator,
        music_path=music_path,
        user_id=request.user_id,
        job_id=job_id,
        progress_callback=progress_callback,
        estimated_voice_duration=estimated_tts_duration,
    )

    if os.path.exists(music_path):
        os.remove(music_path)

    return total_segments


def _handle_hls_error(
    handler: "MeditationHandler",
    request: MeditationRequestModel,
    job_id: str,
    error: BaseException,
) -> None:
    """Retry bookkeeping for a failed HLS generation attempt."""
    job_data = handler.job_service.get_job(request.user_id, job_id)
    current_attempt = job_data.get("generation_attempt", 1) if job_data else 1

    if current_attempt >= MAX_GENERATION_ATTEMPTS:
        handler._mark_job_failed(request, job_id, error, MAX_GENERATION_ATTEMPTS)
        return

    try:
        handler.job_service.increment_generation_attempt(request.user_id, job_id)
    except Exception as inc_error:
        logger.error(
            "Failed to increment generation attempt; not retrying",
            extra={"data": {"job_id": job_id, "error": str(inc_error)}},
        )
        handler._mark_job_failed(request, job_id, error, current_attempt)
        return

    logger.info(
        "Retrying HLS generation",
        extra={"data": {"job_id": job_id, "attempt": current_attempt + 1}},
    )
    try:
        handler._trigger_retry(request, job_id)
    except Exception as invoke_error:
        logger.error(
            "Failed to invoke retry; marking failed",
            extra={"data": {"job_id": job_id, "error": str(invoke_error)}},
        )
        handler._mark_job_failed(request, job_id, error, current_attempt + 1)


def process_hls(handler: "MeditationHandler", job_id: str, request: MeditationRequestModel) -> None:
    """Process meditation with HLS streaming output."""
    voice_path: Optional[str] = None
    try:
        handler.job_service.update_job_status(request.user_id, job_id, JobStatus.PROCESSING)

        timestamp = generate_timestamp()
        voice_path = f"{settings.TEMP_DIR}/voice_{timestamp}.mp3"
        playlist_url = handler.hls_service.generate_playlist_url(request.user_id, job_id)

        total_segments = _generate_hls_audio(
            handler, request, job_id, voice_path, playlist_url, timestamp
        )

        handler.job_service.mark_streaming_complete(request.user_id, job_id, total_segments)

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
        _handle_hls_error(handler, request, job_id, e)
    finally:
        if voice_path:
            cleanup_temp_file(voice_path)
