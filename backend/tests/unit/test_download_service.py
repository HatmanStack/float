"""Unit tests for download service."""
from unittest.mock import MagicMock, mock_open, patch

import pytest


@pytest.fixture
def mock_storage_service():
    """Mock storage service with S3 client."""
    service = MagicMock()
    service.s3_client = MagicMock()
    return service


@pytest.fixture
def mock_hls_service():
    """Mock HLS service."""
    service = MagicMock()
    service.list_segments.return_value = [
        "user123/hls/job456/segment_000.ts",
        "user123/hls/job456/segment_001.ts",
        "user123/hls/job456/segment_002.ts",
    ]
    return service


@pytest.mark.unit
class TestDownloadService:
    """Test download service."""

    def test_service_initialization(self, mock_storage_service, mock_hls_service):
        """Test download service initializes correctly."""
        from src.services.download_service import DownloadService

        service = DownloadService(mock_storage_service, mock_hls_service)
        assert service is not None
        assert service.storage_service == mock_storage_service
        assert service.hls_service == mock_hls_service

    def test_get_download_key(self, mock_storage_service, mock_hls_service):
        """Test download key generation."""
        from src.services.download_service import DownloadService

        service = DownloadService(mock_storage_service, mock_hls_service)
        key = service.get_download_key("user123", "job456")

        assert key == "user123/downloads/job456.mp3"

    def test_check_mp3_exists_true(self, mock_storage_service, mock_hls_service):
        """Test MP3 exists check returns True."""
        from src.services.download_service import DownloadService

        service = DownloadService(mock_storage_service, mock_hls_service)
        result = service.check_mp3_exists("user123", "job456")

        assert result is True
        mock_storage_service.s3_client.head_object.assert_called_once()

    def test_check_mp3_exists_false(self, mock_storage_service, mock_hls_service):
        """Test MP3 exists check returns False when not found."""
        from src.services.download_service import DownloadService

        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")

        service = DownloadService(mock_storage_service, mock_hls_service)
        result = service.check_mp3_exists("user123", "job456")

        assert result is False

    def test_get_download_url_success(self, mock_storage_service, mock_hls_service):
        """Test download URL generation."""
        from src.services.download_service import DownloadService

        mock_storage_service.s3_client.generate_presigned_url.return_value = (
            "https://s3.../downloads/job456.mp3?signature=xyz"
        )

        service = DownloadService(mock_storage_service, mock_hls_service)
        url = service.get_download_url("user123", "job456")

        assert url == "https://s3.../downloads/job456.mp3?signature=xyz"

    def test_get_download_url_failure(self, mock_storage_service, mock_hls_service):
        """Test download URL generation handles errors."""
        from src.services.download_service import DownloadService

        mock_storage_service.s3_client.generate_presigned_url.side_effect = Exception("Error")

        service = DownloadService(mock_storage_service, mock_hls_service)
        url = service.get_download_url("user123", "job456")

        assert url is None

    def test_generate_mp3_returns_existing(self, mock_storage_service, mock_hls_service):
        """Test generate_mp3 returns existing key if MP3 exists."""
        from src.services.download_service import DownloadService

        # MP3 already exists
        service = DownloadService(mock_storage_service, mock_hls_service)
        result = service.generate_mp3("user123", "job456")

        assert result == "user123/downloads/job456.mp3"
        # Should not download segments if MP3 exists
        mock_hls_service.list_segments.assert_not_called()

    def test_generate_mp3_no_segments(self, mock_storage_service, mock_hls_service):
        """Test generate_mp3 handles no segments."""
        from src.services.download_service import DownloadService

        # MP3 doesn't exist
        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")
        # No segments
        mock_hls_service.list_segments.return_value = []

        service = DownloadService(mock_storage_service, mock_hls_service)
        result = service.generate_mp3("user123", "job456")

        assert result is None

    @patch("src.services.download_service.tempfile.mkdtemp")
    @patch("src.services.download_service.subprocess.run")
    @patch("src.services.download_service.shutil.rmtree")
    @patch("builtins.open", mock_open())
    @patch("os.path.exists", return_value=True)
    def test_generate_mp3_success(
        self, mock_exists, mock_rmtree, mock_subprocess, mock_mkdtemp,
        mock_storage_service, mock_hls_service
    ):
        """Test successful MP3 generation."""
        from src.services.download_service import DownloadService

        # Setup mocks
        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")
        mock_mkdtemp.return_value = "/tmp/mp3_gen_123"
        mock_subprocess.return_value = MagicMock(returncode=0)

        service = DownloadService(mock_storage_service, mock_hls_service)
        result = service.generate_mp3("user123", "job456")

        assert result == "user123/downloads/job456.mp3"
        # Should have downloaded segments
        assert mock_storage_service.s3_client.download_file.call_count == 3
        # Should have run FFmpeg
        mock_subprocess.assert_called_once()
        # Should have uploaded result
        mock_storage_service.s3_client.upload_file.assert_called_once()
        # Should have cleaned up
        mock_rmtree.assert_called()

    @patch("src.services.download_service.tempfile.mkdtemp")
    @patch("src.services.download_service.subprocess.run")
    @patch("src.services.download_service.shutil.rmtree")
    @patch("builtins.open", mock_open())
    @patch("os.path.exists", return_value=True)
    def test_generate_mp3_ffmpeg_failure(
        self, mock_exists, mock_rmtree, mock_subprocess, mock_mkdtemp,
        mock_storage_service, mock_hls_service
    ):
        """Test MP3 generation handles FFmpeg failure."""
        from src.services.download_service import DownloadService

        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")
        mock_mkdtemp.return_value = "/tmp/mp3_gen_123"
        mock_subprocess.return_value = MagicMock(returncode=1, stderr="FFmpeg error")

        service = DownloadService(mock_storage_service, mock_hls_service)
        result = service.generate_mp3("user123", "job456")

        assert result is None
        # Should have cleaned up even on failure
        mock_rmtree.assert_called()

    @patch("src.services.download_service.tempfile.mkdtemp")
    @patch("src.services.download_service.shutil.rmtree")
    @patch("os.path.exists", return_value=True)
    def test_generate_mp3_download_failure(
        self, mock_exists, mock_rmtree, mock_mkdtemp,
        mock_storage_service, mock_hls_service
    ):
        """Test MP3 generation handles segment download failure."""
        from src.services.download_service import DownloadService

        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")
        mock_mkdtemp.return_value = "/tmp/mp3_gen_123"
        mock_storage_service.s3_client.download_file.side_effect = Exception("Download failed")

        service = DownloadService(mock_storage_service, mock_hls_service)
        result = service.generate_mp3("user123", "job456")

        assert result is None

    def test_generate_mp3_and_get_url_success(self, mock_storage_service, mock_hls_service):
        """Test generate_mp3_and_get_url returns URL for existing MP3."""
        from src.services.download_service import DownloadService

        mock_storage_service.s3_client.generate_presigned_url.return_value = (
            "https://s3.../downloads/job456.mp3?signature=xyz"
        )

        service = DownloadService(mock_storage_service, mock_hls_service)
        url = service.generate_mp3_and_get_url("user123", "job456")

        assert url == "https://s3.../downloads/job456.mp3?signature=xyz"

    def test_generate_mp3_and_get_url_failure(self, mock_storage_service, mock_hls_service):
        """Test generate_mp3_and_get_url handles generation failure."""
        from src.services.download_service import DownloadService

        # MP3 doesn't exist and no segments
        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")
        mock_hls_service.list_segments.return_value = []

        service = DownloadService(mock_storage_service, mock_hls_service)
        url = service.generate_mp3_and_get_url("user123", "job456")

        assert url is None

    def test_url_expiry_configuration(self, mock_storage_service, mock_hls_service):
        """Test that URL expiry is configured correctly."""
        from src.services.download_service import DOWNLOAD_URL_EXPIRY

        assert DOWNLOAD_URL_EXPIRY == 3600  # 1 hour
