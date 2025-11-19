"""Integration tests for TTS providers with real API calls."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from tests.integration.test_config import test_config


@pytest.mark.integration
@pytest.mark.slow
class TestOpenAITTSIntegration:
    """Integration tests for OpenAI TTS provider with real API."""

    def test_synthesize_simple_text(self, real_openai_tts_provider):
        """Test TTS synthesis with simple text."""
        # Arrange
        text = "Hello, this is a test of text to speech synthesis."
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            start_time = time.time()
            result = real_openai_tts_provider.synthesize_speech(text, output_path)
            elapsed_time = time.time() - start_time

            # Assert
            assert result is True, "Synthesis should succeed"
            assert os.path.exists(output_path), "Audio file should be created"
            file_size = os.path.getsize(output_path)
            assert file_size > 0, "Audio file should not be empty"
            assert file_size > 1000, f"Audio file seems too small: {file_size} bytes"
            assert (
                elapsed_time < test_config.TTS_TIMEOUT
            ), f"TTS took too long: {elapsed_time:.2f}s"

            print(f"\n✓ Simple text synthesis completed in {elapsed_time:.2f}s")
            print(f"  File size: {file_size:,} bytes")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_synthesize_text_with_ssml_tags(self, real_openai_tts_provider):
        """Test TTS synthesis with SSML-like tags."""
        # Arrange
        text = """<speak>
        Welcome to this meditation.
        Take a deep breath.
        And release.
        </speak>"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            result = real_openai_tts_provider.synthesize_speech(text, output_path)

            # Assert
            assert result is True, "Synthesis with SSML tags should succeed"
            assert os.path.exists(output_path), "Audio file should be created"
            assert os.path.getsize(output_path) > 0, "Audio file should not be empty"

            print(f"\n✓ SSML text synthesis completed")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_synthesize_longer_meditation_text(self, real_openai_tts_provider):
        """Test TTS synthesis with longer meditation script."""
        # Arrange
        text = """
        Let's begin this meditation by finding a comfortable position.
        Take a deep breath in through your nose.
        Hold it for a moment.
        And slowly exhale through your mouth.
        Feel the tension leaving your body with each breath.
        Continue breathing deeply and naturally.
        """
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            start_time = time.time()
            result = real_openai_tts_provider.synthesize_speech(text, output_path)
            elapsed_time = time.time() - start_time

            # Assert
            assert result is True, "Longer text synthesis should succeed"
            assert os.path.exists(output_path), "Audio file should be created"
            file_size = os.path.getsize(output_path)
            assert file_size > 5000, f"Longer audio should be larger: {file_size} bytes"
            assert elapsed_time < 30, f"Longer TTS took too long: {elapsed_time:.2f}s"

            print(f"\n✓ Longer meditation text synthesis completed in {elapsed_time:.2f}s")
            print(f"  File size: {file_size:,} bytes")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_audio_format_is_mp3(self, real_openai_tts_provider):
        """Test that generated audio is valid MP3 format."""
        # Arrange
        text = "Testing audio format validation."
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            result = real_openai_tts_provider.synthesize_speech(text, output_path)

            # Assert
            assert result is True, "Synthesis should succeed"
            assert os.path.exists(output_path), "Audio file should be created"

            # Guard against zero-size file before reading
            file_size = os.path.getsize(output_path)
            assert file_size > 0, "Audio file should not be zero bytes"

            # Check MP3 file signature (first 3 bytes should be ID3 or 0xFF 0xFB)
            with open(output_path, "rb") as f:
                header = f.read(3)
                # MP3 files typically start with ID3 tag or FF FB frame sync
                is_valid_mp3 = header[:3] == b"ID3" or header[:2] == b"\xff\xfb"
                assert (
                    is_valid_mp3
                ), f"File should be valid MP3 format, got header: {header.hex()}"

            print(f"\n✓ Audio format validation passed (valid MP3)")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_provider_name(self, real_openai_tts_provider):
        """Test that provider returns correct name."""
        # Act
        provider_name = real_openai_tts_provider.get_provider_name()

        # Assert
        assert provider_name == "openai", f"Expected 'openai', got '{provider_name}'"

        print(f"\n✓ Provider name correct: {provider_name}")

    def test_synthesize_very_short_text(self, real_openai_tts_provider):
        """Test TTS synthesis with very short text."""
        # Arrange
        text = "Hi."
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            result = real_openai_tts_provider.synthesize_speech(text, output_path)

            # Assert
            assert result is True, "Short text synthesis should succeed"
            assert os.path.exists(output_path), "Audio file should be created"
            assert os.path.getsize(output_path) > 0, "Even short audio should have content"

            print(f"\n✓ Very short text synthesis completed")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_synthesize_text_with_special_characters(self, real_openai_tts_provider):
        """Test TTS synthesis with special characters."""
        # Arrange
        text = "Let's breathe... 1, 2, 3! Feel the calm & peace."
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            result = real_openai_tts_provider.synthesize_speech(text, output_path)

            # Assert
            assert result is True, "Special characters should be handled"
            assert os.path.exists(output_path), "Audio file should be created"

            print(f"\n✓ Special characters handled successfully")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_multiple_synthesis_calls(self, real_openai_tts_provider):
        """Test multiple TTS synthesis calls in sequence."""
        texts = [
            "First meditation segment.",
            "Second meditation segment.",
            "Third meditation segment.",
        ]
        output_paths = []

        try:
            # Act - synthesize multiple texts
            for i, text in enumerate(texts):
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    output_path = tmp.name
                    output_paths.append(output_path)

                result = real_openai_tts_provider.synthesize_speech(text, output_path)

                # Assert each synthesis
                assert result is True, f"Synthesis {i+1} should succeed"
                assert os.path.exists(output_path), f"Audio file {i+1} should be created"

            print(f"\n✓ Multiple synthesis calls completed successfully")

        finally:
            # Cleanup all files
            for path in output_paths:
                if os.path.exists(path):
                    os.unlink(path)


