"""Streaming TTS-to-HLS encoder.

Phase 4 revision (iteration 2) moves the full ``process_stream_to_hls``
pipeline out of :mod:`ffmpeg_audio_service` into this module. The facade
now delegates the streaming path here.

Tests that previously patched
``src.services.ffmpeg_audio_service.subprocess.Popen`` and
``src.services.ffmpeg_audio_service.tempfile.mkdtemp`` were migrated to
patch this module's equivalents as part of the same change.
"""

import glob
import os
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional, Set

from ...config.constants import (
    DEFAULT_MUSIC_VOLUME_REDUCTION,
    DEFAULT_SILENCE_DURATION,
    DEFAULT_VOICE_BOOST,
    HLS_FADE_DURATION_SECONDS,
)
from ...exceptions import AudioProcessingError, ErrorCode, ExternalServiceError
from ...utils.logging_utils import get_logger

logger = get_logger(__name__)

HLS_SEGMENT_DURATION = 5
FFMPEG_STREAM_TIMEOUT = 600


@dataclass
class StreamState:
    """Thread-safe state container for ``process_stream_to_hls``."""

    lock: threading.Lock = field(default_factory=threading.Lock)
    uploading: bool = True
    segments_uploaded: int = 0
    segment_durations: List[float] = field(default_factory=list)
    uploaded_segments: Set[str] = field(default_factory=set)
    error: Optional[BaseException] = None
    done: threading.Event = field(default_factory=threading.Event)

    def stop(self) -> None:
        with self.lock:
            self.uploading = False
        self.done.set()


def process_stream_to_hls(
    ffmpeg_executable: str,
    hls_service: object,
    get_duration: Callable[[str], float],
    voice_generator: Iterator[bytes],
    music_path: str,
    user_id: str,
    job_id: str,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    estimated_voice_duration: float = 60.0,
    input_format_flags: Optional[List[str]] = None,
) -> tuple[int, List[float]]:
    """Stream TTS to HLS segments, then append fade-out segments."""
    if not hls_service:
        raise ValueError("HLS service required for streaming HLS output")

    logger.info("Starting streaming HLS generation", extra={"data": {"job_id": job_id}})

    hls_output_dir = tempfile.mkdtemp(prefix="hls_stream_")
    try:
        return _process_stream_to_hls_inner(
            ffmpeg_executable=ffmpeg_executable,
            hls_service=hls_service,
            get_duration=get_duration,
            voice_generator=voice_generator,
            music_path=music_path,
            user_id=user_id,
            job_id=job_id,
            progress_callback=progress_callback,
            estimated_voice_duration=estimated_voice_duration,
            hls_output_dir=hls_output_dir,
            input_format_flags=input_format_flags,
        )
    finally:
        # Always clean the temp tree, even if Popen, the watcher startup,
        # or anything else above the existing try/finally raises before
        # the inner cleanup can run.
        shutil.rmtree(hls_output_dir, ignore_errors=True)


