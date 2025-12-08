import ast
import glob
import os
import random
import re
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING, Callable, List, Optional

from ..config.constants import DEFAULT_MUSIC_VOLUME_REDUCTION, DEFAULT_SILENCE_DURATION
from ..config.settings import settings
from ..utils.logging_utils import get_logger
from .audio_service import AudioService
from .storage_service import StorageService

if TYPE_CHECKING:
    from .hls_service import HLSService

logger = get_logger(__name__)

# HLS Configuration
HLS_SEGMENT_DURATION = 5  # seconds


class FFmpegAudioService(AudioService):

    def __init__(
        self,
        storage_service: StorageService,
        hls_service: Optional["HLSService"] = None,
    ):
        self.storage_service = storage_service
        self.hls_service = hls_service
        self.ffmpeg_executable = settings.FFMPEG_PATH
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        print("--- STARTING FFMPEG DIAGNOSTICS ---", flush=True)
        if not os.path.exists(self.ffmpeg_executable):
            print(
                f"CRITICAL ERROR: ffmpeg executable NOT FOUND at {self.ffmpeg_executable}",
                flush=True,
            )
            return
        print(
            f"SUCCESS: ffmpeg executable FOUND at {self.ffmpeg_executable}", flush=True
        )
        try:
            size = os.path.getsize(self.ffmpeg_executable)
            print(f"INFO: ffmpeg size: {size} bytes.", flush=True)
            if size < 100000:
                print(f"WARNING: ffmpeg size is very small ({size} bytes)", flush=True)
        except Exception as e:
            print(
                f"ERROR: Could not get size of {self.ffmpeg_executable}: {e}",
                flush=True,
            )

    def get_audio_duration(self, file_path: str) -> float:
        try:
            result = subprocess.run(
                [self.ffmpeg_executable, "-i", file_path, "-f", "null", "-"],
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            duration_line = [
                line for line in result.stderr.split("\n") if "Duration" in line
            ][0]
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
        """Combine voice and music into a single MP3 file."""
        print("Combining Audio")
        music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
        music_volume_reduced_path = f"{settings.TEMP_DIR}/music_reduced_{timestamp}.mp3"
        music_length_reduced_path = (
            f"{settings.TEMP_DIR}/music_length_reduced_{timestamp}.mp3"
        )
        silence_path = f"{settings.TEMP_DIR}/silence_{timestamp}.mp3"
        voice_with_silence_path = (
            f"{settings.TEMP_DIR}/voice_with_silence_{timestamp}.mp3"
        )
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

    def combine_voice_and_music_hls(
        self,
        voice_path: str,
        music_list: List[str],
        timestamp: str,
        user_id: str,
        job_id: str,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    ) -> tuple[List[str], int, List[float]]:
        """
        Combine voice and music, outputting HLS segments progressively.

        Args:
            voice_path: Path to voice audio file
            music_list: List of previously used music tracks
            timestamp: Unique timestamp for temp files
            user_id: User identifier
            job_id: Job identifier
            progress_callback: Optional callback(segments_completed, segments_total)

        Returns:
            Tuple of (updated music list, total segments, segment durations)
        """
        if not self.hls_service:
            raise ValueError("HLS service required for HLS output mode")

        logger.info("Starting HLS audio generation", extra={"data": {"job_id": job_id}})

        # Create temp directory for HLS output
        hls_output_dir = tempfile.mkdtemp(prefix="hls_")

        try:
            # Step 1-4: Prepare mixed audio (same as regular combine)
            mixed_audio_path = self._prepare_mixed_audio(
                voice_path, music_list, timestamp
            )

            # Get duration to estimate total segments
            total_duration = self.get_audio_duration(mixed_audio_path)
            estimated_segments = int(total_duration / HLS_SEGMENT_DURATION) + 1
            logger.info(
                "Audio prepared for HLS",
                extra={"data": {"duration": total_duration, "est_segments": estimated_segments}}
            )

            # Step 5: Output as HLS segments
            playlist_path = os.path.join(hls_output_dir, "playlist.m3u8")
            segment_pattern = os.path.join(hls_output_dir, "segment_%03d.ts")

            # Run FFmpeg with HLS output
            ffmpeg_cmd = [
                self.ffmpeg_executable,
                "-i", mixed_audio_path,
                "-f", "hls",
                "-hls_time", str(HLS_SEGMENT_DURATION),
                "-hls_segment_type", "mpegts",
                "-hls_flags", "independent_segments",
                "-hls_segment_filename", segment_pattern,
                "-hls_list_size", "0",  # Keep all segments in playlist
                playlist_path,
            ]

            logger.debug("Running FFmpeg HLS command", extra={"data": {"cmd": " ".join(ffmpeg_cmd)}})

            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

            # Now upload segments progressively
            segment_files = sorted(glob.glob(os.path.join(hls_output_dir, "segment_*.ts")))
            segment_durations = []
            segments_uploaded = 0

            for i, segment_file in enumerate(segment_files):
                # Get segment duration
                seg_duration = self.get_audio_duration(segment_file)
                if seg_duration == 0:
                    seg_duration = float(HLS_SEGMENT_DURATION)
                segment_durations.append(seg_duration)

                # Upload segment
                success = self.hls_service.upload_segment_from_file(
                    user_id, job_id, i, segment_file
                )
                if not success:
                    raise Exception(f"Failed to upload segment {i}")

                segments_uploaded += 1

                # Generate and upload updated playlist
                playlist_content = self.hls_service.generate_live_playlist(
                    user_id, job_id, segments_uploaded, segment_durations, is_complete=False
                )
                self.hls_service.upload_playlist(user_id, job_id, playlist_content)

                # Call progress callback
                if progress_callback:
                    progress_callback(segments_uploaded, estimated_segments)

                logger.debug(
                    "Uploaded segment",
                    extra={"data": {"segment": i, "duration": seg_duration}}
                )

            # Finalize playlist with ENDLIST
            self.hls_service.finalize_playlist(user_id, job_id, segments_uploaded, segment_durations)

            logger.info(
                "HLS generation complete",
                extra={"data": {"job_id": job_id, "segments": segments_uploaded}}
            )

            # Return the music list that was selected
            return (music_list, segments_uploaded, segment_durations)

        finally:
            # Cleanup temp directory
            if os.path.exists(hls_output_dir):
                shutil.rmtree(hls_output_dir, ignore_errors=True)

    def _prepare_mixed_audio(
        self, voice_path: str, music_list: List[str], timestamp: str
    ) -> str:
        """
        Prepare mixed audio file (voice + music) for further processing.
        Returns path to the mixed audio file.
        """
        music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
        music_volume_reduced_path = f"{settings.TEMP_DIR}/music_reduced_{timestamp}.mp3"
        music_length_reduced_path = f"{settings.TEMP_DIR}/music_length_reduced_{timestamp}.mp3"
        silence_path = f"{settings.TEMP_DIR}/silence_{timestamp}.mp3"
        voice_with_silence_path = f"{settings.TEMP_DIR}/voice_with_silence_{timestamp}.mp3"
        mixed_output_path = f"{settings.TEMP_DIR}/mixed_{timestamp}.mp3"

        # Clean up any existing files
        temp_paths = [
            music_path, music_volume_reduced_path, music_length_reduced_path,
            silence_path, voice_with_silence_path, mixed_output_path
        ]
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)

        voice_duration = self.get_audio_duration(voice_path)
        total_duration = voice_duration + 30

        # Select and download background music
        self.select_background_music(music_list, total_duration, music_path)

        # Step 1: Reduce music volume
        subprocess.run(
            [
                self.ffmpeg_executable,
                "-i", music_path,
                "-filter:a", f"volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB",
                music_volume_reduced_path,
            ],
            check=True,
            capture_output=True,
        )

        # Step 2: Create silence
        subprocess.run(
            [
                self.ffmpeg_executable,
                "-f", "lavfi",
                "-i", f"anullsrc=r={settings.AUDIO_SAMPLE_RATE}:cl=stereo",
                "-t", str(DEFAULT_SILENCE_DURATION),
                silence_path,
            ],
            check=True,
            capture_output=True,
        )

        # Step 3: Add silence to voice
        subprocess.run(
            [
                self.ffmpeg_executable,
                "-i", f"concat:{silence_path}|{voice_path}",
                "-c", "copy",
                voice_with_silence_path,
            ],
            check=True,
            capture_output=True,
        )

        # Step 4: Trim music to duration
        subprocess.run(
            [
                self.ffmpeg_executable,
                "-i", music_volume_reduced_path,
                "-t", str(total_duration),
                music_length_reduced_path,
            ],
            check=True,
            capture_output=True,
        )

        # Step 5: Mix voice and music
        subprocess.run(
            [
                self.ffmpeg_executable,
                "-i", music_length_reduced_path,
                "-i", voice_with_silence_path,
                "-filter_complex",
                "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2",
                mixed_output_path,
            ],
            check=True,
            capture_output=True,
        )

        # Cleanup intermediate files (keep mixed output)
        for path in [music_path, music_volume_reduced_path, music_length_reduced_path,
                     silence_path, voice_with_silence_path]:
            if os.path.exists(path):
                os.remove(path)

        return mixed_output_path

    def select_background_music(
        self, used_music: List[str], duration: float, output_path: str
    ) -> List[str]:
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
                list(filtered_keys)
                if filtered_keys
                else ["Hopeful-Elegant-LaidBack_120.wav"]
            )
        file_key = random.choice(available_keys)
        if self.storage_service.download_file(bucket_name, file_key, output_path):
            used_music.append(file_key)
            print(f"USED_MUSIC: {used_music}")
            return used_music
        else:
            raise Exception(f"Failed to download music file: {file_key}")

    def _extract_last_numeric_value(self, filename: str) -> Optional[int]:
        matches = re.findall(r"(\d+)(?=\D*$)", filename)
        if matches:
            return int(matches[-1])
        return None
