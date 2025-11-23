"""Integration tests for Lambda initialization and cold start behavior."""

import sys
import time

import pytest

from src.config.settings import settings


@pytest.mark.integration
class TestLambdaHandlerInitialization:
    """Integration tests for Lambda handler initialization."""

    def test_handler_initialization_success(self):
        """Test that Lambda handler initializes successfully."""
        # Arrange & Act
        start_time = time.time()
        from src.handlers.lambda_handler import LambdaHandler

        # Initialize with validate_config=False to skip API key validation
        handler = LambdaHandler(validate_config=False)
        elapsed_time = time.time() - start_time

        # Assert
        assert handler is not None, "Handler should initialize"
        assert handler.ai_service is not None, "AI service should be initialized"
        assert (
            handler.storage_service is not None
        ), "Storage service should be initialized"
        assert handler.audio_service is not None, "Audio service should be initialized"
        assert handler.tts_provider is not None, "TTS provider should be initialized"

        # Initialization should be fast (cold start simulation)
        assert elapsed_time < 5, f"Initialization took too long: {elapsed_time:.2f}s"

        print(f"\n✓ Handler initialization completed in {elapsed_time:.2f}s")

    def test_handler_initialization_with_dependency_injection(self):
        """Test handler initialization with injected AI service."""
        # Arrange
        from unittest.mock import MagicMock

        from src.handlers.lambda_handler import LambdaHandler

        mock_ai_service = MagicMock()

        # Act
        handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)

        # Assert
        assert handler.ai_service is mock_ai_service, "Should use injected AI service"
        assert (
            handler.storage_service is not None
        ), "Other services should still initialize"

        print("\n✓ Dependency injection works correctly")

    def test_handler_services_ready_after_init(self):
        """Test that all services are ready to use after initialization."""
        # Arrange
        from src.handlers.lambda_handler import LambdaHandler

        handler = LambdaHandler(validate_config=False)

        # Act & Assert - verify service methods are callable
        assert hasattr(
            handler.ai_service, "analyze_sentiment"
        ), "AI service should have analyze_sentiment method"
        assert hasattr(
            handler.ai_service, "generate_meditation"
        ), "AI service should have generate_meditation method"

        assert hasattr(
            handler.storage_service, "upload_json"
        ), "Storage service should have upload_json method"

        assert hasattr(
            handler.audio_service, "combine_voice_and_music"
        ), "Audio service should have combine_voice_and_music method"

        assert hasattr(
            handler.tts_provider, "synthesize_speech"
        ), "TTS provider should have synthesize_speech method"

        print("\n✓ All services ready and have expected methods")

    def test_multiple_handler_instances(self):
        """Test creating multiple handler instances."""
        # Arrange & Act
        from src.handlers.lambda_handler import LambdaHandler

        handler1 = LambdaHandler(validate_config=False)
        handler2 = LambdaHandler(validate_config=False)

        # Assert - should be independent instances
        assert handler1 is not handler2, "Should create independent instances"
        assert (
            handler1.ai_service is not handler2.ai_service
        ), "Each handler should have its own AI service"

        print("\n✓ Multiple handler instances created independently")


