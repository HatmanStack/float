"""Download service for MP3 concatenation from HLS segments."""
import os
import shutil
import subprocess
import tempfile
from typing import Optional

from ..config.settings import settings
from ..utils.logging_utils import get_logger
from .hls_service import HLSService
from .storage_service import StorageService

logger = get_logger(__name__)

# URL expiry for downloads
DOWNLOAD_URL_EXPIRY = 3600  # 1 hour


class DownloadService:
    """Handles MP3 generation from HLS segments for download."""

    def __init__(self, storage_service: StorageService, hls_service: HLSService):
        self.storage_service = storage_service
        self.hls_service = hls_service
        self.bucket = settings.AWS_S3_BUCKET
        self.ffmpeg_executable = settings.FFMPEG_PATH

    def get_download_key(self, user_id: str, job_id: str) -> str:
        """Get S3 key for the downloadable MP3."""
        return f"{user_id}/downloads/{job_id}.mp3"

    def check_mp3_exists(self, user_id: str, job_id: str) -> bool:
        """Check if MP3 has already been generated for this job."""
        key = self.get_download_key(user_id, job_id)
        try:
            self.storage_service.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def get_download_url(self, user_id: str, job_id: str) -> Optional[str]:
        """Generate pre-signed GET URL for the downloadable MP3."""
        key = self.get_download_key(user_id, job_id)
        try:
            url = self.storage_service.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=DOWNLOAD_URL_EXPIRY,
            )
            return url
        except Exception as e:
            logger.error(
                "Failed to generate download URL",
                extra={"data": {"job_id": job_id, "error": str(e)}}
            )
            return None

    def generate_mp3(self, user_id: str, job_id: str) -> Optional[str]:
        """
        Generate MP3 by concatenating HLS segments.

        Args:
            user_id: User identifier
            job_id: Job identifier

        Returns:
            S3 key of generated MP3, or None on failure
        """
        # Check if already exists
        if self.check_mp3_exists(user_id, job_id):
            logger.info("MP3 already exists", extra={"data": {"job_id": job_id}})
            return self.get_download_key(user_id, job_id)

        logger.info("Starting MP3 generation", extra={"data": {"job_id": job_id}})

        # Create temp directory for work
        temp_dir = tempfile.mkdtemp(prefix="mp3_gen_")

        try:
            # List all segments
            segment_keys = self.hls_service.list_segments(user_id, job_id)
            if not segment_keys:
                logger.error("No segments found", extra={"data": {"job_id": job_id}})
                return None

            # Sort segments by index
            segment_keys = sorted(segment_keys)
            logger.info(
                "Found segments",
                extra={"data": {"job_id": job_id, "count": len(segment_keys)}}
            )

            # Download all segments
            segment_files = []
            for i, key in enumerate(segment_keys):
                local_path = os.path.join(temp_dir, f"segment_{i:03d}.ts")
                try:
                    self.storage_service.s3_client.download_file(
                        self.bucket, key, local_path
                    )
                    segment_files.append(local_path)
                except Exception as e:
                    logger.error(
                        "Failed to download segment",
                        extra={"data": {"key": key, "error": str(e)}}
                    )
                    return None

            # Create concat file list for FFmpeg
            concat_file = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file, "w") as f:
                for seg_file in segment_files:
                    # FFmpeg concat demuxer requires escaped paths
                    escaped_path = seg_file.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            # Output path
            output_path = os.path.join(temp_dir, "output.mp3")

            # Run FFmpeg to concatenate and convert to MP3
            ffmpeg_cmd = [
                self.ffmpeg_executable,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:a", "libmp3lame",
                "-q:a", "2",  # High quality VBR
                output_path,
            ]

            logger.debug(
                "Running FFmpeg concat",
                extra={"data": {"cmd": " ".join(ffmpeg_cmd)}}
            )

            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(
                    "FFmpeg concat failed",
                    extra={"data": {"stderr": result.stderr}}
                )
                return None

            # Upload the MP3
            s3_key = self.get_download_key(user_id, job_id)
            try:
                self.storage_service.s3_client.upload_file(
                    output_path,
                    self.bucket,
                    s3_key,
                    ExtraArgs={"ContentType": "audio/mpeg"},
                )
                logger.info(
                    "MP3 uploaded successfully",
                    extra={"data": {"job_id": job_id, "key": s3_key}}
                )
                return s3_key
            except Exception as e:
                logger.error(
                    "Failed to upload MP3",
                    extra={"data": {"job_id": job_id, "error": str(e)}}
                )
                return None

        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def generate_mp3_and_get_url(self, user_id: str, job_id: str) -> Optional[str]:
        """
        Generate MP3 (if needed) and return a pre-signed download URL.

        Args:
            user_id: User identifier
            job_id: Job identifier

        Returns:
            Pre-signed download URL, or None on failure
        """
        # Generate MP3 if needed
        mp3_key = self.generate_mp3(user_id, job_id)
        if not mp3_key:
            return None

        # Generate and return download URL
        return self.get_download_url(user_id, job_id)
