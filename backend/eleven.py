# Migrating to Google TTS 
import requests  
import os
from dotenv import load_dotenv
load_dotenv()

CHUNK_SIZE = 1024 
XI_API_KEY =  os.environ['XI_KEY'] 
VOICE_ID = os.environ['VOICE_ID']  
OUTPUT_PATH = "/tmp/voice.mp3"  

tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

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