"""Job status and download request handlers.

Extracted from :mod:`lambda_handler` as part of Phase 4 Task 1 of the
2026-04-08-audit-float plan.
"""

from typing import Any, Dict, Optional

from ..services.download_service import DownloadService
from ..services.hls_service import HLSService
from ..services.job_service import JobService, JobStatus
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


class JobHandler:
    """Handle job status and download requests."""

    def __init__(self, parent: Any) -> None:
        self._parent = parent

    @property
    def job_service(self) -> JobService:
        return self._parent.job_service

    @property
    def hls_service(self) -> HLSService:
        return self._parent.hls_service

    @property
    def download_service(self) -> DownloadService:
        return self._parent.download_service

    def handle_status(self, user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status with fresh pre-signed URLs."""
        job_data = self.job_service.get_job(user_id, job_id)
        if not job_data:
            return None

        streaming = job_data.get("streaming", {})
        if streaming.get("enabled") and streaming.get("started_at"):
            fresh_playlist_url = self.hls_service.generate_playlist_url(user_id, job_id)
            if fresh_playlist_url:
                job_data["streaming"]["playlist_url"] = fresh_playlist_url
        elif streaming.get("enabled"):
            job_data["streaming"]["playlist_url"] = None

        return job_data

    def handle_download(
        self,
        user_id: str,
        job_id: str,
        job_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Handle download request - generate MP3 and return URL."""
        if job_data is None:
            job_data = self.job_service.get_job(user_id, job_id)
            if not job_data:
                return None

        if job_data.get("status") != JobStatus.COMPLETED.value:
            return {
                "error": {
                    "code": "JOB_NOT_COMPLETED",
                    "message": "Job must be completed before download is available",
                }
            }

        if not job_data.get("download", {}).get("available", False):
            return {
                "error": {
                    "code": "DOWNLOAD_NOT_AVAILABLE",
                    "message": "Download is not available for this job",
                }
            }

        download_url = self.download_service.generate_mp3_and_get_url(user_id, job_id)
        if not download_url:
            return {
                "error": {
                    "code": "GENERATION_FAILED",
                    "message": "Failed to generate downloadable MP3",
                }
            }

        self.job_service.mark_download_ready(user_id, job_id, download_url)

        return {
            "job_id": job_id,
            "download_url": download_url,
            "expires_in": 3600,
        }
