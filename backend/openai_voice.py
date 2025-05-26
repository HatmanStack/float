import openai
import os
import traceback

def create_openai_voice(text, voice_path):
    try:
        print('Trying to create OpenAI voice...')
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="sage",
            input="Today is a wonderful day to build something people love!",
            instructions="Speak in a cheerful and positive tone.",
        ) as response:
            response.stream_to_file(voice_path)
    except Exception as e:
        print(f"Error in create_openai_voice: {e}")
        traceback.print_exc()
        raise