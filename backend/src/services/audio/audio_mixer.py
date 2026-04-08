"""Audio mixing pipeline (voice + music) and temp-file cleanup helper.

Phase 4 revision (iteration 2) moves ``combine_voice_and_music``,
``_prepare_mixed_audio``, and ``_append_fade_segments`` out of
:mod:`ffmpeg_audio_service` so the service there can become a true thin
facade. The cleanup helper that previously lived in this module is
retained.
"""

import glob
import os
import shutil
import subprocess
import tempfile
from typing import Callable, List, Optional

from ...config.constants import (
    DEFAULT_MUSIC_VOLUME_REDUCTION,
    DEFAULT_SILENCE_DURATION,
    HLS_FADE_DURATION_SECONDS,
)
from ...config.settings import settings
from ...exceptions import ErrorCode, ExternalServiceError
from ...utils.logging_utils import get_logger

logger = get_logger(__name__)

FFMPEG_STEP_TIMEOUT = 120
HLS_SEGMENT_DURATION = 5


def cleanup_paths(*paths: Optional[str]) -> None:
    """Best-effort deletion of every non-empty path in ``paths``."""
    for path in paths:
        if not path:
            continue
        if not os.path.exists(path):
            continue
        try:
            os.remove(path)
        except OSError as exc:
            logger.debug(
                "Failed to clean temp file",
                extra={"data": {"path": path, "error": str(exc)}},
            )


def prepare_mixed_audio(
    ffmpeg_executable: str,
    voice_path: str,
    music_list: List[str],
    timestamp: str,
    select_music: Callable[[List[str], float, str], List[str]],
    get_duration: Callable[[str], float],
) -> tuple[str, List[str]]:
    """Prepare mixed audio file (voice + music) for further processing.

    Returns ``(path_to_mixed_audio, updated_music_list)``. Intermediate
    temp files are always cleaned up; the caller owns the returned mixed
    output path.
    """
    music_path = f"{settings.TEMP_DIR}/music_{timestamp}.mp3"
    music_volume_reduced_path = f"{settings.TEMP_DIR}/music_reduced_{timestamp}.mp3"
    music_length_reduced_path = f"{settings.TEMP_DIR}/music_length_reduced_{timestamp}.mp3"
    silence_path = f"{settings.TEMP_DIR}/silence_{timestamp}.mp3"
    voice_with_silence_path = f"{settings.TEMP_DIR}/voice_with_silence_{timestamp}.mp3"
    mixed_output_path = f"{settings.TEMP_DIR}/mixed_{timestamp}.mp3"

    intermediate_paths = [
        music_path,
        music_volume_reduced_path,
        music_length_reduced_path,
        silence_path,
        voice_with_silence_path,
    ]

    for path in intermediate_paths + [mixed_output_path]:
        if os.path.exists(path):
            os.remove(path)

    try:
        voice_duration = get_duration(voice_path)
        total_duration = voice_duration + 30

        updated_music_list = select_music(music_list, total_duration, music_path)

        subprocess.run(
            [
                ffmpeg_executable,
                "-i",
                music_path,
                "-filter:a",
                f"volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB",
                music_volume_reduced_path,
            ],
            check=True,
            capture_output=True,
            timeout=FFMPEG_STEP_TIMEOUT,
        )

        subprocess.run(
            [
                ffmpeg_executable,
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=r={settings.AUDIO_SAMPLE_RATE}:cl=stereo",
                "-t",
                str(DEFAULT_SILENCE_DURATION),
                silence_path,
            ],
            check=True,
            capture_output=True,
            timeout=FFMPEG_STEP_TIMEOUT,
        )

        subprocess.run(
            [
                ffmpeg_executable,
                "-i",
                f"concat:{silence_path}|{voice_path}",
                "-c",
                "copy",
                voice_with_silence_path,
            ],
            check=True,
            capture_output=True,
            timeout=FFMPEG_STEP_TIMEOUT,
        )

        subprocess.run(
            [
                ffmpeg_executable,
                "-i",
                music_volume_reduced_path,
                "-t",
                str(total_duration),
                music_length_reduced_path,
            ],
            check=True,
            capture_output=True,
            timeout=FFMPEG_STEP_TIMEOUT,
        )

        subprocess.run(
            [
                ffmpeg_executable,
                "-i",
                music_length_reduced_path,
                "-i",
                voice_with_silence_path,
                "-filter_complex",
                "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2:normalize=0",
                mixed_output_path,
            ],
            check=True,
            capture_output=True,
            timeout=FFMPEG_STEP_TIMEOUT,
        )

        return mixed_output_path, updated_music_list

    finally:
        cleanup_paths(*intermediate_paths)


