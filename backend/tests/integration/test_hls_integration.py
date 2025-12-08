"""Integration tests for HLS streaming backend flow.

These tests verify the end-to-end HLS streaming functionality when
ENABLE_HLS_STREAMING is enabled. They require AWS credentials and
network access to run.
"""
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_aws_services():
    """Mock AWS services for integration tests."""
    with patch.dict(os.environ, {
        "ENABLE_HLS_STREAMING": "true",
        "AWS_S3_BUCKET": "test-bucket",
        "AWS_AUDIO_BUCKET": "test-audio-bucket",
    }):
        yield


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    client = MagicMock()
    client.generate_presigned_url.return_value = "https://s3.../presigned-url"
    client.put_object.return_value = {}
    client.upload_file.return_value = None
    client.download_file.return_value = None
    client.head_object.return_value = {}
    return client


@pytest.fixture
def mock_storage_service(mock_s3_client):
    """Mock storage service with S3 client."""
    from unittest.mock import MagicMock
    service = MagicMock()
    service.s3_client = mock_s3_client
    service.list_objects.return_value = []
    service.download_json.return_value = None
    service.upload_json.return_value = True
    service.delete_object.return_value = True
    return service


@pytest.mark.integration
class TestHLSIntegration:
    """Integration tests for HLS streaming flow."""

    def test_job_creation_with_hls_enabled(self, mock_storage_service):
        """Test that job creation includes HLS streaming fields."""
        from src.services.job_service import JobService

        service = JobService(mock_storage_service)
        job_id = service.create_job("user123", "meditation", enable_streaming=True)

        assert job_id is not None
        # Verify job data was saved with streaming fields
        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["streaming"]["enabled"] is True
        assert job_data["download"]["available"] is False

    def test_hls_service_segment_workflow(self, mock_storage_service):
        """Test HLS service segment upload and playlist generation."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)

        # Upload segments
        for i in range(3):
            result = service.upload_segment("user123", "job456", i, b"segment_data")
            assert result is True

        # Verify put_object was called for each segment
        assert mock_storage_service.s3_client.put_object.call_count == 3

    def test_playlist_generation_format(self, mock_storage_service):
        """Test HLS playlist format is correct."""
        from src.services.hls_service import HLSService

        mock_storage_service.s3_client.generate_presigned_url.side_effect = lambda *args, **kwargs: (
            "https://s3.../segment.ts?sig=abc"
        )

        service = HLSService(mock_storage_service)
        content = service.generate_live_playlist(
            "user123", "job456",
            segment_count=3,
            segment_durations=[5.0, 5.0, 4.5],
            is_complete=True
        )

        # Verify HLS format
        assert "#EXTM3U" in content
        assert "#EXT-X-VERSION:3" in content
        assert "#EXT-X-ENDLIST" in content
        assert "#EXTINF:" in content

    def test_job_status_transitions(self, mock_storage_service):
        """Test job status transitions through HLS flow."""
        from src.services.job_service import JobService, JobStatus

        # Setup mock to return job data
        job_data = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "pending",
            "streaming": {
                "enabled": True,
                "playlist_url": None,
                "segments_completed": 0,
                "segments_total": None,
                "started_at": None,
            },
            "download": {
                "available": False,
                "url": None,
                "downloaded": False,
            }
        }
        mock_storage_service.download_json.return_value = job_data.copy()

        service = JobService(mock_storage_service)

        # Transition: pending -> processing
        service.update_job_status("user123", "test-job", JobStatus.PROCESSING)

        # Transition: processing -> streaming
        service.mark_streaming_started("user123", "test-job", "https://s3.../playlist.m3u8")

        # Update streaming progress
        for i in range(1, 4):
            service.update_streaming_progress("user123", "test-job", segments_completed=i)

        # Transition: streaming -> completed
        service.mark_streaming_complete("user123", "test-job", segments_total=3)

        # Verify final state
        final_call_args = mock_storage_service.upload_json.call_args_list[-1]
        final_data = final_call_args[1]["data"] if "data" in final_call_args[1] else final_call_args[0][2]

        assert final_data["status"] == "completed"
        assert final_data["download"]["available"] is True

    def test_download_service_mp3_generation(self, mock_storage_service):
        """Test download service checks for segments when generating."""
        from src.services.download_service import DownloadService
        from src.services.hls_service import HLSService

        # Setup HLS service with no segments (so we don't need FFmpeg)
        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")
        mock_storage_service.list_objects.return_value = []  # Empty = no segments

        hls_service = HLSService(mock_storage_service)
        download_service = DownloadService(mock_storage_service, hls_service)

        # Attempting to generate should return None when no segments
        result = download_service.generate_mp3("user123", "job456")

        # Should be None since no segments found
        assert result is None
        # Verify segments were checked
        mock_storage_service.list_objects.assert_called()

    def test_tts_cache_retry_flow(self, mock_storage_service):
        """Test TTS cache enables retry without regeneration."""
        from src.services.hls_service import HLSService

        service = HLSService(mock_storage_service)

        # First attempt - no cache
        mock_storage_service.s3_client.head_object.side_effect = Exception("Not found")
        assert service.tts_cache_exists("user123", "job456") is False

        # Upload TTS cache
        mock_storage_service.s3_client.head_object.side_effect = None
        assert service.upload_tts_cache("user123", "job456", "/tmp/voice.mp3") is True

        # Second attempt - cache exists
        assert service.tts_cache_exists("user123", "job456") is True

    def test_cleanup_flow(self, mock_storage_service):
        """Test cleanup removes HLS artifacts after download."""
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


@pytest.mark.integration
class TestFeatureFlag:
    """Tests for ENABLE_HLS_STREAMING feature flag."""

    def test_feature_flag_parsing_true(self):
        """Test feature flag is parsed as true."""
        with patch.dict(os.environ, {"ENABLE_HLS_STREAMING": "true"}):
            # Re-import to pick up new env var
            import importlib

            from src.handlers import lambda_handler
            importlib.reload(lambda_handler)

            from src.handlers.lambda_handler import ENABLE_HLS_STREAMING
            assert ENABLE_HLS_STREAMING is True

    def test_feature_flag_parsing_false(self):
        """Test feature flag is parsed as false."""
        with patch.dict(os.environ, {"ENABLE_HLS_STREAMING": "false"}):
            import importlib

            from src.handlers import lambda_handler
            importlib.reload(lambda_handler)

            from src.handlers.lambda_handler import ENABLE_HLS_STREAMING
            assert ENABLE_HLS_STREAMING is False

    def test_feature_flag_defaults_to_true(self):
        """Test feature flag defaults to true when not set."""
        env_without_flag = {k: v for k, v in os.environ.items() if k != "ENABLE_HLS_STREAMING"}
        with patch.dict(os.environ, env_without_flag, clear=True):
            import importlib

            from src.handlers import lambda_handler
            importlib.reload(lambda_handler)

            from src.handlers.lambda_handler import ENABLE_HLS_STREAMING
            assert ENABLE_HLS_STREAMING is True


@pytest.mark.integration
class TestEndToEndFlow:
    """End-to-end integration tests simulating full API flow."""

    def test_meditation_request_returns_job_with_streaming(self, mock_storage_service):
        """Test meditation request returns job with streaming info."""
        from unittest.mock import MagicMock, patch

        from src.handlers.lambda_handler import LambdaHandler

        with patch.dict(os.environ, {"ENABLE_HLS_STREAMING": "true"}):
            with patch("src.handlers.lambda_handler.S3StorageService", return_value=mock_storage_service):
                with patch("src.handlers.lambda_handler.boto3.client") as mock_boto:
                    mock_lambda = MagicMock()
                    mock_boto.return_value = mock_lambda

                    handler = LambdaHandler(validate_config=False)

                    from src.config.constants import InferenceType
                    from src.models.requests import MeditationRequest
                    request = MeditationRequest(
                        user_id="test-user",
                        inference_type=InferenceType.MEDITATION,
                        input_data={"sentiment_label": ["Happy"]},
                        music_list=[],
                    )

                    result = handler.handle_meditation_request(request)

                    assert "job_id" in result
                    assert result["status"] == "pending"
                    assert result.get("streaming", {}).get("enabled") is True

    def test_job_status_refreshes_playlist_url(self, mock_storage_service):
        """Test job status returns fresh pre-signed playlist URL."""
        from unittest.mock import patch

        from src.handlers.lambda_handler import LambdaHandler

        # Setup job with streaming
        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "streaming",
            "streaming": {
                "enabled": True,
                "playlist_url": "https://old-url/playlist.m3u8",
                "segments_completed": 5,
                "segments_total": None,
            }
        }

        mock_storage_service.s3_client.generate_presigned_url.return_value = (
            "https://fresh-url/playlist.m3u8?new-sig=xyz"
        )

        with patch("src.handlers.lambda_handler.S3StorageService", return_value=mock_storage_service):
            handler = LambdaHandler(validate_config=False)
            result = handler.handle_job_status("user123", "test-job")

            # Should have fresh URL
            assert result["streaming"]["playlist_url"] == "https://fresh-url/playlist.m3u8?new-sig=xyz"

    def test_download_request_validates_job_state(self, mock_storage_service):
        """Test download request validates job is completed."""
        from unittest.mock import patch

        from src.handlers.lambda_handler import LambdaHandler

        # Job not completed
        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "streaming",  # Not completed
            "download": {"available": False}
        }

        with patch("src.handlers.lambda_handler.S3StorageService", return_value=mock_storage_service):
            handler = LambdaHandler(validate_config=False)
            result = handler.handle_download_request("user123", "test-job")

            assert "error" in result
            assert result["error"]["code"] == "JOB_NOT_COMPLETED"

    def test_download_request_validates_availability(self, mock_storage_service):
        """Test download request validates download is available."""
        from unittest.mock import patch

        from src.handlers.lambda_handler import LambdaHandler

        # Job completed but download not available
        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "completed",
            "download": {"available": False}  # Not available
        }

        with patch("src.handlers.lambda_handler.S3StorageService", return_value=mock_storage_service):
            handler = LambdaHandler(validate_config=False)
            result = handler.handle_download_request("user123", "test-job")

            assert "error" in result
            assert result["error"]["code"] == "DOWNLOAD_NOT_AVAILABLE"
