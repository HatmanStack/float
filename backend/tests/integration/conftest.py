"""Pytest fixtures for integration tests."""

import json
import time
import uuid
from typing import List

import boto3
import pytest
from botocore.exceptions import ClientError

from src.config.settings import settings
from src.providers.openai_tts import OpenAITTSProvider
from src.services.gemini_service import GeminiAIService
from src.services.s3_storage_service import S3StorageService
from tests.integration.test_config import test_config


@pytest.fixture(scope="session")
def skip_if_no_gemini():
    """Skip test if Gemini API key is not available."""
    if not test_config.has_gemini_key():
        pytest.skip("Gemini API key not available (set G_KEY environment variable)")


@pytest.fixture(scope="session")
def skip_if_no_openai():
    """Skip test if OpenAI API key is not available."""
    if not test_config.has_openai_key():
        pytest.skip(
            "OpenAI API key not available (set OPENAI_API_KEY environment variable)"
        )


@pytest.fixture(scope="session")
def skip_if_no_aws():
    """Skip test if AWS credentials are not available."""
    if not test_config.has_aws_credentials():
        pytest.skip("AWS credentials not available (configure AWS credentials)")


@pytest.fixture(scope="session")
def skip_if_integration_disabled():
    """Skip test if integration tests are disabled."""
    if not test_config.can_run_integration_tests():
        pytest.skip("Integration tests disabled or API keys not available")


@pytest.fixture(scope="session")
def skip_if_e2e_disabled():
    """Skip test if E2E tests are disabled."""
    if not test_config.can_run_e2e_tests():
        pytest.skip("E2E tests disabled or required credentials not available")


@pytest.fixture
def real_gemini_service(skip_if_no_gemini):
    """
    Real Gemini AI service for integration testing.

    Uses actual Gemini API with test API key.
    """
    # Temporarily override settings if needed
    original_key = settings.GEMINI_API_KEY
    if test_config.GEMINI_API_KEY:
        settings.GEMINI_API_KEY = test_config.GEMINI_API_KEY

    service = GeminiAIService()

    yield service

    # Restore original settings
    settings.GEMINI_API_KEY = original_key


@pytest.fixture
def real_openai_tts_provider(skip_if_no_openai):
    """
    Real OpenAI TTS provider for integration testing.

    Uses actual OpenAI API with test API key.
    """
    # Temporarily override settings if needed
    original_key = settings.OPENAI_API_KEY
    if test_config.OPENAI_API_KEY:
        settings.OPENAI_API_KEY = test_config.OPENAI_API_KEY

    provider = OpenAITTSProvider()

    yield provider

    # Restore original settings
    settings.OPENAI_API_KEY = original_key


@pytest.fixture
def real_s3_client(skip_if_no_aws):
    """
    Real S3 client for integration testing.

    Uses actual AWS credentials.
    """
    client = boto3.client(
        "s3",
        region_name=test_config.AWS_REGION,
        aws_access_key_id=test_config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=test_config.AWS_SECRET_ACCESS_KEY,
    )

    yield client


@pytest.fixture
def real_s3_storage_service(skip_if_no_aws):
    """
    Real S3 storage service for integration testing.

    Uses actual AWS S3 with test bucket or test prefix.
    """
    service = S3StorageService()

    yield service


@pytest.fixture
def test_user_id():
    """Generate a unique test user ID for each test."""
    return test_config.get_test_user_id()


@pytest.fixture
def test_s3_keys_to_cleanup():
    """
    Track S3 keys created during test for cleanup.

    Usage:
        test_s3_keys_to_cleanup.append((bucket, key))
    """
    keys_to_cleanup = []

    yield keys_to_cleanup

    # Cleanup after test
    if keys_to_cleanup and test_config.has_aws_credentials():
        s3_client = boto3.client(
            "s3",
            region_name=test_config.AWS_REGION,
            aws_access_key_id=test_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=test_config.AWS_SECRET_ACCESS_KEY,
        )

        for bucket, key in keys_to_cleanup:
            try:
                s3_client.delete_object(Bucket=bucket, Key=key)
                print(f"Cleaned up test file: s3://{bucket}/{key}")
            except ClientError as e:
                print(f"Failed to clean up s3://{bucket}/{key}: {e}")


@pytest.fixture
def unique_test_id():
    """Generate a unique identifier for test isolation."""
    return uuid.uuid4().hex[:12]


@pytest.fixture
def retry_on_rate_limit():
    """
    Utility function to retry operations on rate limit errors.

    Usage:
        retry_on_rate_limit(lambda: api_call(), max_retries=3)
    """

    def retry_func(func, max_retries=3, initial_delay=2):
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                error_msg = str(e).lower()
                if (
                    "rate limit" in error_msg
                    or "quota" in error_msg
                    or "429" in error_msg
                ):
                    if attempt < max_retries - 1:
                        delay = initial_delay * (2**attempt)
                        print(
                            f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        continue
                raise
        return None

    return retry_func


@pytest.fixture
def test_sentiment_texts():
    """Sample sentiment texts for testing AI services."""
    return {
        "positive": "I had a wonderful day! Everything went perfectly and I'm feeling great.",
        "negative": "I'm feeling really stressed and overwhelmed with everything going on.",
        "neutral": "Today was an ordinary day. Nothing particularly good or bad happened.",
        "anxious": "I'm worried about the upcoming presentation and can't stop thinking about it.",
        "happy": "I just got great news and I'm so excited about the future!",
        "sad": "I'm feeling down and discouraged after what happened today.",
    }


@pytest.fixture
def test_meditation_input():
    """Sample meditation input data for testing."""
    return {
        "sentiment_label": ["Sad"],
        "intensity": [4],
        "speech_to_text": ["NotAvailable"],
        "added_text": ["I had a difficult day at work"],
        "summary": ["Work-related stress and challenges"],
        "user_summary": ["Had a stressful day at work"],
        "user_short_summary": ["Bad work day"],
    }


@pytest.fixture
def validate_json_response():
    """Utility to validate JSON response structure."""

    def validator(response_str: str, required_fields: List[str]) -> dict:
        """
        Validate that response is valid JSON with required fields.

        Args:
            response_str: JSON string to validate
            required_fields: List of required field names

        Returns:
            Parsed JSON dict

        Raises:
            AssertionError: If validation fails
        """
        # Parse JSON
        try:
            data = json.loads(response_str)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON response: {e}")

        # Check required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise AssertionError(f"Missing required fields: {missing_fields}")

        return data

    return validator


@pytest.fixture
def validate_ssml_response():
    """Utility to validate SSML response structure."""

    def validator(ssml_str: str) -> bool:
        """
        Validate that response contains valid SSML tags.

        Args:
            ssml_str: SSML string to validate

        Returns:
            True if valid

        Raises:
            AssertionError: If validation fails
        """
        # Check for basic SSML structure
        if not ssml_str.strip():
            raise AssertionError("SSML response is empty")

        # Check for speak tag
        if "<speak>" not in ssml_str or "</speak>" not in ssml_str:
            raise AssertionError("SSML missing <speak> tags")

        # Check for voice tag (optional but common)
        if "<voice" not in ssml_str:
            print("Warning: SSML missing <voice> tag (optional)")

        return True

    return validator
