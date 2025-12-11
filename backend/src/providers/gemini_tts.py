import logging
import traceback
from typing import Iterator

from google import genai
from google.genai import types

from ..config.settings import settings
from ..services.tts_service import TTSService

logger = logging.getLogger(__name__)

class GeminiTTSProvider(TTSService):
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_TTS_MODEL

    def stream_speech(self, text: str) -> Iterator[bytes]:
        try:
            logger.info(f"Streaming Gemini voice for text length: {len(text)}")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Kore"
                            )
                        )
                    )
                )
            )

            # Extract raw PCM audio data (audio/L16;codec=pcm;rate=24000)
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        yield part.inline_data.data
        except Exception as e:
            logger.error(f"Error in Gemini TTS streaming: {e}")
            traceback.print_exc()
            raise

    def synthesize_speech(self, text: str, output_path: str) -> bool:
        try:
            with open(output_path, "wb") as f:
                for chunk in self.stream_speech(text):
                    f.write(chunk)
            logger.info(f"Audio successfully saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error in Gemini TTS synthesis: {e}")
            return False

    def get_provider_name(self) -> str:
        return "gemini"

