import os  
import json
import tempfile  
import base64
import combine_voice as cv
import gemini
import eleven
import tts
import openai_voice as ov
import os
import boto3
import random
from datetime import datetime

combined_meditation_path = "/tmp/combined.mp3"
temp_voice_path = "/tmp/voice.mp3"

def analyze_audio(audio, prompt):
    print("Summary Started")
    if 'NotAvailable' not in audio:
        audio_bytes = base64.b64decode(audio)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_bytes)
            audio = temp_file.name
    result = gemini.getSummary(audio, prompt)
    print(f'Result: {result}')
    return result

def get_meditation_transcript(input_data, music_list):
    result = gemini.getMeditation(input_data)
    print(f'Meditation Text Result: {result}')
    ov.create_openai_voice(result) # Change this to dictate different voice Service: 
                                   # OpenAi, Google TTS or Eleven Labs
    
    if os.path.exists(temp_voice_path):
        print('OS PATH VOICE EXISTS')
        new_music = cv.combine_audio_files(True, music_list)
    else:
        print('Using Cached Voice')
        new_music = cv.combine_audio_files(False, music_list)
    print(f'get_meditation new_music: {new_music}')
    if os.path.exists(combined_meditation_path):
        print('Combined exsits and is being returned')
        with open(combined_meditation_path, "rb") as audio_file:
            encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')
        return new_music, encoded_string
    else:
        return music_list, "Error combining meditation audio."
    

def lambda_handler(event, context):
    task = event.get('inference_type')
    print(task)
    holder = {}
    if task == 'summary':
        summary =  analyze_audio(event.get('audio'), event.get('prompt'))
        new_holder = summary[summary.find('{'): summary.rfind('}')+1]
        holder = json.loads(new_holder)
    if task == 'meditation':
        holder['music_list'], holder['base64'] = get_meditation_transcript(event.get('input_data'), event.get('music_list'))
    request_id = random.randint(1,10000000)
    user = event.get('user_id')
    holder['request_id'] = request_id
    holder['user_id'] = user
    holder['inference_type'] = task
    holder_json = json.dumps(holder)
    s3 = boto3.client('s3')
    bucket_name = 'float-cust-data'
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    object_key = f"{user}/{task}/{timestamp}.json"
    object_key_audio = f"{user}/audio/{timestamp}.json"
    print(str(holder))
    try:
        s3.put_object(Bucket=bucket_name, Key=object_key, Body=holder_json)
        if event.get('audio') != "NotAvailable":
            audio = {}
            audio['user_audio'] = event.get('audio')
            audio['user_id'] = user
            audio['request_id'] = request_id
            holder_audio = json.dumps(audio)
            s3.put_object(Bucket=bucket_name, Key=object_key_audio, Body=holder_audio)
        print(f"Successfully uploaded {object_key} to {bucket_name}")
    except Exception as e:
        print(f"Error uploading to S3: {e}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(holder)
    }
