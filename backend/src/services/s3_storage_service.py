import json
from typing import Any, Dict, List, Optional

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from ..utils.logging_utils import get_logger
from .storage_service import StorageService

logger = get_logger(__name__)


class S3StorageService(StorageService):

    def __init__(self):
        self.s3_client = boto3.client("s3")

    def upload_json(self, bucket: str, key: str, data: Dict[str, Any]) -> bool:
        try:
            json_data = json.dumps(data)
            self.s3_client.put_object(Bucket=bucket, Key=key, Body=json_data)
            logger.debug("Uploaded to S3", extra={"data": {"bucket": bucket, "key": key}})
            return True
        except ClientError as e:
            logger.error("Error uploading to S3", extra={"data": {"error": str(e)}})
            return False
        except Exception:
            logger.error("Unexpected error uploading to S3", exc_info=True)
            return False

    def download_json(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            logger.error(
                "Error downloading JSON",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return None
        except Exception:
            logger.error("Unexpected error downloading JSON", exc_info=True)
            return None

    def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        try:
            self.s3_client.download_file(bucket, key, local_path)
            logger.debug(
                "File downloaded",
                extra={"data": {"key": key, "local_path": local_path}}
            )
            return True
        except ClientError as e:
            logger.error(
                "Error downloading file",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return False
        except Exception:
            logger.error("Unexpected error downloading file", exc_info=True)
            return False

    def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from S3."""
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.debug("Deleted from S3", extra={"data": {"bucket": bucket, "key": key}})
            return True
        except ClientError as e:
            logger.error(
                "Error deleting from S3",
                extra={"data": {"key": key, "error": str(e)}}
            )
            return False
        except Exception:
            logger.error("Unexpected error deleting from S3", exc_info=True)
            return False

    def list_objects(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
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
            logger.error(
                "Error listing objects",
                extra={"data": {"bucket": bucket, "error": str(e)}}
            )
            return []
        except Exception:
            logger.error("Unexpected error listing objects", exc_info=True)
            return []
