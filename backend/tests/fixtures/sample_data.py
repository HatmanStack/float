"""Sample request and response data for testing."""

# Sample request data
SAMPLE_SUMMARY_REQUEST = {
    "type": "summary",
    "user_id": "user-123",
    "prompt": "I had a difficult day at work with project deadlines",
    "audio": "NotAvailable",
}

SAMPLE_SUMMARY_REQUEST_WITH_AUDIO = {
    "type": "summary",
    "user_id": "user-123",
    "prompt": "NotAvailable",
    "audio": "base64encodedaudiodata==",  # Placeholder for base64 audio
}

SAMPLE_MEDITATION_REQUEST = {
    "type": "meditation",
    "user_id": "user-123",
    "input_data": {
        "sentiment_label": ["Sad", "Anxious"],
        "intensity": [4, 3],
        "speech_to_text": ["NotAvailable", "I'm worried about upcoming events"],
        "added_text": ["Difficult day at work", "NotAvailable"],
        "summary": ["Work stress", "Future anxiety"],
        "user_summary": ["Had a bad day dealing with deadlines", "Worried about what's coming"],
        "user_short_summary": ["Stressful work", "Anxious about future"],
    },
    "music_list": [
        {"name": "ambient", "path": "s3://audio/ambient.mp3", "volume": 0.3},
        {"name": "nature", "path": "s3://audio/nature.mp3", "volume": 0.2},
    ],
}

SAMPLE_SENTIMENT_ANALYSIS_RESPONSE = {
    "sentiment_label": "Sad",
    "intensity": 4,
    "speech_to_text": "NotAvailable",
    "added_text": "I had a difficult day at work",
    "summary": "User experienced work stress",
    "user_summary": "I struggled with project deadlines",
    "user_short_summary": "Bad work day",
}

SAMPLE_MEDITATION_RESPONSE = {
    "request_id": "req-123",
    "user_id": "user-123",
    "type": "meditation",
    "audio": "base64encodedaudiodata==",
    "duration": 300,
    "music_list": [{"name": "voice", "path": "/tmp/voice.mp3", "duration": 300}],
    "timestamp": "2024-10-31T12:00:00Z",
    "status": "success",
}

SAMPLE_LAMBDA_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://float-app.fun",
    "User-Agent": "Mobile/5.0",
}

SAMPLE_LAMBDA_EVENT = {
    "httpMethod": "POST",
    "headers": SAMPLE_LAMBDA_HEADERS,
    "body": str(SAMPLE_SUMMARY_REQUEST),
}

# Edge cases
EMPTY_PROMPT_REQUEST = {
    "type": "summary",
    "user_id": "user-123",
    "prompt": "",
    "audio": "NotAvailable",
}

VERY_LONG_PROMPT_REQUEST = {
    "type": "summary",
    "user_id": "user-123",
    "prompt": "This is a very long prompt. " * 1000,  # Very long text
    "audio": "NotAvailable",
}

SPECIAL_CHARS_PROMPT_REQUEST = {
    "type": "summary",
    "user_id": "user-123",
    "prompt": "I'm feeling 🎭 with special chars: @#$%^&*()",
    "audio": "NotAvailable",
}
