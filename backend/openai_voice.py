import openai
import os

def create_openai_voice(text):
    voice_path = '/tmp/voice.mp3'
    openai.api_key = os.getenv('OPENAI_API_KEY')  
    response = openai.audio.speech.create(
    model="tts-1-hd",
    voice="alloy",
    input=text
    )
    response.stream_to_file(voice_path)