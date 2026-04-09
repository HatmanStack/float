import asyncio
import queue
import re
import threading
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

_SENTINEL = object()

# Target words per chunk — ~30-45 seconds of speech at ~150 wpm
CHUNK_TARGET_WORDS = 80

# Silence padding between sections: 2 seconds of PCM silence
# (24kHz, 16-bit mono = 48000 bytes/sec)
INTER_SECTION_SILENCE = b"\x00" * (48000 * 2)

# Maximum sections per Live API session before opening a new one.
# The Live API has a ~3-4 minute session deadline, so we cap at 5
# sections (~2.5 min of audio) to stay safely under the limit.
MAX_SECTIONS_PER_SESSION = 5

# System instruction for the Live API to read text verbatim as a meditation
# guide rather than generating a conversational response.
LIVE_TTS_SYSTEM_INSTRUCTION = (
    "You are a meditation text-to-speech reader. You will receive a full meditation "
    "script for context, then be asked to read it aloud section by section. "
    "When reading each section:\n"
    "- Read the text EXACTLY as written, word for word\n"
    "- Use a calm, soothing, slow meditation guide voice\n"
    "- Honor pauses indicated by '...' with natural silence\n"
    "- Do not add, remove, or change any words\n"
    "- Do not respond conversationally or add commentary\n"
    "- Simply read the section aloud, then stop"
)


def _split_meditation_text(text: str) -> list[str]:
    """Split meditation text into chunks at natural pause points.

    Splits on paragraph breaks (double newline) first, then on '...'
    pause markers, then on sentence boundaries. Each chunk targets
    ~CHUNK_TARGET_WORDS words to stay within the Live API's quality
    window (~30-45 seconds of speech).
    """
    # Split on paragraph breaks first
    paragraphs = re.split(r"\n\s*\n", text.strip())

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_words = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_words = len(para.split())

        # If adding this paragraph stays under target, accumulate
        if current_words + para_words <= CHUNK_TARGET_WORDS and current_chunk:
            current_chunk.append(para)
            current_words += para_words
            continue

        # If current chunk is non-empty, flush it
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_words = 0

        # If this single paragraph is over target, split it further
        if para_words > CHUNK_TARGET_WORDS:
            # Split on '...' pause markers
            segments = re.split(r"(\.\.\.)", para)
            sub_chunk: list[str] = []
            sub_words = 0
            for seg in segments:
                seg_words = len(seg.split())
                if sub_words + seg_words > CHUNK_TARGET_WORDS and sub_chunk:
                    chunks.append("".join(sub_chunk))
                    sub_chunk = []
                    sub_words = 0
                sub_chunk.append(seg)
                sub_words += seg_words
            if sub_chunk:
                leftover = "".join(sub_chunk).strip()
                if leftover:
                    current_chunk = [leftover]
                    current_words = len(leftover.split())
        else:
            current_chunk = [para]
            current_words = para_words

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return [c for c in chunks if c.strip()]


