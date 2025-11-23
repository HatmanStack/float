"""End-to-end tests for complete summary request flow."""

import time

import pytest

from tests.integration.test_config import test_config


@pytest.mark.e2e
@pytest.mark.slow
class TestSummaryFlowHappyPath:
    """E2E tests for summary request happy path."""

    def test_complete_summary_flow_sad_emotion(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
        e2e_test_s3_cleanup,
    ):
        """Test complete summary flow for sad emotion."""
        # Arrange
        request_body = summary_request_body_factory(
            user_id=test_user_id,
            prompt="I'm feeling really down today. Work has been overwhelming and I'm stressed.",
        )

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Track S3 objects for cleanup
        if test_config.has_aws_credentials():
            import boto3

            from src.config.settings import settings

            s3_client = boto3.client(
                "s3",
                region_name=test_config.AWS_REGION,
                aws_access_key_id=test_config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=test_config.AWS_SECRET_ACCESS_KEY,
            )

            # List and track all objects created for this test user
            for prefix in [f"{test_user_id}/summary/", f"{test_user_id}/audio/"]:
                try:
                    objects = s3_client.list_objects_v2(
                        Bucket=settings.AWS_S3_BUCKET, Prefix=prefix
                    )
                    if "Contents" in objects:
                        for obj in objects["Contents"]:
                            e2e_test_s3_cleanup.append((settings.AWS_S3_BUCKET, obj["Key"]))
                except Exception as e:
                    print(f"Warning: Could not list S3 objects for cleanup: {e}")

        # Assert
        assert response, "Response should not be None"
        assert "sentiment_label" in response, "Response should have sentiment_label"
        assert "intensity" in response, "Response should have intensity"
        assert "user_summary" in response, "Response should have user_summary"

        # Verify sentiment is appropriate
        assert response["sentiment_label"] in [
            "Sad",
            "Fearful",
            "Angry",
        ], f"Expected negative sentiment, got {response['sentiment_label']}"
        assert 1 <= response["intensity"] <= 5, "Intensity should be between 1 and 5"

        # Verify timing
        assert (
            elapsed_time < 20
        ), f"Summary flow should complete within 20s, took {elapsed_time:.2f}s"

        print(f"\n✓ Complete summary flow (sad) completed in {elapsed_time:.2f}s")
        print(
            f"  Sentiment: {response['sentiment_label']} (intensity: {response['intensity']})"
        )

    def test_complete_summary_flow_happy_emotion(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test complete summary flow for happy emotion."""
        # Arrange
        request_body = summary_request_body_factory(
            user_id=test_user_id,
            prompt="I had an amazing day! Everything went perfectly and I'm so grateful.",
        )

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Response should not be None"
        assert response["sentiment_label"] in [
            "Happy",
            "Neutral",
        ], f"Expected positive sentiment, got {response['sentiment_label']}"

        print(f"\n✓ Complete summary flow (happy) completed in {elapsed_time:.2f}s")

    def test_complete_summary_flow_anxious_emotion(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test complete summary flow for anxious emotion."""
        # Arrange
        request_body = summary_request_body_factory(
            user_id=test_user_id,
            prompt="I'm really anxious about the presentation tomorrow. Can't stop worrying.",
        )

        # Act
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )

        # Assert
        assert response, "Response should not be None"
        assert response["sentiment_label"] in [
            "Fearful",
            "Sad",
            "Angry",
        ], f"Expected anxious sentiment, got {response['sentiment_label']}"

        print("\n✓ Complete summary flow (anxious) completed")

    def test_response_format_complete(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test that response has all required fields."""
        # Arrange
        request_body = summary_request_body_factory(
            user_id=test_user_id,
            prompt="I'm feeling neutral today.",
        )

        # Act
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )

        # Assert - verify all required fields present
        required_fields = [
            "sentiment_label",
            "intensity",
            "speech_to_text",
            "added_text",
            "summary",
            "user_summary",
            "user_short_summary",
        ]

        for field in required_fields:
            assert field in response, f"Response missing required field: {field}"

        # Verify field types
        assert isinstance(response["sentiment_label"], str), "sentiment_label should be string"
        assert isinstance(response["intensity"], int), "intensity should be integer"
        assert isinstance(response["summary"], str), "summary should be string"

        print("\n✓ Response format complete with all required fields")


@pytest.mark.e2e
@pytest.mark.slow
class TestSummaryFlowEdgeCases:
    """E2E tests for summary request edge cases."""

    def test_very_long_input_text(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test summary flow with very long input text."""
        # Arrange - 500 word text
        long_text = (
            "I had a very difficult and challenging day at work today. "
            "Everything seemed to go wrong from the moment I woke up. "
        ) * 50  # ~500 words

        request_body = summary_request_body_factory(
            user_id=test_user_id, prompt=long_text
        )

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Should handle long text"
        assert "sentiment_label" in response, "Should return sentiment"
        assert (
            elapsed_time < 30
        ), f"Long text should complete within 30s, took {elapsed_time:.2f}s"

        print(f"\n✓ Long text handled successfully in {elapsed_time:.2f}s")

    def test_text_with_special_characters(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test summary flow with special characters and emojis."""
        # Arrange
        special_text = "I'm feeling 😢 so sad & stressed!!! Can't believe it's happening... $#@% 123"

        request_body = summary_request_body_factory(
            user_id=test_user_id, prompt=special_text
        )

        # Act
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )

        # Assert
        assert response, "Should handle special characters"
        assert "sentiment_label" in response, "Should return sentiment"

        print("\n✓ Special characters handled successfully")

    def test_minimal_input_text(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test summary flow with minimal input text."""
        # Arrange
        minimal_text = "Sad."

        request_body = summary_request_body_factory(
            user_id=test_user_id, prompt=minimal_text
        )

        # Act
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )

        # Assert
        assert response, "Should handle minimal text"
        assert "sentiment_label" in response, "Should return sentiment"

        print("\n✓ Minimal text handled successfully")

    def test_multiple_requests_in_sequence(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test multiple summary requests in sequence."""
        # Arrange
        prompts = [
            "I'm feeling happy today.",
            "I'm feeling sad today.",
            "I'm feeling neutral today.",
        ]

        # Act & Assert
        for i, prompt in enumerate(prompts):
            request_body = summary_request_body_factory(
                user_id=test_user_id, prompt=prompt
            )

            response = lambda_handler_real.handle_summary_request(
                parse_request_from_dict(request_body)
            )

            assert response, f"Request {i+1} should succeed"
            assert "sentiment_label" in response, f"Request {i+1} should return sentiment"

            print(f"  ✓ Request {i+1} completed: {response['sentiment_label']}")


@pytest.mark.e2e
@pytest.mark.slow
class TestSummaryFlowErrorHandling:
    """E2E tests for summary request error handling."""

    def test_invalid_request_missing_prompt(
        self,
        lambda_handler_real,
        test_user_id,
    ):
        """Test summary flow with missing prompt field."""
        # Arrange - create request missing prompt
        from src.models.requests import SummaryRequest

        # Act & Assert - should raise validation error
        with pytest.raises(Exception):  # Will fail validation
            request = SummaryRequest(
                type="summary",
                user_id=test_user_id,
                prompt=None,  # Invalid - prompt required
                audio="NotAvailable",
            )
            lambda_handler_real.handle_summary_request(request)

        print("\n✓ Missing prompt handled with validation error")

    def test_invalid_request_missing_user_id(self):
        """Test summary flow with missing user_id."""
        # Arrange
        from src.models.requests import SummaryRequest

        # Act & Assert - should raise validation error
        with pytest.raises(Exception):  # Will fail validation
            SummaryRequest(
                type="summary",
                user_id=None,  # Invalid - user_id required
                prompt="Test prompt",
                audio="NotAvailable",
            )

        print("\n✓ Missing user_id handled with validation error")


@pytest.mark.e2e
@pytest.mark.slow
class TestSummaryFlowPerformance:
    """E2E tests for summary flow performance."""

    def test_summary_flow_performance_within_limits(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test that summary flow completes within acceptable time."""
        # Arrange
        request_body = summary_request_body_factory(
            user_id=test_user_id,
            prompt="I'm feeling stressed about work deadlines.",
        )

        # Act
        start_time = time.time()
        response = lambda_handler_real.handle_summary_request(
            parse_request_from_dict(request_body)
        )
        elapsed_time = time.time() - start_time

        # Assert
        assert response, "Should return response"
        assert (
            elapsed_time < 15
        ), f"Summary flow should complete within 15s, took {elapsed_time:.2f}s"

        print(f"\n✓ Summary flow performance: {elapsed_time:.2f}s (target: <15s)")

    def test_average_performance_over_multiple_requests(
        self,
        lambda_handler_real,
        summary_request_body_factory,
        test_user_id,
    ):
        """Test average performance over multiple requests."""
        # Arrange
        num_requests = 3
        prompts = [
            "I'm feeling happy.",
            "I'm feeling sad.",
            "I'm feeling anxious.",
        ]

        # Act
        times = []
        for prompt in prompts:
            request_body = summary_request_body_factory(
                user_id=test_user_id, prompt=prompt
            )

            start_time = time.time()
            response = lambda_handler_real.handle_summary_request(
                parse_request_from_dict(request_body)
            )
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)

            assert response, "Each request should succeed"

        # Assert
        avg_time = sum(times) / len(times)
        assert (
            avg_time < 15
        ), f"Average time should be <15s, got {avg_time:.2f}s"

        print(f"\n✓ Average performance over {num_requests} requests: {avg_time:.2f}s")
        print(f"  Min: {min(times):.2f}s, Max: {max(times):.2f}s")


# Helper function to parse request from dict
def parse_request_from_dict(request_dict):
    """Parse request dict into SummaryRequest object."""
    from src.models.requests import SummaryRequest

    return SummaryRequest(**request_dict)
