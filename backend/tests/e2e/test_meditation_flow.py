"""End-to-end tests for complete meditation request flow."""

import base64
import time

import pytest


@pytest.mark.e2e
@pytest.mark.slow
class TestMeditationFlowHappyPath:
    """E2E tests for meditation request happy path."""

    def test_complete_meditation_flow_sad_emotion(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test complete meditation flow for sad emotion."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Sad"],
            intensity=[4],
            music_list=[],  # No background music for faster test
        )

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Response should not be None"
        assert "base64_audio" in response, "Response should have base64_audio"
        assert "music_list" in response, "Response should have music_list"

        # Verify audio is valid base64
        audio_data = response["base64_audio"]
        assert audio_data, "Audio data should not be empty"
        assert len(audio_data) > 1000, "Audio data should have substantial content"

        # Try to decode base64 to verify it's valid
        try:
            decoded = base64.b64decode(audio_data)
            assert len(decoded) > 0, "Decoded audio should have content"
        except Exception as e:
            pytest.fail(f"Audio is not valid base64: {e}")

        # Verify timing
        assert (
            elapsed_time < 90
        ), f"Meditation flow should complete within 90s, took {elapsed_time:.2f}s"

        print(f"\n✓ Complete meditation flow (sad) completed in {elapsed_time:.2f}s")
        print(f"  Audio size: {len(audio_data):,} characters (base64)")

    def test_complete_meditation_flow_happy_emotion(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test complete meditation flow for happy emotion."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Happy"],
            intensity=[3],
            music_list=[],
        )

        # Update input_data for happy emotion
        request_body["input_data"]["added_text"] = ["I had a wonderful day"]
        request_body["input_data"]["summary"] = ["User experiencing happiness"]
        request_body["input_data"]["user_summary"] = ["Had an amazing day"]

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Response should not be None"
        assert "base64_audio" in response, "Should return audio"
        assert len(response["base64_audio"]) > 1000, "Audio should have content"

        print(f"\n✓ Complete meditation flow (happy) completed in {elapsed_time:.2f}s")

    def test_complete_meditation_flow_anxious_emotion(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test complete meditation flow for anxious emotion."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Fearful"],
            intensity=[5],
            music_list=[],
        )

        # Update input_data for anxious emotion
        request_body["input_data"]["added_text"] = ["Worried about presentation"]
        request_body["input_data"]["summary"] = ["User experiencing anxiety"]
        request_body["input_data"]["user_summary"] = [
            "Anxious about upcoming presentation"
        ]

        # Act
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )

        # Assert
        assert response, "Response should not be None"
        assert "base64_audio" in response, "Should return audio"

        print("\n✓ Complete meditation flow (anxious) completed")

    def test_meditation_with_various_intensities(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test meditation generation with different intensity levels."""
        for intensity in [1, 3, 5]:
            # Arrange
            request_body = meditation_request_body_factory(
                user_id=test_user_id,
                sentiment_label=["Sad"],
                intensity=[intensity],
                music_list=[],
            )

            # Act
            response = lambda_handler_real.handle_meditation_request(
                parse_meditation_request_from_dict(request_body)
            )

            # Assert
            assert response, f"Should return response for intensity {intensity}"
            assert (
                "base64_audio" in response
            ), f"Should have audio for intensity {intensity}"
            assert (
                len(response["base64_audio"]) > 500
            ), f"Should have audio content for intensity {intensity}"

            print(f"  ✓ Meditation generated for intensity {intensity}")

    def test_response_format_complete(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test that meditation response has all required fields."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Neutral"],
            intensity=[2],
            music_list=[],
        )

        # Act
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )

        # Assert - verify all required fields present
        required_fields = ["base64_audio", "music_list"]

        for field in required_fields:
            assert field in response, f"Response missing required field: {field}"

        # Verify field types
        assert isinstance(
            response["base64_audio"], str
        ), "base64_audio should be string"
        assert isinstance(response["music_list"], list), "music_list should be list"

        print("\n✓ Meditation response format complete with all required fields")


@pytest.mark.e2e
@pytest.mark.slow
class TestMeditationFlowWithMusic:
    """E2E tests for meditation with background music integration."""

    @pytest.mark.skip(reason="Requires actual music files in Lambda environment")
    def test_meditation_with_background_music(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test meditation with background music combination."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Sad"],
            intensity=[3],
            music_list=["Ambient-Peaceful-Meditation_300.wav"],
        )

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Response should not be None"
        assert "base64_audio" in response, "Should return combined audio"
        assert "music_list" in response, "Should return music list"

        # Audio should be larger with music
        assert len(response["base64_audio"]) > 5000, "Combined audio should be larger"

        print(f"\n✓ Meditation with music completed in {elapsed_time:.2f}s")

    def test_meditation_without_music(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test meditation without background music."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Happy"],
            intensity=[2],
            music_list=[],  # No music
        )

        # Act
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )

        # Assert
        assert response, "Response should not be None"
        assert "base64_audio" in response, "Should return voice-only audio"
        assert len(response["base64_audio"]) > 1000, "Voice audio should have content"

        print("\n✓ Meditation without music completed successfully")


@pytest.mark.e2e
@pytest.mark.slow
class TestMeditationFlowEdgeCases:
    """E2E tests for meditation request edge cases."""

    def test_meditation_with_multiple_instances(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test meditation generation with multiple instances."""
        # Arrange - multiple incidents
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Sad", "Angry"],
            intensity=[4, 3],
            music_list=[],
        )

        # Update for multiple instances
        request_body["input_data"]["sentiment_label"] = ["Sad", "Angry"]
        request_body["input_data"]["intensity"] = [4, 3]
        request_body["input_data"]["speech_to_text"] = ["NotAvailable", "NotAvailable"]
        request_body["input_data"]["added_text"] = [
            "Work stress",
            "Argument with friend",
        ]
        request_body["input_data"]["summary"] = [
            "Stressful work situation",
            "Conflict with friend",
        ]
        request_body["input_data"]["user_summary"] = [
            "Had stressful day at work",
            "Had argument with friend",
        ]
        request_body["input_data"]["user_short_summary"] = [
            "Work stress",
            "Friend conflict",
        ]

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Should handle multiple instances"
        assert "base64_audio" in response, "Should return audio"
        # Meditation for multiple instances should be longer
        assert (
            len(response["base64_audio"]) > 2000
        ), "Multiple instances should produce longer meditation"

        print(f"\n✓ Multiple instances handled in {elapsed_time:.2f}s")

    def test_meditation_edge_case_intensity_values(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test meditation with edge case intensity values."""
        for intensity in [1, 5]:  # Min and max
            # Arrange
            request_body = meditation_request_body_factory(
                user_id=test_user_id,
                sentiment_label=["Sad"],
                intensity=[intensity],
                music_list=[],
            )

            # Act
            response = lambda_handler_real.handle_meditation_request(
                parse_meditation_request_from_dict(request_body)
            )

            # Assert
            assert response, f"Should handle intensity {intensity}"
            assert (
                "base64_audio" in response
            ), f"Should return audio for intensity {intensity}"

            print(f"  ✓ Edge case intensity {intensity} handled")


@pytest.mark.e2e
@pytest.mark.slow
class TestMeditationFlowErrorHandling:
    """E2E tests for meditation request error handling."""

    def test_invalid_request_missing_input_data(
        self,
        lambda_handler_real,
        test_user_id,
    ):
        """Test meditation flow with missing input_data."""
        # Arrange
        from src.models.requests import MeditationRequest

        # Act & Assert - should raise validation error
        with pytest.raises(Exception):  # Will fail validation
            request = MeditationRequest(
                type="meditation",
                user_id=test_user_id,
                input_data=None,  # Invalid - input_data required
                music_list=[],
            )
            lambda_handler_real.handle_meditation_request(request)

        print("\n✓ Missing input_data handled with validation error")

    def test_invalid_request_missing_user_id(self):
        """Test meditation flow with missing user_id."""
        # Arrange
        from src.models.requests import MeditationRequest

        # Act & Assert - should raise validation error
        with pytest.raises(Exception):  # Will fail validation
            MeditationRequest(
                type="meditation",
                user_id=None,  # Invalid - user_id required
                input_data={"sentiment_label": ["Sad"]},
                music_list=[],
            )

        print("\n✓ Missing user_id handled with validation error")


@pytest.mark.e2e
@pytest.mark.slow
class TestMeditationFlowPerformance:
    """E2E tests for meditation flow performance."""

    def test_meditation_flow_performance_within_limits(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test that meditation flow completes within acceptable time."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Sad"],
            intensity=[3],
            music_list=[],  # No music for faster test
        )

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Should return response"
        assert (
            elapsed_time < 90
        ), f"Meditation flow should complete within 90s, took {elapsed_time:.2f}s"

        print(f"\n✓ Meditation flow performance: {elapsed_time:.2f}s (target: <90s)")

    def test_audio_size_reasonable(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test that generated audio size is reasonable."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Happy"],
            intensity=[2],
            music_list=[],
        )

        # Act
        response = lambda_handler_real.handle_meditation_request(
            parse_meditation_request_from_dict(request_body)
        )

        # Assert
        audio_size = len(response["base64_audio"])
        assert (
            1000 < audio_size < 10000000
        ), f"Audio size should be reasonable, got {audio_size} characters"

        # Decode to get actual byte size
        decoded_size = len(base64.b64decode(response["base64_audio"]))

        print("\n✓ Audio size reasonable:")
        print(f"  Base64: {audio_size:,} characters")
        print(f"  Decoded: {decoded_size:,} bytes ({decoded_size/1024/1024:.2f} MB)")


# Helper function to parse meditation request from dict
def parse_meditation_request_from_dict(request_dict):
    """Parse request dict into MeditationRequest object."""
    from src.models.requests import MeditationRequest

    return MeditationRequest(**request_dict)
