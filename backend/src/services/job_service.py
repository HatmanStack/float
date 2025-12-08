"""Async job management for long-running tasks."""
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ..config.settings import settings
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)

# Job TTL: jobs older than this will be cleaned up
JOB_TTL_HOURS = 24


def _utcnow() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


class JobService:
    """Manages async job status in S3."""

    def __init__(self, storage_service):
        self.storage_service = storage_service
        self.bucket = settings.AWS_S3_BUCKET

    def create_job(self, user_id: str, job_type: str, enable_streaming: bool = False) -> str:
        """Create a new job and return job_id."""
        job_id = str(uuid.uuid4())
        now = _utcnow()
        job_data = {
            "job_id": job_id,
            "user_id": user_id,
            "job_type": job_type,
            "status": JobStatus.PENDING.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=JOB_TTL_HOURS)).isoformat(),
            "result": None,
            "error": None,
        }

        # Add HLS streaming fields for meditation jobs
        if job_type == "meditation" and enable_streaming:
            job_data["streaming"] = {
                "enabled": True,
                "playlist_url": None,
                "segments_completed": 0,
                "segments_total": None,
                "started_at": None,
            }
            job_data["download"] = {
                "available": False,
                "url": None,
                "downloaded": False,
            }
            job_data["tts_cache_key"] = None
            job_data["generation_attempt"] = 1

        self._save_job(user_id, job_id, job_data)
        return job_id

    def update_job_status(
        self,
        user_id: str,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """Update job status."""
        job_data = self.get_job(user_id, job_id)
        if job_data:
            job_data["status"] = status.value
            job_data["updated_at"] = _utcnow().isoformat()
            if result is not None:
                job_data["result"] = result
            if error is not None:
                job_data["error"] = error
            self._save_job(user_id, job_id, job_data)

    def update_streaming_progress(
        self,
        user_id: str,
        job_id: str,
        segments_completed: int,
        segments_total: Optional[int] = None,
        playlist_url: Optional[str] = None,
    ):
        """Update streaming progress for an HLS job."""
        job_data = self.get_job(user_id, job_id)
        if not job_data:
            logger.warning(
                "Cannot update streaming progress: job not found",
                extra={"data": {"job_id": job_id}}
            )
            return

        # Initialize streaming dict if missing (backward compatibility)
        if "streaming" not in job_data:
            job_data["streaming"] = {
                "enabled": True,
                "playlist_url": None,
                "segments_completed": 0,
                "segments_total": None,
                "started_at": None,
            }

        streaming = job_data["streaming"]
        streaming["segments_completed"] = segments_completed

        if segments_total is not None:
            streaming["segments_total"] = segments_total

        if playlist_url is not None:
            streaming["playlist_url"] = playlist_url

        # Set started_at on first segment
        if segments_completed == 1 and streaming.get("started_at") is None:
            streaming["started_at"] = _utcnow().isoformat()

        job_data["updated_at"] = _utcnow().isoformat()
        self._save_job(user_id, job_id, job_data)

        logger.debug(
            "Updated streaming progress",
            extra={"data": {"job_id": job_id, "segments": segments_completed}}
        )

    def mark_streaming_started(
        self,
        user_id: str,
        job_id: str,
        playlist_url: str,
    ):
        """Mark job as streaming and set initial playlist URL."""
        job_data = self.get_job(user_id, job_id)
        if not job_data:
            return

        job_data["status"] = JobStatus.STREAMING.value
        job_data["updated_at"] = _utcnow().isoformat()

        if "streaming" not in job_data:
            job_data["streaming"] = {
                "enabled": True,
                "playlist_url": None,
                "segments_completed": 0,
                "segments_total": None,
                "started_at": None,
            }

        job_data["streaming"]["playlist_url"] = playlist_url
        job_data["streaming"]["started_at"] = _utcnow().isoformat()

        self._save_job(user_id, job_id, job_data)
        logger.info("Marked job as streaming", extra={"data": {"job_id": job_id}})

    def mark_streaming_complete(
        self,
        user_id: str,
        job_id: str,
        segments_total: int,
    ):
        """Mark streaming as complete, set status to COMPLETED, enable download."""
        job_data = self.get_job(user_id, job_id)
        if not job_data:
            return

        job_data["status"] = JobStatus.COMPLETED.value
        job_data["updated_at"] = _utcnow().isoformat()

        if "streaming" in job_data:
            job_data["streaming"]["segments_completed"] = segments_total
            job_data["streaming"]["segments_total"] = segments_total

        # Mark download as available
        if "download" not in job_data:
            job_data["download"] = {
                "available": False,
                "url": None,
                "downloaded": False,
            }
        job_data["download"]["available"] = True

        self._save_job(user_id, job_id, job_data)
        logger.info(
            "Marked streaming complete",
            extra={"data": {"job_id": job_id, "total_segments": segments_total}}
        )

    def mark_download_ready(
        self,
        user_id: str,
        job_id: str,
        download_url: str,
    ):
        """Set the download URL for a completed job."""
        job_data = self.get_job(user_id, job_id)
        if not job_data:
            return

        if "download" not in job_data:
            job_data["download"] = {
                "available": False,
                "url": None,
                "downloaded": False,
            }

        job_data["download"]["available"] = True
        job_data["download"]["url"] = download_url
        job_data["updated_at"] = _utcnow().isoformat()

        self._save_job(user_id, job_id, job_data)

    def mark_download_completed(self, user_id: str, job_id: str):
        """Mark download as completed (for cleanup tracking)."""
        job_data = self.get_job(user_id, job_id)
        if not job_data:
            return

        if "download" in job_data:
            job_data["download"]["downloaded"] = True
            job_data["updated_at"] = _utcnow().isoformat()
            self._save_job(user_id, job_id, job_data)
            logger.info("Marked download completed", extra={"data": {"job_id": job_id}})

    def set_tts_cache_key(self, user_id: str, job_id: str, cache_key: str):
        """Set the TTS cache key for retry capability."""
        job_data = self.get_job(user_id, job_id)
        if not job_data:
            return

        job_data["tts_cache_key"] = cache_key
        job_data["updated_at"] = _utcnow().isoformat()
        self._save_job(user_id, job_id, job_data)

    def increment_generation_attempt(self, user_id: str, job_id: str) -> int:
        """Increment and return the generation attempt count."""
        job_data = self.get_job(user_id, job_id)
        if not job_data:
            return 1

        attempt = job_data.get("generation_attempt", 1) + 1
        job_data["generation_attempt"] = attempt
        job_data["updated_at"] = _utcnow().isoformat()
        self._save_job(user_id, job_id, job_data)
        return attempt

    def get_job(self, user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status. Returns None if job doesn't exist or is expired."""
        key = f"{user_id}/jobs/{job_id}.json"
        try:
            data = self.storage_service.download_json(self.bucket, key)

            # Check if job is expired
            if data and self._is_job_expired(data):
                logger.info(
                    "Job expired, cleaning up",
                    extra={"data": {"job_id": job_id, "user_id": user_id}}
                )
                self._delete_job(user_id, job_id)
                return None

            return data
        except Exception as e:
            logger.debug(
                "Failed to get job",
                extra={"data": {"job_id": job_id, "error": str(e)}}
            )
            return None

    def _is_job_expired(self, job_data: Dict[str, Any]) -> bool:
        """Check if a job has exceeded its TTL."""
        expires_at_str = job_data.get("expires_at")
        if not expires_at_str:
            # For backwards compatibility with jobs without expires_at,
            # check against created_at
            created_at_str = job_data.get("created_at")
            if not created_at_str:
                return False
            try:
                created_at = datetime.fromisoformat(created_at_str)
                # Handle both naive and aware datetimes
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                return _utcnow() > created_at + timedelta(hours=JOB_TTL_HOURS)
            except (ValueError, TypeError):
                return False

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            # Handle both naive and aware datetimes
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            return _utcnow() > expires_at
        except (ValueError, TypeError):
            return False

    def _delete_job(self, user_id: str, job_id: str):
        """Delete a job from S3."""
        key = f"{user_id}/jobs/{job_id}.json"
        try:
            self.storage_service.delete_object(self.bucket, key)
            logger.debug("Deleted expired job", extra={"data": {"job_id": job_id}})
        except Exception as e:
            logger.warning(
                "Failed to delete job",
                extra={"data": {"job_id": job_id, "error": str(e)}}
            )

    def cleanup_expired_jobs(self, user_id: str) -> List[str]:
        """Clean up expired jobs for a user. Returns list of deleted job IDs."""
        deleted_jobs = []
        try:
            prefix = f"{user_id}/jobs/"
            job_keys = self.storage_service.list_objects(self.bucket, prefix)

            for key in job_keys:
                try:
                    job_data = self.storage_service.download_json(self.bucket, key)
                    if job_data and self._is_job_expired(job_data):
                        job_id = job_data.get("job_id", key.split("/")[-1].replace(".json", ""))
                        self.storage_service.delete_object(self.bucket, key)
                        deleted_jobs.append(job_id)
                except Exception as e:
                    logger.warning(
                        "Error checking job for cleanup",
                        extra={"data": {"key": key, "error": str(e)}}
                    )

            if deleted_jobs:
                logger.info(
                    "Cleaned up expired jobs",
                    extra={"data": {"user_id": user_id, "count": len(deleted_jobs)}}
                )
        except Exception as e:
            logger.error(
                "Error during job cleanup",
                extra={"data": {"user_id": user_id, "error": str(e)}}
            )

        return deleted_jobs

    def _save_job(self, user_id: str, job_id: str, job_data: Dict[str, Any]):
        """Save job data to S3."""
        key = f"{user_id}/jobs/{job_id}.json"
        self.storage_service.upload_json(self.bucket, key, job_data)
