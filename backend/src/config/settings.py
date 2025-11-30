import os

from dotenv import load_dotenv

load_dotenv()
class Settings:
    """Centralized configuration management for the application."""

    # AWS Configuration
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "float-cust-data")
    AWS_AUDIO_BUCKET: str = os.getenv("AWS_AUDIO_BUCKET", "audio-er-lambda")

    # AI Services
    GEMINI_API_KEY: str = os.getenv("G_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Audio Processing
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "/opt/bin/ffmpeg")
    TEMP_DIR: str = "/tmp"
    AUDIO_SAMPLE_RATE: int = 44100

    # Safety settings for Gemini
    GEMINI_SAFETY_LEVEL: int = 4

    @classmethod
    def validate(cls, require_keys: bool = True) -> bool:
        """
        Validate that all required environment variables are set.

        Args:
            require_keys: If False, validation is skipped (useful for testing)
        """
        if not require_keys:
            return True

        required_vars = [
            ("GEMINI_API_KEY", cls.GEMINI_API_KEY),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
        ]

        missing = [name for name, value in required_vars if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True
# Global settings instance
settings = Settings()