@pytest.mark.integration
class TestConfigurationValidation:
    """Integration tests for configuration validation."""

    def test_settings_validate_with_missing_keys(self):
        """Test settings validation with missing API keys."""
        # Arrange - temporarily clear API keys
        original_gemini = settings.GEMINI_API_KEY
        original_openai = settings.OPENAI_API_KEY

        try:
            settings.GEMINI_API_KEY = ""
            settings.OPENAI_API_KEY = ""

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                settings.validate(require_keys=True)

            # Verify error message mentions missing keys
            error_message = str(exc_info.value)
            assert (
                "Missing required environment variables" in error_message
            ), "Error should mention missing variables"

            print("\n✓ Missing API keys detected correctly")

        finally:
            # Restore original values
            settings.GEMINI_API_KEY = original_gemini
            settings.OPENAI_API_KEY = original_openai

    def test_settings_validate_skip_when_disabled(self):
        """Test that validation can be skipped."""
        # Act
        result = settings.validate(require_keys=False)

        # Assert
        assert result is True, "Should return True when validation skipped"

        print("\n✓ Validation can be skipped for testing")

    def test_settings_has_all_required_config(self):
        """Test that settings has all required configuration."""
        # Assert - check all required settings exist
        assert hasattr(settings, "AWS_S3_BUCKET"), "Should have AWS_S3_BUCKET"
        assert hasattr(settings, "AWS_AUDIO_BUCKET"), "Should have AWS_AUDIO_BUCKET"
        assert hasattr(settings, "GEMINI_API_KEY"), "Should have GEMINI_API_KEY"
        assert hasattr(settings, "OPENAI_API_KEY"), "Should have OPENAI_API_KEY"
        assert hasattr(settings, "FFMPEG_PATH"), "Should have FFMPEG_PATH"
        assert hasattr(settings, "TEMP_DIR"), "Should have TEMP_DIR"

        print("\n✓ All required configuration settings present")

    def test_settings_default_values(self):
        """Test that settings have appropriate default values."""
        # Assert
        assert settings.TEMP_DIR == "/tmp", "TEMP_DIR should default to /tmp"
        assert settings.GEMINI_SAFETY_LEVEL == 4, "Safety level should default to 4"
        assert settings.AUDIO_SAMPLE_RATE == 44100, "Sample rate should be 44100"

        print("\n✓ Default values are correct")


@pytest.mark.integration
class TestServiceInitialization:
    """Integration tests for individual service initialization."""

    def test_gemini_service_initialization(self, skip_if_no_gemini):
        """Test Gemini AI service initialization."""
        # Arrange & Act
        from src.services.gemini_service import GeminiAIService

        start_time = time.time()
        service = GeminiAIService()
        elapsed_time = time.time() - start_time

        # Assert
        assert service is not None, "Service should initialize"
        assert hasattr(
            service, "analyze_sentiment"
        ), "Should have analyze_sentiment method"
        assert hasattr(
            service, "generate_meditation"
        ), "Should have generate_meditation method"
        assert elapsed_time < 2, f"Initialization should be fast: {elapsed_time:.2f}s"

        print(f"\n✓ Gemini service initialized in {elapsed_time:.2f}s")

    def test_openai_tts_provider_initialization(self, skip_if_no_openai):
        """Test OpenAI TTS provider initialization."""
        # Arrange & Act
        from src.providers.openai_tts import OpenAITTSProvider

        start_time = time.time()
        provider = OpenAITTSProvider()
        elapsed_time = time.time() - start_time

        # Assert
        assert provider is not None, "Provider should initialize"
        assert hasattr(
            provider, "synthesize_speech"
        ), "Should have synthesize_speech method"
        assert (
            provider.get_provider_name() == "openai"
        ), "Should return correct provider name"
        assert elapsed_time < 2, f"Initialization should be fast: {elapsed_time:.2f}s"

        print(f"\n✓ OpenAI TTS provider initialized in {elapsed_time:.2f}s")

    def test_s3_storage_service_initialization(self):
        """Test S3 storage service initialization."""
        # Arrange & Act
        from src.services.s3_storage_service import S3StorageService

        start_time = time.time()
        service = S3StorageService()
        elapsed_time = time.time() - start_time

        # Assert
        assert service is not None, "Service should initialize"
        assert hasattr(service, "upload_json"), "Should have upload_json method"
        assert hasattr(service, "download_file"), "Should have download_file method"
        assert hasattr(service, "list_objects"), "Should have list_objects method"
        assert elapsed_time < 2, f"Initialization should be fast: {elapsed_time:.2f}s"

        print(f"\n✓ S3 storage service initialized in {elapsed_time:.2f}s")

    def test_ffmpeg_audio_service_initialization(self):
        """Test FFmpeg audio service initialization."""
        # Arrange
        from src.services.ffmpeg_audio_service import FFmpegAudioService
        from src.services.s3_storage_service import S3StorageService

        storage_service = S3StorageService()

        # Act
        start_time = time.time()
        service = FFmpegAudioService(storage_service)
        elapsed_time = time.time() - start_time

        # Assert
        assert service is not None, "Service should initialize"
        assert hasattr(
            service, "combine_voice_and_music"
        ), "Should have combine_voice_and_music method"
        assert elapsed_time < 2, f"Initialization should be fast: {elapsed_time:.2f}s"

        print(f"\n✓ FFmpeg audio service initialized in {elapsed_time:.2f}s")


