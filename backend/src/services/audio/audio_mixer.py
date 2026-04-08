"""Temp-file cleanup helper for the audio pipeline.

Phase 4 Task 2 collapses the three near-identical
``try/except OSError: pass`` blocks scattered throughout
:mod:`ffmpeg_audio_service` into this single helper.
"""

import os
from typing import Optional

from ...utils.logging_utils import get_logger

logger = get_logger(__name__)


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
