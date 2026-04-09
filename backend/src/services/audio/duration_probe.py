"""Shared audio duration helper.

Extracted from :mod:`ffmpeg_audio_service` as part of Phase 4 Task 2.
Every audio collaborator that needs an MP3/TS duration probe calls through
here so the ffmpeg invocation lives in exactly one place.
"""

import subprocess

from ...utils.logging_utils import get_logger

logger = get_logger(__name__)

FFMPEG_STEP_TIMEOUT = 120  # 2 minutes per individual step


def probe_duration(ffmpeg_executable: str, file_path: str) -> float:
    """Return the duration (seconds) of ``file_path`` or ``0.0`` on failure.

    ``ffmpeg -i <file> -f null -`` often exits non-zero on partial files
    while still emitting a parseable ``Duration:`` line on stderr. We use
    ``check=False`` so the stderr scrape works for both clean and noisy
    exits, preserving timeout behaviour via ``subprocess.run`` itself.
    """
    try:
        result = subprocess.run(
            [ffmpeg_executable, "-i", file_path, "-f", "null", "-"],
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=FFMPEG_STEP_TIMEOUT,
        )
        stderr = result.stderr or ""
    except subprocess.TimeoutExpired as exc:
        logger.warning(
            "ffmpeg duration probe timed out",
            extra={"data": {"file": file_path, "timeout": FFMPEG_STEP_TIMEOUT}},
        )
        stderr = (exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr) or ""
    except Exception as e:
        logger.warning(
            "Error getting audio duration",
            extra={"data": {"error": str(e)}},
        )
        return 0.0

    duration_lines = [line for line in stderr.split("\n") if "Duration" in line]
    if not duration_lines:
        logger.warning("No Duration line in ffmpeg output", extra={"data": {"file": file_path}})
        return 0.0
    try:
        duration_str = duration_lines[0].split(",")[0].split("Duration:")[1].strip()
        h, m, s = map(float, duration_str.split(":"))
        return h * 3600 + m * 60 + s
    except (IndexError, ValueError) as e:
        logger.warning(
            "Failed to parse Duration line",
            extra={"data": {"file": file_path, "error": str(e)}},
        )
        return 0.0
