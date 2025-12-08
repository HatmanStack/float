"""HLS streaming service for segment and playlist management."""
from typing import List, Optional

from ..config.settings import settings
from ..utils.logging_utils import get_logger
from .storage_service import StorageService

logger = get_logger(__name__)

# HLS Configuration
SEGMENT_DURATION = 5  # seconds per segment
URL_EXPIRY = 3600  # 1 hour expiry for pre-signed URLs


class HLSService:
    """Handles HLS-specific operations: segments, playlists, pre-signed URLs."""

    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service
        self.bucket = settings.AWS_S3_BUCKET

    def get_hls_prefix(self, user_id: str, job_id: str) -> str:
        """Get S3 key prefix for HLS artifacts."""
        return f"{user_id}/hls/{job_id}/"

    def get_segment_key(self, user_id: str, job_id: str, segment_index: int) -> str:
        """Get S3 key for a specific segment."""
        prefix = self.get_hls_prefix(user_id, job_id)
        return f"{prefix}segment_{segment_index:03d}.ts"

    def get_playlist_key(self, user_id: str, job_id: str) -> str:
        """Get S3 key for the playlist file."""
        prefix = self.get_hls_prefix(user_id, job_id)
        return f"{prefix}playlist.m3u8"

    def get_tts_cache_key(self, user_id: str, job_id: str) -> str:
        """Get S3 key for cached TTS audio."""
        prefix = self.get_hls_prefix(user_id, job_id)
        return f"{prefix}voice.mp3"

    def generate_presigned_url(self, key: str, expiry: int = URL_EXPIRY) -> Optional[str]:
        """Generate a pre-signed GET URL for an S3 object."""
        try:
            # Access the underlying S3 client
            url = self.storage_service.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiry,
            )
            return url
        except Exception as e:
            logger.error(
                "Failed to generate pre-signed URL",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return None

    def generate_playlist_url(self, user_id: str, job_id: str) -> Optional[str]:
        """Generate pre-signed GET URL for playlist.m3u8."""
        key = self.get_playlist_key(user_id, job_id)
        return self.generate_presigned_url(key)

    def generate_segment_url(self, user_id: str, job_id: str, segment_index: int) -> Optional[str]:
        """Generate pre-signed GET URL for a specific segment."""
        key = self.get_segment_key(user_id, job_id, segment_index)
        return self.generate_presigned_url(key)

    def upload_segment(self, user_id: str, job_id: str, segment_index: int, data: bytes) -> bool:
        """Upload a segment to S3."""
        key = self.get_segment_key(user_id, job_id, segment_index)
        try:
            self.storage_service.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType="video/MP2T",
            )
            logger.debug(
                "Uploaded segment",
                extra={"data": {"key": key, "segment": segment_index}}
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to upload segment",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return False

    def upload_segment_from_file(
        self, user_id: str, job_id: str, segment_index: int, local_path: str
    ) -> bool:
        """Upload a segment from a local file to S3."""
        key = self.get_segment_key(user_id, job_id, segment_index)
        try:
            self.storage_service.s3_client.upload_file(
                local_path,
                self.bucket,
                key,
                ExtraArgs={"ContentType": "video/MP2T"},
            )
            logger.debug(
                "Uploaded segment from file",
                extra={"data": {"key": key, "segment": segment_index}}
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to upload segment from file",
                extra={"data": {"key": key, "local_path": local_path, "error": str(e)}}
            )
            return False

    def upload_playlist(self, user_id: str, job_id: str, content: str) -> bool:
        """Upload/update the playlist.m3u8 file."""
        key = self.get_playlist_key(user_id, job_id)
        try:
            self.storage_service.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="application/vnd.apple.mpegurl",
            )
            logger.debug("Uploaded playlist", extra={"data": {"key": key}})
            return True
        except Exception as e:
            logger.error(
                "Failed to upload playlist",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return False

    def generate_live_playlist(
        self,
        user_id: str,
        job_id: str,
        segment_count: int,
        segment_durations: Optional[List[float]] = None,
        is_complete: bool = False,
    ) -> str:
        """
        Generate HLS playlist content for live streaming.

        Args:
            user_id: User identifier
            job_id: Job identifier
            segment_count: Number of segments completed
            segment_durations: Optional list of actual segment durations
            is_complete: Whether generation is complete (adds ENDLIST)

        Returns:
            HLS playlist content as string
        """
        # Use default duration if not provided
        if segment_durations is None:
            segment_durations = [float(SEGMENT_DURATION)] * segment_count

        # Calculate max duration for target duration
        max_duration = max(segment_durations) if segment_durations else SEGMENT_DURATION

        lines = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{int(max_duration) + 1}",
            "#EXT-X-MEDIA-SEQUENCE:0",
            "#EXT-X-PLAYLIST-TYPE:EVENT",
        ]

        # Add segment entries with pre-signed URLs
        for i in range(segment_count):
            duration = segment_durations[i] if i < len(segment_durations) else SEGMENT_DURATION
            segment_url = self.generate_segment_url(user_id, job_id, i)
            if segment_url:
                lines.append(f"#EXTINF:{duration:.3f},")
                lines.append(segment_url)

        # Add ENDLIST if complete
        if is_complete:
            lines.append("#EXT-X-ENDLIST")

        return "\n".join(lines)

    def finalize_playlist(
        self,
        user_id: str,
        job_id: str,
        segment_count: int,
        segment_durations: Optional[List[float]] = None,
    ) -> bool:
        """Finalize the playlist by adding ENDLIST and uploading."""
        content = self.generate_live_playlist(
            user_id, job_id, segment_count, segment_durations, is_complete=True
        )
        return self.upload_playlist(user_id, job_id, content)

    def upload_tts_cache(self, user_id: str, job_id: str, local_path: str) -> bool:
        """Upload TTS audio for retry capability."""
        key = self.get_tts_cache_key(user_id, job_id)
        try:
            self.storage_service.s3_client.upload_file(
                local_path,
                self.bucket,
                key,
                ExtraArgs={"ContentType": "audio/mpeg"},
            )
            logger.info("Uploaded TTS cache", extra={"data": {"key": key}})
            return True
        except Exception as e:
            logger.error(
                "Failed to upload TTS cache",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return False

    def download_tts_cache(self, user_id: str, job_id: str, local_path: str) -> bool:
        """Download cached TTS audio if it exists."""
        key = self.get_tts_cache_key(user_id, job_id)
        try:
            self.storage_service.s3_client.download_file(self.bucket, key, local_path)
            logger.info("Downloaded TTS cache", extra={"data": {"key": key}})
            return True
        except Exception as e:
            logger.debug(
                "TTS cache not found or download failed",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return False

    def tts_cache_exists(self, user_id: str, job_id: str) -> bool:
        """Check if TTS cache exists for a job."""
        key = self.get_tts_cache_key(user_id, job_id)
        try:
            self.storage_service.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def list_segments(self, user_id: str, job_id: str) -> List[str]:
        """List all segment keys for a job."""
        prefix = self.get_hls_prefix(user_id, job_id)
        try:
            keys = self.storage_service.list_objects(self.bucket, prefix)
            return [k for k in keys if k.endswith(".ts")]
        except Exception as e:
            logger.error(
                "Failed to list segments",
                extra={"data": {"prefix": prefix, "error": str(e)}}
            )
            return []

    def cleanup_hls_artifacts(self, user_id: str, job_id: str) -> bool:
        """Delete all HLS artifacts for a job (segments, playlist, TTS cache)."""
        prefix = self.get_hls_prefix(user_id, job_id)
        try:
            keys = self.storage_service.list_objects(self.bucket, prefix)
            deleted_count = 0
            for key in keys:
                try:
                    self.storage_service.delete_object(self.bucket, key)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(
                        "Failed to delete HLS artifact",
                        extra={"data": {"key": key, "error": str(e)}}
                    )

            logger.info(
                "Cleaned up HLS artifacts",
                extra={"data": {"job_id": job_id, "deleted": deleted_count}}
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to cleanup HLS artifacts",
                extra={"data": {"job_id": job_id, "error": str(e)}}
            )
            return False

    def download_segment(self, user_id: str, job_id: str, segment_index: int, local_path: str) -> bool:
        """Download a segment to a local file."""
        key = self.get_segment_key(user_id, job_id, segment_index)
        try:
            self.storage_service.s3_client.download_file(self.bucket, key, local_path)
            return True
        except Exception as e:
            logger.error(
                "Failed to download segment",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return False
