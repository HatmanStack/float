"""Thin facade over the focused audio collaborators in ``audio/``.

Phase 4 revision (iteration 2) completed the decomposition started in the
first iteration: ``combine_voice_and_music``, ``_prepare_mixed_audio``,
``combine_voice_and_music_hls``, ``process_stream_to_hls``, and
``_append_fade_segments`` now live in their own single-responsibility
modules under :mod:`src.services.audio`. This module constructs the
collaborators and delegates the public method surface so the rest of the
application keeps importing :class:`FFmpegAudioService` unchanged.
"""

import os
from typing import TYPE_CHECKING, Callable, Iterator, List, Optional

from ..config.settings import settings
from ..utils.logging_utils import get_logger
from .audio import audio_mixer, hls_batch_encoder, hls_stream_encoder
from .audio.audio_mixer import cleanup_paths  # noqa: F401 -- re-export
from .audio.duration_probe import probe_duration
from .audio.hls_stream_encoder import StreamState
from .audio.music_selector import MusicSelector
from .audio_service import AudioService
from .storage_service import StorageService

if TYPE_CHECKING:
    from .hls_service import HLSService

logger = get_logger(__name__)

# HLS configuration re-exported for back-compat (``from ... import HLS_SEGMENT_DURATION``).
HLS_SEGMENT_DURATION = 5

# Backwards-compatible alias for the dataclass previously defined inline.
_StreamState = StreamState


class FFmpegAudioService(AudioService):
    """Thin facade that wires audio collaborators together."""

    def __init__(
        self,
        storage_service: StorageService,
        hls_service: Optional["HLSService"] = None,
    ) -> None:
        self.storage_service = storage_service
        self.hls_service = hls_service
        self.ffmpeg_executable = settings.FFMPEG_PATH
        self._music_selector = MusicSelector(storage_service)
        self._verify_ffmpeg()

    def _verify_ffmpeg(self) -> None:
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
        return probe_duration(self.ffmpeg_executable, file_path)

    def select_background_music(
        self, used_music: List[str], duration: float, output_path: str
    ) -> List[str]:
        return self._music_selector.select(used_music, duration, output_path)

    def _extract_last_numeric_value(self, filename: str) -> Optional[int]:
        return MusicSelector._extract_last_numeric_value(filename)

    def combine_voice_and_music(
        self, voice_path: str, music_list: List[str], timestamp: str, output_path: str
    ) -> List[str]:
        return audio_mixer.combine_voice_and_music(
            self.ffmpeg_executable,
            voice_path,
            music_list,
            timestamp,
            output_path,
            self.select_background_music,
            self.get_audio_duration,
        )

    def combine_voice_and_music_hls(
        self,
        voice_path: str,
        music_list: List[str],
        timestamp: str,
        user_id: str,
        job_id: str,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    ) -> tuple[List[str], int, List[float]]:
        return hls_batch_encoder.combine_voice_and_music_hls(
            self.ffmpeg_executable,
            self.hls_service,
            self.select_background_music,
            self.get_audio_duration,
            voice_path,
            music_list,
            timestamp,
            user_id,
            job_id,
            progress_callback,
        )

    def _append_fade_segments(
        self,
        music_path: str,
        total_streamed_duration: float,
        user_id: str,
        job_id: str,
        total_segments: int,
        segment_durations: List[float],
    ) -> int:
        return audio_mixer.append_fade_segments(
            self.ffmpeg_executable,
            self.hls_service,
            self.get_audio_duration,
            music_path,
            total_streamed_duration,
            user_id,
            job_id,
            total_segments,
            segment_durations,
        )

    def process_stream_to_hls(
        self,
        voice_generator: Iterator[bytes],
        music_path: str,
        user_id: str,
        job_id: str,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        estimated_voice_duration: float = 60.0,
        input_format_flags: Optional[List[str]] = None,
    ) -> tuple[int, List[float]]:
        return hls_stream_encoder.process_stream_to_hls(
            self.ffmpeg_executable,
            self.hls_service,
            self.get_audio_duration,
            voice_generator,
            music_path,
            user_id,
            job_id,
            progress_callback,
            estimated_voice_duration,
            input_format_flags=input_format_flags,
        )
