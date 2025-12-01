import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import boto3  # type: ignore[import-untyped]

from ..config.constants import HTTP_BAD_REQUEST, HTTP_NOT_FOUND
from ..config.settings import settings
from ..models.requests import MeditationRequest, SummaryRequest, parse_request_body
from ..models.responses import create_meditation_response, create_summary_response
from ..providers.openai_tts import OpenAITTSProvider
from ..services.ai_service import AIService
from ..services.ffmpeg_audio_service import FFmpegAudioService
from ..services.job_service import JobService, JobStatus
from ..services.s3_storage_service import S3StorageService
from ..utils.audio_utils import (
    cleanup_temp_file,
    decode_audio_base64,
    encode_audio_to_base64,
)
from ..utils.file_utils import generate_request_id, generate_timestamp
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


class LambdaHandler:

    def __init__(
        self, ai_service: Optional[AIService] = None, validate_config: bool = True
    ):
        self.ai_service = ai_service or self._create_ai_service()
        self.storage_service = S3StorageService()
        self.audio_service = FFmpegAudioService(self.storage_service)
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
        print(f"Processing summary request for user: {request.user_id}")
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
        print("Voice generation completed")
        return voice_path, combined_path

    def handle_meditation_request(self, request: MeditationRequest) -> Dict[str, Any]:
        """Create job and invoke async processing, return job_id immediately."""
        print(f"Processing meditation request for user: {request.user_id}")

        # Create job for tracking
        job_id = self.job_service.create_job(request.user_id, "meditation")
        print(f"Created meditation job: {job_id}")

        # Invoke Lambda asynchronously for the actual processing
        self._invoke_async_meditation(request, job_id)

        # Return job_id immediately
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Meditation generation started. Poll /job/{job_id} for status."
        }

    def _invoke_async_meditation(self, request: MeditationRequest, job_id: str):
        """Invoke this Lambda asynchronously to process meditation."""
        lambda_client = boto3.client("lambda")
        function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")

        async_payload = {
            "_async_meditation": True,
            "job_id": job_id,
            "request": request.to_dict(),
        }

        print(f"Invoking async meditation for job {job_id}")
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="Event",  # Async invocation
            Payload=json.dumps(async_payload),
        )
        print(f"Async invocation triggered for job {job_id}")

    def process_meditation_async(self, job_id: str, request_dict: Dict[str, Any]):
        """Process meditation in async Lambda invocation."""
        from ..models.requests import MeditationRequest

        request = MeditationRequest(**request_dict)
        print(f"Processing async meditation for job {job_id}, user: {request.user_id}")

        voice_path = None
        combined_path = None
        try:
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.PROCESSING
            )

            input_data = self._ensure_input_data_is_dict(request.input_data)
            meditation_text = self.ai_service.generate_meditation(input_data)
            print(f"Meditation text generated, length: {len(meditation_text)}")
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
            print(f"Audio combination completed: {new_music_list}")
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
            print(f"Job {job_id} completed successfully")

        except Exception as e:
            print(f"Error processing meditation job {job_id}: {e}")
            self.job_service.update_job_status(
                request.user_id, job_id, JobStatus.FAILED, error=str(e)
            )
        finally:
            if voice_path:
                cleanup_temp_file(voice_path)
            if combined_path:
                cleanup_temp_file(combined_path)

    def handle_job_status(self, user_id: str, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        job_data = self.job_service.get_job(user_id, job_id)
        if not job_data:
            return None
        return job_data

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
        except Exception as e:
            print(f"Error in handle_request: {e}")
            raise


_handler: Optional[LambdaHandler] = None


def _get_handler() -> LambdaHandler:
    global _handler
    if _handler is None:
        _handler = LambdaHandler()
    return _handler


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    print(f"[LAMBDA_HANDLER] Function called with event keys: {list(event.keys())}")
    try:
        handler = _get_handler()

        # Check for async meditation processing (self-invoked)
        if event.get("_async_meditation"):
            print(f"[LAMBDA_HANDLER] Processing async meditation job: {event.get('job_id')}")
            handler.process_meditation_async(event["job_id"], event["request"])
            return {"status": "async_completed"}

        # Check for job status request (GET /job/{job_id})
        raw_path = event.get("rawPath", "")
        http_method = event.get("requestContext", {}).get("http", {}).get("method", "")

        if http_method == "GET" and "/job/" in raw_path:
            return _handle_job_status_request(handler, event)

        result: Dict[str, Any] = handler.handle_request(event, context)
        print(f"[LAMBDA_HANDLER] Handler returned: {result}")
        return result
    except Exception as e:
        print(f"[LAMBDA_HANDLER] Exception: {e}")
        raise


def _handle_job_status_request(handler: LambdaHandler, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /job/{job_id} requests."""
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

    response = create_success_response(job_data)
    return cors_middleware(lambda e, c: response)(event, None)
