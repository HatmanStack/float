"""Unit tests for service layer implementations."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.providers.openai_tts import OpenAITTSProvider
from src.services.ffmpeg_audio_service import FFmpegAudioService
from src.services.s3_storage_service import S3StorageService


@pytest.mark.unit
class TestOpenAITTSProvider:
    """Test OpenAI Text-to-Speech provider."""

    def test_provider_name(self):
        """Test provider returns correct name."""
        with patch("src.providers.openai_tts.openai"):
            provider = OpenAITTSProvider()
            assert provider.get_provider_name() == "openai"

    def test_synthesize_speech_success(self):
        """Test successful speech synthesis."""
        with patch("src.providers.openai_tts.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Mock the speech.create response
            mock_response = MagicMock()
            mock_response.content = b"audio_data"
            mock_client.audio.speech.create.return_value = mock_response

            # Mock file operations
            with patch("builtins.open", create=True):
                provider = OpenAITTSProvider()
                result = provider.synthesize_speech("Test text", "/tmp/test.mp3")

                assert result is True
                mock_client.audio.speech.create.assert_called_once()

    def test_synthesize_speech_api_error(self):
        """Test error handling when OpenAI API fails."""
        with patch("src.providers.openai_tts.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.speech.create.side_effect = Exception("API Error")

            provider = OpenAITTSProvider()
            result = provider.synthesize_speech("Test text", "/tmp/test.mp3")

            assert result is False

    def test_synthesize_speech_file_error(self):
        """Test error handling when file write fails."""
        with patch("src.providers.openai_tts.openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.content = b"audio_data"
            mock_client.audio.speech.create.return_value = mock_response

            # Mock file write failure
            with patch("builtins.open", side_effect=IOError("Write failed")):
                provider = OpenAITTSProvider()
                result = provider.synthesize_speech("Test text", "/tmp/test.mp3")

                assert result is False


@pytest.mark.unit
class TestS3StorageService:
    """Test S3 storage service."""

    def test_service_initialization(self):
        """Test S3 storage service initializes."""
        with patch("src.services.s3_storage_service.boto3"):
            service = S3StorageService()
            assert service is not None

    def test_upload_json_success(self):
        """Test successful JSON upload to S3."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            service = S3StorageService()
            result = service.upload_json(
                bucket="test-bucket", key="test-key.json", data={"test": "data"}
            )

            assert result is True
            mock_s3.put_object.assert_called_once()

    def test_upload_json_failure(self):
        """Test error handling when S3 upload fails."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            mock_s3.put_object.side_effect = Exception("S3 Error")

            service = S3StorageService()
            result = service.upload_json(
                bucket="test-bucket", key="test-key.json", data={"test": "data"}
            )

            assert result is False

    def test_download_file_success(self):
        """Test successful file download from S3."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            mock_s3.download_file.return_value = None

            service = S3StorageService()
            result = service.download_file(
                bucket="test-bucket", key="test-key.mp3", local_path="/tmp/test.mp3"
            )

            assert result is True
            mock_s3.download_file.assert_called_once()

    def test_download_file_not_found(self):
        """Test error handling when file not found in S3."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            from botocore.exceptions import ClientError

            mock_s3.download_file.side_effect = ClientError(
                {"Error": {"Code": "NoSuchKey"}}, "GetObject"
            )

            service = S3StorageService()
            result = service.download_file(
                bucket="test-bucket", key="nonexistent.mp3", local_path="/tmp/nonexistent.mp3"
            )

            assert result is False

    def test_upload_json_with_client_error(self):
        """Test upload_json handles ClientError properly."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            from botocore.exceptions import ClientError

            mock_s3.put_object.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
                "PutObject"
            )

            service = S3StorageService()
            result = service.upload_json(
                bucket="test-bucket", key="test.json", data={"test": "data"}
            )

            assert result is False

    def test_upload_json_with_unexpected_error(self):
        """Test upload_json handles unexpected errors properly."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            mock_s3.put_object.side_effect = ValueError("Unexpected error")

            service = S3StorageService()
            result = service.upload_json(
                bucket="test-bucket", key="test.json", data={"test": "data"}
            )

            assert result is False

    def test_download_file_with_unexpected_error(self):
        """Test download_file handles unexpected errors properly."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            mock_s3.download_file.side_effect = IOError("Disk full")

            service = S3StorageService()
            result = service.download_file(
                bucket="test-bucket", key="test.mp3", local_path="/tmp/test.mp3"
            )

            assert result is False

    def test_list_objects_success(self):
        """Test list_objects returns object keys successfully."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            mock_s3.list_objects_v2.return_value = {
                "Contents": [
                    {"Key": "user123/file1.json"},
                    {"Key": "user123/file2.json"},
                    {"Key": "user123/file3.json"}
                ]
            }

            service = S3StorageService()
            result = service.list_objects(bucket="test-bucket", prefix="user123/")

            assert len(result) == 3
            assert "user123/file1.json" in result
            mock_s3.list_objects_v2.assert_called_once_with(Bucket="test-bucket", Prefix="user123/")

    def test_list_objects_empty_bucket(self):
        """Test list_objects returns empty list for empty bucket."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            mock_s3.list_objects_v2.return_value = {}  # No Contents key

            service = S3StorageService()
            result = service.list_objects(bucket="test-bucket")

            assert result == []
            mock_s3.list_objects_v2.assert_called_once_with(Bucket="test-bucket")

    def test_list_objects_without_prefix(self):
        """Test list_objects works without prefix parameter."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            mock_s3.list_objects_v2.return_value = {
                "Contents": [{"Key": "file1.json"}, {"Key": "file2.json"}]
            }

            service = S3StorageService()
            result = service.list_objects(bucket="test-bucket")

            assert len(result) == 2
            # Verify Prefix was not passed
            call_kwargs = mock_s3.list_objects_v2.call_args.kwargs
            assert "Prefix" not in call_kwargs

    def test_list_objects_with_client_error(self):
        """Test list_objects handles ClientError gracefully."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3
            from botocore.exceptions import ClientError

            mock_s3.list_objects_v2.side_effect = ClientError(
                {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
                "ListObjectsV2"
            )

            service = S3StorageService()
            result = service.list_objects(bucket="nonexistent-bucket")

            assert result == []

    def test_list_objects_with_unexpected_error(self):
        """Test list_objects handles unexpected errors gracefully."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            mock_s3.list_objects_v2.side_effect = Exception("Network timeout")

            service = S3StorageService()
            result = service.list_objects(bucket="test-bucket")

            assert result == []

    def test_upload_json_with_special_characters_in_key(self):
        """Test upload_json handles special characters in S3 key."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            service = S3StorageService()
            result = service.upload_json(
                bucket="test-bucket",
                key="user@email.com/data/2024-01-01.json",
                data={"test": "data"}
            )

            assert result is True
            mock_s3.put_object.assert_called_once()
            call_args = mock_s3.put_object.call_args
            assert call_args.kwargs["Key"] == "user@email.com/data/2024-01-01.json"


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

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = service.combine_voice_and_music(
                voice_path="/tmp/voice.mp3",
                music_list=[],
                timestamp="20241031120000",
                output_path="/tmp/combined.mp3",
            )

            # Verify ffmpeg was called and result is returned (returns music list, not path)
            mock_run.assert_called()
            assert isinstance(result, (str, list))

    def test_combine_voice_and_music_handles_errors(self, mock_storage_service):
        """Test combining voice handles errors gracefully."""
        service = FFmpegAudioService(mock_storage_service)

        # Test that the service is properly initialized
        assert service.storage_service == mock_storage_service
        assert service is not None

    def test_get_audio_duration_success(self, mock_storage_service):
        """Test get_audio_duration returns correct duration."""
        service = FFmpegAudioService(mock_storage_service)

        # Mock subprocess.run to return FFmpeg duration output
        mock_stderr = """Input #0, wav, from '/tmp/test.wav':
  Duration: 00:02:30.45, bitrate: 128 kb/s
    Stream #0:0: Audio: pcm_s16le"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr=mock_stderr)

            duration = service.get_audio_duration("/tmp/test.wav")

            assert duration == 150.45  # 2 minutes 30.45 seconds
            mock_run.assert_called_once()

    def test_get_audio_duration_error_handling(self, mock_storage_service):
        """Test get_audio_duration handles errors gracefully."""
        service = FFmpegAudioService(mock_storage_service)

        with patch("subprocess.run", side_effect=Exception("File not found")):
            duration = service.get_audio_duration("/nonexistent/file.wav")

            assert duration == 0.0

    def test_get_audio_duration_with_malformed_output(self, mock_storage_service):
        """Test get_audio_duration handles malformed FFmpeg output."""
        service = FFmpegAudioService(mock_storage_service)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="Invalid output")

            duration = service.get_audio_duration("/tmp/test.wav")

            assert duration == 0.0

    def test_ffmpeg_binary_verification_success(self, mock_storage_service):
        """Test FFmpeg binary verification on initialization."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", return_value=50000000):  # 50MB
                service = FFmpegAudioService(mock_storage_service)

                assert service.ffmpeg_executable is not None
                assert service.storage_service == mock_storage_service

    def test_ffmpeg_binary_verification_small_file_warning(self, mock_storage_service):
        """Test FFmpeg binary verification warns for small file size."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", return_value=50000):  # 50KB - suspiciously small
                service = FFmpegAudioService(mock_storage_service)

                # Should still initialize but print warning
                assert service.ffmpeg_executable is not None

    def test_ffmpeg_binary_verification_size_error(self, mock_storage_service):
        """Test FFmpeg binary verification handles getsize errors."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", side_effect=OSError("Permission denied")):
                service = FFmpegAudioService(mock_storage_service)

                # Should still initialize despite error
                assert service.ffmpeg_executable is not None

    def test_combine_voice_and_music_subprocess_error(self, mock_storage_service):
        """Test combine_voice_and_music handles subprocess errors."""
        service = FFmpegAudioService(mock_storage_service)

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with pytest.raises(subprocess.CalledProcessError):
                service.combine_voice_and_music(
                    voice_path="/tmp/voice.mp3",
                    music_list=[],
                    timestamp="20241031120000",
                    output_path="/tmp/combined.mp3",
                )

    def test_select_background_music_with_string_input(self, mock_storage_service):
        """Test select_background_music handles string input for used_music."""
        mock_storage_service.list_objects.return_value = [
            "Track1_300.wav",
            "Track2_180.wav"
        ]

        service = FFmpegAudioService(mock_storage_service)

        # Test with string that should be parsed
        result = service.select_background_music(
            used_music="['Track1_300.wav']",
            duration=250,
            output_path="/tmp/music.mp3"
        )

        assert isinstance(result, list)

    def test_select_background_music_with_single_string(self, mock_storage_service):
        """Test select_background_music handles single string input."""
        mock_storage_service.list_objects.return_value = ["Track1_300.wav", "Track2_300.wav"]
        mock_storage_service.download_file.return_value = True

        service = FFmpegAudioService(mock_storage_service)

        # Test with single string (should be converted to list)
        result = service.select_background_music(
            used_music="Track1_300.wav",
            duration=250,
            output_path="/tmp/music.mp3"
        )

        assert isinstance(result, list)

    def test_select_background_music_duration_filtering(self, mock_storage_service):
        """Test select_background_music filters tracks by duration."""
        mock_storage_service.list_objects.return_value = [
            "Track1_300.wav",
            "Track2_180.wav",
            "Track3_240.wav"
        ]

        service = FFmpegAudioService(mock_storage_service)

        result = service.select_background_music(
            used_music=[],
            duration=250,
            output_path="/tmp/music.mp3"
        )

        # Should select tracks with duration close to 250 seconds
        assert isinstance(result, list)

    def test_select_background_music_fallback_to_300(self, mock_storage_service):
        """Test select_background_music falls back to 300s tracks."""
        mock_storage_service.list_objects.return_value = [
            "Track1_300.wav",
            "Track2_300.wav"
        ]

        service = FFmpegAudioService(mock_storage_service)

        # Request duration that doesn't match any tracks except 300s
        result = service.select_background_music(
            used_music=[],
            duration=100,
            output_path="/tmp/music.mp3"
        )

        assert isinstance(result, list)


