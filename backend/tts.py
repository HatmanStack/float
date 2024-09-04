import sys
import os
import time

from google.cloud import texttospeech
import subprocess

client = texttospeech.TextToSpeechClient()

def split_text(text, max_length):
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
    formatted_chunks = []
    start_tag = '<speak><voice name="en-US-Neural2-J"><google:style name="calm">'
    end_tag = '</google:style></voice></speak>'
    for chunk in chunks:
        formatted_chunk = start_tag + chunk + end_tag
        
        formatted_chunks.append(formatted_chunk)
    return formatted_chunks

def create_tts_meditation(text):
    chunks = split_text(text, 300)
    voice_path = '/tmp/voice.mp3'
    if os.path.exists(voice_path):
        os.remove(voice_path)
    paths = []
    for index, ssml_data in enumerate(chunks):
        # Set the text input to be synthesized
        print(index)
        try:
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
            
            # Perform the text-to-speech request on the text input with the selected
            # voice parameters and audio file type
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            print(index)
            # The response's audio_content is binary.
            {int(time.time())}
            paths.append(f'/tmp/tts_voice_{int(time.time())}.mp3')
            with open(paths[index], "wb") as out:
                # Write the response to the output file.
                out.write(response.audio_content)
                print(f'Audio content written to file {paths[index]}')
        except Exception as e:
            print(e)
            return
    
    concat_paths = '|'.join(paths)
    subprocess.run(["ffmpeg", "-i", f"concat:{concat_paths}", "-c", "copy", voice_path], check=True)


