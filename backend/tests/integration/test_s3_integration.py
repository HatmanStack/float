"""Integration tests for S3 storage service with real AWS API calls."""

import json
import os
import tempfile
import time
from datetime import datetime

import pytest

from tests.integration.test_config import test_config


@pytest.mark.integration
@pytest.mark.slow
class TestS3UploadIntegration:
    """Integration tests for S3 upload operations with real AWS."""

    def test_upload_json_data(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test uploading JSON data to S3."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = test_config.get_test_s3_key(
            test_user_id, f"test_upload_{timestamp}.json"
        )
        test_data = {
            "user_id": test_user_id,
            "timestamp": timestamp,
            "sentiment_label": "Happy",
            "intensity": 4,
            "test": True,
        }

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Act
        start_time = time.time()
        result = real_s3_storage_service.upload_json(bucket, key, test_data)
        elapsed_time = time.time() - start_time

        # Assert
        assert result is True, "Upload should succeed"
        assert (
            elapsed_time < test_config.S3_TIMEOUT
        ), f"Upload took too long: {elapsed_time:.2f}s"

        print(f"\n✓ JSON upload completed in {elapsed_time:.2f}s")
        print(f"  Bucket: {bucket}")
        print(f"  Key: {key}")

    def test_upload_sentiment_result(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test uploading a sentiment analysis result to S3."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = test_config.get_test_s3_key(
            test_user_id, f"sentiment_{timestamp}.json"
        )
        sentiment_data = {
            "user_id": test_user_id,
            "sentiment_label": "Sad",
            "intensity": 4,
            "speech_to_text": "NotAvailable",
            "added_text": "I had a difficult day",
            "summary": "User experienced sadness",
            "user_summary": "I had a difficult day at work",
            "user_short_summary": "Bad work day",
            "timestamp": timestamp,
        }

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Act
        result = real_s3_storage_service.upload_json(bucket, key, sentiment_data)

        # Assert
        assert result is True, "Sentiment result upload should succeed"

        print("\n✓ Sentiment result uploaded successfully")

    def test_upload_meditation_metadata(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test uploading meditation metadata to S3."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = test_config.get_test_s3_key(
            test_user_id, f"meditation_{timestamp}.json"
        )
        meditation_data = {
            "user_id": test_user_id,
            "timestamp": timestamp,
            "meditation_text": "Let's begin this meditation...",
            "audio_url": "s3://bucket/path/to/audio.mp3",
            "duration": 180,
            "background_music": "Ambient-Peaceful_300.wav",
        }

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Act
        result = real_s3_storage_service.upload_json(bucket, key, meditation_data)

        # Assert
        assert result is True, "Meditation metadata upload should succeed"

        print("\n✓ Meditation metadata uploaded successfully")

    def test_upload_with_user_id_path_structure(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test that uploads use proper user_id path structure."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = test_config.get_test_s3_key(test_user_id, f"data_{timestamp}.json")
        test_data = {"test": "data"}

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Act
        result = real_s3_storage_service.upload_json(bucket, key, test_data)

        # Assert
        assert result is True, "Upload should succeed"
        # Verify key contains user_id
        assert test_user_id in key, f"Key should contain user_id: {key}"

        print("\n✓ Upload with correct user_id path structure")

    def test_upload_complex_nested_data(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test uploading complex nested JSON data."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = test_config.get_test_s3_key(test_user_id, f"complex_{timestamp}.json")
        complex_data = {
            "user_id": test_user_id,
            "sessions": [
                {"timestamp": timestamp, "data": {"nested": {"deeply": "value1"}}},
                {"timestamp": timestamp, "data": {"nested": {"deeply": "value2"}}},
            ],
            "metadata": {"tags": ["test", "integration"], "version": 1},
        }

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Act
        result = real_s3_storage_service.upload_json(bucket, key, complex_data)

        # Assert
        assert result is True, "Complex data upload should succeed"

        print("\n✓ Complex nested data uploaded successfully")


@pytest.mark.integration
@pytest.mark.slow
class TestS3DownloadIntegration:
    """Integration tests for S3 download operations with real AWS."""

    def test_download_uploaded_file(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test downloading a file that was just uploaded."""
        # Arrange - first upload a file
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = test_config.get_test_s3_key(
            test_user_id, f"download_test_{timestamp}.json"
        )
        original_data = {"test": "download", "user_id": test_user_id}

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Upload first
        upload_result = real_s3_storage_service.upload_json(bucket, key, original_data)
        assert upload_result is True, "Upload should succeed first"

        # Act - download the file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            local_path = tmp.name

        try:
            download_result = real_s3_storage_service.download_file(
                bucket, key, local_path
            )

            # Assert
            assert download_result is True, "Download should succeed"
            assert os.path.exists(local_path), "Downloaded file should exist"

            # Verify contents match
            with open(local_path, "r") as f:
                downloaded_data = json.load(f)
            assert downloaded_data == original_data, "Downloaded data should match original"

            print("\n✓ File downloaded and verified successfully")

        finally:
            # Cleanup local file
            if os.path.exists(local_path):
                os.unlink(local_path)

    def test_download_nonexistent_file(self, real_s3_storage_service, test_user_id):
        """Test downloading a file that doesn't exist."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        key = test_config.get_test_s3_key(
            test_user_id, "nonexistent_file_12345.json"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            local_path = tmp.name

        try:
            # Act
            result = real_s3_storage_service.download_file(bucket, key, local_path)

            # Assert - should fail gracefully
            assert result is False, "Download of nonexistent file should return False"

            print("\n✓ Nonexistent file handled gracefully")

        finally:
            # Cleanup
            if os.path.exists(local_path):
                os.unlink(local_path)


@pytest.mark.integration
@pytest.mark.slow
class TestS3ListIntegration:
    """Integration tests for S3 list operations with real AWS."""

    def test_list_objects_with_prefix(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test listing objects with a specific prefix."""
        # Arrange - upload multiple files with same prefix
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = test_config.get_test_s3_key(test_user_id, "")

        # Upload 3 test files
        for i in range(3):
            key = test_config.get_test_s3_key(
                test_user_id, f"list_test_{timestamp}_{i}.json"
            )
            test_data = {"index": i}
            test_s3_keys_to_cleanup.append((bucket, key))
            result = real_s3_storage_service.upload_json(bucket, key, test_data)
            assert result is True, f"Upload {i} should succeed"

        # Act - list objects with prefix
        objects = real_s3_storage_service.list_objects(bucket, prefix)

        # Assert
        assert isinstance(objects, list), "Should return a list"
        assert len(objects) >= 3, f"Should find at least 3 objects, found {len(objects)}"

        # Verify our test files are in the list
        uploaded_keys = [
            test_config.get_test_s3_key(
                test_user_id, f"list_test_{timestamp}_{i}.json"
            )
            for i in range(3)
        ]
        for uploaded_key in uploaded_keys:
            assert uploaded_key in objects, f"Should find uploaded file: {uploaded_key}"

        print(f"\n✓ List objects with prefix found {len(objects)} objects")

    def test_list_objects_empty_prefix(self, real_s3_storage_service):
        """Test listing objects without prefix returns results."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET

        # Act - list all objects (no prefix)
        objects = real_s3_storage_service.list_objects(bucket, prefix=None)

        # Assert
        assert isinstance(objects, list), "Should return a list"
        # May be empty or have objects depending on bucket state

        print(f"\n✓ List all objects returned {len(objects)} objects")

    def test_list_objects_with_nonexistent_prefix(self, real_s3_storage_service):
        """Test listing objects with a prefix that has no matches."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        nonexistent_prefix = f"test-data/nonexistent-user-{time.time()}/data/"

        # Act
        objects = real_s3_storage_service.list_objects(bucket, prefix=nonexistent_prefix)

        # Assert
        assert isinstance(objects, list), "Should return a list"
        assert len(objects) == 0, "Should return empty list for nonexistent prefix"

        print("\n✓ Nonexistent prefix returns empty list")


@pytest.mark.integration
@pytest.mark.slow
class TestS3ErrorHandling:
    """Integration tests for S3 error handling."""

    def test_upload_to_invalid_bucket(self, real_s3_storage_service):
        """Test uploading to a bucket that doesn't exist."""
        # Arrange
        invalid_bucket = f"nonexistent-bucket-{time.time()}"
        key = "test/data.json"
        data = {"test": "data"}

        # Act
        result = real_s3_storage_service.upload_json(invalid_bucket, key, data)

        # Assert - should handle gracefully
        assert result is False, "Should return False for invalid bucket"

        print("\n✓ Invalid bucket handled gracefully")

    def test_upload_with_invalid_key_characters(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test uploading with various key formats."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        # S3 supports most characters in keys
        key = test_config.get_test_s3_key(
            test_user_id, "test-file_with.various+chars.json"
        )
        data = {"test": "data"}

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Act
        result = real_s3_storage_service.upload_json(bucket, key, data)

        # Assert
        assert result is True, "Should handle various characters in key"

        print("\n✓ Various key characters handled successfully")


@pytest.mark.integration
@pytest.mark.slow
class TestS3Performance:
    """Integration tests for S3 performance metrics."""

    def test_upload_performance(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test that S3 upload completes within acceptable time."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = test_config.get_test_s3_key(
            test_user_id, f"perf_test_{timestamp}.json"
        )
        data = {"test": "performance", "timestamp": timestamp}

        # Track for cleanup
        test_s3_keys_to_cleanup.append((bucket, key))

        # Act
        start_time = time.time()
        result = real_s3_storage_service.upload_json(bucket, key, data)
        elapsed_time = time.time() - start_time

        # Assert
        assert result is True, "Upload should succeed"
        assert (
            elapsed_time < 5
        ), f"Upload should complete within 5s, took {elapsed_time:.2f}s"

        print(f"\n✓ Upload performance: {elapsed_time:.2f}s (target: <5s)")

    def test_multiple_uploads_performance(
        self, real_s3_storage_service, test_user_id, test_s3_keys_to_cleanup
    ):
        """Test multiple sequential uploads complete in reasonable time."""
        # Arrange
        bucket = test_config.AWS_S3_BUCKET
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        num_uploads = 5

        # Act
        start_time = time.time()
        for i in range(num_uploads):
            key = test_config.get_test_s3_key(
                test_user_id, f"multi_perf_{timestamp}_{i}.json"
            )
            data = {"index": i, "timestamp": timestamp}
            test_s3_keys_to_cleanup.append((bucket, key))

            result = real_s3_storage_service.upload_json(bucket, key, data)
            assert result is True, f"Upload {i} should succeed"

        elapsed_time = time.time() - start_time

        # Assert
        assert (
            elapsed_time < 15
        ), f"{num_uploads} uploads should complete within 15s, took {elapsed_time:.2f}s"

        print(
            f"\n✓ {num_uploads} uploads performance: {elapsed_time:.2f}s ({elapsed_time/num_uploads:.2f}s avg)"
        )