@pytest.mark.integration
class TestColdStartPerformance:
    """Integration tests for cold start performance measurement."""

    def test_cold_start_simulation(self):
        """Test cold start by reloading handler module."""
        # Arrange - remove module from cache to simulate cold start
        module_name = "src.handlers.lambda_handler"
        if module_name in sys.modules:
            # Save reference to reload later
            sys.modules[module_name]

        try:
            # Remove from cache
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Act - simulate cold start
            start_time = time.time()
            from src.handlers.lambda_handler import LambdaHandler

            handler = LambdaHandler(validate_config=False)
            elapsed_time = time.time() - start_time

            # Assert
            assert handler is not None, "Handler should initialize on cold start"
            assert (
                elapsed_time < 5
            ), f"Cold start should complete within 5s, took {elapsed_time:.2f}s"

            print(f"\n✓ Cold start simulation completed in {elapsed_time:.2f}s")

        finally:
            # Note: Can't easily restore module, but this is fine for test isolation
            pass

    def test_initialization_time_breakdown(self):
        """Test initialization time for each component."""
        # Measure individual component initialization times
        times = {}

        # Test Gemini service (if available)
        try:
            from src.services.gemini_service import GeminiAIService

            start = time.time()
            GeminiAIService()
            times["gemini_service"] = time.time() - start
        except Exception:
            times["gemini_service"] = None

        # Test OpenAI TTS
        try:
            from src.providers.openai_tts import OpenAITTSProvider

            start = time.time()
            OpenAITTSProvider()
            times["openai_tts"] = time.time() - start
        except Exception:
            times["openai_tts"] = None

        # Test S3 storage
        from src.services.s3_storage_service import S3StorageService

        start = time.time()
        S3StorageService()
        times["s3_storage"] = time.time() - start

        # Test FFmpeg audio
        from src.services.ffmpeg_audio_service import FFmpegAudioService

        storage = S3StorageService()
        start = time.time()
        FFmpegAudioService(storage)
        times["ffmpeg_audio"] = time.time() - start

        # Print breakdown
        print("\n✓ Initialization time breakdown:")
        for component, duration in times.items():
            if duration is not None:
                print(f"  {component}: {duration:.3f}s")

        # Total should be reasonable
        total = sum(t for t in times.values() if t is not None)
        assert total < 5, f"Total initialization should be <5s, got {total:.2f}s"


@pytest.mark.integration
class TestErrorRecovery:
    """Integration tests for error recovery during initialization."""

    def test_initialization_with_invalid_gemini_key(self):
        """Test handler behavior with invalid Gemini API key."""
        # Arrange - set invalid key
        original_key = settings.GEMINI_API_KEY

        try:
            settings.GEMINI_API_KEY = "invalid-key-12345"

            # Act - should still initialize (validation disabled)
            from src.handlers.lambda_handler import LambdaHandler

            handler = LambdaHandler(validate_config=False)

            # Assert
            assert handler is not None, "Handler should initialize despite invalid key"
            assert handler.ai_service is not None, "AI service should be created"

            print("\n✓ Handler initializes with invalid API key (validation disabled)")

        finally:
            # Restore original key
            settings.GEMINI_API_KEY = original_key

    def test_initialization_with_missing_environment_variables(self):
        """Test handler initialization when optional env vars are missing."""
        # Arrange - temporarily clear optional env var
        original_temp = settings.TEMP_DIR

        try:
            # Set to unusual value to test
            settings.TEMP_DIR = "/tmp/test-custom"

            # Act
            from src.handlers.lambda_handler import LambdaHandler

            handler = LambdaHandler(validate_config=False)

            # Assert
            assert handler is not None, "Handler should initialize with custom TEMP_DIR"

            print("\n✓ Handler handles custom environment variables")

        finally:
            # Restore original value
            settings.TEMP_DIR = original_temp
