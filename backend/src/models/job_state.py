"""TypedDict definitions for the S3-backed job state.

Phase 4 Task 3 introduced these shapes so the chained ``job_data.get(...)``
call sites in :mod:`job_service` and :mod:`meditation_handler` can be
checked for key presence at review time instead of relying on
``Dict[str, Any]`` to swallow typos.

These are structural annotations only -- ``JobService`` still persists
plain dicts to S3 so the wire format is unchanged.
"""

from typing import Any, Dict, List, Optional, TypedDict


class StreamingState(TypedDict, total=False):
    """HLS streaming bookkeeping for a single job."""

    enabled: bool
    playlist_url: Optional[str]
    segments_completed: int
    segments_total: Optional[int]
    started_at: Optional[str]
    completed_at: Optional[str]


class DownloadState(TypedDict, total=False):
    """Downloadable MP3 state for a single job."""

    available: bool
    url: Optional[str]
    downloaded: bool


class JobData(TypedDict, total=False):
    """Canonical job-state shape persisted to S3 by :mod:`job_service`."""

    job_id: str
    user_id: str
    job_type: str
    status: str
    created_at: str
    updated_at: str
    expires_at: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    streaming: StreamingState
    download: DownloadState
    tts_cache_key: Optional[str]
    generation_attempt: int
    segments: List[str]
