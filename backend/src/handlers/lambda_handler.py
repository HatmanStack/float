from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from ..config.constants import HTTP_BAD_REQUEST
from ..config.settings import settings
from ..models.requests import MeditationRequest, SummaryRequest, parse_request_body
from ..models.responses import create_meditation_response, create_summary_response
from ..providers.openai_tts import OpenAITTSProvider
from ..services.ai_service import AIService
from ..services.ffmpeg_audio_service import FFmpegAudioService
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
    pass
    def __init__(self, ai_service: Optional[AIService] = None, validate_config: bool = True):
        self.ai_service = ai_service or self._create_ai_service()
        self.storage_service = S3StorageService()
        self.audio_service = FFmpegAudioService(self.storage_service)
        self.tts_provider = OpenAITTSProvider()
        if validate_config:
            settings.validate()
    @staticmethod
    def _create_ai_service() -> AIService:
        pass
        from ..services.gemini_service import GeminiAIService
        return GeminiAIService()
    def get_tts_provider(self):
        pass
        return self.tts_provider
    def handle_summary_request(self, request: SummaryRequest) -> Dict[str, Any]:
        pass
        print(f"Processing summary request for user: {request.user_id}")
        audio_file = None
        if request.audio and request.audio != "NotAvailable":
            audio_file = decode_audio_base64(request.audio)
        try:
            summary_result = self.ai_service.analyze_sentiment(
                audio_file=audio_file, user_text=request.prompt
            )
            request_id = generate_request_id()
            response = create_summary_response(request_id, request.user_id, summary_result)
            self._store_summary_results(request, response, audio_file is not None)
            return response.to_dict()
        finally:
            if audio_file:
                cleanup_temp_file(audio_file)
    def _ensure_input_data_is_dict(
        self, input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        pass
        return input_data if isinstance(input_data, dict) else {"floats": input_data}
    def _generate_meditation_audio(self, meditation_text: str, timestamp: str) -> tuple[str, str]:
        pass
        voice_path = f"{settings.TEMP_DIR}/voice_{timestamp}.mp3"
        combined_path = f"{settings.TEMP_DIR}/combined_{timestamp}.mp3"
        tts_provider = self.get_tts_provider()
        success = tts_provider.synthesize_speech(meditation_text, voice_path)
        if not success:
            raise Exception("Failed to generate speech audio")
        print("Voice generation completed")
        return voice_path, combined_path
    def handle_meditation_request(self, request: MeditationRequest) -> Dict[str, Any]:
        pass
        print(f"Processing meditation request for user: {request.user_id}")
        input_data = self._ensure_input_data_is_dict(request.input_data)
        meditation_text = self.ai_service.generate_meditation(input_data)
        print(f"Meditation text result: {meditation_text}")
        timestamp = generate_timestamp()
        try:
            voice_path, combined_path = self._generate_meditation_audio(meditation_text, timestamp)
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
            return response.to_dict()
        finally:
            cleanup_temp_file(voice_path)
            cleanup_temp_file(combined_path)
    def _store_summary_results(self, request: SummaryRequest, response, has_audio: bool):
        pass
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
        pass
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
        pass
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
    pass
    global _handler
    if _handler is None:
        _handler = LambdaHandler()
    return _handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    pass
    print(f"[LAMBDA_HANDLER] Function called with event keys: {list(event.keys())}")
    print(f"[LAMBDA_HANDLER] Event: {event}")
    try:
        handler = _get_handler()
        result: Dict[str, Any] = handler.handle_request(event, context)
        print(f"[LAMBDA_HANDLER] Handler returned: {result}")
        return result
    except Exception as e:
        print(f"[LAMBDA_HANDLER] Exception: {e}")
        raise
