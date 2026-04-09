import traceback
from typing import Iterator

from google import genai
from google.genai import types

from ..config.settings import settings
from ..exceptions import TTSError
from ..services.tts_service import TTSService
from ..utils.circuit_breaker import gemini_tts_circuit
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


class GeminiTTSProvider(TTSService):
    def __init__(self):
        self._client: genai.Client | None = None
        self.model_name = settings.GEMINI_TTS_MODEL

    @property
    def client(self) -> genai.Client:
        """Lazy-initialize genai.Client on first use to avoid requiring API key at construction."""
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def stream_speech(self, text: str) -> Iterator[bytes]:
        """Stream audio chunks from Gemini TTS.

        Circuit breaker bookkeeping is done during iteration (not at return time)
        so that success/failure reflect actual audio consumption.

        Raises:
            TTSError: If TTS synthesis fails.
            CircuitBreakerOpenError: If circuit breaker is open.
        """
        if not gemini_tts_circuit.can_execute():
            from ..exceptions import CircuitBreakerOpenError

            raise CircuitBreakerOpenError(gemini_tts_circuit.name)

        completed = False
        try:
            for chunk in self._stream_speech_internal(text):
                yield chunk
            completed = True
            gemini_tts_circuit.record_success()
        except GeneratorExit:
            raise
        except Exception:
            gemini_tts_circuit.record_failure()
            raise
        finally:
            if not completed:
                gemini_tts_circuit.release_half_open_probe()

    def _stream_speech_internal(self, text: str) -> Iterator[bytes]:
        """Internal streaming without circuit breaker for synthesize_speech."""
        try:
            logger.info(f"Streaming Gemini TTS for text length: {len(text)}")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                        )
                    ),
                ),
            )

            chunks_yielded = 0
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        chunks_yielded += 1
                        yield part.inline_data.data

            if chunks_yielded == 0:
                logger.error("Gemini TTS returned no audio data")
                raise TTSError("Gemini TTS returned no audio data")

            logger.info("Gemini TTS streaming completed successfully")

        except TTSError:
            raise
        except Exception as e:
            logger.error(f"Error in Gemini TTS streaming: {e}")
            raise TTSError(
                f"Gemini TTS streaming failed: {str(e)}",
                details=traceback.format_exc(),
            ) from e

    def synthesize_speech(self, text: str, output_path: str) -> bool:
        """Synthesize speech to a file using streaming.

        Writes to a temp file and atomically renames on success to avoid
        leaving truncated files on failure.
        """
        import os
        import tempfile

        tmp_fd = None
        tmp_path = None
        try:
            logger.info("Creating Gemini voice", extra={"data": {"text_length": len(text)}})
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=os.path.dirname(output_path) or ".", suffix=".tmp"
            )
            with os.fdopen(tmp_fd, "wb") as f:
                tmp_fd = None  # fdopen takes ownership
                for chunk in self.stream_speech(text):
                    f.write(chunk)
            os.replace(tmp_path, output_path)
            logger.info(f"Audio successfully saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error in Gemini TTS synthesis: {e}")
            if tmp_fd is not None:
                os.close(tmp_fd)
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False

    def get_provider_name(self) -> str:
        return "gemini"

    def get_stream_format(self) -> list[str]:
        """Gemini TTS returns raw 16-bit little-endian PCM at 24 kHz mono."""
        return ["-f", "s16le", "-ar", "24000", "-ac", "1"]