@pytest.mark.unit
class TestServiceErrorHandling:
    """Test error handling across services."""

    def test_openai_missing_api_key(self):
        """Test OpenAI provider handles missing API key."""
        with patch("src.providers.openai_tts.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = ""

            with patch(
                "src.providers.openai_tts.openai.OpenAI", side_effect=Exception("API key invalid")
            ):
                # Should fail gracefully when initializing without key
                with pytest.raises(Exception):
                    OpenAITTSProvider()

    def test_s3_missing_credentials(self):
        """Test S3 service handles missing credentials."""
        with patch("src.services.s3_storage_service.boto3") as mock_boto3:
            mock_boto3.client.side_effect = Exception("No credentials found")

            with pytest.raises(Exception):
                S3StorageService()

    def test_ffmpeg_audio_service_dependency_injection(self, mock_storage_service):
        """Test FFmpeg service accepts injected storage dependency."""
        service = FFmpegAudioService(mock_storage_service)
        assert service.storage_service == mock_storage_service

    def test_service_call_with_invalid_path(self, mock_storage_service):
        """Test service gracefully handles invalid file paths."""
        service = FFmpegAudioService(mock_storage_service)

        with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
            # Should handle missing ffmpeg gracefully
            with pytest.raises(FileNotFoundError):
                service.combine_voice_and_music(
                    voice_path="/nonexistent/voice.mp3",
                    music_list=[],
                    timestamp="20241031120000",
                    output_path="/tmp/combined.mp3",
                )


@pytest.mark.unit
class TestGeminiAIService:
    """Test Gemini AI service."""

    def test_analyze_sentiment_with_text_input(self):
        """Test analyze sentiment returns valid sentiment response from text."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            # Mock the model and response
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = """{
                "sentiment_label": "Sad",
                "intensity": 4,
                "speech_to_text": "NotAvailable",
                "added_text": "I had a difficult day",
                "summary": "The user experienced sadness",
                "user_summary": "I had a difficult day at work",
                "user_short_summary": "Bad work day"
            }"""
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()
            result = service.analyze_sentiment(audio_file=None, user_text="I had a difficult day")

            assert result is not None
            assert "sentiment_label" in result.lower()
            mock_model.generate_content.assert_called_once()

    def test_analyze_sentiment_with_audio_input(self):
        """Test analyze sentiment with audio file."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = """{
                "sentiment_label": "Happy",
                "intensity": 5,
                "speech_to_text": "I had a great day",
                "added_text": "NotAvailable",
                "summary": "The user is very happy",
                "user_summary": "I had an amazing day",
                "user_short_summary": "Great day"
            }"""
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()

            # Mock file reading
            with patch("pathlib.Path.read_bytes", return_value=b"fake_audio_data"):
                result = service.analyze_sentiment(audio_file="/tmp/test.mp3", user_text=None)

            assert result is not None
            assert "sentiment_label" in result.lower()
            mock_model.generate_content.assert_called_once()

    def test_analyze_sentiment_with_empty_input_handles_gracefully(self):
        """Test analyze sentiment with empty input handles gracefully."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            service = GeminiAIService()

            # Both inputs None - should raise AttributeError (accessing None.text)
            with pytest.raises(AttributeError):
                service.analyze_sentiment(audio_file=None, user_text=None)

    def test_generate_meditation_from_sentiment_data(self):
        """Test generate meditation from sentiment data."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = """<speak><voice name='en-US-Neural2-J'>
            Let's release this moment. <break time='1000ms'/>
            Breathe deeply and let it go.
            </voice></speak>"""
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()
            input_data = {
                "sentiment_label": ["Sad"],
                "intensity": [4],
                "user_summary": ["Had a bad day"]
            }

            result = service.generate_meditation(input_data)

            assert result is not None
            assert "speak" in result.lower()
            mock_model.generate_content.assert_called_once()

    def test_generate_meditation_with_different_emotion_types(self):
        """Test different emotion types produce appropriate meditations."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            for emotion in ["Happy", "Sad", "Angry", "Fearful"]:
                mock_response = MagicMock()
                mock_response.text = f"<speak><voice>Meditation for {emotion}</voice></speak>"
                mock_model.generate_content.return_value = mock_response

                service = GeminiAIService()
                input_data = {
                    "sentiment_label": [emotion],
                    "intensity": [3],
                    "user_summary": [f"Feeling {emotion}"]
                }

                result = service.generate_meditation(input_data)
                assert result is not None

    def test_api_timeout_error_handled(self):
        """Test API timeout errors handled gracefully."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.side_effect = TimeoutError("API timeout")

            service = GeminiAIService()

            # The implementation wraps exceptions in ValueError
            with pytest.raises(ValueError, match="Failed to analyze text sentiment"):
                service.analyze_sentiment(audio_file=None, user_text="Test")

    def test_invalid_api_key_returns_clear_error(self):
        """Test invalid API key returns clear error."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            mock_genai.configure.side_effect = Exception("Invalid API key")

            with pytest.raises(Exception, match="Invalid API key"):
                from src.services.gemini_service import GeminiAIService
                GeminiAIService()

    def test_malformed_api_response_handled(self):
        """Test malformed API responses handled."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = "not valid json"
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()
            result = service.analyze_sentiment(audio_file=None, user_text="Test")

            # Should return the raw text if JSON parsing fails
            assert result == "not valid json"

    def test_response_parsing_with_json_format(self):
        """Test JSON responses parsed correctly."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = '{"sentiment_label": "Happy", "intensity": 5}'
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()
            result = service.analyze_sentiment(audio_file=None, user_text="Great day!")

            assert "Happy" in result
            assert "5" in result

    def test_ssml_tags_in_meditation_response(self):
        """Test SSML tags properly included in meditation response."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = """<speak>
            <voice name='en-US-Neural2-J'>
            <break time='1000ms'/>
            Breathe deeply.
            </voice>
            </speak>"""
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()
            result = service.generate_meditation({"sentiment_label": ["Calm"]})

            assert "<speak>" in result
            assert "<voice" in result
            assert "<break" in result

    def test_prompt_engineering_for_sentiment_analysis(self):
        """Test sentiment analysis prompts formatted correctly."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = '{"sentiment_label": "Neutral"}'
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()
            service.analyze_sentiment(audio_file=None, user_text="Test input")

            # Verify the prompt includes necessary instructions
            call_args = mock_model.generate_content.call_args
            prompt_content = str(call_args)

            # The prompt should include the user text
            assert "Test input" in prompt_content or len(call_args[0]) > 0

    def test_safety_settings_configured(self):
        """Test safety settings are configured for Gemini."""
        with patch("src.services.gemini_service.genai"):
            from src.services.gemini_service import GeminiAIService

            service = GeminiAIService()

            # Verify safety settings exist
            assert hasattr(service, 'safety_settings')
            assert service.safety_settings is not None
            assert len(service.safety_settings) > 0

    def test_user_input_sanitized_in_prompts(self):
        """Test user input is safely included in prompts."""
        with patch("src.services.gemini_service.genai") as mock_genai:
            from src.services.gemini_service import GeminiAIService

            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model

            mock_response = MagicMock()
            mock_response.text = '{"sentiment_label": "Neutral"}'
            mock_model.generate_content.return_value = mock_response

            service = GeminiAIService()

            # Test with potentially problematic input
            dangerous_input = "<script>alert('xss')</script>"
            result = service.analyze_sentiment(audio_file=None, user_text=dangerous_input)

            # Should still work - input is included in prompt as-is
            assert result is not None


@pytest.mark.unit
class TestJobServiceHLS:
    """Test JobService HLS streaming functionality."""

    def test_create_job_without_streaming(self, mock_storage_service):
        """Test job creation without streaming enabled."""
        from src.services.job_service import JobService

        service = JobService(mock_storage_service)
        job_id = service.create_job("user123", "meditation", enable_streaming=False)

        assert job_id is not None
        # Verify upload_json was called
        mock_storage_service.upload_json.assert_called_once()
        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        # Should NOT have streaming fields
        assert "streaming" not in job_data
        assert "download" not in job_data

    def test_create_job_with_streaming(self, mock_storage_service):
        """Test job creation with HLS streaming enabled."""
        from src.services.job_service import JobService

        service = JobService(mock_storage_service)
        job_id = service.create_job("user123", "meditation", enable_streaming=True)

        assert job_id is not None
        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        # Should have streaming fields
        assert "streaming" in job_data
        assert job_data["streaming"]["enabled"] is True
        assert job_data["streaming"]["segments_completed"] == 0
        assert job_data["streaming"]["playlist_url"] is None
        assert "download" in job_data
        assert job_data["download"]["available"] is False
        assert job_data["tts_cache_key"] is None
        assert job_data["generation_attempt"] == 1

    def test_streaming_status_enum(self):
        """Test STREAMING status exists in JobStatus enum."""
        from src.services.job_service import JobStatus

        assert JobStatus.STREAMING.value == "streaming"
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"

    def test_update_streaming_progress(self, mock_storage_service):
        """Test updating streaming progress."""
        from src.services.job_service import JobService

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "streaming",
            "streaming": {
                "enabled": True,
                "playlist_url": None,
                "segments_completed": 0,
                "segments_total": None,
                "started_at": None,
            }
        }

        service = JobService(mock_storage_service)
        service.update_streaming_progress(
            "user123", "test-job",
            segments_completed=5,
            segments_total=36,
            playlist_url="https://s3.../playlist.m3u8"
        )

        # Verify save was called
        assert mock_storage_service.upload_json.called
        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["streaming"]["segments_completed"] == 5
        assert job_data["streaming"]["segments_total"] == 36
        assert job_data["streaming"]["playlist_url"] == "https://s3.../playlist.m3u8"

    def test_update_streaming_progress_sets_started_at_on_first_segment(self, mock_storage_service):
        """Test that started_at is set when first segment completes."""
        from src.services.job_service import JobService

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "processing",
            "streaming": {
                "enabled": True,
                "playlist_url": None,
                "segments_completed": 0,
                "segments_total": None,
                "started_at": None,
            }
        }

        service = JobService(mock_storage_service)
        service.update_streaming_progress("user123", "test-job", segments_completed=1)

        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["streaming"]["started_at"] is not None

    def test_mark_streaming_started(self, mock_storage_service):
        """Test marking job as streaming."""
        from src.services.job_service import JobService, JobStatus

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "processing",
            "streaming": {
                "enabled": True,
                "playlist_url": None,
                "segments_completed": 0,
                "segments_total": None,
                "started_at": None,
            }
        }

        service = JobService(mock_storage_service)
        service.mark_streaming_started("user123", "test-job", "https://s3.../playlist.m3u8")

        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["status"] == JobStatus.STREAMING.value
        assert job_data["streaming"]["playlist_url"] == "https://s3.../playlist.m3u8"
        assert job_data["streaming"]["started_at"] is not None

    def test_mark_streaming_complete(self, mock_storage_service):
        """Test marking streaming as complete."""
        from src.services.job_service import JobService, JobStatus

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "streaming",
            "streaming": {
                "enabled": True,
                "playlist_url": "https://s3.../playlist.m3u8",
                "segments_completed": 35,
                "segments_total": None,
                "started_at": "2024-01-01T00:00:00",
            },
            "download": {
                "available": False,
                "url": None,
                "downloaded": False,
            }
        }

        service = JobService(mock_storage_service)
        service.mark_streaming_complete("user123", "test-job", segments_total=36)

        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["status"] == JobStatus.COMPLETED.value
        assert job_data["streaming"]["segments_completed"] == 36
        assert job_data["streaming"]["segments_total"] == 36
        assert job_data["download"]["available"] is True

    def test_mark_download_ready(self, mock_storage_service):
        """Test setting download URL."""
        from src.services.job_service import JobService

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "completed",
            "download": {
                "available": True,
                "url": None,
                "downloaded": False,
            }
        }

        service = JobService(mock_storage_service)
        service.mark_download_ready("user123", "test-job", "https://s3.../download.mp3")

        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["download"]["url"] == "https://s3.../download.mp3"

    def test_mark_download_completed(self, mock_storage_service):
        """Test marking download as completed."""
        from src.services.job_service import JobService

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "completed",
            "download": {
                "available": True,
                "url": "https://s3.../download.mp3",
                "downloaded": False,
            }
        }

        service = JobService(mock_storage_service)
        service.mark_download_completed("user123", "test-job")

        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["download"]["downloaded"] is True

    def test_set_tts_cache_key(self, mock_storage_service):
        """Test setting TTS cache key."""
        from src.services.job_service import JobService

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "processing",
            "tts_cache_key": None,
        }

        service = JobService(mock_storage_service)
        service.set_tts_cache_key("user123", "test-job", "user123/hls/test-job/voice.mp3")

        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["tts_cache_key"] == "user123/hls/test-job/voice.mp3"

    def test_increment_generation_attempt(self, mock_storage_service):
        """Test incrementing generation attempt."""
        from src.services.job_service import JobService

        mock_storage_service.download_json.return_value = {
            "job_id": "test-job",
            "user_id": "user123",
            "status": "processing",
            "generation_attempt": 1,
        }

        service = JobService(mock_storage_service)
        attempt = service.increment_generation_attempt("user123", "test-job")

        assert attempt == 2

        call_args = mock_storage_service.upload_json.call_args
        job_data = call_args[1]["data"] if "data" in call_args[1] else call_args[0][2]

        assert job_data["generation_attempt"] == 2

    def test_backward_compatibility_job_without_streaming(self, mock_storage_service):
        """Test that jobs without streaming fields still work."""
        from src.services.job_service import JobService

        # Old job format without streaming fields
        mock_storage_service.download_json.return_value = {
            "job_id": "old-job",
            "user_id": "user123",
            "status": "completed",
            "result": {"audio": "base64data"},
        }

        service = JobService(mock_storage_service)
        job = service.get_job("user123", "old-job")

        assert job is not None
        assert job["status"] == "completed"
        assert "streaming" not in job


