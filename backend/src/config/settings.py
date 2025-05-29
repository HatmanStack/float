import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Centralized configuration management for the application."""
    
    # AWS Configuration
    AWS_S3_BUCKET: str = os.getenv('AWS_S3_BUCKET', 'float-cust-data')
    AWS_AUDIO_BUCKET: str = os.getenv('AWS_AUDIO_BUCKET', 'audio-er-lambda')
    
    # AI Services
    GEMINI_API_KEY: str = os.getenv('G_KEY', '')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str = os.getenv('XI_KEY', '')
    ELEVENLABS_VOICE_ID: str = os.getenv('VOICE_ID', '')
    ELEVENLABS_STABILITY: float = float(os.getenv('STABILITY', '0.5'))
    ELEVENLABS_SIMILARITY_BOOST: float = float(os.getenv('SIMILARITY_BOOST', '0.5'))
    ELEVENLABS_STYLE: float = float(os.getenv('STYLE', '0.0'))
    
    # Audio Processing
    FFMPEG_PATH: str = os.getenv('FFMPEG_PATH', '/opt/bin/ffmpeg')
    TEMP_DIR: str = '/tmp'
    AUDIO_SAMPLE_RATE: int = 44100
    
    # TTS Provider Selection
    DEFAULT_TTS_PROVIDER: str = os.getenv('TTS_PROVIDER', 'openai')  # 'openai', 'google', 'elevenlabs'
    
    # Safety settings for Gemini
    GEMINI_SAFETY_LEVEL: int = 4
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required environment variables are set."""
        required_vars = [
            ('GEMINI_API_KEY', cls.GEMINI_API_KEY),
            ('OPENAI_API_KEY', cls.OPENAI_API_KEY),
        ]
        
        missing = [name for name, value in required_vars if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True

# Global settings instance
settings = Settings()