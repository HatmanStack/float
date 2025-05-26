import subprocess
import random
import os
import boto3
import ast
import re
import os
import subprocess

ffmpeg_executable = "/opt/bin/ffmpeg"  # Or the correct absolute path to ffmpeg in your layer

print(f"--- STARTING FFMPEG DIAGNOSTICS ---", flush=True)

# 1. Check if the ffmpeg executable file exists
if not os.path.exists(ffmpeg_executable):
    print(f"CRITICAL ERROR: ffmpeg executable NOT FOUND at {ffmpeg_executable}", flush=True)
else:
    print(f"SUCCESS: ffmpeg executable FOUND at {ffmpeg_executable}", flush=True)

    # 2. Check file size (a very small size might indicate a problem)
    try:
        size = os.path.getsize(ffmpeg_executable)
        print(f"INFO: ffmpeg size: {size} bytes.", flush=True)
        if size < 100000: # A typical ffmpeg binary is many MBs
            print(f"WARNING: ffmpeg size is very small ({size} bytes), which might indicate it's not a full binary.", flush=True)
    except Exception as e:
        print(f"ERROR: Could not get size of {ffmpeg_executable}: {e}", flush=True)

    # 3. Check execute permissions (using ls -la)
    print(f"INFO: Checking permissions for {ffmpeg_executable} directory and file...", flush=True)
    parent_dir = os.path.dirname(ffmpeg_executable)
    ls_parent_result = subprocess.run(['ls', '-ld', parent_dir], capture_output=True, text=True, check=False)
    print(f"'ls -ld {parent_dir}' stdout:\n{ls_parent_result.stdout.strip()}", flush=True)
    print(f"'ls -ld {parent_dir}' stderr:\n{ls_parent_result.stderr.strip()}", flush=True)
    
    ls_exe_result = subprocess.run(['ls', '-la', ffmpeg_executable], capture_output=True, text=True, check=False)
    print(f"'ls -la {ffmpeg_executable}' stdout:\n{ls_exe_result.stdout.strip()}", flush=True)
    print(f"'ls -la {ffmpeg_executable}' stderr:\n{ls_exe_result.stderr.strip()}", flush=True)
    if 'x' not in ls_exe_result.stdout.split()[0]:
         print(f"WARNING: Execute permission might be missing for {ffmpeg_executable}.", flush=True)


    # 4. Try to run ffmpeg with just -L (lists licenses, should print to stderr)
    # This is one of the simplest commands that should produce output if ffmpeg is minimally functional.
    print(f"INFO: Attempting to run '{ffmpeg_executable} -L'...", flush=True)
    cmd_list_L = [ffmpeg_executable, "-L"]
    try:
        # Using a timeout and not using check=True initially to see raw output
        result_L = subprocess.run(cmd_list_L, timeout=15, capture_output=True, text=True, check=False)
        print(f"'{' '.join(cmd_list_L)}' STDOUT:\n{result_L.stdout.strip() if result_L.stdout else '<<NO STDOUT>>'}", flush=True)
        print(f"'{' '.join(cmd_list_L)}' STDERR:\n{result_L.stderr.strip() if result_L.stderr else '<<NO STDERR>>'}", flush=True)
        print(f"'{' '.join(cmd_list_L)}' RETURN CODE: {result_L.returncode}", flush=True)
        if result_L.returncode != 0 and not result_L.stderr and not result_L.stdout:
            print(f"WARNING: '{' '.join(cmd_list_L)}' exited with {result_L.returncode} but produced no output.", flush=True)
        elif not result_L.stderr and not result_L.stdout: # If exit code was 0 but still no output
             print(f"WARNING: '{' '.join(cmd_list_L)}' exited with {result_L.returncode} but produced NO output to stdout or stderr. This is highly unusual for '-L'.", flush=True)

    except subprocess.TimeoutExpired:
        print(f"ERROR: '{' '.join(cmd_list_L)}' TIMED OUT.", flush=True)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Executable '{ffmpeg_executable}' not found by subprocess when trying to run '-L'.", flush=True)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred running '{' '.join(cmd_list_L)}': {e}", flush=True)

    # 5. If 'file' command is available (add it to your layer if needed for debugging)
    # print(f"INFO: Attempting to run 'file {ffmpeg_executable}'...", flush=True)
    # file_cmd_result = subprocess.run(["file", ffmpeg_executable], capture_output=True, text=True, check=False)
    # print(f"'file {ffmpeg_executable}' stdout: {file_cmd_result.stdout.strip()}", flush=True)
    # print(f"'file {ffmpeg_executable}' stderr: {file_cmd_result.stderr.strip()}", flush=True)

    # 6. Check ldd output again, very carefully looking at its stderr too
    # print(f"INFO: Attempting to run 'ldd {ffmpeg_executable}'...", flush=True)
    # ldd_cmd_result = subprocess.run(["ldd", ffmpeg_executable], capture_output=True, text=True, check=False)
    # print(f"'ldd {ffmpeg_executable}' stdout:\n{ldd_cmd_result.stdout.strip()}", flush=True)
    # print(f"IMPORTANT: 'ldd {ffmpeg_executable}' stderr:\n{ldd_cmd_result.stderr.strip()}", flush=True) # ldd can print "statically linked" or errors to stderr

