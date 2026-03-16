"""Pytest configuration and global fixtures for backend tests."""

from unittest.mock import MagicMock

import pytest

from tests.integration.test_config import test_config


@pytest.fixture
def test_user_id():
    """Generate a unique test user ID for each test."""
    return test_config.get_test_user_id()


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    service = MagicMock()
    service.analyze_sentiment.return_value = """{
        "sentiment_label": "Sad",
        "intensity": 4,
        "speech_to_text": "I had a difficult day at work",
        "added_text": "NotAvailable",
        "summary": "The user experienced a challenging work situation",
        "user_summary": "I had a difficult day at work",
        "user_short_summary": "Bad work day"
    }"""
    service.generate_meditation.return_value = (
        "<speak><voice name='en-US-Neural2-J'>"
        "Let's release this moment. <break time='1000ms'/>"
        "Breathe deeply and let it go."
        "</voice></speak>"
    )
    return service


@pytest.fixture
def mock_storage_service():
    """Mock storage service for testing."""
    service = MagicMock()
    service.upload_json.return_value = True
    service.upload_file.return_value = "s3://bucket/path/to/file"
    return service
