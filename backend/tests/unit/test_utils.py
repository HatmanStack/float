"""Unit tests for utility functions."""

import base64
import os
import tempfile
from unittest.mock import patch

import pytest

from src.utils.audio_utils import (
    cleanup_temp_file,
    decode_audio_base64,
    encode_audio_to_base64,
    validate_audio_file,
)
from src.utils.file_utils import (
    ensure_directory_exists,
    generate_request_id,
    generate_timestamp,
    get_file_extension,
    get_temp_file_path,
    is_audio_file,
    safe_filename,
)


@pytest.mark.unit
class TestAudioUtils:
    """Test audio utility functions."""

    def test_decode_audio_base64_success(self):
        """Test decoding base64 audio data."""
        # Create base64 encoded test data
        test_data = b"test audio data"
        encoded = base64.b64encode(test_data).decode("utf-8")

        # Decode and verify
        temp_path = decode_audio_base64(encoded, suffix=".mp3")

        try:
            assert os.path.exists(temp_path)
            assert temp_path.endswith(".mp3")

            with open(temp_path, "rb") as f:
                assert f.read() == test_data
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_decode_audio_base64_with_custom_suffix(self):
        """Test decoding with custom file suffix."""
        test_data = b"test wav data"
        encoded = base64.b64encode(test_data).decode("utf-8")

        temp_path = decode_audio_base64(encoded, suffix=".wav")

        try:
            assert temp_path.endswith(".wav")
            assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_cleanup_temp_file_removes_existing_file(self):
        """Test cleanup removes existing temporary file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        # Verify it exists
        assert os.path.exists(temp_path)

        # Clean up
        result = cleanup_temp_file(temp_path)

        assert result is True
        assert not os.path.exists(temp_path)

    def test_cleanup_temp_file_handles_nonexistent_file(self):
        """Test cleanup handles nonexistent files gracefully."""
        result = cleanup_temp_file("/tmp/nonexistent_file_12345.mp3")
        assert result is True

    def test_cleanup_temp_file_handles_errors(self):
        """Test cleanup handles permission errors gracefully."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        with patch("os.path.exists", return_value=True):
            with patch("os.remove", side_effect=PermissionError("Access denied")):
                result = cleanup_temp_file(temp_path)
                assert result is False

        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_encode_audio_to_base64_success(self):
        """Test encoding audio file to base64."""
        test_data = b"test audio content"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_data)
            temp_path = f.name

        try:
            encoded = encode_audio_to_base64(temp_path)

            assert encoded is not None
            decoded = base64.b64decode(encoded)
            assert decoded == test_data
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_encode_audio_to_base64_handles_missing_file(self):
        """Test encoding handles missing files."""
        result = encode_audio_to_base64("/tmp/nonexistent_file.mp3")
        assert result is None

    def test_validate_audio_file_success(self):
        """Test validating existing audio file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"audio data")
            temp_path = f.name

        try:
            assert validate_audio_file(temp_path) is True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_validate_audio_file_missing_file(self):
        """Test validating nonexistent file."""
        assert validate_audio_file("/tmp/nonexistent.mp3") is False

    def test_validate_audio_file_empty_file(self):
        """Test validating empty file returns False."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            # File is empty

        try:
            assert validate_audio_file(temp_path) is False
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_validate_audio_file_handles_exceptions(self):
        """Test validation handles exceptions gracefully."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.getsize", side_effect=OSError("Permission denied")):
                assert validate_audio_file("/tmp/test.mp3") is False


@pytest.mark.unit
class TestFileUtils:
    """Test file utility functions."""

    def test_generate_timestamp_format(self):
        """Test timestamp generation format."""
        timestamp = generate_timestamp()

        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS
        assert timestamp[8] == "_"
        assert timestamp[:8].isdigit()
        assert timestamp[9:].isdigit()

    def test_generate_request_id_in_range(self):
        """Test request ID generation."""
        request_id = generate_request_id()

        assert isinstance(request_id, int)
        assert 1 <= request_id <= 10000000

    def test_generate_request_id_randomness(self):
        """Test request IDs are different."""
        ids = [generate_request_id() for _ in range(10)]

        # At least some should be different (very high probability)
        assert len(set(ids)) > 1

    def test_ensure_directory_exists_creates_new_directory(self):
        """Test directory creation."""
        test_dir = f"/tmp/test_dir_{generate_timestamp()}"

        try:
            result = ensure_directory_exists(test_dir)

            assert result is True
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_ensure_directory_exists_handles_existing_directory(self):
        """Test handling of existing directory."""
        test_dir = f"/tmp/test_dir_exists_{generate_timestamp()}"
        os.makedirs(test_dir)

        try:
            result = ensure_directory_exists(test_dir)
            assert result is True
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_ensure_directory_exists_handles_errors(self):
        """Test error handling in directory creation."""
        with patch("os.makedirs", side_effect=PermissionError("Access denied")):
            result = ensure_directory_exists("/protected/path")
            assert result is False

    def test_get_file_extension_various_formats(self):
        """Test extracting file extensions."""
        assert get_file_extension("file.mp3") == ".mp3"
        assert get_file_extension("audio.WAV") == ".wav"  # Lowercase
        assert get_file_extension("music.m4a") == ".m4a"
        assert get_file_extension("noextension") == ""
        assert get_file_extension("path/to/file.aac") == ".aac"

    def test_is_audio_file_valid_extensions(self):
        """Test audio file detection with valid extensions."""
        assert is_audio_file("song.mp3") is True
        assert is_audio_file("track.wav") is True
        assert is_audio_file("audio.M4A") is True  # Case insensitive
        assert is_audio_file("music.aac") is True
        assert is_audio_file("sound.ogg") is True
        assert is_audio_file("hq.flac") is True

    def test_is_audio_file_invalid_extensions(self):
        """Test audio file detection with invalid extensions."""
        assert is_audio_file("video.mp4") is False
        assert is_audio_file("document.pdf") is False
        assert is_audio_file("image.jpg") is False
        assert is_audio_file("noextension") is False

    @pytest.mark.parametrize("unsafe,expected", [
        ("file<name>.mp3", "file_name_.mp3"),
        ("path/to:file.wav", "path_to_file.wav"),
        ("file|name?.mp3", "file_name_.mp3"),
        ("  .dotfile  ", "dotfile"),
        ("", "untitled"),
        ("normal_file.mp3", "normal_file.mp3"),
    ])
    def test_safe_filename_sanitization(self, unsafe, expected):
        """Test filename sanitization."""
        assert safe_filename(unsafe) == expected

    def test_get_temp_file_path_default_directory(self):
        """Test temp file path generation with defaults."""
        path = get_temp_file_path(prefix="test_", suffix=".mp3")

        assert path.startswith("/tmp/test_")
        assert path.endswith(".mp3")
        assert len(path) > len("/tmp/test_.mp3")

    def test_get_temp_file_path_custom_directory(self):
        """Test temp file path with custom directory."""
        custom_dir = "/var/tmp"
        path = get_temp_file_path(prefix="audio_", suffix=".wav", directory=custom_dir)

        assert path.startswith(f"{custom_dir}/audio_")
        assert path.endswith(".wav")

    def test_get_temp_file_path_uniqueness(self):
        """Test temp file paths are unique when generated at different times."""
        import time

        path1 = get_temp_file_path(prefix="test_")
        time.sleep(1.1)  # Wait to ensure different timestamp (second precision)
        path2 = get_temp_file_path(prefix="test_")

        # Paths should be different due to timestamp
        assert path1 != path2
