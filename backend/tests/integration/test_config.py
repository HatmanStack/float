"""Configuration and utilities for integration tests."""

import os
import uuid
from typing import Optional


class IntegrationTestConfig:
    """Configuration for integration tests with external services."""

    # API Keys for integration testing
    GEMINI_API_KEY: Optional[str] = os.getenv("G_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # AWS Configuration for testing
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_TEST_BUCKET", os.getenv("AWS_S3_BUCKET", "float-cust-data"))
    AWS_AUDIO_BUCKET: str = os.getenv("AWS_AUDIO_TEST_BUCKET", os.getenv("AWS_AUDIO_BUCKET", "audio-er-lambda"))
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # Test data prefix in S3 (to isolate test data)
    TEST_DATA_PREFIX: str = "test-data/"

    # Timeouts for integration tests (in seconds)
    GEMINI_TIMEOUT: int = 30
    TTS_TIMEOUT: int = 30
    S3_TIMEOUT: int = 10
    E2E_TIMEOUT: int = 120

    # Test execution control
    SKIP_INTEGRATION_TESTS: bool = os.getenv("SKIP_INTEGRATION_TESTS", "false").lower() == "true"
    SKIP_E2E_TESTS: bool = os.getenv("SKIP_E2E_TESTS", "false").lower() == "true"

    @classmethod
    def has_gemini_key(cls) -> bool:
        """Check if Gemini API key is available."""
        return bool(cls.GEMINI_API_KEY)

    @classmethod
    def has_openai_key(cls) -> bool:
        """Check if OpenAI API key is available."""
        return bool(cls.OPENAI_API_KEY)

    @classmethod
    def has_aws_credentials(cls) -> bool:
        """Check if AWS credentials are available."""
        return bool(cls.AWS_ACCESS_KEY_ID and cls.AWS_SECRET_ACCESS_KEY)

    @classmethod
    def can_run_integration_tests(cls) -> bool:
        """Check if integration tests can run (has required API keys)."""
        if cls.SKIP_INTEGRATION_TESTS:
            return False
        return cls.has_gemini_key() and cls.has_openai_key()

    @classmethod
    def can_run_e2e_tests(cls) -> bool:
        """Check if E2E tests can run (has all required credentials)."""
        if cls.SKIP_E2E_TESTS:
            return False
        return cls.has_gemini_key() and cls.has_openai_key() and cls.has_aws_credentials()

    @classmethod
    def get_test_user_id(cls) -> str:
        """Generate a unique test user ID."""
        return f"test-user-{uuid.uuid4().hex[:8]}"

    @classmethod
    def get_test_s3_key(cls, user_id: str, filename: str) -> str:
        """Generate a test S3 key with test data prefix."""
        return f"{cls.TEST_DATA_PREFIX}{user_id}/{filename}"


# Global config instance
test_config = IntegrationTestConfig()
