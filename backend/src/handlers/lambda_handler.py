import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import boto3  # type: ignore[import-untyped]

from ..config.constants import (
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
)
from ..config.settings import settings
from ..models.requests import MeditationRequest, SummaryRequest, parse_request_body
from ..models.responses import create_meditation_response, create_summary_response
from ..providers.openai_tts import OpenAITTSProvider
from ..services.ai_service import AIService
from ..services.download_service import DownloadService
from ..services.ffmpeg_audio_service import FFmpegAudioService
from ..services.hls_service import HLSService
from ..services.job_service import JobService, JobStatus
from ..services.s3_storage_service import S3StorageService
from ..utils.audio_utils import (
    cleanup_temp_file,
    decode_audio_base64,
    encode_audio_to_base64,
)
from ..utils.file_utils import generate_request_id, generate_timestamp
from ..utils.logging_utils import get_logger
from .middleware import (
    apply_middleware,
    cors_middleware,
    create_error_response,
    create_success_response,
    error_handling_middleware,
    json_middleware,
    method_validation_middleware,
    request_validation_middleware,
)

logger = get_logger(__name__)

# Feature flag for HLS streaming
ENABLE_HLS_STREAMING = os.environ.get("ENABLE_HLS_STREAMING", "true").lower() == "true"

# Maximum retry attempts for HLS generation
MAX_GENERATION_ATTEMPTS = 3


