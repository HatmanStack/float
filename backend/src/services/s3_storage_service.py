import json
from typing import Any, Dict, List, Optional

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from .storage_service import StorageService


class S3StorageService(StorageService):
    """AWS S3 storage service implementation."""

    def __init__(self):
        self.s3_client = boto3.client("s3")

    def upload_json(self, bucket: str, key: str, data: Dict[str, Any]) -> bool:
        """
        Upload JSON data to S3.

        Args:
            bucket: S3 bucket name
            key: Object key/path
            data: Data to upload as JSON

        Returns:
            True if successful, False otherwise
        """
        try:
            json_data = json.dumps(data)
            self.s3_client.put_object(Bucket=bucket, Key=key, Body=json_data)
            print(f"Successfully uploaded {key} to {bucket}")
            return True

        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error uploading to S3: {e}")
            return False

    def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """
        Download file from S3 to local path.

        Args:
            bucket: S3 bucket name
            key: Object key/path
            local_path: Local file path to save to

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(bucket, key, local_path)
            print(f"File downloaded successfully: {key} -> {local_path}")
            return True

        except ClientError as e:
            print(f"Error downloading file {key}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error downloading file {key}: {e}")
            return False

    def list_objects(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
        """
        List objects in S3 bucket.

        Args:
            bucket: S3 bucket name
            prefix: Optional prefix to filter objects

        Returns:
            List of object keys
        """
        try:
            kwargs = {"Bucket": bucket}
            if prefix:
                kwargs["Prefix"] = prefix

            response = self.s3_client.list_objects_v2(**kwargs)

            if "Contents" in response:
                return [obj["Key"] for obj in response["Contents"]]
            else:
                return []

        except ClientError as e:
            print(f"Error listing objects in bucket {bucket}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error listing objects in bucket {bucket}: {e}")
            return []
