"""End-to-end tests for complete meditation request flow.

Tests the async meditation API contract:
  1. handle_meditation_request() returns {job_id, status: "pending", message}
  2. process_meditation_async() processes the job in the background
  3. Job status transitions: pending -> processing -> completed/failed
"""

import time

import pytest


@pytest.mark.e2e
@pytest.mark.slow
class TestMeditationFlowHappyPath:
    """E2E tests for meditation request happy path (async job contract)."""

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
            music_list=[],
        )
        request = parse_meditation_request_from_dict(request_body)

        # Act - Step 1: Submit returns job_id immediately
        submit_response = lambda_handler_real.handle_meditation_request(request)

        # Assert async job creation response
        assert submit_response, "Response should not be None"
        assert "job_id" in submit_response, "Response should have job_id"
        assert submit_response["status"] == "pending", "Initial status should be pending"
        assert "message" in submit_response, "Response should have message"

        job_id = submit_response["job_id"]

        # Act - Step 2: Process the meditation asynchronously
        start_time = time.time()
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())
        elapsed_time = time.time() - start_time

        # Assert - Job should be completed
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", (
            f"Job should be completed, got {job_data['status']}"
        )

        # Verify timing
        assert elapsed_time < 90, (
            f"Meditation flow should complete within 90s, took {elapsed_time:.2f}s"
        )

        print(f"\n✓ Complete meditation flow (sad) completed in {elapsed_time:.2f}s")

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
        request_body["input_data"]["added_text"] = ["I had a wonderful day"]
        request_body["input_data"]["summary"] = ["User experiencing happiness"]
        request_body["input_data"]["user_summary"] = ["Had an amazing day"]
        request = parse_meditation_request_from_dict(request_body)

        # Act
        submit_response = lambda_handler_real.handle_meditation_request(request)
        assert "job_id" in submit_response, "Should return job_id"

        job_id = submit_response["job_id"]
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())

        # Assert
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", "Job should be completed"

        print("\n✓ Complete meditation flow (happy) completed")

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
        request_body["input_data"]["added_text"] = ["Worried about presentation"]
        request_body["input_data"]["summary"] = ["User experiencing anxiety"]
        request_body["input_data"]["user_summary"] = ["Anxious about upcoming presentation"]
        request = parse_meditation_request_from_dict(request_body)

        # Act
        submit_response = lambda_handler_real.handle_meditation_request(request)
        assert "job_id" in submit_response, "Should return job_id"

        job_id = submit_response["job_id"]
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())

        # Assert
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", "Job should be completed"

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
            request = parse_meditation_request_from_dict(request_body)

            # Act
            submit_response = lambda_handler_real.handle_meditation_request(request)
            assert "job_id" in submit_response, f"Should return job_id for intensity {intensity}"

            job_id = submit_response["job_id"]
            lambda_handler_real.process_meditation_async(job_id, request.to_dict())

            # Assert
            job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
            assert job_data is not None, f"Job should exist for intensity {intensity}"
            assert job_data["status"] == "completed", (
                f"Job should be completed for intensity {intensity}"
            )

            print(f"  ✓ Meditation generated for intensity {intensity}")

    def test_response_format_complete(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test that meditation submit response has all required async fields."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Neutral"],
            intensity=[2],
            music_list=[],
        )
        request = parse_meditation_request_from_dict(request_body)

        # Act
        submit_response = lambda_handler_real.handle_meditation_request(request)

        # Assert - verify all required async fields present
        required_fields = ["job_id", "status", "message"]
        for field in required_fields:
            assert field in submit_response, f"Response missing required field: {field}"

        # Verify field types
        assert isinstance(submit_response["job_id"], str), "job_id should be string"
        assert submit_response["status"] == "pending", "status should be 'pending'"
        assert isinstance(submit_response["message"], str), "message should be string"

        print("\n✓ Meditation response format complete with all required async fields")


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
        request = parse_meditation_request_from_dict(request_body)

        # Act
        start_time = time.time()
        submit_response = lambda_handler_real.handle_meditation_request(request)
        job_id = submit_response["job_id"]
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())
        elapsed_time = time.time() - start_time

        # Assert
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", "Job should be completed"

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
            music_list=[],
        )
        request = parse_meditation_request_from_dict(request_body)

        # Act
        submit_response = lambda_handler_real.handle_meditation_request(request)
        assert "job_id" in submit_response, "Should return job_id"

        job_id = submit_response["job_id"]
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())

        # Assert
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", "Job should be completed"

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
        request = parse_meditation_request_from_dict(request_body)

        # Act
        start_time = time.time()
        submit_response = lambda_handler_real.handle_meditation_request(request)
        job_id = submit_response["job_id"]
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())
        elapsed_time = time.time() - start_time

        # Assert
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", "Job should be completed"

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
            request = parse_meditation_request_from_dict(request_body)

            # Act
            submit_response = lambda_handler_real.handle_meditation_request(request)
            job_id = submit_response["job_id"]
            lambda_handler_real.process_meditation_async(job_id, request.to_dict())

            # Assert
            job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
            assert job_data is not None, f"Job should exist for intensity {intensity}"
            assert job_data["status"] == "completed", (
                f"Job should be completed for intensity {intensity}"
            )

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
        from src.models.requests import MeditationRequestModel

        # Act & Assert - should raise validation error
        with pytest.raises(Exception):  # Will fail validation
            request = MeditationRequestModel(
                inference_type="meditation",
                user_id=test_user_id,
                input_data=None,  # Invalid - input_data required
                music_list=[],
            )
            lambda_handler_real.handle_meditation_request(request)

        print("\n✓ Missing input_data handled with validation error")

    def test_invalid_request_missing_user_id(self):
        """Test meditation flow with missing user_id."""
        # Arrange
        from src.models.requests import MeditationRequestModel

        # Act & Assert - should raise validation error
        with pytest.raises(Exception):  # Will fail validation
            MeditationRequestModel(
                inference_type="meditation",
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
            music_list=[],
        )
        request = parse_meditation_request_from_dict(request_body)

        # Act
        start_time = time.time()
        submit_response = lambda_handler_real.handle_meditation_request(request)
        job_id = submit_response["job_id"]
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())
        elapsed_time = time.time() - start_time

        # Assert
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", "Job should be completed"
        assert elapsed_time < 90, (
            f"Meditation flow should complete within 90s, took {elapsed_time:.2f}s"
        )

        print(f"\n✓ Meditation flow performance: {elapsed_time:.2f}s (target: <90s)")

    def test_job_status_after_completion(
        self,
        lambda_handler_real,
        meditation_request_body_factory,
        test_user_id,
    ):
        """Test that job status is correctly set after completion."""
        # Arrange
        request_body = meditation_request_body_factory(
            user_id=test_user_id,
            sentiment_label=["Happy"],
            intensity=[2],
            music_list=[],
        )
        request = parse_meditation_request_from_dict(request_body)

        # Act
        submit_response = lambda_handler_real.handle_meditation_request(request)
        job_id = submit_response["job_id"]
        lambda_handler_real.process_meditation_async(job_id, request.to_dict())

        # Assert
        job_data = lambda_handler_real.job_service.get_job(test_user_id, job_id)
        assert job_data is not None, "Job should exist"
        assert job_data["status"] == "completed", "Job should be completed"
        assert job_data["job_id"] == job_id, "Job ID should match"
        assert job_data["user_id"] == test_user_id, "User ID should match"

        print("\n✓ Job status correctly set after completion")


# Helper function to parse meditation request from dict
def parse_meditation_request_from_dict(request_dict):
    """Parse request dict into MeditationRequestModel object."""
    from src.models.requests import MeditationRequestModel

    return MeditationRequestModel(**request_dict)