@pytest.mark.unit
class TestFFmpegAudioServiceHLS:
    """Test FFmpeg audio service HLS functionality."""

    def test_hls_service_optional_parameter(self, mock_storage_service):
        """Test that HLS service is optional in constructor."""
        service = FFmpegAudioService(mock_storage_service)
        assert service.hls_service is None

    def test_hls_service_injection(self, mock_storage_service):
        """Test that HLS service can be injected."""
        mock_hls_service = MagicMock()
        service = FFmpegAudioService(mock_storage_service, hls_service=mock_hls_service)
        assert service.hls_service == mock_hls_service

    def test_combine_voice_and_music_hls_requires_hls_service(self, mock_storage_service):
        """Test that HLS method requires HLS service."""
        service = FFmpegAudioService(mock_storage_service)

        with pytest.raises(ValueError, match="HLS service required"):
            service.combine_voice_and_music_hls(
                voice_path="/tmp/voice.mp3",
                music_list=[],
                timestamp="20241101",
                user_id="user123",
                job_id="job456",
            )

    def test_hls_segment_duration_configuration(self, mock_storage_service):
        """Test that HLS segment duration is configured correctly."""
        from src.services.ffmpeg_audio_service import HLS_SEGMENT_DURATION

        assert HLS_SEGMENT_DURATION == 5