class GeminiTTSProvider(TTSService):
    def __init__(self):
        self._client: genai.Client | None = None
        self.model_name = settings.GEMINI_TTS_MODEL
        self.live_model_name = settings.GEMINI_LIVE_TTS_MODEL

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
        """Stream audio via the Gemini Live API WebSocket in chunked turns.

        Opens a single Live API session and sends the full meditation text
        for context, then feeds it section by section for the model to read
        aloud. Each section is ~30-45 seconds of speech, keeping audio
        quality high. Audio chunks from all turns are yielded through a
        single queue so the HLS encoder sees one continuous PCM stream.
        """
        import time

        text_chunks = _split_meditation_text(text)
        logger.info(
            f"Streaming Gemini Live TTS: {len(text)} chars split into {len(text_chunks)} sections"
        )

        chunk_queue: queue.Queue = queue.Queue(maxsize=64)
        error_holder: list = []

        client = self.client
        live_model = self.live_model_name

        live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=LIVE_TTS_SYSTEM_INSTRUCTION)]
            ),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                )
            ),
        )

        async def _send_context_and_ack(session, full_text: str) -> None:
            """Send the full meditation for context and consume the ack turn."""
            context_msg = (
                "Here is the full meditation script for context. I will send "
                "it to you in sections to read aloud one at a time. Do not "
                "read anything yet, just acknowledge.\n\n"
                f"---\n{full_text}\n---"
            )
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=context_msg)],
                ),
                turn_complete=True,
            )
            async for message in session.receive():
                sc = message.server_content
                if sc and sc.turn_complete:
                    break

        async def _read_section(session, section: str) -> tuple[int, int]:
            """Send a section to read and collect audio. Returns (chunks, bytes)."""
            prompt = f"Read this section aloud now:\n\n{section}"
            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
                turn_complete=True,
            )
            section_chunks = 0
            section_bytes = 0
            async for message in session.receive():
                sc = message.server_content
                if sc and sc.model_turn:
                    for part in sc.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            chunk_queue.put(part.inline_data.data)
                            section_chunks += 1
                            section_bytes += len(part.inline_data.data)
                if sc and sc.turn_complete:
                    break
            return section_chunks, section_bytes

        async def _live_api_producer() -> None:
            total_chunks = 0
            total_bytes = 0
            start_time = time.monotonic()
            sections_in_session = 0

            try:
                session_ctx = client.aio.live.connect(model=live_model, config=live_config)
                session = await session_ctx.__aenter__()

                try:
                    await _send_context_and_ack(session, text)
                    logger.info("Live TTS context accepted, starting section reads")

                    for i, section in enumerate(text_chunks):
                        section_start = time.monotonic()

                        # Rotate session if we've hit the limit to avoid
                        # the ~3-4 min server-side deadline timeout.
                        # Note: rotation re-sends the full meditation text for
                        # context, adding ~1-2s latency per rotation boundary.
                        if sections_in_session >= MAX_SECTIONS_PER_SESSION:
                            logger.info(
                                f"Rotating Live API session after {sections_in_session} sections"
                            )
                            await session_ctx.__aexit__(None, None, None)
                            session_ctx = client.aio.live.connect(
                                model=live_model, config=live_config
                            )
                            session = await session_ctx.__aenter__()
                            await _send_context_and_ack(session, text)
                            sections_in_session = 0

                        section_chunks, section_bytes = await _read_section(session, section)
                        total_chunks += section_chunks
                        total_bytes += section_bytes
                        sections_in_session += 1

                        section_elapsed = time.monotonic() - section_start
                        section_audio = section_bytes / 48000
                        logger.info(
                            f"Live TTS section {i + 1}/{len(text_chunks)}: "
                            f"{section_chunks} chunks, {section_audio:.1f}s audio "
                            f"in {section_elapsed:.1f}s "
                            f"({len(section.split())} words)"
                        )

                        # Insert 2 seconds of silence between sections
                        if i < len(text_chunks) - 1:
                            chunk_queue.put(INTER_SECTION_SILENCE)
                            total_bytes += len(INTER_SECTION_SILENCE)

                finally:
                    await session_ctx.__aexit__(None, None, None)

                elapsed = time.monotonic() - start_time
                total_audio = total_bytes / 48000
                logger.info(
                    f"Live TTS complete: {total_chunks} chunks, "
                    f"{total_audio:.1f}s audio in {elapsed:.1f}s wall time"
                )

                if total_chunks == 0:
                    raise TTSError("Gemini Live API returned no audio data")
            except Exception as exc:
                error_holder.append(exc)
            finally:
                chunk_queue.put(_SENTINEL)

        def _run_producer() -> None:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_live_api_producer())
            finally:
                loop.close()

        producer_thread = threading.Thread(target=_run_producer, daemon=True)
        producer_thread.start()

        try:
            chunks_yielded = 0
            while True:
                item = chunk_queue.get(timeout=300)
                if item is _SENTINEL:
                    break
                chunks_yielded += 1
                yield item

            if error_holder:
                exc = error_holder[0]
                if isinstance(exc, TTSError):
                    raise exc
                raise TTSError(
                    f"Gemini Live API streaming failed: {exc}",
                    details=traceback.format_exc(),
                ) from exc

            if chunks_yielded == 0:
                raise TTSError("Gemini Live API returned no audio data")

            logger.info("Gemini Live TTS streaming completed successfully")

        except queue.Empty as exc:
            raise TTSError("Gemini Live API timed out waiting for audio chunks") from exc
        finally:
            producer_thread.join(timeout=10)

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
