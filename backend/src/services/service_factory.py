"""Service factory for dependency injection and service management."""

from typing import Dict, Any
from .ai_service import AIService
from .tts_service import TTSService
from .storage_service import StorageService
from .audio_service import AudioService
from .gemini_service import GeminiAIService
from .s3_storage_service import S3StorageService
from .ffmpeg_audio_service import FFmpegAudioService
from ..providers.openai_tts import OpenAITTSProvider
from ..providers.google_tts import GoogleTTSProvider
from ..providers.eleven_labs_tts import ElevenLabsTTSProvider
from ..config.constants import TTSProvider
from ..config.settings import settings

class ServiceFactory:
    """Factory class for creating and managing service instances."""
    
    def __init__(self):
        self._ai_service = None
        self._storage_service = None
        self._audio_service = None
        self._tts_providers = {}
    
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
    
    def get_tts_provider(self, provider_type: str = None) -> TTSService:
        """
        Get TTS provider instance.
        
        Args:
            provider_type: Type of TTS provider ('openai', 'google', 'elevenlabs')
                          If None, uses default from settings
        
        Returns:
            TTS service instance
        """
        if provider_type is None:
            provider_type = settings.DEFAULT_TTS_PROVIDER
        
        if provider_type not in self._tts_providers:
            if provider_type == TTSProvider.OPENAI.value:
                self._tts_providers[provider_type] = OpenAITTSProvider()
            elif provider_type == TTSProvider.GOOGLE.value:
                self._tts_providers[provider_type] = GoogleTTSProvider()
            elif provider_type == TTSProvider.ELEVENLABS.value:
                self._tts_providers[provider_type] = ElevenLabsTTSProvider()
            else:
                raise ValueError(f"Unknown TTS provider: {provider_type}")
        
        return self._tts_providers[provider_type]
    
    def get_all_tts_providers(self) -> Dict[str, TTSService]:
        """Get all available TTS providers."""
        providers = {}
        for provider_type in [TTSProvider.OPENAI, TTSProvider.GOOGLE, TTSProvider.ELEVENLABS]:
            providers[provider_type.value] = self.get_tts_provider(provider_type.value)
        return providers
    
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