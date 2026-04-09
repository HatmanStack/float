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
    DURATION_TIER_MINUTES,
    HLS_TRAILING_PAD_BASE_SECONDS,
    HLS_TRAILING_PAD_PER_TIER,
)
from ...exceptions import AudioProcessingError, ErrorCode, ExternalServiceError
from ...utils.logging_utils import get_logger
from .audio_mixer import append_fade_segments

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
) -> tuple[int, List[float]]:
    playlist_path = os.path.join(hls_output_dir, "playlist.m3u8")
    segment_pattern = os.path.join(hls_output_dir, "segment_%03d.ts")

    voice_temp_path = os.path.join(hls_output_dir, "voice.mp3")

    est_minutes = estimated_voice_duration / 60
    tier = sum(1 for t in DURATION_TIER_MINUTES if est_minutes >= t) or 1
    trailing_pad = HLS_TRAILING_PAD_BASE_SECONDS + (HLS_TRAILING_PAD_PER_TIER * tier)
    logger.info(
        f"Trailing pad: {trailing_pad}s (base={HLS_TRAILING_PAD_BASE_SECONDS} + "
        f"{HLS_TRAILING_PAD_PER_TIER}s x tier {tier})"
    )

    ffmpeg_cmd = [
        ffmpeg_executable,
        "-f",
        "mp3",
        "-i",
        "pipe:0",
        "-stream_loop",
        "-1",
        "-i",
        music_path,
        "-filter_complex",
        f"[0:a]volume={DEFAULT_VOICE_BOOST}dB,"
        f"adelay={int(DEFAULT_SILENCE_DURATION * 1000)}|{int(DEFAULT_SILENCE_DURATION * 1000)},"
        f"apad=pad_dur={trailing_pad}[voice_padded];"
        f"[1:a]volume={DEFAULT_MUSIC_VOLUME_REDUCTION}dB[music];"
        f"[voice_padded][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[out]",
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

    logger.info("Starting FFmpeg streaming process (fade appended after completion)")

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

            with state.lock:
                while len(state.segment_durations) <= segment_index:
                    state.segment_durations.append(float(HLS_SEGMENT_DURATION))
                state.segment_durations[segment_index] = seg_duration

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
                state.uploaded_segments.add(segment_file)
                state.segments_uploaded += 1
                segments_uploaded_snapshot = state.segments_uploaded
                durations_snapshot = list(state.segment_durations[:segments_uploaded_snapshot])

            playlist_content = hls_service.generate_live_playlist(  # type: ignore[attr-defined]
                user_id,
                job_id,
                segments_uploaded_snapshot,
                durations_snapshot,
                is_complete=False,
            )
            hls_service.upload_playlist(user_id, job_id, playlist_content)  # type: ignore[attr-defined]

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
            with open(voice_temp_path, "wb") as voice_file:
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
                        raise AudioProcessingError(
                            f"FFmpeg pipe closed mid-stream: {stderr}"
                        ) from bpe
                    voice_file.write(chunk)
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
            logger.warning(
                "Upload watcher did not finish within 30s; some segments may be missing",
                extra={"data": {"job_id": job_id}},
            )

        # ``join`` is a happens-before barrier so this read is safe even
        # without the lock, but holding it makes the intent explicit for
        # future readers and is essentially free at this point.
        with state.lock:
            watcher_error = state.error
        if watcher_error:
            raise watcher_error

    with state.lock:
        total_streamed_duration = sum(state.segment_durations)
        current_segments = state.segments_uploaded
        durations_list = state.segment_durations
    new_segments = append_fade_segments(
        ffmpeg_executable,
        hls_service,
        get_duration,
        music_path,
        total_streamed_duration,
        user_id,
        job_id,
        current_segments,
        durations_list,
    )
    with state.lock:
        state.segments_uploaded = new_segments
        final_segments = state.segments_uploaded
        final_durations = list(state.segment_durations)

    hls_service.finalize_playlist(user_id, job_id, final_segments, final_durations)  # type: ignore[attr-defined]

    return (final_segments, final_durations)
