"""Mock implementations of external API responses for testing."""

from unittest.mock import Mock


class MockGeminiResponse:
    """Mock response from Google Gemini API."""

    def __init__(self, text: str):
        self.text = text


class MockOpenAIResponse:
    """Mock response from OpenAI TTS API."""

    def __init__(self, content: bytes):
        self.content = content


def create_sentiment_analysis_response() -> str:
    """Create a mock sentiment analysis response."""
    return """{
        "sentiment_label": "Sad",
        "intensity": 4,
        "speech_to_text": "NotAvailable",
        "added_text": "I had a difficult day at work",
        "summary": "The user experienced a challenging work situation and feels stressed",
        "user_summary": "I had a difficult day at work dealing with project deadlines",
        "user_short_summary": "Stressful work day"
    }"""


def create_meditation_transcript() -> str:
    """Create a mock meditation transcript."""
    return (
        "<speak>"
        "<voice name='en-US-Neural2-J'>"
        "<google:style name='calm'>"
        "Let's begin by taking a moment to acknowledge the stress you experienced today. "
        "<break time='1000ms'/>"
        "You were dealing with project deadlines, and that's a real challenge. "
        "<break time='1000ms'/>"
        "Now, let's release that tension. "
        "<break time='2000ms'/>"
        "As you breathe in, imagine breathing in calm and peace. "
        "<break time='1500ms'/>"
        "As you breathe out, imagine releasing all the stress from your day. "
        "<break time='2000ms'/>"
        "You did your best today, and that's enough."
        "</google:style>"
        "</voice>"
        "</speak>"
    )


def mock_gemini_service(ai_service):
    """Configure mock AI service to return valid responses."""
    ai_service.analyze_sentiment.return_value = create_sentiment_analysis_response()
    ai_service.generate_meditation.return_value = create_meditation_transcript()
    return ai_service


def mock_openai_tts_provider(tts_provider):
    """Configure mock TTS provider to return valid responses."""
    tts_provider.synthesize_speech.return_value = True
    tts_provider.get_provider_name.return_value = "openai"
    return tts_provider


def mock_s3_storage_service(storage_service):
    """Configure mock S3 storage service to return valid responses."""
    storage_service.upload_json.return_value = True
    storage_service.upload_file.return_value = "s3://float-cust-data/test/file.json"
    storage_service.download_file.return_value = b"test data"
    return storage_service


def mock_audio_service(audio_service):
    """Configure mock audio service to return valid responses."""
    audio_service.combine_voice_and_music.return_value = [
        {"name": "ambient", "path": "/tmp/combined.mp3", "duration": 300}
    ]
    return audio_service
