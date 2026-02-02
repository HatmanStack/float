import logging
import traceback
from typing import Iterator

import openai

from ..config.settings import settings
from ..exceptions import TTSError
from ..services.tts_service import TTSService
from ..utils.circuit_breaker import openai_circuit, with_circuit_breaker

logger = logging.getLogger(__name__)

# Voice instructions for meditation TTS
MEDITATION_VOICE_INSTRUCTIONS = """Speak in a calm, soothing, and gentle meditation guide voice.
Use a slow, measured pace with natural pauses for breathing.
Your tone should be warm, peaceful, and reassuring - like a trusted meditation instructor
guiding someone through a relaxing session. Emphasize words related to relaxation,
breathing, and letting go. When you encounter "..." in the text, pause naturally."""


class OpenAITTSProvider(TTSService):

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    @with_circuit_breaker(openai_circuit)
    def stream_speech(self, text: str) -> Iterator[bytes]:
        """Stream audio chunks from OpenAI TTS using gpt-4o-mini-tts for meditation voice.

        Raises:
            TTSError: If TTS synthesis fails.
            CircuitBreakerOpenError: If circuit breaker is open.
        """
        try:
            logger.info(f"Streaming OpenAI TTS for text length: {len(text)}")

            with self.client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts-2025-12-15",
                voice="sage",
                input=text,
                response_format="mp3",
                instructions=MEDITATION_VOICE_INSTRUCTIONS,
            ) as response:
                for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk

        except Exception as e:
            logger.error(f"Error in OpenAI TTS streaming: {e}")
            traceback.print_exc()
            raise TTSError(
                f"OpenAI TTS streaming failed: {str(e)}",
                details=traceback.format_exc(),
            )

    def synthesize_speech(self, text: str, output_path: str) -> bool:
        """Synthesize speech to a file using streaming.

        Note: This method catches exceptions and returns bool for backward
        compatibility. For new code, prefer stream_speech which raises TTSError.
        """
        try:
            logger.info(f"Creating OpenAI voice for text: {text[:100]}...")
            with open(output_path, "wb") as f:
                for chunk in self._stream_speech_internal(text):
                    f.write(chunk)
            logger.info(f"Audio successfully saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error in OpenAI TTS synthesis: {e}")
            return False

    def _stream_speech_internal(self, text: str) -> Iterator[bytes]:
        """Internal streaming without circuit breaker for synthesize_speech."""
        with self.client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts-2025-12-15",
            voice="sage",
            input=text,
            response_format="mp3",
            instructions=MEDITATION_VOICE_INSTRUCTIONS,
        ) as response:
            for chunk in response.iter_bytes(chunk_size=4096):
                yield chunk

    def get_provider_name(self) -> str:
        return "openai"