print(f"--- FFMPEG DIAGNOSTICS COMPLETE ---", flush=True)

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

def extract_last_numeric_value(filename):
    matches = re.findall(r'(\d+)(?=\D*$)', filename)
    if matches:
        # Return the last numeric match as an integer
        return int(matches[-1])
    return None

def run_ffmpeg(cmd):
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise

    
def get_music(used_music, total_duration, music_path):
    s3 = boto3.client('s3')
    bucket_name = 'audio-er-lambda'
    if used_music is None:
        used_music = []
    else:
        if isinstance(used_music, str):
            try:
                used_music = ast.literal_eval(used_music)
                if not isinstance(used_music, list):
                    used_music = [used_music]
            except (ValueError, SyntaxError):
                used_music = [used_music]
        elif not isinstance(used_music, list):
            used_music = [used_music]
    
    try:
        existing_objects = s3.list_objects_v2(Bucket=bucket_name)
        existing_keys = {obj['Key'] for obj in existing_objects.get('Contents', [])}
    except Exception as e:
        print(f"Error listing objects in bucket {bucket_name}: {e}")
        return

    filtered_keys = set()
    
    for key in existing_keys:
        duration = extract_last_numeric_value(key)
        if duration is not None:
            if total_duration <= duration <= total_duration + 30:
                filtered_keys.add(key)
    
    if not filtered_keys:
        for key in existing_keys:
            duration = extract_last_numeric_value(key)
            if duration == 300:
                filtered_keys.add(key)

    available_keys = list(filtered_keys - set(used_music))
    if not available_keys:
        print("No new music tracks available.")
        available_keys = filtered_keys
    if available_keys is None:
        available_keys = set('Hopeful-Elegant-LaidBack_120.wav')
    file_key = random.choice(available_keys)

    try:
        s3.download_file(bucket_name, file_key, music_path)
        print(f"File downloaded successfully: {file_key}")
        
        used_music.append(file_key)
        print(f'USED_MUSIC: {used_music}')
        return used_music
    except Exception as e:
        print(f"Error downloading file {file_key}: {e}")
    
def run_ffmpeg(cmd):
    print('Running ffmpeg')
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise

def combine_audio_files(Cached, used_music, timestamp):
    print('Combining Audio')
    music_path = f'/tmp/music_{timestamp}.mp3'
    music_volume_reduced_path = f'/tmp/music_reduced_{timestamp}.mp3'
    music_length_reduced_path = f'/tmp/music_length_reduced_{timestamp}.mp3'
    silence_path = f'/tmp/silence_{timestamp}.mp3'
    voice_with_silence_path = f'/tmp/voice_with_silence_{timestamp}d.mp3'
    combined_path = f'/tmp/combined_{timestamp}.mp3'
    refresh_paths = [music_path, music_volume_reduced_path, music_length_reduced_path, silence_path, voice_with_silence_path, combined_path]
    for i in refresh_paths:
        if os.path.exists(i):
            os.remove(i)
    voice_path = f'/tmp/voice_{timestamp}.mp3' if Cached else '/var/task/voice.mp3'
    voice_duration = get_audio_duration(voice_path)
    print(f"Voice duration: {voice_duration}")
    total_duration = voice_duration + 30 
    new_music = get_music(used_music, total_duration, music_path)
    print(f'Music: {new_music}')
    print(f'MUSIC_PATH', music_path)
    print(f'VOICE_PATH', voice_path)
    # Step 0: Resample both music and voice to 44100 Hz, stereo
    

    # Step 1: Reduce the volume of the music by 10 dB
    subprocess.run([
        ffmpeg_executable , "-i", music_path, "-filter:a", "volume=-5dB", music_volume_reduced_path
    ], check=True)
    print("Step 1 Complete")
    
    # Step 2: Create 10 seconds of silence
    subprocess.run([
        ffmpeg_executable, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "10", silence_path
    ], check=True)
    print("Step 2 Complete")
    
    # Step 3: Concatenate the silence and the voice
    subprocess.run([
        ffmpeg_executable, "-i", f"concat:{silence_path}|{voice_path}", "-c", "copy", voice_with_silence_path
    ], check=True)
    print("Step 3 Complete")
    
    subprocess.run([
        ffmpeg_executable, "-i", music_volume_reduced_path, "-t", str(total_duration), music_length_reduced_path
    ], check=True)
    
    # Step 4: Overlay the voice with silence on the music
    subprocess.run([
        ffmpeg_executable, "-i", music_volume_reduced_path, "-i", voice_with_silence_path, 
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2", combined_path
    ], check=True)
    print("Step 4 Complete")
    return new_music

    
