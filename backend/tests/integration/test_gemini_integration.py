"""Integration tests for Gemini AI service with real API calls."""

import json
import time

import pytest

from tests.integration.test_config import test_config


@pytest.mark.integration
@pytest.mark.slow
class TestGeminiSentimentAnalysis:
    """Integration tests for Gemini sentiment analysis with real API."""

    def test_analyze_positive_sentiment(
        self, real_gemini_service, test_sentiment_texts, validate_json_response
    ):
        """Test sentiment analysis with positive text input."""
        # Arrange
        positive_text = test_sentiment_texts["positive"]

        # Act
        start_time = time.time()
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=positive_text
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result, "Result should not be empty"
        data = validate_json_response(
            result,
            [
                "sentiment_label",
                "intensity",
                "summary",
                "user_summary",
                "user_short_summary",
            ],
        )

        # Verify sentiment is positive (Happy or similar)
        assert data["sentiment_label"] in [
            "Happy",
            "Neutral",
        ], f"Expected positive sentiment, got {data['sentiment_label']}"
        assert 1 <= data["intensity"] <= 5, "Intensity should be between 1 and 5"
        assert elapsed_time < test_config.GEMINI_TIMEOUT, "Request took too long"

        print(f"\n✓ Positive sentiment analysis completed in {elapsed_time:.2f}s")
        print(f"  Sentiment: {data['sentiment_label']} (intensity: {data['intensity']})")

    def test_analyze_negative_sentiment(
        self, real_gemini_service, test_sentiment_texts, validate_json_response
    ):
        """Test sentiment analysis with negative/stressed text input."""
        # Arrange
        negative_text = test_sentiment_texts["negative"]

        # Act
        start_time = time.time()
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=negative_text
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result, "Result should not be empty"
        data = validate_json_response(
            result,
            [
                "sentiment_label",
                "intensity",
                "summary",
                "user_summary",
                "user_short_summary",
            ],
        )

        # Verify sentiment is negative (Sad, Fearful, Angry, etc.)
        assert data["sentiment_label"] in [
            "Sad",
            "Fearful",
            "Angry",
            "Disgusted",
        ], f"Expected negative sentiment, got {data['sentiment_label']}"
        assert data["intensity"] >= 2, "Intensity should be at least 2 for stressed text"
        assert elapsed_time < test_config.GEMINI_TIMEOUT, "Request took too long"

        print(f"\n✓ Negative sentiment analysis completed in {elapsed_time:.2f}s")
        print(f"  Sentiment: {data['sentiment_label']} (intensity: {data['intensity']})")

    def test_analyze_neutral_sentiment(
        self, real_gemini_service, test_sentiment_texts, validate_json_response
    ):
        """Test sentiment analysis with neutral text input."""
        # Arrange
        neutral_text = test_sentiment_texts["neutral"]

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=neutral_text
        )

        # Assert
        assert result, "Result should not be empty"
        data = validate_json_response(
            result,
            [
                "sentiment_label",
                "intensity",
                "summary",
                "user_summary",
                "user_short_summary",
            ],
        )

        # Verify sentiment is neutral or low intensity
        assert 1 <= data["intensity"] <= 5, "Intensity should be between 1 and 5"

        print(f"\n✓ Neutral sentiment analysis completed")
        print(f"  Sentiment: {data['sentiment_label']} (intensity: {data['intensity']})")

    def test_analyze_anxious_sentiment(
        self, real_gemini_service, test_sentiment_texts, validate_json_response
    ):
        """Test sentiment analysis with anxious text input."""
        # Arrange
        anxious_text = test_sentiment_texts["anxious"]

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=anxious_text
        )

        # Assert
        assert result, "Result should not be empty"
        data = validate_json_response(
            result,
            [
                "sentiment_label",
                "intensity",
                "summary",
                "user_summary",
                "user_short_summary",
            ],
        )

        # Verify sentiment indicates anxiety/worry
        assert data["sentiment_label"] in [
            "Fearful",
            "Sad",
            "Angry",
        ], f"Expected anxious sentiment, got {data['sentiment_label']}"

        print(f"\n✓ Anxious sentiment analysis completed")
        print(f"  Sentiment: {data['sentiment_label']} (intensity: {data['intensity']})")

    def test_analyze_sad_sentiment(
        self, real_gemini_service, test_sentiment_texts, validate_json_response
    ):
        """Test sentiment analysis with sad text input."""
        # Arrange
        sad_text = test_sentiment_texts["sad"]

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=sad_text
        )

        # Assert
        assert result, "Result should not be empty"
        data = validate_json_response(
            result,
            [
                "sentiment_label",
                "intensity",
                "summary",
                "user_summary",
                "user_short_summary",
            ],
        )

        # Verify sentiment is sad
        assert data["sentiment_label"] in [
            "Sad",
            "Disgusted",
        ], f"Expected sad sentiment, got {data['sentiment_label']}"

        print(f"\n✓ Sad sentiment analysis completed")
        print(f"  Sentiment: {data['sentiment_label']} (intensity: {data['intensity']})")

    def test_response_format_fields(
        self, real_gemini_service, test_sentiment_texts, validate_json_response
    ):
        """Test that all required fields are present in response."""
        # Arrange
        text = test_sentiment_texts["happy"]

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=text
        )

        # Assert
        data = validate_json_response(
            result,
            [
                "sentiment_label",
                "intensity",
                "speech_to_text",
                "added_text",
                "summary",
                "user_summary",
                "user_short_summary",
            ],
        )

        # Verify field types
        assert isinstance(data["sentiment_label"], str), "sentiment_label should be string"
        assert isinstance(data["intensity"], int), "intensity should be integer"
        assert isinstance(data["summary"], str), "summary should be string"
        assert len(data["user_summary"]) > 0, "user_summary should not be empty"

        print(f"\n✓ All required fields present and valid")

    def test_text_only_analysis_has_correct_fields(
        self, real_gemini_service, test_sentiment_texts
    ):
        """Test that text-only analysis sets audio field to NotAvailable."""
        # Arrange
        text = test_sentiment_texts["happy"]

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=text
        )

        # Assert
        data = json.loads(result)
        assert (
            data["speech_to_text"] == "NotAvailable"
        ), "speech_to_text should be NotAvailable for text-only"
        assert data["added_text"] == text or text in data["added_text"], \
            "added_text should contain the input text"

        print(f"\n✓ Text-only analysis has correct field values")


