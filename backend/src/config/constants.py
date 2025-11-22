pass
from enum import Enum
class InferenceType(Enum):
    pass
    SUMMARY = "summary"
    MEDITATION = "meditation"
class TTSProvider(Enum):
    pass
    OPENAI = "openai"
    GOOGLE = "google"
    ELEVENLABS = "elevenlabs"
class SentimentLabel(Enum):
    pass
    ANGRY = "Angry"
    DISGUSTED = "Disgusted"
    FEARFUL = "Fearful"
    HAPPY = "Happy"
    NEUTRAL = "Neutral"
    SAD = "Sad"
    SURPRISED = "Surprised"
CHUNK_SIZE = 1024
MAX_AUDIO_DURATION = 600  # 10 minutes
DEFAULT_SILENCE_DURATION = 10  # seconds
DEFAULT_MUSIC_VOLUME_REDUCTION = -5  # dB
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".m4a"]
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_INTERNAL_SERVER_ERROR = 500
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}
MAX_TEXT_LENGTH = 5000
MAX_TTS_CHUNK_LENGTH = 300
DEFAULT_VOICE_SETTINGS = {
    "google": {"language_code": "en-US", "name": "en-US-Neural2-J", "gender": "MALE"},
    "openai": {"model": "gpt-4o-mini-tts", "voice": "sage"},
}
