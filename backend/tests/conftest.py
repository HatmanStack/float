"""Pytest configuration and global fixtures for backend tests."""

from unittest.mock import MagicMock

import pytest

from src.models.requests import MeditationRequest, SummaryRequest


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


@pytest.fixture
def mock_audio_service():
    """Mock audio service for testing."""
    service = MagicMock()
    service.combine_voice_and_music.return_value = [
        {"name": "voice", "path": "/tmp/voice.mp3", "duration": 60}
    ]
    return service


@pytest.fixture
def mock_tts_provider():
    """Mock TTS provider for testing."""
    provider = MagicMock()
    provider.synthesize_speech.return_value = True
    provider.get_provider_name.return_value = "openai"
    return provider


@pytest.fixture
def valid_summary_request():
    """Valid summary request fixture."""
    return SummaryRequest(
        type="summary",
        user_id="test-user-123",
        prompt="I had a difficult day at work",
        audio="NotAvailable",
    )


@pytest.fixture
def valid_meditation_request():
    """Valid meditation request fixture."""
    return MeditationRequest(
        type="meditation",
        user_id="test-user-123",
        input_data={
            "sentiment_label": ["Sad"],
            "intensity": [4],
            "speech_to_text": ["NotAvailable"],
            "added_text": ["I had a difficult day"],
            "summary": ["Work stress"],
            "user_summary": ["Challenging work day"],
            "user_short_summary": ["Bad day"],
        },
        music_list=[{"name": "ambient", "path": "s3://bucket/ambient.mp3", "volume": 0.3}],
    )


@pytest.fixture
def invalid_summary_request():
    """Invalid summary request (missing required fields)."""
    return {
        "type": "summary",
        # Missing user_id and prompt
        "audio": "NotAvailable",
    }


@pytest.fixture
def mock_event_factory():
    """Factory for creating mock Lambda events."""

    def create_event(body: dict, method: str = "POST") -> dict:
        return {
            "httpMethod": method,
            "headers": {"Content-Type": "application/json", "Origin": "https://float-app.fun"},
            "body": str(body).replace("'", '"'),  # Simple JSON conversion
        }

    return create_event


@pytest.fixture
def mock_lambda_context():
    """Mock Lambda context object."""
    context = MagicMock()
    context.function_name = "float-meditation"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:float-meditation"
    context.memory_limit_in_mb = 512
    context.aws_request_id = "test-request-id-12345"
    context.log_group_name = "/aws/lambda/float-meditation"
    context.log_stream_name = "2024/10/31/[$LATEST]abc123def456"
    context.get_remaining_time_in_millis = MagicMock(return_value=30000)
    return context
