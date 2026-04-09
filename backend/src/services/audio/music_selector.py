"""Background music selection and caching.

Extracted from :mod:`ffmpeg_audio_service` as part of Phase 4 Task 2.
Owns the S3 listing cache, the filename parsing helper, and the actual
music-picking logic.
"""

import ast
import random
import re
from typing import List, Optional, Union

from ...config.settings import settings
from ...exceptions import AudioProcessingError
from ...utils.cache import music_list_cache
from ...utils.logging_utils import get_logger
from ..storage_service import StorageService

logger = get_logger(__name__)


class MusicSelector:
    """Pick a background music track matching the requested duration."""

    def __init__(self, storage_service: StorageService) -> None:
        self.storage_service = storage_service

    def select(
        self,
        used_music: Optional[Union[List[str], str]],
        duration: float,
        output_path: str,
    ) -> List[str]:
        """Download a matching track to ``output_path`` and return the updated used list.

        ``used_music`` accepts ``None``, a single track string, a stringified
        list (legacy DB shape), or a real list of track names. The
        normalization branch below collapses all four into ``List[str]``.
        """
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
        # Coerce all elements to str so set(used_music) never fails on
        # unhashable items (e.g., dicts from ast.literal_eval).
        used_music = [str(item) for item in used_music]

        bucket_name = settings.AWS_AUDIO_BUCKET

        cache_key = f"music_list:{bucket_name}"
        existing_keys = music_list_cache.get(cache_key)
        if existing_keys is None:
            existing_keys = self.storage_service.list_objects(bucket_name)
            music_list_cache.set(cache_key, existing_keys)
            logger.debug("Cached music list from S3", extra={"data": {"count": len(existing_keys)}})

        filtered_keys = set()
        for key in existing_keys:
            track_duration = self._extract_last_numeric_value(key)
            if track_duration is not None and duration <= track_duration <= duration + 30:
                filtered_keys.add(key)
        if not filtered_keys:
            for key in existing_keys:
                if self._extract_last_numeric_value(key) == 300:
                    filtered_keys.add(key)

        available_keys = list(filtered_keys - set(used_music))
        if not available_keys:
            logger.debug("No new music tracks available, reusing from pool")
            if filtered_keys:
                available_keys = list(filtered_keys)
            elif existing_keys:
                # No duration-matched track exists; reuse any track in the
                # bucket so the request still succeeds.
                available_keys = list(existing_keys)
                logger.warning(
                    "No duration-matched music found; falling back to full S3 listing",
                    extra={
                        "data": {
                            "requested_duration": duration,
                            "pool": len(available_keys),
                        }
                    },
                )
            else:
                logger.error(
                    "No music tracks available in S3 bucket",
                    extra={"data": {"bucket": bucket_name}},
                )
                raise AudioProcessingError(
                    "No background music available",
                    details=f"bucket={bucket_name}",
                )

        file_key = random.choice(available_keys)
        if self.storage_service.download_file(bucket_name, file_key, output_path):
            used_music.append(file_key)
            return used_music
        raise AudioProcessingError(
            f"Failed to download music file: {file_key}",
            details=f"bucket={bucket_name}, key={file_key}",
        )

    @staticmethod
    def _extract_last_numeric_value(filename: str) -> Optional[int]:
        match = re.search(r"(\d+)\D*$", filename)
        return int(match.group(1)) if match else None
