import traceback

import openai

from ..config.settings import settings
from ..services.tts_service import TTSService


class OpenAITTSProvider(TTSService):

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def synthesize_speech(self, text: str, output_path: str) -> bool:
        try:
            print(f"Creating OpenAI voice for text: {text[:100]}...")
            response = self.client.audio.speech.create(
                model="tts-1-hd",
                voice="alloy",
                input=text,
            )
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Audio successfully saved to: {output_path}")
            return True
        except Exception as e:
            print(f"Error in OpenAI TTS synthesis: {e}")
            traceback.print_exc()
            return False

    def get_provider_name(self) -> str:
        return "openai"
