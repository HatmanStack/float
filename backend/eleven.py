# Import necessary libraries
import requests  # Used for making HTTP requests
import os
from dotenv import load_dotenv
load_dotenv()

CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
XI_API_KEY =  os.environ['XI_KEY'] # Your API key for authentication
VOICE_ID = os.environ['VOICE_ID']  # ID of the voice model to use
OUTPUT_PATH = "/tmp/voice.mp3"  # Path to save the output audio file

# Construct the URL for the Text-to-Speech API request
tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

# Set up headers for the API request, including the API key for authentication
headers = {
    "Accept": "application/json",
    "xi-api-key": XI_API_KEY
}


def get_voice(prompt):
    print("Getting voice")
    print(prompt)
    data = {
        "text": prompt,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": os.environ['STABILITY'] ,
            "similarity_boost": os.environ['SIMILARITY_BOOST'] ,
            "style": os.environ['STYLE'] ,
            "use_speaker_boost": True
        }
    }
    print(data)
    
    response = requests.post(tts_url, headers=headers, json=data, stream=True)
    if response.ok:
        with open(OUTPUT_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        print("Audio stream saved successfully.")
    else:
        print(response.text)
    return