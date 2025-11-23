import ast
import os
import random
import re
import subprocess
from typing import List, Optional

from ..config.constants import DEFAULT_MUSIC_VOLUME_REDUCTION, DEFAULT_SILENCE_DURATION
from ..config.settings import settings
from .audio_service import AudioService
from .storage_service import StorageService


class FFmpegAudioService(AudioService):
    pass
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service
        self.ffmpeg_executable = settings.FFMPEG_PATH
        self._verify_ffmpeg()
    def _verify_ffmpeg(self):
        pass
        print("--- STARTING FFMPEG DIAGNOSTICS ---", flush=True)
        if not os.path.exists(self.ffmpeg_executable):
            print(
                f"CRITICAL ERROR: ffmpeg executable NOT FOUND at {self.ffmpeg_executable}",
                flush=True,
            )
            return
        print(f"SUCCESS: ffmpeg executable FOUND at {self.ffmpeg_executable}", flush=True)
        try:
            size = os.path.getsize(self.ffmpeg_executable)
            print(f"INFO: ffmpeg size: {size} bytes.", flush=True)
            if size < 100000:
                print(f"WARNING: ffmpeg size is very small ({size} bytes)", flush=True)
        except Exception as e:
            print(f"ERROR: Could not get size of {self.ffmpeg_executable}: {e}", flush=True)
    def get_audio_duration(self, file_path: str) -> float:
        pass
        try:
            result = subprocess.run(
                [self.ffmpeg_executable, "-i", file_path, "-f", "null", "-"],
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            duration_line = [line for line in result.stderr.split("\n") if "Duration" in line][0]
            duration_str = duration_line.split(",")[0].split("Duration:")[1].strip()
            h, m, s = map(float, duration_str.split(":"))
            duration = h * 3600 + m * 60 + s
            return duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0
    def combine_voice_and_music(
        self, voice_path: str, music_list: List[str], timestamp: str, output_path: str
    ) -> List[str]:
        pass
        print("Combining Audio")
        music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
        music_volume_reduced_path = f"{settings.TEMP_DIR}/music_reduced_{timestamp}.mp3"
        music_length_reduced_path = f"{settings.TEMP_DIR}/music_length_reduced_{timestamp}.mp3"
        silence_path = f"{settings.TEMP_DIR}/silence_{timestamp}.mp3"
        voice_with_silence_path = f"{settings.TEMP_DIR}/voice_with_silence_{timestamp}.mp3"
        temp_paths = [
            music_path,
            music_volume_reduced_path,
            music_length_reduced_path,
            silence_path,
            voice_with_silence_path,
            output_path,
        ]
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
        voice_duration = self.get_audio_duration(voice_path)
        print(f"Voice duration: {voice_duration}")
        total_duration = voice_duration + 30  # Add 30 seconds buffer
        new_music = self.select_background_music(music_list, total_duration, music_path)
        print(f"Music: {new_music}")
        print(f"MUSIC_PATH: {music_path}")
        print(f"VOICE_PATH: {voice_path}")
        try:
            subprocess.run(
                [
                    self.ffmpeg_executable,
                    "-i",
                    music_path,
                    "-filter:a",
                    f"volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB",
                    music_volume_reduced_path,
                ],
                check=True,
            )
            print("Step 1 Complete: Music volume reduced")
            subprocess.run(
                [
                    self.ffmpeg_executable,
                    "-f",
                    "lavfi",
                    "-i",
                    f"anullsrc=r={settings.AUDIO_SAMPLE_RATE}:cl=stereo",
                    "-t",
                    str(DEFAULT_SILENCE_DURATION),
                    silence_path,
                ],
                check=True,
            )
            print("Step 2 Complete: Silence created")
            subprocess.run(
                [
                    self.ffmpeg_executable,
                    "-i",
                    f"concat:{silence_path}|{voice_path}",
                    "-c",
                    "copy",
                    voice_with_silence_path,
                ],
                check=True,
            )
            print("Step 3 Complete: Voice with silence")
            subprocess.run(
                [
                    self.ffmpeg_executable,
                    "-i",
                    music_volume_reduced_path,
                    "-t",
                    str(total_duration),
                    music_length_reduced_path,
                ],
                check=True,
            )
            print("Step 4 Complete: Music length adjusted")
            subprocess.run(
                [
                    self.ffmpeg_executable,
                    "-i",
                    music_length_reduced_path,
                    "-i",
                    voice_with_silence_path,
                    "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2",
                    output_path,
                ],
                check=True,
            )
            print("Step 5 Complete: Audio combined")
            for path in temp_paths[:-1]:  # Keep output_path
                if os.path.exists(path):
                    os.remove(path)
            return new_music
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg command failed: {e}")
            print(f"Command: {e.cmd}")
            print(f"Return code: {e.returncode}")
            raise
        except Exception as e:
            print(f"Error in audio combination: {e}")
            raise
    def select_background_music(
        self, used_music: List[str], duration: float, output_path: str
    ) -> List[str]:
        pass
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
        bucket_name = settings.AWS_AUDIO_BUCKET
        existing_keys = self.storage_service.list_objects(bucket_name)
        filtered_keys = set()
        for key in existing_keys:
            track_duration = self._extract_last_numeric_value(key)
            if track_duration is not None:
                if duration <= track_duration <= duration + 30:
                    filtered_keys.add(key)
        if not filtered_keys:
            for key in existing_keys:
                track_duration = self._extract_last_numeric_value(key)
                if track_duration == 300:
                    filtered_keys.add(key)
        available_keys = list(filtered_keys - set(used_music))
        if not available_keys:
            print("No new music tracks available.")
            available_keys = (
                list(filtered_keys) if filtered_keys else ["Hopeful-Elegant-LaidBack_120.wav"]
            )
        file_key = random.choice(available_keys)
        if self.storage_service.download_file(bucket_name, file_key, output_path):
            used_music.append(file_key)
            print(f"USED_MUSIC: {used_music}")
            return used_music
        else:
            raise Exception(f"Failed to download music file: {file_key}")
    def _extract_last_numeric_value(self, filename: str) -> Optional[int]:
        pass
        matches = re.findall(r"(\d+)(?=\D*$)", filename)
        if matches:
            return int(matches[-1])
        return None
