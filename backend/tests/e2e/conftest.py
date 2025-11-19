"""Pytest fixtures for end-to-end tests."""

import json
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from src.handlers.lambda_handler import LambdaHandler


@pytest.fixture(scope="session")
def skip_if_e2e_disabled():
    """Skip test if E2E tests are disabled."""
    # Import here to avoid circular import
    from tests.integration.test_config import test_config

    if not test_config.can_run_e2e_tests():
        pytest.skip("E2E tests disabled or required credentials not available")


@pytest.fixture
def lambda_handler_real(skip_if_e2e_disabled):
    """
    Real Lambda handler for E2E testing.

    Uses actual services (no mocks) with validate_config=False for testing.
    """
    handler = LambdaHandler(validate_config=False)
    return handler


@pytest.fixture
def lambda_event_factory():
    """Factory for creating Lambda events."""

    def create_event(body: Dict[str, Any], method: str = "POST", origin: str = "https://float-app.fun") -> dict:
        """
        Create a Lambda event dict.

        Args:
            body: Request body dict
            method: HTTP method (default: POST)
            origin: Origin header (default: https://float-app.fun)

        Returns:
            Lambda event dict
        """
        return {
            "httpMethod": method,
            "headers": {
                "Content-Type": "application/json",
                "Origin": origin,
            },
            "body": json.dumps(body),
        }

    return create_event


@pytest.fixture
def lambda_context():
    """Mock Lambda context object."""
    context = MagicMock()
    context.function_name = "float-meditation-test"
    context.function_version = "$LATEST"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:123456789012:function:float-meditation-test"
    )
    context.memory_limit_in_mb = 512
    context.aws_request_id = "test-request-id-e2e"
    context.log_group_name = "/aws/lambda/float-meditation-test"
    context.log_stream_name = "2024/11/18/[$LATEST]test123"
    context.get_remaining_time_in_millis = MagicMock(return_value=30000)
    return context


@pytest.fixture
def summary_request_body_factory():
    """Factory for creating summary request bodies."""

    def create_summary_body(
        user_id: str = None,
        prompt: str = None,
        audio: str = "NotAvailable",
    ) -> Dict[str, Any]:
        """
        Create a summary request body.

        Args:
            user_id: User ID (default: test-user-e2e)
            prompt: User prompt text
            audio: Audio data or NotAvailable

        Returns:
            Summary request body dict
        """
        from tests.integration.test_config import test_config

        return {
            "type": "summary",
            "user_id": user_id or test_config.get_test_user_id(),
            "prompt": prompt or "I had a difficult day at work",
            "audio": audio,
        }

    return create_summary_body


@pytest.fixture
def meditation_request_body_factory():
    """Factory for creating meditation request bodies."""

    def create_meditation_body(
        user_id: str = None,
        sentiment_label: list = None,
        intensity: list = None,
        music_list: list = None,
    ) -> Dict[str, Any]:
        """
        Create a meditation request body.

        Args:
            user_id: User ID (default: test-user-e2e)
            sentiment_label: List of sentiment labels
            intensity: List of intensity values
            music_list: List of music files

        Returns:
            Meditation request body dict
        """
        from tests.integration.test_config import test_config

        return {
            "type": "meditation",
            "user_id": user_id or test_config.get_test_user_id(),
            "input_data": {
                "sentiment_label": sentiment_label or ["Sad"],
                "intensity": intensity or [4],
                "speech_to_text": ["NotAvailable"],
                "added_text": ["I had a difficult day"],
                "summary": ["Work-related stress"],
                "user_summary": ["Had a stressful day at work"],
                "user_short_summary": ["Bad work day"],
            },
            "music_list": music_list or [],
        }

    return create_meditation_body


@pytest.fixture
def e2e_test_s3_cleanup():
    """
    Track and cleanup S3 test data created during E2E tests.

    Usage:
        e2e_test_s3_cleanup.append((bucket, key))
    """
    keys_to_cleanup = []

    yield keys_to_cleanup

    # Cleanup after test
    from tests.integration.test_config import test_config

    if keys_to_cleanup and test_config.has_aws_credentials():
        import boto3
        from botocore.exceptions import ClientError

        s3_client = boto3.client(
            "s3",
            region_name=test_config.AWS_REGION,
            aws_access_key_id=test_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=test_config.AWS_SECRET_ACCESS_KEY,
        )

        for bucket, key in keys_to_cleanup:
            try:
                s3_client.delete_object(Bucket=bucket, Key=key)
                print(f"Cleaned up E2E test file: s3://{bucket}/{key}")
            except ClientError as e:
                print(f"Failed to clean up s3://{bucket}/{key}: {e}")
