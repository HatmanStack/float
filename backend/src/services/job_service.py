"""Async job management for long-running tasks."""
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from ..config.settings import settings


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
        job_data = {
            "job_id": job_id,
            "user_id": user_id,
            "job_type": job_type,
            "status": JobStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
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
            job_data["updated_at"] = datetime.utcnow().isoformat()
            if result is not None:
                job_data["result"] = result
            if error is not None:
                job_data["error"] = error
            self._save_job(user_id, job_id, job_data)

    def get_job(self, user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        key = f"{user_id}/jobs/{job_id}.json"
        try:
            data = self.storage_service.download_json(self.bucket, key)
            return data
        except Exception as e:
            print(f"Failed to get job {job_id}: {e}")
            return None

    def _save_job(self, user_id: str, job_id: str, job_data: Dict[str, Any]):
        """Save job data to S3."""
        key = f"{user_id}/jobs/{job_id}.json"
        self.storage_service.upload_json(self.bucket, key, job_data)
