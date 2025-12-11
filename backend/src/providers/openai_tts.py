import logging
import traceback
from typing import Iterator

import openai

from ..config.settings import settings
from ..services.tts_service import TTSService

logger = logging.getLogger(__name__)


class OpenAITTSProvider(TTSService):

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def stream_speech(self, text: str) -> Iterator[bytes]:
        """Stream audio chunks from OpenAI TTS."""
        try:
            logger.info(f"Streaming OpenAI TTS for text length: {len(text)}")

            with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=text,
                response_format="mp3",
            ) as response:
                for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk

        except Exception as e:
            logger.error(f"Error in OpenAI TTS streaming: {e}")
            traceback.print_exc()
            raise

    def synthesize_speech(self, text: str, output_path: str) -> bool:
        """Synthesize speech to a file using streaming."""
        try:
            logger.info(f"Creating OpenAI voice for text: {text[:100]}...")
            with open(output_path, "wb") as f:
                for chunk in self.stream_speech(text):
                    f.write(chunk)
            logger.info(f"Audio successfully saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error in OpenAI TTS synthesis: {e}")
            return False

    def get_provider_name(self) -> str:
        return "openai"
