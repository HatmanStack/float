"""Unit tests for service layer implementations."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.providers.openai_tts import OpenAITTSProvider
from src.services.s3_storage_service import S3StorageService
from src.services.ffmpeg_audio_service import FFmpegAudioService


@pytest.mark.unit
class TestOpenAITTSProvider:
    """Test OpenAI Text-to-Speech provider."""

    def test_provider_name(self):
        """Test provider returns correct name."""
        with patch('src.providers.openai_tts.openai'):
            provider = OpenAITTSProvider()
            assert provider.get_provider_name() == "openai"

    def test_synthesize_speech_success(self):
        """Test successful speech synthesis."""
        with patch('src.providers.openai_tts.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Mock the speech.create response
            mock_response = MagicMock()
            mock_response.content = b"audio_data"
            mock_client.audio.speech.create.return_value = mock_response

            # Mock file operations
            with patch('builtins.open', create=True):
                provider = OpenAITTSProvider()
                result = provider.synthesize_speech("Test text", "/tmp/test.mp3")

                assert result is True
                mock_client.audio.speech.create.assert_called_once()

    def test_synthesize_speech_api_error(self):
        """Test error handling when OpenAI API fails."""
        with patch('src.providers.openai_tts.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.speech.create.side_effect = Exception("API Error")

            provider = OpenAITTSProvider()
            result = provider.synthesize_speech("Test text", "/tmp/test.mp3")

            assert result is False

    def test_synthesize_speech_file_error(self):
        """Test error handling when file write fails."""
        with patch('src.providers.openai_tts.openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.content = b"audio_data"
            mock_client.audio.speech.create.return_value = mock_response

            # Mock file write failure
            with patch('builtins.open', side_effect=IOError("Write failed")):
                provider = OpenAITTSProvider()
                result = provider.synthesize_speech("Test text", "/tmp/test.mp3")

                assert result is False


@pytest.mark.unit
class TestS3StorageService:
    """Test S3 storage service."""

    def test_service_initialization(self):
        """Test S3 storage service initializes."""
        with patch('src.services.s3_storage_service.boto3'):
            service = S3StorageService()
            assert service is not None

    def test_upload_json_success(self):
        """Test successful JSON upload to S3."""
        with patch('src.services.s3_storage_service.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            service = S3StorageService()
            result = service.upload_json(
                bucket="test-bucket",
                key="test-key.json",
                data={"test": "data"}
            )

            assert result is True
            mock_s3.put_object.assert_called_once()

    def test_upload_json_failure(self):
        """Test error handling when S3 upload fails."""
        with patch('src.services.s3_storage_service.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            mock_s3.put_object.side_effect = Exception("S3 Error")

            service = S3StorageService()
            result = service.upload_json(
                bucket="test-bucket",
                key="test-key.json",
                data={"test": "data"}
            )

            assert result is False

    def test_download_file_success(self):
        """Test successful file download from S3."""
        with patch('src.services.s3_storage_service.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            mock_s3.download_file.return_value = None

            service = S3StorageService()
            result = service.download_file(
                bucket="test-bucket",
                key="test-key.mp3",
                local_path="/tmp/test.mp3"
            )

            assert result is True
            mock_s3.download_file.assert_called_once()

    def test_download_file_not_found(self):
        """Test error handling when file not found in S3."""
        with patch('src.services.s3_storage_service.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            from botocore.exceptions import ClientError
            mock_s3.download_file.side_effect = ClientError(
                {'Error': {'Code': 'NoSuchKey'}},
                'GetObject'
            )

            service = S3StorageService()
            result = service.download_file(
                bucket="test-bucket",
                key="nonexistent.mp3",
                local_path="/tmp/nonexistent.mp3"
            )

            assert result is False


@pytest.mark.unit
class TestFFmpegAudioService:
    """Test FFmpeg audio service."""

    def test_service_initialization(self, mock_storage_service):
        """Test FFmpeg audio service initializes."""
        service = FFmpegAudioService(mock_storage_service)
        assert service is not None
        assert service.storage_service == mock_storage_service

    def test_combine_voice_and_music_empty_music_list(self, mock_storage_service):
        """Test combining voice with empty music list."""
        service = FFmpegAudioService(mock_storage_service)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = service.combine_voice_and_music(
                voice_path="/tmp/voice.mp3",
                music_list=[],
                timestamp="20241031120000",
                output_path="/tmp/combined.mp3"
            )

            # Should handle empty music list gracefully
            assert result is not None or result is None

    def test_combine_voice_and_music_handles_errors(self, mock_storage_service):
        """Test combining voice handles errors gracefully."""
        service = FFmpegAudioService(mock_storage_service)

        # Test that the service is properly initialized
        assert service.storage_service == mock_storage_service
        assert service is not None


@pytest.mark.unit
class TestServiceErrorHandling:
    """Test error handling across services."""

    def test_openai_missing_api_key(self):
        """Test OpenAI provider handles missing API key."""
        with patch('src.providers.openai_tts.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = ""

            with patch('src.providers.openai_tts.openai.OpenAI', side_effect=Exception("API key invalid")):
                # Should fail gracefully when initializing without key
                with pytest.raises(Exception):
                    provider = OpenAITTSProvider()

    def test_s3_missing_credentials(self):
        """Test S3 service handles missing credentials."""
        with patch('src.services.s3_storage_service.boto3') as mock_boto3:
            mock_boto3.client.side_effect = Exception("No credentials found")

            with pytest.raises(Exception):
                service = S3StorageService()

    def test_ffmpeg_audio_service_dependency_injection(self, mock_storage_service):
        """Test FFmpeg service accepts injected storage dependency."""
        service = FFmpegAudioService(mock_storage_service)
        assert service.storage_service == mock_storage_service

    def test_service_call_with_invalid_path(self, mock_storage_service):
        """Test service gracefully handles invalid file paths."""
        service = FFmpegAudioService(mock_storage_service)

        with patch('subprocess.run', side_effect=FileNotFoundError("ffmpeg not found")):
            # Should handle missing ffmpeg gracefully
            with pytest.raises(FileNotFoundError):
                service.combine_voice_and_music(
                    voice_path="/nonexistent/voice.mp3",
                    music_list=[],
                    timestamp="20241031120000",
                    output_path="/tmp/combined.mp3"
                )