def combine_voice_and_music(
    ffmpeg_executable: str,
    voice_path: str,
    music_list: List[str],
    timestamp: str,
    output_path: str,
    select_music: Callable[[List[str], float, str], List[str]],
    get_duration: Callable[[str], float],
) -> List[str]:
    """Combine voice and music into a single MP3 file at ``output_path``."""
    logger.info("Combining audio")
    mixed_audio_path: Optional[str] = None
    try:
        mixed_audio_path, updated_music_list = prepare_mixed_audio(
            ffmpeg_executable,
            voice_path,
            music_list,
            timestamp,
            select_music,
            get_duration,
        )
        if os.path.exists(mixed_audio_path):
            shutil.move(mixed_audio_path, output_path)
            mixed_audio_path = None
        return updated_music_list
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg command failed: {e.cmd}, return code: {e.returncode}")
        raise
    except Exception as e:
        logger.error(f"Error in audio combination: {e}")
        raise
    finally:
        cleanup_paths(mixed_audio_path)


def append_fade_segments(
    ffmpeg_executable: str,
    hls_service: object,
    get_duration: Callable[[str], float],
    music_path: str,
    total_streamed_duration: float,
    user_id: str,
    job_id: str,
    total_segments: int,
    segment_durations: List[float],
) -> int:
    """Append music-only fade-out segments after the last streamed segment.

    Returns new total segment count.
    """
    fade_duration = HLS_FADE_DURATION_SECONDS

    music_file_duration = get_duration(music_path)
    if music_file_duration <= 0:
        logger.warning("Could not determine music duration, skipping fade segments")
        return total_segments

    music_offset = total_streamed_duration % music_file_duration

    logger.info(
        f"Appending fade segments: music_offset={music_offset:.1f}s, "
        f"fade_duration={fade_duration}s, starting at segment {total_segments}"
    )

    fade_output_dir = tempfile.mkdtemp(prefix="hls_fade_")
    fade_segment_pattern = os.path.join(fade_output_dir, "segment_%03d.ts")
    fade_playlist_path = os.path.join(fade_output_dir, "playlist.m3u8")

    ffmpeg_fade_cmd = [
        ffmpeg_executable,
        "-ss",
        str(music_offset),
        "-stream_loop",
        "-1",
        "-i",
        music_path,
        "-t",
        str(fade_duration),
        "-filter_complex",
        f"[0:a]volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB,afade=t=out:st=0:d={fade_duration}[out]",
        "-map",
        "[out]",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "128k",
        "-f",
        "hls",
        "-hls_time",
        str(HLS_SEGMENT_DURATION),
        "-hls_segment_type",
        "mpegts",
        "-hls_flags",
        "independent_segments",
        "-hls_segment_filename",
        fade_segment_pattern,
        "-hls_list_size",
        "0",
        fade_playlist_path,
    ]

    try:
        subprocess.run(
            ffmpeg_fade_cmd, check=True, capture_output=True, timeout=FFMPEG_STEP_TIMEOUT
        )

        fade_segments = sorted(glob.glob(os.path.join(fade_output_dir, "segment_*.ts")))
        for i, fade_segment in enumerate(fade_segments):
            segment_index = total_segments + i

            seg_duration = get_duration(fade_segment)
            if seg_duration == 0:
                seg_duration = float(HLS_SEGMENT_DURATION)

            success = hls_service.upload_segment_from_file(  # type: ignore[attr-defined]
                user_id, job_id, segment_index, fade_segment
            )
            if not success:
                raise ExternalServiceError(
                    f"Failed to upload fade segment {segment_index}",
                    ErrorCode.STORAGE_FAILURE,
                    details=f"user_id={user_id}, job_id={job_id}",
                )
            segment_durations.append(seg_duration)
            logger.info(f"Uploaded fade segment {segment_index}")

        return len(segment_durations)
    except Exception as e:
        logger.error(f"Failed to append fade segments: {e}")
        return total_segments
    finally:
        shutil.rmtree(fade_output_dir, ignore_errors=True)
