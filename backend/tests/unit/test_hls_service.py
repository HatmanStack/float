"""Unit tests for HLS streaming service."""
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_storage_service():
    """Mock storage service with S3 client."""
    service = MagicMock()
    service.s3_client = MagicMock()
    service.list_objects.return_value = []
    service.delete_object.return_value = True
    return service


@pytest.mark.unit
class TestHLSService:
    """Test HLS streaming service."""

    def test_service_initialization(self, mock_storage_service):
        """Test HLS service initializes correctly."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        assert service is not None
        assert service.storage_service == mock_storage_service

    def test_get_hls_prefix(self, mock_storage_service):
        """Test HLS prefix generation."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        prefix = service.get_hls_prefix("user123", "job456")

        assert prefix == "hls/user123/job456/"

    def test_get_segment_key(self, mock_storage_service):
        """Test segment key generation."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)

        # Test various segment indices
        assert service.get_segment_key("user123", "job456", 0) == "hls/user123/job456/segment_000.ts"
        assert service.get_segment_key("user123", "job456", 5) == "hls/user123/job456/segment_005.ts"
        assert service.get_segment_key("user123", "job456", 99) == "hls/user123/job456/segment_099.ts"

    def test_get_playlist_key(self, mock_storage_service):
        """Test playlist key generation."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        key = service.get_playlist_key("user123", "job456")

        assert key == "hls/user123/job456/playlist.m3u8"

    def test_get_tts_cache_key(self, mock_storage_service):
        """Test TTS cache key generation."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        key = service.get_tts_cache_key("user123", "job456")

        assert key == "hls/user123/job456/voice.mp3"

    def test_generate_presigned_url_success(self, mock_storage_service):
        """Test pre-signed URL generation."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.return_value = (
            "https://s3.../segment_000.ts?signature=abc"
        )

        service = HLSService(mock_storage_service)
        url = service.generate_presigned_url("user123/hls/job456/segment_000.ts")

        assert url == "https://s3.../segment_000.ts?signature=abc"
        mock_storage_service.s3_client.generate_presigned_url.assert_called_once()

    def test_generate_presigned_url_failure(self, mock_storage_service):
        """Test pre-signed URL generation handles errors."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.side_effect = Exception("S3 error")

        service = HLSService(mock_storage_service)
        url = service.generate_presigned_url("user123/hls/job456/segment_000.ts")

        assert url is None

    def test_generate_playlist_url(self, mock_storage_service):
        """Test playlist URL generation."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.return_value = (
            "https://s3.../playlist.m3u8?signature=xyz"
        )

        service = HLSService(mock_storage_service)
        url = service.generate_playlist_url("user123", "job456")

        assert url == "https://s3.../playlist.m3u8?signature=xyz"

    def test_generate_segment_url(self, mock_storage_service):
        """Test segment URL generation."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.return_value = (
            "https://s3.../segment_005.ts?signature=abc"
        )

        service = HLSService(mock_storage_service)
        url = service.generate_segment_url("user123", "job456", 5)

        assert url == "https://s3.../segment_005.ts?signature=abc"

    def test_upload_segment_success(self, mock_storage_service):
        """Test segment upload."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        result = service.upload_segment("user123", "job456", 0, b"segment_data")

        assert result is True
        mock_storage_service.s3_client.put_object.assert_called_once()
        call_kwargs = mock_storage_service.s3_client.put_object.call_args.kwargs
        assert call_kwargs["ContentType"] == "video/MP2T"
        assert call_kwargs["Body"] == b"segment_data"

    def test_upload_segment_failure(self, mock_storage_service):
        """Test segment upload handles errors."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.put_object.side_effect = Exception("Upload failed")

        service = HLSService(mock_storage_service)
        result = service.upload_segment("user123", "job456", 0, b"segment_data")

        assert result is False

    def test_upload_segment_from_file(self, mock_storage_service):
        """Test segment upload from file."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        result = service.upload_segment_from_file("user123", "job456", 0, "/tmp/segment_000.ts")

        assert result is True
        mock_storage_service.s3_client.upload_file.assert_called_once()

    def test_upload_playlist(self, mock_storage_service):
        """Test playlist upload."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        content = "#EXTM3U\n#EXT-X-VERSION:3"
        result = service.upload_playlist("user123", "job456", content)

        assert result is True
        call_kwargs = mock_storage_service.s3_client.put_object.call_args.kwargs
        assert call_kwargs["ContentType"] == "application/vnd.apple.mpegurl"

    def test_generate_live_playlist_basic(self, mock_storage_service):
        """Test basic live playlist generation."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.side_effect = lambda *args, **kwargs: (
            f"https://s3.../{kwargs['Params']['Key']}?sig=abc"
        )

        service = HLSService(mock_storage_service)
        content = service.generate_live_playlist("user123", "job456", segment_count=3)

        assert "#EXTM3U" in content
        assert "#EXT-X-VERSION:3" in content
        assert "#EXT-X-TARGETDURATION:" in content
        assert "#EXT-X-PLAYLIST-TYPE:EVENT" in content
        assert "#EXTINF:" in content
        # Should NOT have ENDLIST since not complete
        assert "#EXT-X-ENDLIST" not in content

    def test_generate_live_playlist_with_endlist(self, mock_storage_service):
        """Test live playlist with ENDLIST when complete."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.side_effect = lambda *args, **kwargs: (
            f"https://s3.../{kwargs['Params']['Key']}?sig=abc"
        )

        service = HLSService(mock_storage_service)
        content = service.generate_live_playlist(
            "user123", "job456", segment_count=3, is_complete=True
        )

        assert "#EXT-X-ENDLIST" in content

    def test_generate_live_playlist_custom_durations(self, mock_storage_service):
        """Test live playlist with custom segment durations."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.side_effect = lambda *args, **kwargs: (
            f"https://s3.../{kwargs['Params']['Key']}?sig=abc"
        )

        service = HLSService(mock_storage_service)
        content = service.generate_live_playlist(
            "user123", "job456",
            segment_count=2,
            segment_durations=[4.5, 5.2]
        )

        assert "#EXTINF:4.500," in content
        assert "#EXTINF:5.200," in content

    def test_finalize_playlist(self, mock_storage_service):
        """Test playlist finalization."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.side_effect = lambda *args, **kwargs: (
            f"https://s3.../{kwargs['Params']['Key']}?sig=abc"
        )

        service = HLSService(mock_storage_service)
        result = service.finalize_playlist("user123", "job456", segment_count=5)

        assert result is True
        # Verify put_object was called with content containing ENDLIST
        call_kwargs = mock_storage_service.s3_client.put_object.call_args.kwargs
        content = call_kwargs["Body"].decode("utf-8")
        assert "#EXT-X-ENDLIST" in content

    def test_upload_tts_cache(self, mock_storage_service):
        """Test TTS cache upload."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        result = service.upload_tts_cache("user123", "job456", "/tmp/voice.mp3")

        assert result is True
        mock_storage_service.s3_client.upload_file.assert_called_once()

    def test_download_tts_cache_success(self, mock_storage_service):
        """Test TTS cache download."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        result = service.download_tts_cache("user123", "job456", "/tmp/voice.mp3")

        assert result is True
        mock_storage_service.s3_client.download_file.assert_called_once()

    def test_download_tts_cache_not_found(self, mock_storage_service):
        """Test TTS cache download when not found."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.download_file.side_effect = Exception("Not found")

        service = HLSService(mock_storage_service)
        result = service.download_tts_cache("user123", "job456", "/tmp/voice.mp3")

        assert result is False

    def test_tts_cache_exists_true(self, mock_storage_service):
        """Test TTS cache exists check returns True."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        result = service.tts_cache_exists("user123", "job456")

        assert result is True
        mock_storage_service.s3_client.head_object.assert_called_once()

    def test_tts_cache_exists_false(self, mock_storage_service):
        """Test TTS cache exists check returns False when not found."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")

        service = HLSService(mock_storage_service)
        result = service.tts_cache_exists("user123", "job456")

        assert result is False

    def test_list_segments(self, mock_storage_service):
        """Test listing segments for a job."""
        from src.services.hls_service import HLSService

        mock_storage_service.list_objects.return_value = [
            "user123/hls/job456/segment_000.ts",
            "user123/hls/job456/segment_001.ts",
            "user123/hls/job456/playlist.m3u8",
            "user123/hls/job456/voice.mp3",
        ]

        service = HLSService(mock_storage_service)
        segments = service.list_segments("user123", "job456")

        assert len(segments) == 2
        assert "user123/hls/job456/segment_000.ts" in segments
        assert "user123/hls/job456/segment_001.ts" in segments
        assert "user123/hls/job456/playlist.m3u8" not in segments

    def test_cleanup_hls_artifacts(self, mock_storage_service):
        """Test cleanup of HLS artifacts."""
        from src.services.hls_service import HLSService

        mock_storage_service.list_objects.return_value = [
            "user123/hls/job456/segment_000.ts",
            "user123/hls/job456/segment_001.ts",
            "user123/hls/job456/playlist.m3u8",
            "user123/hls/job456/voice.mp3",
        ]

        service = HLSService(mock_storage_service)
        result = service.cleanup_hls_artifacts("user123", "job456")

        assert result is True
        assert mock_storage_service.delete_object.call_count == 4

    def test_cleanup_hls_artifacts_handles_errors(self, mock_storage_service):
        """Test cleanup handles individual delete errors gracefully."""
        from src.services.hls_service import HLSService

        mock_storage_service.list_objects.return_value = [
            "user123/hls/job456/segment_000.ts",
            "user123/hls/job456/segment_001.ts",
        ]
        # First delete succeeds, second fails
        mock_storage_service.delete_object.side_effect = [True, Exception("Delete failed")]

        service = HLSService(mock_storage_service)
        result = service.cleanup_hls_artifacts("user123", "job456")

        # Should still return True (best effort cleanup)
        assert result is True

    def test_download_segment(self, mock_storage_service):
        """Test segment download."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)
        result = service.download_segment("user123", "job456", 0, "/tmp/segment_000.ts")

        assert result is True
        mock_storage_service.s3_client.download_file.assert_called_once()

    def test_url_expiry_configuration(self, mock_storage_service):
        """Test that URL expiry is configured correctly."""
        from src.services.hls_service import URL_EXPIRY

        assert URL_EXPIRY == 3600  # 1 hour

    def test_segment_duration_configuration(self, mock_storage_service):
        """Test that segment duration is configured correctly."""
        from src.services.hls_service import SEGMENT_DURATION

        assert SEGMENT_DURATION == 5  # 5 seconds
