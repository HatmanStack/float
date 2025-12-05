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
    COMPLETED = "completed"
    FAILED = "failed"


class JobService:
    """Manages async job status in S3."""

    def __init__(self, storage_service):
        self.storage_service = storage_service
        self.bucket = settings.AWS_S3_BUCKET

    def create_job(self, user_id: str, job_type: str) -> str:
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