def _process_stream_to_hls_inner(
    ffmpeg_executable: str,
    hls_service: object,
    get_duration: Callable[[str], float],
    voice_generator: Iterator[bytes],
    music_path: str,
    user_id: str,
    job_id: str,
    progress_callback: Optional[Callable[[int, Optional[int]], None]],
    estimated_voice_duration: float,
    hls_output_dir: str,
    input_format_flags: Optional[List[str]] = None,
) -> tuple[int, List[float]]:
    playlist_path = os.path.join(hls_output_dir, "playlist.m3u8")
    segment_pattern = os.path.join(hls_output_dir, "segment_%03d.ts")

    # Pad the voice to at least est_dur + fade so the music fade timing is
    # deterministic within a single FFmpeg process (no second process = no
    # audio seam). If the voice runs longer than the estimate the music will
    # have already faded and the voice finishes over silence — acceptable.
    fade_duration = HLS_FADE_DURATION_SECONDS
    padded_duration = estimated_voice_duration + fade_duration
    fade_start = estimated_voice_duration
    delay_ms = int(DEFAULT_SILENCE_DURATION * 1000)

    logger.info(
        f"Starting FFmpeg: est_voice={estimated_voice_duration:.0f}s, "
        f"fade_start={fade_start:.0f}s, padded={padded_duration:.0f}s"
    )

    fmt_flags = input_format_flags or ["-f", "s16le", "-ar", "24000", "-ac", "1"]
    ffmpeg_cmd = [
        ffmpeg_executable,
        *fmt_flags,
        "-i",
        "pipe:0",
        "-stream_loop",
        "-1",
        "-i",
        music_path,
        "-filter_complex",
        f"[0:a]volume={DEFAULT_VOICE_BOOST}dB,"
        f"adelay={delay_ms}|{delay_ms},"
        f"apad=whole_dur={padded_duration}[voice];"
        f"[1:a]atrim=0:{padded_duration},"
        f"volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB,"
        f"afade=t=out:st={fade_start}:d={fade_duration}[music];"
        f"[voice][music]amix=inputs=2:duration=first:normalize=0[out]",
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
        segment_pattern,
        "-hls_list_size",
        "0",
        playlist_path,
    ]

    process = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    state = StreamState()

    def _drain_segments() -> None:
        segment_files = sorted(glob.glob(os.path.join(hls_output_dir, "segment_*.ts")))
        for segment_file in segment_files:
            with state.lock:
                if segment_file in state.uploaded_segments:
                    continue

            if not os.path.exists(segment_file):
                continue
            file_size = os.path.getsize(segment_file)
            if file_size == 0:
                continue

            segment_name = os.path.basename(segment_file)
            segment_index = int(segment_name.replace("segment_", "").replace(".ts", ""))

            seg_duration = get_duration(segment_file)
            if seg_duration == 0:
                seg_duration = float(HLS_SEGMENT_DURATION)

            uploaded = hls_service.upload_segment_from_file(  # type: ignore[attr-defined]
                user_id, job_id, segment_index, segment_file
            )
            if not uploaded:
                # Treat upload failure as fatal: do not mutate state, do not
                # publish a partial playlist, do not invoke the progress
                # callback. Raising propagates to the caller's retry path.
                raise ExternalServiceError(
                    f"Failed to upload segment {segment_index}",
                    ErrorCode.STORAGE_FAILURE,
                    details=f"user_id={user_id}, job_id={job_id}",
                )

            with state.lock:
                # Only mutate the durations array AFTER a successful upload
                # so a failed retry cannot leave a stale duration in the
                # slot. Then advance ``segments_uploaded`` to the longest
                # contiguous prefix of the uploaded set so the published
                # playlist only references segments that are actually in S3.
                while len(state.segment_durations) <= segment_index:
                    state.segment_durations.append(float(HLS_SEGMENT_DURATION))
                state.segment_durations[segment_index] = seg_duration
                state.uploaded_segments.add(segment_file)
                while True:
                    next_name = f"segment_{state.segments_uploaded:03d}.ts"
                    next_path = os.path.join(hls_output_dir, next_name)
                    if next_path in state.uploaded_segments:
                        state.segments_uploaded += 1
                        continue
                    break
                segments_uploaded_snapshot = state.segments_uploaded
                durations_snapshot = list(state.segment_durations[:segments_uploaded_snapshot])

            playlist_content = hls_service.generate_live_playlist(  # type: ignore[attr-defined]
                user_id,
                job_id,
                segments_uploaded_snapshot,
                durations_snapshot,
                is_complete=False,
            )
            playlist_uploaded = hls_service.upload_playlist(  # type: ignore[attr-defined]
                user_id, job_id, playlist_content
            )
            if not playlist_uploaded:
                raise ExternalServiceError(
                    "Failed to upload live HLS playlist",
                    ErrorCode.STORAGE_FAILURE,
                    details=(
                        f"user_id={user_id}, job_id={job_id}, "
                        f"segments_uploaded={segments_uploaded_snapshot}"
                    ),
                )

            if progress_callback:
                progress_callback(segments_uploaded_snapshot, None)

            logger.info(f"Uploaded segment {segment_index}")

    def upload_watcher() -> None:
        while True:
            try:
                _drain_segments()
                if state.done.wait(timeout=0.3):
                    _drain_segments()
                    break
            except Exception as e:
                logger.error(f"Watcher error: {e}")
                with state.lock:
                    state.error = e
                break

    watcher_thread = threading.Thread(target=upload_watcher)
    watcher_thread.start()

    try:
        try:
            for chunk in voice_generator:
                # Honor watcher-side upload failures: if the watcher has
                # recorded an error (e.g., S3 upload returned False), stop
                # consuming TTS chunks and let the failure propagate via
                # the finally block instead of burning more provider time.
                with state.lock:
                    if state.error is not None:
                        logger.warning("Watcher reported failure; halting FFmpeg producer")
                        break
                if process.poll() is not None:
                    stderr = process.stderr.read().decode()
                    logger.error(f"FFmpeg exited early: {stderr}")
                    raise AudioProcessingError(f"FFmpeg exited unexpectedly: {stderr}")
                try:
                    process.stdin.write(chunk)
                    process.stdin.flush()
                except BrokenPipeError as bpe:
                    stderr = process.stderr.read().decode() if process.stderr else "unknown"
                    logger.error(f"FFmpeg broken pipe - stderr: {stderr}")
                    raise AudioProcessingError(f"FFmpeg pipe closed mid-stream: {stderr}") from bpe
        finally:
            close = getattr(voice_generator, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    logger.debug("voice_generator.close() raised; ignoring")

        process.stdin.close()
        process.wait(timeout=FFMPEG_STREAM_TIMEOUT)

        if process.returncode != 0:
            stderr = process.stderr.read().decode()
            raise AudioProcessingError(f"FFmpeg failed: {stderr}")

    except subprocess.TimeoutExpired as err:
        logger.error(f"FFmpeg streaming process timed out after {FFMPEG_STREAM_TIMEOUT}s")
        process.kill()
        process.wait()
        raise AudioProcessingError(
            f"FFmpeg streaming timed out after {FFMPEG_STREAM_TIMEOUT}s"
        ) from err
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        if process.poll() is None:
            process.kill()
        raise
    finally:
        state.stop()
        watcher_thread.join(timeout=30)
        if watcher_thread.is_alive():
            # The watcher is still draining/uploading after the join
            # timeout. Continuing to ``finalize_playlist`` would race with
            # those uploads, so treat this as fatal.
            logger.error(
                "Upload watcher did not finish within 30s; aborting finalization",
                extra={"data": {"job_id": job_id}},
            )
            raise ExternalServiceError(
                "Upload watcher did not finish before timeout",
                ErrorCode.STORAGE_FAILURE,
                details=f"job_id={job_id}",
            )

        # ``join`` is a happens-before barrier so this read is safe even
        # without the lock, but holding it makes the intent explicit for
        # future readers and is essentially free at this point.
        with state.lock:
            watcher_error = state.error
        if watcher_error:
            raise watcher_error

    # Music fade is handled within the single FFmpeg process via afade,
    # so no separate append_fade_segments call is needed.
    with state.lock:
        final_segments = state.segments_uploaded
        final_durations = list(state.segment_durations)

    finalized = hls_service.finalize_playlist(  # type: ignore[attr-defined]
        user_id, job_id, final_segments, final_durations
    )
    if not finalized:
        raise ExternalServiceError(
            "Failed to finalize HLS playlist",
            ErrorCode.STORAGE_FAILURE,
            details=f"user_id={user_id}, job_id={job_id}, segments={final_segments}",
        )

    return (final_segments, final_durations)
