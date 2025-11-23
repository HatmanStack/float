from typing import Optional

from ..config.settings import settings
from ..providers.openai_tts import OpenAITTSProvider
from .ai_service import AIService
from .audio_service import AudioService
from .ffmpeg_audio_service import FFmpegAudioService
from .gemini_service import GeminiAIService
from .s3_storage_service import S3StorageService
from .storage_service import StorageService
from .tts_service import TTSService


class ServiceFactory:
    pass
    def __init__(self) -> None:
        self._ai_service: Optional[AIService] = None
        self._storage_service: Optional[StorageService] = None
        self._audio_service: Optional[AudioService] = None
        self._tts_service: Optional[TTSService] = None
    def get_ai_service(self) -> AIService:
        pass
        if self._ai_service is None:
            self._ai_service = GeminiAIService()
        return self._ai_service
    def get_storage_service(self) -> StorageService:
        pass
        if self._storage_service is None:
            self._storage_service = S3StorageService()
        return self._storage_service
    def get_audio_service(self) -> AudioService:
        pass
        if self._audio_service is None:
            storage_service = self.get_storage_service()
            self._audio_service = FFmpegAudioService(storage_service)
        return self._audio_service
    def get_tts_provider(self) -> TTSService:
        pass
        if self._tts_service is None:
            self._tts_service = OpenAITTSProvider()
        return self._tts_service
    def validate_services(self) -> bool:
        pass
        try:
            self.get_ai_service()
            self.get_storage_service()
            self.get_audio_service()
            self.get_tts_provider()
            settings.validate()
            print("All services validated successfully")
            return True
        except Exception as e:
            print(f"Service validation failed: {e}")
            return False
service_factory = ServiceFactory()