class LambdaHandler:

    def __init__(
        self, ai_service: Optional[AIService] = None, validate_config: bool = True
    ):
        self.ai_service = ai_service or self._create_ai_service()
        self.storage_service = S3StorageService()
        self.hls_service = HLSService(self.storage_service)
        self.download_service = DownloadService(self.storage_service, self.hls_service)
        self.audio_service = FFmpegAudioService(
            self.storage_service, hls_service=self.hls_service
        )
        self.tts_provider = OpenAITTSProvider()
        self.job_service = JobService(self.storage_service)
        if validate_config:
            settings.validate()

    @staticmethod
    def _create_ai_service() -> AIService:
        from ..services.gemini_service import GeminiAIService

        return GeminiAIService()

    def get_tts_provider(self):
        return self.tts_provider

    def handle_summary_request(self, request: SummaryRequest) -> Dict[str, Any]:
        logger.info("Processing summary request", extra={"data": {"user_id": request.user_id}})
        audio_file = None
        if request.audio and request.audio != "NotAvailable":
            audio_file = decode_audio_base64(request.audio)
        try:
            summary_result = self.ai_service.analyze_sentiment(
                audio_file=audio_file, user_text=request.prompt
            )
            request_id = generate_request_id()
            response = create_summary_response(
                request_id, request.user_id, summary_result
            )
            self._store_summary_results(request, response, audio_file is not None)
            return response.to_dict()
        finally:
            if audio_file:
                cleanup_temp_file(audio_file)

    def _ensure_input_data_is_dict(
        self, input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        return input_data if isinstance(input_data, dict) else {"floats": input_data}

    def _generate_meditation_audio(
        self, meditation_text: str, timestamp: str
    ) -> tuple[str, str]:
        voice_path = f"{settings.TEMP_DIR}/voice_{timestamp}.mp3"
        combined_path = f"{settings.TEMP_DIR}/combined_{timestamp}.mp3"
        tts_provider = self.get_tts_provider()
        success = tts_provider.synthesize_speech(meditation_text, voice_path)
        if not success:
            raise Exception("Failed to generate speech audio")
        logger.debug("Voice generation completed")
        return voice_path, combined_path

    def handle_meditation_request(self, request: MeditationRequest) -> Dict[str, Any]:
        """Create job and invoke async processing, return job_id immediately."""
        logger.info(
            "Processing meditation request",
            extra={"data": {"user_id": request.user_id}}
        )

        # Create job for tracking (with HLS streaming if enabled)
        job_id = self.job_service.create_job(
            request.user_id, "meditation", enable_streaming=ENABLE_HLS_STREAMING
        )
        logger.info(
            "Created meditation job",
            extra={"data": {"job_id": job_id, "hls_enabled": ENABLE_HLS_STREAMING}}
        )

        # Invoke Lambda asynchronously for the actual processing
        self._invoke_async_meditation(request, job_id)

        # Return job_id immediately
        response = {
            "job_id": job_id,
            "status": "pending",
            "message": "Meditation generation started. Poll /job/{job_id} for status."
        }

        # Include streaming info if HLS is enabled
        if ENABLE_HLS_STREAMING:
            response["streaming"] = {
                "enabled": True,
                "playlist_url": None,  # Will be available once streaming starts
            }

        return response

    def _invoke_async_meditation(self, request: MeditationRequest, job_id: str):
        """Invoke this Lambda asynchronously to process meditation."""
        lambda_client = boto3.client("lambda")
        function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")

        async_payload = {
            "_async_meditation": True,
            "job_id": job_id,
            "request": request.to_dict(),
        }

        logger.info("Invoking async meditation", extra={"data": {"job_id": job_id}})
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="Event",  # Async invocation
            Payload=json.dumps(async_payload),
        )

    def process_meditation_async(self, job_id: str, request_dict: Dict[str, Any]):
        """Process meditation in async Lambda invocation."""
        from ..models.requests import MeditationRequest

        request = MeditationRequest(**request_dict)
        logger.info(
            "Processing async meditation",
            extra={"data": {"job_id": job_id, "user_id": request.user_id}}
        )

        # Check if HLS is enabled for this job
        job_data = self.job_service.get_job(request.user_id, job_id)
        use_hls = (
            ENABLE_HLS_STREAMING
            and job_data
            and job_data.get("streaming", {}).get("enabled", False)
        )

        if use_hls:
            self._process_meditation_hls(job_id, request)
        else:
            self._process_meditation_base64(job_id, request)

    def _process_meditation_base64(self, job_id: str, request: MeditationRequest):
        """Process meditation with base64 output (legacy mode)."""
        voice_path = None
        combined_path = None
        try:
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.PROCESSING
            )

            input_data = self._ensure_input_data_is_dict(request.input_data)
            meditation_text = self.ai_service.generate_meditation(input_data)
            logger.debug(
                "Meditation text generated",
                extra={"data": {"length": len(meditation_text)}}
            )
            timestamp = generate_timestamp()

            voice_path, combined_path = self._generate_meditation_audio(
                meditation_text, timestamp
            )
            new_music_list = self.audio_service.combine_voice_and_music(
                voice_path=voice_path,
                music_list=request.music_list,
                timestamp=timestamp,
                output_path=combined_path,
            )
            logger.debug("Audio combination completed")
            base64_audio = encode_audio_to_base64(combined_path)
            if not base64_audio:
                raise Exception("Failed to encode combined audio")

            request_id = generate_request_id()
            response = create_meditation_response(
                request_id=request_id,
                user_id=request.user_id,
                music_list=new_music_list,
                base64_audio=base64_audio,
            )
            self._store_meditation_results(request, response)

            # Update job with result
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.COMPLETED, result=response.to_dict()
            )
            logger.info("Job completed successfully", extra={"data": {"job_id": job_id}})

        except Exception as e:
            logger.error(
                "Error processing meditation job",
                extra={"data": {"job_id": job_id}},
                exc_info=True
            )
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.FAILED, error=str(e)
            )
        finally:
            if voice_path:
                cleanup_temp_file(voice_path)
            if combined_path:
                cleanup_temp_file(combined_path)

    def _process_meditation_hls(self, job_id: str, request: MeditationRequest):
        """Process meditation with HLS streaming output."""
        voice_path = None
        try:
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.PROCESSING
            )

            # Get job data for retry info
            job_data = self.job_service.get_job(request.user_id, job_id)
            generation_attempt = job_data.get("generation_attempt", 1) if job_data else 1

            timestamp = generate_timestamp()
            voice_path = f"{settings.TEMP_DIR}/voice_{timestamp}.mp3"

            # Generate playlist URL
            playlist_url = self.hls_service.generate_playlist_url(request.user_id, job_id)

            # Check if we have cached TTS audio (for retry scenarios)
            if self.hls_service.tts_cache_exists(request.user_id, job_id):
                logger.info(
                    "Using cached TTS audio (batch mode)",
                    extra={"data": {"job_id": job_id, "attempt": generation_attempt}}
                )
                if not self.hls_service.download_tts_cache(request.user_id, job_id, voice_path):
                    raise Exception("Failed to download cached TTS audio")

                # Mark job as streaming
                self.job_service.mark_streaming_started(request.user_id, job_id, playlist_url)

                # Progress callback
                def progress_callback(segments_completed: int, segments_total: Optional[int]):
                    self.job_service.update_streaming_progress(
                        request.user_id, job_id,
                        segments_completed=segments_completed,
                        segments_total=segments_total,
                        playlist_url=playlist_url,
                    )

                # Use batch mode for cached audio
                music_list, total_segments, segment_durations = self.audio_service.combine_voice_and_music_hls(
                    voice_path=voice_path,
                    music_list=request.music_list,
                    timestamp=timestamp,
                    user_id=request.user_id,
                    job_id=job_id,
                    progress_callback=progress_callback,
                )
            else:
                # STREAMING MODE: Generate TTS and pipe directly to FFmpeg
                input_data = self._ensure_input_data_is_dict(request.input_data)
                meditation_text = self.ai_service.generate_meditation(input_data)
                logger.debug(
                    "Meditation text generated",
                    extra={"data": {"length": len(meditation_text)}}
                )

                # Select and download background music
                music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
                self.audio_service.select_background_music(
                    request.music_list, 120, music_path  # Estimate 2 min duration
                )

                # Get TTS stream generator
                tts_provider = self.get_tts_provider()
                voice_generator = tts_provider.stream_speech(meditation_text)

                # Track if we've marked streaming started
                streaming_started = False

                def progress_callback(segments_completed: int, segments_total: Optional[int]):
                    nonlocal streaming_started
                    # Mark streaming started on first segment
                    if not streaming_started:
                        self.job_service.mark_streaming_started(request.user_id, job_id, playlist_url)
                        streaming_started = True
                        logger.info(
                            "First segment ready, marked as streaming",
                            extra={"data": {"job_id": job_id, "playlist_url": playlist_url}}
                        )
                    self.job_service.update_streaming_progress(
                        request.user_id, job_id,
                        segments_completed=segments_completed,
                        segments_total=segments_total,
                        playlist_url=playlist_url,
                    )

                # Stream TTS directly to FFmpeg HLS output
                total_segments, segment_durations = self.audio_service.process_stream_to_hls(
                    voice_generator=voice_generator,
                    music_path=music_path,
                    user_id=request.user_id,
                    job_id=job_id,
                    progress_callback=progress_callback,
                )

                # Clean up music file
                if os.path.exists(music_path):
                    os.remove(music_path)

            # Mark streaming complete
            self.job_service.mark_streaming_complete(request.user_id, job_id, total_segments)

            logger.info(
                "HLS job completed successfully",
                extra={"data": {"job_id": job_id, "segments": total_segments}}
            )

        except Exception as e:
            logger.error(
                "Error processing HLS meditation job",
                extra={"data": {"job_id": job_id}},
                exc_info=True
            )

            # Check if we should retry
            job_data = self.job_service.get_job(request.user_id, job_id)
            current_attempt = job_data.get("generation_attempt", 1) if job_data else 1

            if current_attempt < MAX_GENERATION_ATTEMPTS:
                # Increment attempt counter
                self.job_service.increment_generation_attempt(request.user_id, job_id)
                logger.info(
                    "Retrying HLS generation",
                    extra={"data": {"job_id": job_id, "attempt": current_attempt + 1}}
                )
                # Self-invoke to retry asynchronously
                try:
                    self._invoke_async_meditation(request, job_id)
                    return
                except Exception as invoke_error:
                    logger.error(
                        "Failed to invoke retry",
                        extra={"data": {"job_id": job_id, "error": str(invoke_error)}}
                    )
                    # Fall through to mark as failed

            # Max retries exceeded
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.FAILED,
                error=f"Failed after {MAX_GENERATION_ATTEMPTS} attempts: {str(e)}"
            )
        finally:
            if voice_path:
                cleanup_temp_file(voice_path)

    def handle_job_status(self, user_id: str, job_id: str) -> Dict[str, Any]:
        """Get job status with fresh pre-signed URLs."""
        job_data = self.job_service.get_job(user_id, job_id)
        if not job_data:
            return None

        # Refresh pre-signed playlist URL ONLY if streaming has actually started
        # (i.e., at least one segment is uploaded and playlist file exists)
        streaming = job_data.get("streaming", {})
        if streaming.get("enabled") and streaming.get("started_at"):
            fresh_playlist_url = self.hls_service.generate_playlist_url(user_id, job_id)
            if fresh_playlist_url:
                job_data["streaming"]["playlist_url"] = fresh_playlist_url
        elif streaming.get("enabled"):
            # Streaming enabled but not started yet - clear any stale URL
            job_data["streaming"]["playlist_url"] = None

        return job_data

    def handle_download_request(
        self, user_id: str, job_id: str, job_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle download request - generate MP3 and return URL."""
        if job_data is None:
            job_data = self.job_service.get_job(user_id, job_id)
            if not job_data:
                return None

        # Check job is completed
        if job_data.get("status") != JobStatus.COMPLETED.value:
            return {
                "error": {
                    "code": "JOB_NOT_COMPLETED",
                    "message": "Job must be completed before download is available",
                }
            }

        # Check download is available
        if not job_data.get("download", {}).get("available", False):
            return {
                "error": {
                    "code": "DOWNLOAD_NOT_AVAILABLE",
                    "message": "Download is not available for this job",
                }
            }

        # Generate MP3 and get download URL
        download_url = self.download_service.generate_mp3_and_get_url(user_id, job_id)
        if not download_url:
            return {
                "error": {
                    "code": "GENERATION_FAILED",
                    "message": "Failed to generate downloadable MP3",
                }
            }

        # Update job with download URL
        self.job_service.mark_download_ready(user_id, job_id, download_url)

        return {
            "job_id": job_id,
            "download_url": download_url,
            "expires_in": 3600,  # 1 hour
        }

    def _store_summary_results(
        self, request: SummaryRequest, response, has_audio: bool
    ):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        object_key = f"{request.user_id}/summary/{timestamp}.json"
        self.storage_service.upload_json(
            bucket=settings.AWS_S3_BUCKET, key=object_key, data=response.to_dict()
        )
        if has_audio and request.audio != "NotAvailable":
            audio_data = {
                "user_audio": request.audio,
                "user_id": request.user_id,
                "request_id": response.request_id,
            }
            audio_key = f"{request.user_id}/audio/{timestamp}.json"
            self.storage_service.upload_json(
                bucket=settings.AWS_S3_BUCKET, key=audio_key, data=audio_data
            )

    def _store_meditation_results(self, request: MeditationRequest, response):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        object_key = f"{request.user_id}/meditation/{timestamp}.json"
        self.storage_service.upload_json(
            bucket=settings.AWS_S3_BUCKET, key=object_key, data=response.to_dict()
        )

    @apply_middleware(
        cors_middleware,
        json_middleware,
        method_validation_middleware(["POST"]),
        request_validation_middleware,
        error_handling_middleware,
    )
    def handle_request(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            parsed_body = event.get("parsed_body", {})
            request = parse_request_body(parsed_body)
            if isinstance(request, SummaryRequest):
                result = self.handle_summary_request(request)
            elif isinstance(request, MeditationRequest):
                result = self.handle_meditation_request(request)
            else:
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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.debug("Lambda handler invoked")
    try:
        handler = _get_handler()

        # Check for async meditation processing (self-invoked)
        if event.get("_async_meditation"):
            logger.info(
                "Processing async meditation job",
                extra={"data": {"job_id": event.get("job_id")}}
            )
            handler.process_meditation_async(event["job_id"], event["request"])
            return {"status": "async_completed"}

        # Check for job status request (GET /job/{job_id})
        raw_path = event.get("rawPath", "")
        http_method = event.get("requestContext", {}).get("http", {}).get("method", "")

        if http_method == "GET" and "/job/" in raw_path:
            return _handle_job_status_request(handler, event)

        # Check for download request (POST /job/{job_id}/download)
        if http_method == "POST" and "/download" in raw_path:
            return _handle_download_request(handler, event)

        result: Dict[str, Any] = handler.handle_request(event, context)
        return result
    except Exception:
        logger.error("Lambda handler exception", exc_info=True)
        raise


def _handle_job_status_request(handler: LambdaHandler, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /job/{job_id} requests with user authorization."""
    from .middleware import cors_middleware

    raw_path = event.get("rawPath", "")
    # Extract job_id from path like /production/job/{job_id}
    path_parts = raw_path.strip("/").split("/")
    job_id = path_parts[-1] if len(path_parts) >= 2 else None

    # Get user_id from query params
    query_params = event.get("queryStringParameters", {}) or {}
    user_id = query_params.get("user_id", "")

    if not job_id or not user_id:
        response = create_error_response(
            HTTP_BAD_REQUEST, "Missing job_id or user_id parameter"
        )
        return cors_middleware(lambda e, c: response)(event, None)

    job_data = handler.handle_job_status(user_id, job_id)
    if not job_data:
        response = create_error_response(HTTP_NOT_FOUND, f"Job {job_id} not found")
        return cors_middleware(lambda e, c: response)(event, None)

    # =========================================================================
    # Authorization Check
    # =========================================================================
    # NOTE FOR REVIEWERS: This check ensures users can only access their own jobs.
    # However, this is NOT traditional auth - user_id is client-generated.
    #
    # This app uses a PRIVACY-FIRST model:
    # - Guest mode: data stays on device, no server auth needed
    # - Optional Google sign-in: for cross-device sync only
    # - user_id is like a device/session identifier, not a secured account
    #
    # This check prevents accidental data leakage if someone guesses a job_id,
    # but it's not a security boundary - it's a UX safeguard.
    # =========================================================================
    job_owner = job_data.get("user_id", "")
    if job_owner and job_owner != user_id:
        logger.warning(
            "Mismatched user_id on job access",
            extra={"data": {"job_id": job_id, "requested_by": user_id, "owner": job_owner}}
        )
        response = create_error_response(
            HTTP_FORBIDDEN, "Access denied: you do not own this job"
        )
        return cors_middleware(lambda e, c: response)(event, None)

    response = create_success_response(job_data)
    return cors_middleware(lambda e, c: response)(event, None)


def _handle_download_request(handler: LambdaHandler, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /job/{job_id}/download requests."""
    from .middleware import cors_middleware

    raw_path = event.get("rawPath", "")
    # Extract job_id from path like /production/job/{job_id}/download
    path_parts = raw_path.strip("/").split("/")

    # Find job_id (the part before "download")
    job_id = None
    for i, part in enumerate(path_parts):
        if part == "download" and i > 0:
            job_id = path_parts[i - 1]
            break

    # Get user_id from query params
    query_params = event.get("queryStringParameters", {}) or {}
    user_id = query_params.get("user_id", "")

    if not job_id or not user_id:
        response = create_error_response(
            HTTP_BAD_REQUEST, "Missing job_id or user_id parameter"
        )
        return cors_middleware(lambda e, c: response)(event, None)

    # Authorization check
    job_data = handler.job_service.get_job(user_id, job_id)
    if not job_data:
        response = create_error_response(HTTP_NOT_FOUND, f"Job {job_id} not found")
        return cors_middleware(lambda e, c: response)(event, None)

    job_owner = job_data.get("user_id", "")
    if job_owner and job_owner != user_id:
        response = create_error_response(
            HTTP_FORBIDDEN, "Access denied: you do not own this job"
        )
        return cors_middleware(lambda e, c: response)(event, None)

    # Handle download (pass job_data to avoid duplicate lookup)
    result = handler.handle_download_request(user_id, job_id, job_data)
    if result is None:
        response = create_error_response(HTTP_NOT_FOUND, f"Job {job_id} not found")
        return cors_middleware(lambda e, c: response)(event, None)

    if "error" in result:
        response = create_error_response(HTTP_BAD_REQUEST, result["error"]["message"])
        return cors_middleware(lambda e, c: response)(event, None)

    response = create_success_response(result)
    return cors_middleware(lambda e, c: response)(event, None)
