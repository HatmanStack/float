from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageService(ABC):
    """Abstract base class for storage services."""

    @abstractmethod
    def upload_json(self, bucket: str, key: str, data: Dict[str, Any]) -> bool:
        """
        Upload JSON data to storage.

        Args:
            bucket: Storage bucket name
            key: Object key/path
            data: Data to upload

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """
        Download file from storage to local path.

        Args:
            bucket: Storage bucket name
            key: Object key/path
            local_path: Local file path to save to

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_objects(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
        """
        List objects in storage bucket.

        Args:
            bucket: Storage bucket name
            prefix: Optional prefix to filter objects

        Returns:
            List of object keys
        """
        pass