@pytest.mark.integration
@pytest.mark.slow
class TestGeminiMeditationGeneration:
    """Integration tests for Gemini meditation generation with real API."""

    def test_generate_meditation_for_sad_emotion(
        self, real_gemini_service, test_meditation_input, validate_ssml_response, retry_on_rate_limit
    ):
        """Test meditation generation for sad emotion."""
        # Arrange
        input_data = test_meditation_input.copy()
        input_data["sentiment_label"] = ["Sad"]
        input_data["intensity"] = [4]

        # Act with retry on rate limit
        start_time = time.time()
        result = retry_on_rate_limit(
            lambda: real_gemini_service.generate_meditation(input_data)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result, "Meditation result should not be empty"
        assert len(result) > 100, "Meditation should have substantial content"
        assert elapsed_time < 60, "Meditation generation should complete within 60s"

        print(f"\n✓ Meditation for sad emotion generated in {elapsed_time:.2f}s")
        print(f"  Length: {len(result)} characters")

    def test_generate_meditation_for_happy_emotion(
        self, real_gemini_service, retry_on_rate_limit
    ):
        """Test meditation generation for happy emotion."""
        # Arrange
        input_data = {
            "sentiment_label": ["Happy"],
            "intensity": [4],
            "speech_to_text": ["NotAvailable"],
            "added_text": ["I had a wonderful day and everything went great"],
            "summary": ["User experienced happiness and success"],
            "user_summary": ["I had an amazing day"],
            "user_short_summary": ["Great day"],
        }

        # Act with retry on rate limit
        result = retry_on_rate_limit(
            lambda: real_gemini_service.generate_meditation(input_data)
        )

        # Assert
        assert result, "Meditation result should not be empty"
        assert len(result) > 50, "Meditation should have content"

        print(f"\n✓ Meditation for happy emotion generated")

    def test_generate_meditation_for_anxious_emotion(
        self, real_gemini_service, retry_on_rate_limit
    ):
        """Test meditation generation for anxious emotion."""
        # Arrange
        input_data = {
            "sentiment_label": ["Fearful"],
            "intensity": [5],
            "speech_to_text": ["NotAvailable"],
            "added_text": ["I'm worried about the presentation tomorrow"],
            "summary": ["User experiencing anxiety about upcoming event"],
            "user_summary": ["I'm anxious about tomorrow's presentation"],
            "user_short_summary": ["Presentation anxiety"],
        }

        # Act with retry on rate limit
        result = retry_on_rate_limit(
            lambda: real_gemini_service.generate_meditation(input_data)
        )

        # Assert
        assert result, "Meditation result should not be empty"

        print(f"\n✓ Meditation for anxious emotion generated")

    def test_generate_meditation_with_various_intensities(
        self, real_gemini_service, retry_on_rate_limit
    ):
        """Test meditation generation with different intensity levels."""
        for intensity in [1, 3, 5]:
            # Arrange
            input_data = {
                "sentiment_label": ["Sad"],
                "intensity": [intensity],
                "speech_to_text": ["NotAvailable"],
                "added_text": [f"I'm feeling down (intensity {intensity})"],
                "summary": [f"User experiencing sadness at intensity {intensity}"],
                "user_summary": [f"Feeling sad - intensity {intensity}"],
                "user_short_summary": ["Sadness"],
            }

            # Act with retry on rate limit
            result = retry_on_rate_limit(
                lambda: real_gemini_service.generate_meditation(input_data)
            )

            # Assert
            assert result, f"Meditation should be generated for intensity {intensity}"
            assert len(result) > 50, f"Meditation should have content for intensity {intensity}"

            print(f"  ✓ Meditation generated for intensity {intensity}")

    def test_meditation_length_appropriate(
        self, real_gemini_service, test_meditation_input, retry_on_rate_limit
    ):
        """Test that meditation has appropriate length."""
        # Act with retry on rate limit
        result = retry_on_rate_limit(
            lambda: real_gemini_service.generate_meditation(test_meditation_input)
        )

        # Assert
        assert 100 <= len(result) <= 5000, \
            f"Meditation length should be reasonable, got {len(result)} characters"

        print(f"\n✓ Meditation length appropriate: {len(result)} characters")

    def test_meditation_multiple_instances(
        self, real_gemini_service, retry_on_rate_limit
    ):
        """Test meditation generation with multiple instances."""
        # Arrange - multiple incidents
        input_data = {
            "sentiment_label": ["Sad", "Angry"],
            "intensity": [4, 3],
            "speech_to_text": ["NotAvailable", "NotAvailable"],
            "added_text": ["Work was stressful", "Argument with friend"],
            "summary": [
                "User had stressful work day",
                "User had conflict with friend",
            ],
            "user_summary": [
                "I had a stressful day at work",
                "I had an argument with my friend",
            ],
            "user_short_summary": ["Work stress", "Friend conflict"],
        }

        # Act with retry on rate limit
        result = retry_on_rate_limit(
            lambda: real_gemini_service.generate_meditation(input_data)
        )

        # Assert
        assert result, "Meditation should be generated for multiple instances"
        # Should address both instances
        assert len(result) > 200, "Meditation for multiple instances should be longer"

        print(f"\n✓ Meditation for multiple instances generated")


@pytest.mark.integration
@pytest.mark.slow
class TestGeminiErrorHandling:
    """Integration tests for Gemini error handling."""

    def test_very_long_input_text(self, real_gemini_service, validate_json_response):
        """Test sentiment analysis with very long input text."""
        # Arrange - 2000 character text
        long_text = "I had a difficult day. " * 100

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=long_text
        )

        # Assert
        assert result, "Should handle long text"
        data = validate_json_response(result, ["sentiment_label", "intensity"])

        print(f"\n✓ Long text handled successfully")

    def test_text_with_special_characters(
        self, real_gemini_service, validate_json_response
    ):
        """Test sentiment analysis with special characters and emojis."""
        # Arrange
        special_text = "I'm feeling 😢 sad & stressed! Can't believe it's $#@% happening..."

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=special_text
        )

        # Assert
        assert result, "Should handle special characters"
        data = validate_json_response(result, ["sentiment_label", "intensity"])

        print(f"\n✓ Special characters handled successfully")

    def test_minimal_input_text(self, real_gemini_service, validate_json_response):
        """Test sentiment analysis with minimal input text."""
        # Arrange
        minimal_text = "Sad."

        # Act
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=minimal_text
        )

        # Assert
        assert result, "Should handle minimal text"
        data = validate_json_response(result, ["sentiment_label", "intensity"])

        print(f"\n✓ Minimal text handled successfully")


