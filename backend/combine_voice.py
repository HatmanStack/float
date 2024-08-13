import subprocess
import boto3
import ast
import random

def get_audio_duration(file_path):
    result = subprocess.run(
        ["ffmpeg", "-i", file_path, "-f", "null", "-"],
        stderr=subprocess.PIPE, text=True, check=True
    )
    duration_line = [line for line in result.stderr.split('\n') if "Duration" in line][0]
    duration_str = duration_line.split(",")[0].split("Duration:")[1].strip()
    h, m, s = map(float, duration_str.split(":"))
    duration = h * 3600 + m * 60 + s
    return duration

def get_music(used_music):
    s3 = boto3.client('s3')
    bucket_name = 'audio-er-lambda'
    if used_music is None:
        used_music = []
    else:
        try:
            used_music = ast.literal_eval(used_music)
        except (ValueError, SyntaxError):
            used_music = [used_music]
    
    try:
        existing_objects = s3.list_objects_v2(Bucket=bucket_name)
        existing_keys = {obj['Key'] for obj in existing_objects.get('Contents', [])}
    except Exception as e:
        print(f"Error listing objects in bucket {bucket_name}: {e}")
        return

     # Filter out used music keys
    available_keys = list(existing_keys - set(used_music))

    file_key = ''
    if not available_keys:
        print("No available music files to choose from.")
        file_key = 'Hopeful-200-1.wav'
    else:
        # Select a random file key from the available keys
        file_key = random.choice(available_keys)

    try:
        s3.download_file(bucket_name, file_key, '/tmp/music.mp3')
        print(f"File downloaded successfully: {file_key}")
        
        used_music.append(file_key)
        print(f'USED_MUSIC: {used_music}')
        return used_music
    except Exception as e:
        print(f"Error downloading file {file_key}: {e}")
    
    
def combine_audio_files(Cached, used_music):
    print('Combining Audio')
    music_path = '/tmp/music.mp3'
    voice_path = '/tmp/voice.mp3' if Cached else '/var/task/voice.mp3'
    new_music = get_music(used_music)
    
    print(f'Music: {new_music}')
    music_volume_reduced_path = '/tmp/music_reduced.mp3'
    music_length_reduced_path = '/tmp/music_length_reduced.mp3'
    silence_path = '/tmp/silence.mp3'
    voice_with_silence_path = '/tmp/voice_with_silence.mp3'
    combined_path = '/tmp/combined.mp3'
    
    voice_duration = get_audio_duration(voice_path)
    print(f"Voice duration: {voice_duration}")
    total_duration = voice_duration + 30 
    
    # Step 1: Reduce the volume of the music by 10 dB
    subprocess.run([
        "ffmpeg", "-i", music_path, "-filter:a", "volume=-15dB", music_volume_reduced_path
    ], check=True)
    print("Step 1 Complete")
    
    # Step 2: Create 10 seconds of silence
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "10", silence_path
    ], check=True)
    print("Step 2 Complete")
    
    # Step 3: Concatenate the silence and the voice
    subprocess.run([
        "ffmpeg", "-i", f"concat:{silence_path}|{voice_path}", "-c", "copy", voice_with_silence_path
    ], check=True)
    print("Step 3 Complete")
    
    subprocess.run([
        "ffmpeg", "-i", music_volume_reduced_path, "-t", str(total_duration), music_length_reduced_path
    ], check=True)
    
    # Step 4: Overlay the voice with silence on the music
    subprocess.run([
        "ffmpeg", "-i", music_volume_reduced_path, "-i", voice_with_silence_path, 
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2", combined_path
    ], check=True)
    print("Step 4 Complete")
    return new_music

    
            