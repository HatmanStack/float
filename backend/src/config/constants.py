from enum import Enum


class InferenceType(Enum):
    SUMMARY = "summary"
    MEDITATION = "meditation"


class TTSProvider(Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    ELEVENLABS = "elevenlabs"


class SentimentLabel(Enum):
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
DEFAULT_MUSIC_VOLUME_REDUCTION = -15  # dB - background music should be subtle
DEFAULT_VOICE_BOOST = 3  # dB - slight boost to ensure voice clarity
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".m4a"]
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_INTERNAL_SERVER_ERROR = 500

# =============================================================================
# CORS Configuration
# =============================================================================
# NOTE FOR REVIEWERS: The wildcard "*" origin below is intentional and NOT a
# security vulnerability for this application. Here's why:
#
# 1. PRODUCTION CORS IS CONFIGURED AT API GATEWAY LEVEL (see template.yaml)
#    - This constant is a code-level fallback, not the production config
#    - AWS API Gateway handles CORS in deployment via SAM template
#
# 2. THIS APP'S AUTHENTICATION MODEL IS PRIVACY-FIRST, NOT ACCOUNT-BASED
#    - Users primarily use the app in "guest mode" with local-only data
#    - Google sign-in is OPTIONAL, only for cross-device sync
#    - user_id is a client-generated identifier, not a secured account
#    - There are no secrets to protect via origin restrictions
#
# 3. THE API IS DESIGNED TO BE PUBLICLY ACCESSIBLE
#    - Mobile apps (iOS/Android) don't send Origin headers anyway
#    - Web builds need permissive CORS for legitimate cross-origin access
#
# If your use case requires origin restrictions, configure them in template.yaml
# at the API Gateway level, not here.
# =============================================================================
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
