import os  
import tempfile  
import base64
import combine_voice as cv
import gemini
import eleven
import os

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
    print(f'Result: {result}')
    eleven.get_voice(result)
    
    if os.path.exists("/tmp/voice.mp3"):
        print('OS PATH VOICE EXISTS')
        new_music = cv.combine_audio_files(True, music_list)
    else:
        print('Using Cached Voice')
        new_music = cv.combine_audio_files(False, music_list)
    print(f'get_meditation new_music: {new_music}')
    if os.path.exists("/tmp/combined.mp3"):
        print('Combined exsits and is being returned')
        return new_music, base64.b64encode(open("/tmp/combined.mp3", "rb").read())
    else:
        return music_list, "Error combining meditation audio."
    

def lambda_handler(event, context):
    task = event.get('inference_type')
    holder = {}
    if task == 'summary':
        summary =  analyze_audio(event.get('audio'), event.get('prompt'))
        holder = summary[summary.find('{'): summary.rfind('}')+1]
    if task == 'meditation':
        holder['music_list'], holder['base64'] = get_meditation_transcript(event.get('input_data'), event.get('music_list'))
        
    
    return {
        'statusCode': 200,
        'body': str(holder)
    }
