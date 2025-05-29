import os
import time
import subprocess
from typing import List

from google.cloud import texttospeech

from ..services.tts_service import TTSService
from ..config.settings import settings
from ..config.constants import MAX_TTS_CHUNK_LENGTH

class GoogleTTSProvider(TTSService):
    """Google Cloud Text-to-Speech service implementation."""
    
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
    
    def synthesize_speech(self, text: str, output_path: str) -> bool:
        """
        Convert text to speech using Google TTS API.
        
        Args:
            text: Text content to convert to speech (with SSML tags)
            output_path: Path where the audio file should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            chunks = self._split_text(text, MAX_TTS_CHUNK_LENGTH)
            
            # Remove existing file
            if os.path.exists(output_path):
                os.remove(output_path)
            
            temp_paths = []
            
            for index, ssml_data in enumerate(chunks):
                try:
                    # Set the text input to be synthesized
                    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_data)
                    
                    # Define the voice parameters
                    voice = texttospeech.VoiceSelectionParams(
                        language_code='en-US',
                        name='en-US-Neural2-J',
                        ssml_gender=texttospeech.SsmlVoiceGender.MALE
                    )
                    
                    # Define the audio configuration
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3
                    )
                    
                    # Perform the text-to-speech request
                    response = self.client.synthesize_speech(
                        input=synthesis_input, voice=voice, audio_config=audio_config
                    )
                    
                    # Save chunk to temporary file
                    temp_path = f'/tmp/tts_voice_{int(time.time())}_{index}.mp3'
                    temp_paths.append(temp_path)
                    
                    with open(temp_path, "wb") as out:
                        out.write(response.audio_content)
                        print(f'Audio chunk {index} written to {temp_path}')
                        
                except Exception as e:
                    print(f"Error processing chunk {index}: {e}")
                    return False
            
            # Concatenate all chunks into final output
            if len(temp_paths) > 1:
                concat_paths = '|'.join(temp_paths)
                subprocess.run(
                    ["ffmpeg", "-i", f"concat:{concat_paths}", "-c", "copy", output_path], 
                    check=True
                )
            elif len(temp_paths) == 1:
                # Just move the single file
                os.rename(temp_paths[0], output_path)
            
            # Clean up temporary files
            for temp_path in temp_paths:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            print(f"Google TTS audio successfully saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error in Google TTS synthesis: {e}")
            return False
    
    def get_provider_name(self) -> str:
        """Get the name of the TTS provider."""
        return "google"
    
    def _split_text(self, text: str, max_length: int) -> List[str]:
        """Split text by break tags and format with SSML."""
        # Split the text by <break> tags
        parts = text.split('<break')
        chunks = []
        current_chunk = ""
        first_iteration = True

        for part in parts:
            # Skip the first iteration
            if first_iteration:
                first_iteration = False
                current_chunk += part
                continue
            if part.strip():
                part = '<break' + part
            # Check if adding this part would exceed the max_length
            if len(current_chunk) + len(part) <= max_length:
                current_chunk += part
            else:
                # If the current chunk is not empty, add it to chunks
                if current_chunk:
                    chunks.append(current_chunk)
                # Start a new chunk with the current part
                current_chunk = part

        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        # Format chunks with SSML wrapper
        formatted_chunks = []
        start_tag = '<speak><voice name="en-US-Neural2-J"><google:style name="calm">'
        end_tag = '</google:style></voice></speak>'
        
        for chunk in chunks:
            formatted_chunk = start_tag + chunk + end_tag
            formatted_chunks.append(formatted_chunk)
        
        return formatted_chunks