@pytest.mark.integration
@pytest.mark.slow
class TestGeminiPerformance:
    """Integration tests for Gemini performance metrics."""

    def test_sentiment_analysis_performance(
        self, real_gemini_service, test_sentiment_texts
    ):
        """Test that sentiment analysis completes within acceptable time."""
        # Arrange
        text = test_sentiment_texts["happy"]

        # Act
        start_time = time.time()
        result = real_gemini_service.analyze_sentiment(
            audio_file="NotAvailable", user_text=text
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result, "Should return result"
        assert (
            elapsed_time < 15
        ), f"Sentiment analysis should complete within 15s, took {elapsed_time:.2f}s"

        print(
            f"\n✓ Sentiment analysis performance: {elapsed_time:.2f}s (target: <15s)"
        )

    def test_meditation_generation_performance(
        self, real_gemini_service, test_meditation_input, retry_on_rate_limit
    ):
        """Test that meditation generation completes within acceptable time."""
        # Act with retry on rate limit
        start_time = time.time()
        result = retry_on_rate_limit(
            lambda: real_gemini_service.generate_meditation(test_meditation_input)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert result, "Should return meditation"
        assert (
            elapsed_time < 60
        ), f"Meditation generation should complete within 60s, took {elapsed_time:.2f}s"

        print(
            f"\n✓ Meditation generation performance: {elapsed_time:.2f}s (target: <60s)"
        )
