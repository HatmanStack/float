from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Pydantic BaseSettings automatically reads from environment variables
    and .env files, with proper type coercion and validation.
    """

    AWS_S3_BUCKET: str = "float-cust-data"
    AWS_AUDIO_BUCKET: str = "audio-er-lambda"
    # Support both GEMINI_API_KEY and legacy G_KEY env var names.
    # AliasChoices with validation_alias is the pydantic-settings v2 way
    # to accept multiple env var names for the same field.
    GEMINI_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "G_KEY"),
    )
    OPENAI_API_KEY: str = ""
    FFMPEG_PATH: str = "/opt/bin/ffmpeg"
    TEMP_DIR: str = "/tmp"
    AUDIO_SAMPLE_RATE: int = 44100
    GEMINI_TTS_MODEL: str = "gemini-2.5-flash-preview-tts"
    GEMINI_LIVE_TTS_MODEL: str = "gemini-2.5-flash-native-audio-preview-12-2025"
    GEMINI_AI_MODEL: str = "gemini-2.5-flash"
    GEMINI_SAFETY_LEVEL: int = 4

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": True,
    }

    def validate_keys(self, require_keys: bool = True) -> bool:
        """Validate that required API keys are present on this instance."""
        if not require_keys:
            return True
        required_vars = [
            ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            ("OPENAI_API_KEY", self.OPENAI_API_KEY),
        ]
        missing = [name for name, value in required_vars if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return True


settings = Settings()
