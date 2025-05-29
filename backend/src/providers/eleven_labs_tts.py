import requests
from typing import Dict, Any

from ..services.tts_service import TTSService
from ..config.settings import settings
from ..config.constants import CHUNK_SIZE

class ElevenLabsTTSProvider(TTSService):
    """ElevenLabs Text-to-Speech service implementation."""
    
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
        self.headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
    
    def synthesize_speech(self, text: str, output_path: str) -> bool:
        """
        Convert text to speech using ElevenLabs TTS API.
        
        Args:
            text: Text content to convert to speech
            output_path: Path where the audio file should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Getting ElevenLabs voice for text: {text[:100]}...")
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": settings.ELEVENLABS_STABILITY,
                    "similarity_boost": settings.ELEVENLABS_SIMILARITY_BOOST,
                    "style": settings.ELEVENLABS_STYLE,
                    "use_speaker_boost": True
                }
            }
            
            print(f"ElevenLabs request data: {data}")
            
            response = requests.post(self.tts_url, headers=self.headers, json=data, stream=True)
            
            if response.ok:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        f.write(chunk)
                print(f"ElevenLabs audio stream saved successfully to: {output_path}")
                return True
            else:
                print(f"ElevenLabs API error: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error in ElevenLabs TTS synthesis: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of the TTS provider."""
        return "elevenlabs"