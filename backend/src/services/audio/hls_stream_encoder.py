"""Thread-safe state container for the HLS streaming encoder.

Phase 4 Task 2 extracted the ``_StreamState`` dataclass that used to live
inside :mod:`ffmpeg_audio_service`. The actual streaming pipeline
(``process_stream_to_hls``) still lives on the :class:`FFmpegAudioService`
facade so that existing ``patch.object(service, "get_audio_duration", ...)``
test fixtures continue to work unchanged.
"""

import threading
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class StreamState:
    """Thread-safe state container for ``process_stream_to_hls``.

    All mutable fields MUST be read or written while holding ``lock``.
    Cross-thread termination happens via ``done`` (a ``threading.Event``)
    rather than polling ``os.path.exists`` on the output directory.
    """

    lock: threading.Lock = field(default_factory=threading.Lock)
    uploading: bool = True
    segments_uploaded: int = 0
    segment_durations: List[float] = field(default_factory=list)
    uploaded_segments: Set[str] = field(default_factory=set)
    error: Optional[BaseException] = None
    done: threading.Event = field(default_factory=threading.Event)

    def stop(self) -> None:
        """Signal the watcher that streaming is finished."""
        with self.lock:
            self.uploading = False
        self.done.set()
