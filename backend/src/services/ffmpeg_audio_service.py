import ast
import glob
import os
import random
import re
import shutil
import subprocess
import tempfile
import threading
import time
from typing import TYPE_CHECKING, Callable, Iterator, List, Optional

from ..config.constants import (
    DEFAULT_MUSIC_VOLUME_REDUCTION,
    DEFAULT_SILENCE_DURATION,
    DEFAULT_VOICE_BOOST,
)
from ..config.settings import settings
from ..exceptions import AudioProcessingError
from ..utils.cache import music_list_cache
from ..utils.logging_utils import get_logger
from .audio_service import AudioService
from .storage_service import StorageService

if TYPE_CHECKING:
    from .hls_service import HLSService

logger = get_logger(__name__)

# HLS Configuration
HLS_SEGMENT_DURATION = 5  # seconds

# FFmpeg timeout configuration (seconds)
FFMPEG_STEP_TIMEOUT = 120  # 2 minutes per individual step
FFMPEG_HLS_TIMEOUT = 300   # 5 minutes for full HLS generation


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
        if not os.path.exists(self.ffmpeg_executable):
            logger.error(f"ffmpeg executable not found at {self.ffmpeg_executable}")
            return
        logger.debug(f"ffmpeg executable found at {self.ffmpeg_executable}")
        try:
            size = os.path.getsize(self.ffmpeg_executable)
            if size < 100000:
                logger.warning(f"ffmpeg size is very small ({size} bytes)")
        except Exception as e:
            logger.error(f"Could not get size of {self.ffmpeg_executable}: {e}")

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
            logger.warning(f"Error getting audio duration: {e}")
            return 0.0

    def combine_voice_and_music(
        self, voice_path: str, music_list: List[str], timestamp: str, output_path: str
    ) -> List[str]:
        """Combine voice and music into a single MP3 file."""
        logger.info("Combining audio")
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
        logger.debug(f"Voice duration: {voice_duration}")
        total_duration = voice_duration + 30  # Add 30 seconds buffer
        new_music = self.select_background_music(music_list, total_duration, music_path)
        logger.debug(f"Selected music: {new_music}")
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
            logger.debug("Step 1: Music volume reduced")
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
            logger.debug("Step 2: Silence created")
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
            logger.debug("Step 3: Voice with silence")
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
            logger.debug("Step 4: Music length adjusted")
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
            logger.debug("Step 5: Audio combined")
            for path in temp_paths[:-1]:  # Keep output_path
                if os.path.exists(path):
                    os.remove(path)
            return new_music
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg command failed: {e.cmd}, return code: {e.returncode}")
            raise
        except Exception as e:
            logger.error(f"Error in audio combination: {e}")
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
        mixed_audio_path = None

        try:
            # Step 1-4: Prepare mixed audio (same as regular combine)
            mixed_audio_path, updated_music_list = self._prepare_mixed_audio(
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
                "-c:a", "aac",  # AAC codec required for HLS browser compatibility
                "-f", "hls",
                "-hls_time", str(HLS_SEGMENT_DURATION),
                "-hls_segment_type", "mpegts",
                "-hls_flags", "independent_segments",
                "-hls_segment_filename", segment_pattern,
                "-hls_list_size", "0",  # Keep all segments in playlist
                playlist_path,
            ]

            logger.debug("Running FFmpeg HLS command", extra={"data": {"cmd": " ".join(ffmpeg_cmd)}})

            try:
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True, timeout=FFMPEG_HLS_TIMEOUT)
            except subprocess.TimeoutExpired as e:
                logger.error(
                    "FFmpeg HLS generation timed out",
                    extra={"data": {"timeout": FFMPEG_HLS_TIMEOUT, "cmd": " ".join(ffmpeg_cmd)}}
                )
                raise Exception(f"FFmpeg HLS generation timed out after {FFMPEG_HLS_TIMEOUT}s") from e

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

            # Return the updated music list from _prepare_mixed_audio
            return (updated_music_list, segments_uploaded, segment_durations)

        finally:
            # Cleanup temp directory
            if os.path.exists(hls_output_dir):
                shutil.rmtree(hls_output_dir, ignore_errors=True)
            # Cleanup mixed audio file
            if mixed_audio_path and os.path.exists(mixed_audio_path):
                try:
                    os.remove(mixed_audio_path)
                except OSError:
                    pass

    def _prepare_mixed_audio(
        self, voice_path: str, music_list: List[str], timestamp: str
    ) -> tuple[str, List[str]]:
        """
        Prepare mixed audio file (voice + music) for further processing.
        Returns tuple of (path to mixed audio file, updated music list).
        """
        music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
        music_volume_reduced_path = f"{settings.TEMP_DIR}/music_reduced_{timestamp}.mp3"
        music_length_reduced_path = f"{settings.TEMP_DIR}/music_length_reduced_{timestamp}.mp3"
        silence_path = f"{settings.TEMP_DIR}/silence_{timestamp}.mp3"
        voice_with_silence_path = f"{settings.TEMP_DIR}/voice_with_silence_{timestamp}.mp3"
        mixed_output_path = f"{settings.TEMP_DIR}/mixed_{timestamp}.mp3"

        # Intermediate files to clean up (excludes mixed_output_path which is returned)
        intermediate_paths = [
            music_path, music_volume_reduced_path, music_length_reduced_path,
            silence_path, voice_with_silence_path
        ]

        # Clean up any existing files
        for path in intermediate_paths + [mixed_output_path]:
            if os.path.exists(path):
                os.remove(path)

        try:
            voice_duration = self.get_audio_duration(voice_path)
            total_duration = voice_duration + 30

            # Select and download background music
            updated_music_list = self.select_background_music(music_list, total_duration, music_path)

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
                timeout=FFMPEG_STEP_TIMEOUT,
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
                timeout=FFMPEG_STEP_TIMEOUT,
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
                timeout=FFMPEG_STEP_TIMEOUT,
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
                timeout=FFMPEG_STEP_TIMEOUT,
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
                timeout=FFMPEG_STEP_TIMEOUT,
            )

            return mixed_output_path, updated_music_list

        finally:
            # Cleanup intermediate files (always, even on failure)
            for path in intermediate_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass

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

        # Use cached music list to avoid repeated S3 API calls
        cache_key = f"music_list:{bucket_name}"
        existing_keys = music_list_cache.get(cache_key)
        if existing_keys is None:
            existing_keys = self.storage_service.list_objects(bucket_name)
            music_list_cache.set(cache_key, existing_keys)
            logger.debug("Cached music list from S3", extra={"data": {"count": len(existing_keys)}})
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
            logger.debug("No new music tracks available, reusing from pool")
            available_keys = (
                list(filtered_keys)
                if filtered_keys
                else ["Hopeful-Elegant-LaidBack_120.wav"]
            )
        file_key = random.choice(available_keys)
        if self.storage_service.download_file(bucket_name, file_key, output_path):
            used_music.append(file_key)
            return used_music
        else:
            raise AudioProcessingError(
                f"Failed to download music file: {file_key}",
                details=f"bucket={bucket_name}, key={file_key}",
            )

    def _extract_last_numeric_value(self, filename: str) -> Optional[int]:
        matches = re.findall(r"(\d+)(?=\D*$)", filename)
        if matches:
            return int(matches[-1])
        return None

    def _get_audio_duration_from_file(self, audio_path: str) -> float:
        """Get audio duration using ffmpeg (ffprobe not available in Lambda layer)."""
        try:
            # Use ffmpeg to probe the file - same approach as get_audio_duration
            result = subprocess.run(
                [self.ffmpeg_executable, "-i", audio_path, "-f", "null", "-"],
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
            # Parse duration from stderr output
            for line in result.stderr.split("\n"):
                if "Duration" in line:
                    duration_str = line.split(",")[0].split("Duration:")[1].strip()
                    h, m, s = map(float, duration_str.split(":"))
                    return h * 3600 + m * 60 + s
            return 0.0
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return 0.0

    def _apply_fade_to_segments(
        self,
        hls_output_dir: str,
        music_path: str,
        voice_temp_path: str,
        actual_voice_duration: float,
        user_id: str,
        job_id: str,
        total_segments: int,
        segment_durations: List[float],
    ) -> int:
        """Re-process the last few segments to add proper fade. Returns new total segment count."""
        trailing_music_seconds = 20
        fade_duration = 20
        total_duration = DEFAULT_SILENCE_DURATION + actual_voice_duration + trailing_music_seconds
        fade_start = total_duration - fade_duration

        # Determine which segments need fade (last ~25 seconds worth)
        segments_to_redo = 5  # ~25 seconds at 5 sec/segment
        first_segment_to_redo = max(0, total_segments - segments_to_redo)
        redo_start_time = sum(segment_durations[:first_segment_to_redo])

        logger.info(f"Applying fade: redoing segments {first_segment_to_redo}-{total_segments-1}, "
                    f"fade_start={fade_start:.1f}s, total={total_duration:.1f}s")

        # Generate faded audio for the tail portion
        fade_output_dir = tempfile.mkdtemp(prefix="hls_fade_")
        fade_segment_pattern = os.path.join(fade_output_dir, "segment_%03d.ts")
        fade_playlist_path = os.path.join(fade_output_dir, "playlist.m3u8")

        # Adjusted fade_start relative to the redo portion
        adjusted_fade_start = fade_start - redo_start_time
        if adjusted_fade_start < 0:
            adjusted_fade_start = 0

        ffmpeg_fade_cmd = [
            self.ffmpeg_executable,
            "-ss", str(redo_start_time - DEFAULT_SILENCE_DURATION) if redo_start_time > DEFAULT_SILENCE_DURATION else "0",
            "-i", voice_temp_path,
            "-stream_loop", "-1", "-ss", str(redo_start_time), "-i", music_path,
            "-filter_complex",
            f"[0:a]volume={DEFAULT_VOICE_BOOST}dB,"
            f"adelay={int(max(0, DEFAULT_SILENCE_DURATION - redo_start_time) * 1000)}|{int(max(0, DEFAULT_SILENCE_DURATION - redo_start_time) * 1000)},"
            f"apad=pad_dur={trailing_music_seconds}[voice_padded];"
            f"[1:a]volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB[music];"
            f"[voice_padded][music]amix=inputs=2:duration=first:dropout_transition=2,"
            f"afade=t=out:st={adjusted_fade_start}:d={fade_duration}[out]",
            "-map", "[out]",
            "-c:a", "aac",
            "-f", "hls",
            "-hls_time", str(HLS_SEGMENT_DURATION),
            "-hls_segment_type", "mpegts",
            "-hls_flags", "independent_segments",
            "-hls_segment_filename", fade_segment_pattern,
            "-hls_list_size", "0",
            fade_playlist_path,
        ]

        try:
            subprocess.run(ffmpeg_fade_cmd, check=True, capture_output=True)

            # Re-upload the faded segments (replace existing + add new ones for fadeout)
            fade_segments = sorted(glob.glob(os.path.join(fade_output_dir, "segment_*.ts")))
            for i, fade_segment in enumerate(fade_segments):
                segment_index = first_segment_to_redo + i

                seg_duration = self.get_audio_duration(fade_segment)
                if seg_duration == 0:
                    seg_duration = float(HLS_SEGMENT_DURATION)

                self.hls_service.upload_segment_from_file(user_id, job_id, segment_index, fade_segment)

                if segment_index >= total_segments:
                    logger.info(f"Uploaded new faded segment {segment_index} (extending for fadeout)")
                    segment_durations.append(seg_duration)
                else:
                    logger.info(f"Re-uploaded faded segment {segment_index}")
                    segment_durations[segment_index] = seg_duration

            return len(segment_durations)
        except Exception as e:
            logger.error(f"Failed to apply fade: {e}")
            return total_segments
        finally:
            shutil.rmtree(fade_output_dir, ignore_errors=True)

    def process_stream_to_hls(
        self,
        voice_generator: Iterator[bytes],
        music_path: str,
        user_id: str,
        job_id: str,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        estimated_voice_duration: float = 60.0,
    ) -> tuple[int, List[float]]:
        """
        Stream TTS to HLS segments, then apply fade to final segments.

        Strategy:
        1. Stream without fade for fast delivery
        2. Save TTS audio to temp file while streaming
        3. After TTS completes, re-process last few segments with proper fade

        Args:
            voice_generator: Iterator yielding audio chunks from TTS
            music_path: Path to downloaded background music file
            user_id: User identifier
            job_id: Job identifier
            progress_callback: Optional callback(segments_completed, segments_total)
            estimated_voice_duration: Fallback if duration detection fails

        Returns:
            Tuple of (total_segments, segment_durations)
        """
        if not self.hls_service:
            raise ValueError("HLS service required for streaming HLS output")

        logger.info("Starting streaming HLS generation", extra={"data": {"job_id": job_id}})

        hls_output_dir = tempfile.mkdtemp(prefix="hls_stream_")
        playlist_path = os.path.join(hls_output_dir, "playlist.m3u8")
        segment_pattern = os.path.join(hls_output_dir, "segment_%03d.ts")

        # Save TTS to temp file for later fade processing
        voice_temp_path = os.path.join(hls_output_dir, "voice.mp3")

        # Stream WITHOUT fade - we'll add fade to final segments later
        trailing_music_seconds = 20
        ffmpeg_cmd = [
            self.ffmpeg_executable,
            "-f", "mp3", "-i", "pipe:0",
            "-stream_loop", "-1", "-i", music_path,
            "-filter_complex",
            f"[0:a]volume={DEFAULT_VOICE_BOOST}dB,"
            f"adelay={int(DEFAULT_SILENCE_DURATION * 1000)}|{int(DEFAULT_SILENCE_DURATION * 1000)},"
            f"apad=pad_dur={trailing_music_seconds}[voice_padded];"
            f"[1:a]volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB[music];"
            f"[voice_padded][music]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-c:a", "aac",
            "-f", "hls",
            "-hls_time", str(HLS_SEGMENT_DURATION),
            "-hls_segment_type", "mpegts",
            "-hls_flags", "independent_segments",
            "-hls_segment_filename", segment_pattern,
            "-hls_list_size", "0",
            playlist_path,
        ]

        logger.info("Starting FFmpeg streaming process (no fade - will add later)")

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # State for watcher thread
        state = {
            "uploading": True,
            "segments_uploaded": 0,
            "segment_durations": [],
            "error": None,
        }
        uploaded_segments = set()

        def upload_watcher():
            """Watch for new segments and upload them progressively."""
            while state["uploading"] or os.path.exists(hls_output_dir):
                try:
                    segment_files = sorted(glob.glob(os.path.join(hls_output_dir, "segment_*.ts")))
                    for segment_file in segment_files:
                        if segment_file in uploaded_segments:
                            continue

                        # Wait for file to be fully written
                        if not os.path.exists(segment_file):
                            continue
                        file_size = os.path.getsize(segment_file)
                        if file_size == 0:
                            continue

                        # Extract segment index
                        segment_name = os.path.basename(segment_file)
                        segment_index = int(segment_name.replace("segment_", "").replace(".ts", ""))

                        # Get duration
                        seg_duration = self.get_audio_duration(segment_file)
                        if seg_duration == 0:
                            seg_duration = float(HLS_SEGMENT_DURATION)

                        while len(state["segment_durations"]) <= segment_index:
                            state["segment_durations"].append(float(HLS_SEGMENT_DURATION))
                        state["segment_durations"][segment_index] = seg_duration

                        # Upload segment
                        if self.hls_service.upload_segment_from_file(user_id, job_id, segment_index, segment_file):
                            uploaded_segments.add(segment_file)
                            state["segments_uploaded"] += 1

                            # Update playlist
                            playlist_content = self.hls_service.generate_live_playlist(
                                user_id, job_id,
                                state["segments_uploaded"],
                                state["segment_durations"][:state["segments_uploaded"]],
                                is_complete=False
                            )
                            self.hls_service.upload_playlist(user_id, job_id, playlist_content)

                            if progress_callback:
                                progress_callback(state["segments_uploaded"], None)

                            logger.info(f"Uploaded segment {segment_index}")
                        else:
                            logger.error(f"Failed to upload segment {segment_index}")

                    if not state["uploading"]:
                        break
                    time.sleep(0.3)
                except Exception as e:
                    logger.error(f"Watcher error: {e}")
                    state["error"] = e
                    break

        watcher_thread = threading.Thread(target=upload_watcher)
        watcher_thread.start()

        try:
            # Stream voice data to FFmpeg stdin AND save to temp file
            with open(voice_temp_path, "wb") as voice_file:
                for chunk in voice_generator:
                    # Check if FFmpeg is still running before writing
                    if process.poll() is not None:
                        stderr = process.stderr.read().decode()
                        logger.error(f"FFmpeg exited early: {stderr}")
                        raise Exception(f"FFmpeg exited unexpectedly: {stderr}")
                    process.stdin.write(chunk)
                    process.stdin.flush()
                    voice_file.write(chunk)  # Save for fade processing

            process.stdin.close()
            process.wait()

            if process.returncode != 0:
                stderr = process.stderr.read().decode()
                raise Exception(f"FFmpeg failed: {stderr}")

        except BrokenPipeError as e:
            stderr = process.stderr.read().decode() if process.stderr else "unknown"
            logger.error(f"FFmpeg broken pipe - stderr: {stderr}")
            raise Exception(f"FFmpeg pipe closed: {stderr}") from e
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            if process.poll() is None:
                process.kill()
            raise
        finally:
            state["uploading"] = False
            watcher_thread.join(timeout=30)

            if state["error"]:
                raise state["error"]

        # Get actual voice duration and apply fade to final segments
        actual_voice_duration = self._get_audio_duration_from_file(voice_temp_path)
        if actual_voice_duration > 0:
            logger.info(f"Voice duration: {actual_voice_duration:.1f}s, applying fade to final segments")
            state["segments_uploaded"] = self._apply_fade_to_segments(
                hls_output_dir,
                music_path,
                voice_temp_path,
                actual_voice_duration,
                user_id,
                job_id,
                state["segments_uploaded"],
                state["segment_durations"],
            )

        # Finalize playlist with updated segments (including any new fade segments)
        self.hls_service.finalize_playlist(
            user_id, job_id, state["segments_uploaded"], state["segment_durations"]
        )

        # Cleanup
        shutil.rmtree(hls_output_dir, ignore_errors=True)

        return (state["segments_uploaded"], state["segment_durations"])
