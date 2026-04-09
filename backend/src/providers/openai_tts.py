import traceback
from typing import Iterator

import openai

from ..config.settings import settings
from ..exceptions import TTSError
from ..services.tts_service import TTSService
from ..utils.circuit_breaker import openai_circuit, with_circuit_breaker
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)

# Voice instructions for meditation TTS
MEDITATION_VOICE_INSTRUCTIONS = """Speak in a calm, soothing, and gentle meditation guide voice.
Use a slow, measured pace with natural pauses for breathing.
Your tone should be warm, peaceful, and reassuring - like a trusted meditation instructor
guiding someone through a relaxing session. Speak clearly and with enough volume to be
heard easily over soft background music. Emphasize words related to relaxation,
breathing, and letting go. When you encounter "..." in the text, pause naturally."""

# OpenAI TTS API parameters
_TTS_MODEL = "gpt-4o-mini-tts"
_TTS_VOICE = "sage"
_TTS_FORMAT = "mp3"
_TTS_CHUNK_SIZE = 4096


class OpenAITTSProvider(TTSService):
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def _create_streaming_response(self, text: str):
        """Create a streaming TTS response with standard parameters."""
        return self.client.audio.speech.with_streaming_response.create(
            model=_TTS_MODEL,
            voice=_TTS_VOICE,
            input=text,
            response_format=_TTS_FORMAT,
            instructions=MEDITATION_VOICE_INSTRUCTIONS,
        )

    @with_circuit_breaker(openai_circuit)
    def stream_speech(self, text: str) -> Iterator[bytes]:
        """Stream audio chunks from OpenAI TTS for meditation voice.

        Raises:
            TTSError: If TTS synthesis fails.
            CircuitBreakerOpenError: If circuit breaker is open.
        """
        try:
            logger.info(f"Streaming OpenAI TTS for text length: {len(text)}")

            with self._create_streaming_response(text) as response:
                for chunk in response.iter_bytes(chunk_size=_TTS_CHUNK_SIZE):
                    yield chunk

        except Exception as e:
            logger.error(f"Error in OpenAI TTS streaming: {e}")
            raise TTSError(
                f"OpenAI TTS streaming failed: {str(e)}",
                details=traceback.format_exc(),
            ) from e

    def synthesize_speech(self, text: str, output_path: str) -> bool:
        """Synthesize speech to a file using streaming.

        Note: This method catches exceptions and returns bool for backward
        compatibility. For new code, prefer stream_speech which raises TTSError.
        """
        try:
            logger.info("Creating OpenAI voice", extra={"data": {"text_length": len(text)}})
            with open(output_path, "wb") as f:
                with self._create_streaming_response(text) as response:
                    for chunk in response.iter_bytes(chunk_size=_TTS_CHUNK_SIZE):
                        f.write(chunk)
            logger.info(f"Audio successfully saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error in OpenAI TTS synthesis: {e}")
            return False

    def get_provider_name(self) -> str:
        return "openai"
