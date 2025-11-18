"""Pytest configuration and global fixtures for backend tests."""

import json
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
    service.combine_voice_and_music.return_value = ["Ambient-Peaceful-Meditation_300.wav"]
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
        music_list=["Ambient-Peaceful-Meditation_300.wav"],
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
            "body": json.dumps(body),
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


@pytest.fixture
def request_factory():
    """Factory for creating customizable request bodies."""

    def create_request(
        user_id="test-user-123",
        inference_type="summary",
        prompt=None,
        audio="NotAvailable",
        **kwargs
    ):
        """Create a request body with customizable fields."""
        body = {
            "user_id": user_id,
            "inference_type": inference_type,
        }

        if inference_type == "summary":
            body["prompt"] = prompt or "I had a difficult day"
            body["audio"] = audio
        elif inference_type == "meditation":
            body["input_data"] = kwargs.get("input_data", {
                "sentiment_label": ["Sad"],
                "intensity": [4],
                "user_summary": ["Had a bad day"]
            })
            body["music_list"] = kwargs.get("music_list", [])

        # Allow additional custom fields
        body.update(kwargs.get("extra_fields", {}))
        return body

    return create_request


@pytest.fixture
def sample_sentiment_response():
    """Sample sentiment analysis response from AI service."""
    return """{
        "sentiment_label": "Sad",
        "intensity": 4,
        "speech_to_text": "NotAvailable",
        "added_text": "I had a difficult day",
        "summary": "The user experienced sadness",
        "user_summary": "I had a difficult day at work",
        "user_short_summary": "Bad work day"
    }"""


@pytest.fixture
def sample_meditation_response():
    """Sample meditation script from AI service."""
    return """<speak><voice name='en-US-Neural2-J'>
    Let's take a moment to release this difficult day.
    <break time='1000ms'/>
    Breathe in peace. <break time='2000ms'/>
    Breathe out stress.
    </voice></speak>"""


@pytest.fixture
def sample_audio_data():
    """Sample base64-encoded audio data for testing."""
    return "dGVzdCBhdWRpbyBkYXRhIGZvciB0ZXN0aW5n"  # "test audio data for testing" in base64


@pytest.fixture
def mock_s3_response():
    """Mock S3 API response."""
    return {
        "Contents": [
            {"Key": "user123/2024/01/summary_001.json"},
            {"Key": "user123/2024/01/meditation_001.mp3"},
            {"Key": "user123/2024/01/meditation_002.mp3"}
        ]
    }


@pytest.fixture
def mock_ffmpeg_output():
    """Mock FFmpeg command output for duration calculation."""
    return """Input #0, mp3, from '/tmp/test.mp3':
  Metadata:
    encoder         : Lavf58.76.100
  Duration: 00:03:45.50, start: 0.025056, bitrate: 128 kb/s
  Stream #0:0: Audio: mp3, 44100 Hz, stereo, fltp, 128 kb/s"""


@pytest.fixture
def test_music_list():
    """List of test music tracks."""
    return [
        "Ambient-Peaceful_300.wav",
        "Nature-Calm_180.wav",
        "Meditation-Deep_240.wav"
    ]


@pytest.fixture
def test_input_data():
    """Complete test input data for meditation generation."""
    return {
        "sentiment_label": ["Sad", "Anxious"],
        "intensity": [4, 3],
        "speech_to_text": ["NotAvailable", "NotAvailable"],
        "added_text": ["Work stress", "Meeting anxiety"],
        "summary": ["Work-related stress", "Pre-meeting anxiety"],
        "user_summary": ["I'm stressed about work", "I'm anxious about the meeting"],
        "user_short_summary": ["Work stress", "Meeting anxiety"]
    }


@pytest.fixture
def parametrized_requests(request_factory):
    """Parametrized test requests for various scenarios."""
    return {
        "valid_summary_text": request_factory(
            inference_type="summary",
            prompt="I'm feeling happy today"
        ),
        "valid_summary_audio": request_factory(
            inference_type="summary",
            prompt="NotAvailable",
            audio="dGVzdCBhdWRpbyBkYXRh"
        ),
        "valid_meditation": request_factory(
            inference_type="meditation",
            input_data={"sentiment_label": ["Happy"]},
            music_list=["Track1.wav"]
        ),
        "invalid_no_user_id": {
            "inference_type": "summary",
            "prompt": "Test"
        },
        "invalid_no_type": {
            "user_id": "test-123",
            "prompt": "Test"
        }
    }


@pytest.fixture
def mock_gemini_model():
    """Mock Gemini AI model with realistic responses."""
    model = MagicMock()
    model.generate_content.return_value = MagicMock(
        text='{"sentiment_label": "Neutral", "intensity": 3}'
    )
    return model