@pytest.mark.integration
@pytest.mark.slow
class TestTTSErrorHandling:
    """Integration tests for TTS error handling."""

    def test_invalid_output_path(self, real_openai_tts_provider):
        """Test TTS synthesis with invalid output path."""
        # Arrange
        text = "Test text"
        invalid_path = "/nonexistent/directory/output.mp3"

        # Act
        result = real_openai_tts_provider.synthesize_speech(text, invalid_path)

        # Assert - should handle gracefully
        assert result is False, "Should return False for invalid path"

        print(f"\n✓ Invalid path handled gracefully")

    def test_empty_text(self, real_openai_tts_provider):
        """Test TTS synthesis with empty text."""
        # Arrange
        text = ""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act - this may fail or succeed depending on API behavior
            result = real_openai_tts_provider.synthesize_speech(text, output_path)

            # Assert - should handle empty text (either fail gracefully or create minimal audio)
            if result:
                assert os.path.exists(output_path), "If successful, file should exist"
            else:
                print("  Empty text rejected by API (expected behavior)")

            print(f"\n✓ Empty text handled (result: {result})")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_very_long_text(self, real_openai_tts_provider):
        """Test TTS synthesis with very long text."""
        # Arrange - 1000 word text
        text = "Let's begin this meditation session. " * 200  # ~1000 words
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            start_time = time.time()
            result = real_openai_tts_provider.synthesize_speech(text, output_path)
            elapsed_time = time.time() - start_time

            # Assert
            if result:
                assert os.path.exists(output_path), "Audio file should be created"
                file_size = os.path.getsize(output_path)
                assert file_size > 10000, "Long text should produce larger audio file"
                print(
                    f"\n✓ Very long text handled successfully in {elapsed_time:.2f}s ({file_size:,} bytes)"
                )
            else:
                print(f"\n✓ Very long text rejected (may exceed API limits)")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)


@pytest.mark.integration
@pytest.mark.slow
class TestTTSPerformance:
    """Integration tests for TTS performance metrics."""

    def test_synthesis_performance(self, real_openai_tts_provider):
        """Test that TTS synthesis completes within acceptable time."""
        # Arrange
        text = "This is a performance test for text to speech synthesis."
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = tmp.name

        try:
            # Act
            start_time = time.time()
            result = real_openai_tts_provider.synthesize_speech(text, output_path)
            elapsed_time = time.time() - start_time

            # Assert
            assert result is True, "Synthesis should succeed"
            assert (
                elapsed_time < 10
            ), f"TTS should complete within 10s, took {elapsed_time:.2f}s"

            print(f"\n✓ TTS performance: {elapsed_time:.2f}s (target: <10s)")

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_file_size_consistency(self, real_openai_tts_provider):
        """Test that similar text produces similar file sizes."""
        # Arrange
        text1 = "This is the first test sentence for consistency."
        text2 = "This is the second test sentence for consistency."
        output_paths = []

        try:
            # Act - synthesize both texts
            for text in [text1, text2]:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    output_path = tmp.name
                    output_paths.append(output_path)

                result = real_openai_tts_provider.synthesize_speech(text, output_path)
                assert result is True, "Synthesis should succeed"

            # Get file sizes
            size1 = os.path.getsize(output_paths[0])
            size2 = os.path.getsize(output_paths[1])

            # Assert - sizes should be similar (within 50% variance)
            ratio = max(size1, size2) / min(size1, size2)
            assert ratio < 1.5, f"File sizes should be similar, got {size1} and {size2}"

            print(f"\n✓ File size consistency verified (size1: {size1}, size2: {size2})")

        finally:
            # Cleanup
            for path in output_paths:
                if os.path.exists(path):
                    os.unlink(path)
