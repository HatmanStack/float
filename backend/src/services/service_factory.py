"""Service factory for dependency injection and service management."""

from typing import Dict, Optional

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
    """Factory class for creating and managing service instances."""

    def __init__(self) -> None:
        self._ai_service: Optional[AIService] = None
        self._storage_service: Optional[StorageService] = None
        self._audio_service: Optional[AudioService] = None
        self._tts_providers: Dict[str, TTSService] = {}

    def get_ai_service(self) -> AIService:
        """Get AI service instance (singleton)."""
        if self._ai_service is None:
            self._ai_service = GeminiAIService()
        return self._ai_service

    def get_storage_service(self) -> StorageService:
        """Get storage service instance (singleton)."""
        if self._storage_service is None:
            self._storage_service = S3StorageService()
        return self._storage_service

    def get_audio_service(self) -> AudioService:
        """Get audio service instance (singleton)."""
        if self._audio_service is None:
            storage_service = self.get_storage_service()
            self._audio_service = FFmpegAudioService(storage_service)
        return self._audio_service

    def get_tts_provider(self) -> TTSService:
        """
        Get TTS provider instance (OpenAI only).

        Returns:
            OpenAI TTS service instance
        """
        if "openai" not in self._tts_providers:
            self._tts_providers["openai"] = OpenAITTSProvider()

        return self._tts_providers["openai"]

    def validate_services(self) -> bool:
        """Validate that all services can be created successfully."""
        try:
            # Test service creation
            self.get_ai_service()
            self.get_storage_service()
            self.get_audio_service()
            self.get_tts_provider()

            # Validate configuration
            settings.validate()

            print("All services validated successfully")
            return True

        except Exception as e:
            print(f"Service validation failed: {e}")
            return False


# Global service factory instance
service_factory = ServiceFactory()
