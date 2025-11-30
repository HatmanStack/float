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
    """Main Lambda request handler with dependency injection."""

    def __init__(self, ai_service: Optional[AIService] = None, validate_config: bool = True):
        # Initialize services (allow dependency injection for testing)
        self.ai_service = ai_service or self._create_ai_service()
        self.storage_service = S3StorageService()
        self.audio_service = FFmpegAudioService(self.storage_service)

        # Initialize TTS provider (only OpenAI supported)
        self.tts_provider = OpenAITTSProvider()

        # Validate configuration (skip in tests)
        if validate_config:
            settings.validate()

    @staticmethod
    def _create_ai_service() -> AIService:
        """Factory method to create AI service."""
        # Import here to avoid circular dependencies
        from ..services.gemini_service import GeminiAIService

        return GeminiAIService()

    def get_tts_provider(self):
        """Get TTS provider (OpenAI only)."""
        return self.tts_provider

    def handle_summary_request(self, request: SummaryRequest) -> Dict[str, Any]:
        """Handle sentiment analysis/summary request."""
# Prepare audio file if provided
        audio_file = None
        if request.audio and request.audio != "NotAvailable":
            audio_file = decode_audio_base64(request.audio)

        try:
            # Get sentiment analysis from AI service
            summary_result = self.ai_service.analyze_sentiment(
                audio_file=audio_file, user_text=request.prompt
            )

            # Generate request ID and create response
            request_id = generate_request_id()
            response = create_summary_response(request_id, request.user_id, summary_result)

            # Store results in S3
            self._store_summary_results(request, response, audio_file is not None)

            return response.to_dict()

        finally:
            # Clean up temporary audio file
            if audio_file:
                cleanup_temp_file(audio_file)

    def _ensure_input_data_is_dict(
        self, input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Ensure input_data is a dictionary, converting list to dict if needed.

        Args:
            input_data: Either a dict or list of dicts

        Returns:
            Dictionary representation of input_data
        """
        return input_data if isinstance(input_data, dict) else {"floats": input_data}

    def _generate_meditation_audio(self, meditation_text: str, timestamp: str) -> tuple[str, str]:
        """Generate meditation audio and combine with background music.

        Args:
            meditation_text: The meditation transcript text
            timestamp: Timestamp for file naming

        Returns:
            Tuple of (voice_path, combined_path)

        Raises:
            Exception: If audio generation or synthesis fails
        """
        voice_path = f"{settings.TEMP_DIR}/voice_{timestamp}.mp3"
        combined_path = f"{settings.TEMP_DIR}/combined_{timestamp}.mp3"

        # Convert text to speech
        tts_provider = self.get_tts_provider()
        success = tts_provider.synthesize_speech(meditation_text, voice_path)

        if not success:
            raise Exception("Failed to generate speech audio")
return voice_path, combined_path

    def handle_meditation_request(self, request: MeditationRequest) -> Dict[str, Any]:
        """Handle meditation generation request.

        Generates a personalized meditation from user input, synthesizes speech,
        combines with background music, and returns encoded audio.

        Args:
            request: MeditationRequest with user data and music selections

        Returns:
            Dictionary containing meditation response data
        """
# Ensure input_data is a dict (convert list to dict if needed)
        input_data = self._ensure_input_data_is_dict(request.input_data)

        # Generate meditation transcript
        meditation_text = self.ai_service.generate_meditation(input_data)
# Generate timestamp for file naming
        timestamp = generate_timestamp()

        try:
            # Generate voice and get file paths
            voice_path, combined_path = self._generate_meditation_audio(meditation_text, timestamp)

            # Combine voice with background music
            new_music_list = self.audio_service.combine_voice_and_music(
                voice_path=voice_path,
                music_list=request.music_list,
                timestamp=timestamp,
                output_path=combined_path,
            )
# Encode combined audio to base64
            base64_audio = encode_audio_to_base64(combined_path)
            if not base64_audio:
                raise Exception("Failed to encode combined audio")

            # Generate response
            request_id = generate_request_id()
            response = create_meditation_response(
                request_id=request_id,
                user_id=request.user_id,
                music_list=new_music_list,
                base64_audio=base64_audio,
            )

            # Store results in S3
            self._store_meditation_results(request, response)

            return response.to_dict()

        finally:
            # Clean up temporary files
            cleanup_temp_file(voice_path)
            cleanup_temp_file(combined_path)

    def _store_summary_results(self, request: SummaryRequest, response, has_audio: bool):
        """Store summary results and audio data in S3."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # Store main results
        object_key = f"{request.user_id}/summary/{timestamp}.json"
        self.storage_service.upload_json(
            bucket=settings.AWS_S3_BUCKET, key=object_key, data=response.to_dict()
        )

        # Store audio data separately if provided
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
        """Store meditation results in S3."""
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
        """Main request handler with middleware applied."""
        try:
            # Parse request
            parsed_body = event.get("parsed_body", {})
            request = parse_request_body(parsed_body)

            # Route to appropriate handler
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
raise
# Global handler instance (lazy initialization)
_handler: Optional[LambdaHandler] = None
def _get_handler() -> LambdaHandler:
    """Get or create global handler instance (lazy initialization)."""
    global _handler
    if _handler is None:
        _handler = LambdaHandler()
    return _handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda entry point."""
)}")
try:
        handler = _get_handler()
        result: Dict[str, Any] = handler.handle_request(event, context)
return result
    except Exception as e:
raise
