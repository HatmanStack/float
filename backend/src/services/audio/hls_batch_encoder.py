"""Cached-TTS HLS batch encoder.

Phase 4 revision (iteration 2) moves ``combine_voice_and_music_hls`` out
of :mod:`ffmpeg_audio_service` into its own module. The facade now
delegates the cached-TTS path here.
"""

import glob
import os
import shutil
import subprocess
import tempfile
from typing import Callable, List, Optional

from ...exceptions import AudioProcessingError, ErrorCode, ExternalServiceError
from ...utils.logging_utils import get_logger
from .audio_mixer import cleanup_paths, prepare_mixed_audio

logger = get_logger(__name__)

HLS_SEGMENT_DURATION = 5
FFMPEG_HLS_TIMEOUT = 300


def combine_voice_and_music_hls(
    ffmpeg_executable: str,
    hls_service: object,
    select_music: Callable[[List[str], float, str], List[str]],
    get_duration: Callable[[str], float],
    voice_path: str,
    music_list: List[str],
    timestamp: str,
    user_id: str,
    job_id: str,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
) -> tuple[List[str], int, List[float]]:
    """Combine voice and music, outputting HLS segments progressively."""
    if not hls_service:
        raise ValueError("HLS service required for HLS output mode")

    logger.info("Starting HLS audio generation", extra={"data": {"job_id": job_id}})

    hls_output_dir = tempfile.mkdtemp(prefix="hls_")
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

        total_duration = get_duration(mixed_audio_path)
        estimated_segments = int(total_duration / HLS_SEGMENT_DURATION) + 1
        logger.info(
            "Audio prepared for HLS",
            extra={"data": {"duration": total_duration, "est_segments": estimated_segments}},
        )

        playlist_path = os.path.join(hls_output_dir, "playlist.m3u8")
        segment_pattern = os.path.join(hls_output_dir, "segment_%03d.ts")

        ffmpeg_cmd = [
            ffmpeg_executable,
            "-i",
            mixed_audio_path,
            "-c:a",
            "aac",
            "-f",
            "hls",
            "-hls_time",
            str(HLS_SEGMENT_DURATION),
            "-hls_segment_type",
            "mpegts",
            "-hls_flags",
            "independent_segments",
            "-hls_segment_filename",
            segment_pattern,
            "-hls_list_size",
            "0",
            playlist_path,
        ]

        logger.debug("Running FFmpeg HLS command", extra={"data": {"cmd": " ".join(ffmpeg_cmd)}})

        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, timeout=FFMPEG_HLS_TIMEOUT)
        except subprocess.TimeoutExpired as e:
            logger.error(
                "FFmpeg HLS generation timed out",
                extra={"data": {"timeout": FFMPEG_HLS_TIMEOUT, "cmd": " ".join(ffmpeg_cmd)}},
            )
            raise AudioProcessingError(
                f"FFmpeg HLS generation timed out after {FFMPEG_HLS_TIMEOUT}s"
            ) from e

        segment_files = sorted(glob.glob(os.path.join(hls_output_dir, "segment_*.ts")))
        segment_durations: List[float] = []
        segments_uploaded = 0

        for i, segment_file in enumerate(segment_files):
            seg_duration = get_duration(segment_file)
            if seg_duration == 0:
                seg_duration = float(HLS_SEGMENT_DURATION)
            segment_durations.append(seg_duration)

            success = hls_service.upload_segment_from_file(  # type: ignore[attr-defined]
                user_id, job_id, i, segment_file
            )
            if not success:
                raise ExternalServiceError(
                    f"Failed to upload segment {i}",
                    ErrorCode.STORAGE_FAILURE,
                    details=f"user_id={user_id}, job_id={job_id}",
                )

            segments_uploaded += 1

            playlist_content = hls_service.generate_live_playlist(  # type: ignore[attr-defined]
                user_id, job_id, segments_uploaded, segment_durations, is_complete=False
            )
            hls_service.upload_playlist(user_id, job_id, playlist_content)  # type: ignore[attr-defined]

            if progress_callback:
                progress_callback(segments_uploaded, estimated_segments)

            logger.debug(
                "Uploaded segment", extra={"data": {"segment": i, "duration": seg_duration}}
            )

        hls_service.finalize_playlist(  # type: ignore[attr-defined]
            user_id, job_id, segments_uploaded, segment_durations
        )

        logger.info(
            "HLS generation complete",
            extra={"data": {"job_id": job_id, "segments": segments_uploaded}},
        )

        return (updated_music_list, segments_uploaded, segment_durations)

    finally:
        if os.path.exists(hls_output_dir):
            shutil.rmtree(hls_output_dir, ignore_errors=True)
        cleanup_paths(mixed_audio_path)
