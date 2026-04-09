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
    """Mock storage service for testing.

    Seeds ``list_objects`` with a real list so ``MusicSelector`` can fall
    back through its three-way ``filtered_keys / existing_keys / raise``
    chain instead of inheriting an auto-mock that is truthy but yields no
    items. Also clears the module-level music list cache so test ordering
    cannot leak a previous run's listing into this one.
    """
    from src.utils.cache import music_list_cache

    music_list_cache.clear()
    service = MagicMock()
    service.upload_json.return_value = True
    service.upload_file.return_value = "s3://bucket/path/to/file"
    service.list_objects.return_value = [
        "Hopeful-Elegant-LaidBack_120.wav",
        "Calm-Track_180.wav",
        "Default-Track_300.wav",
    ]
    service.download_file.return_value = True
    return service
