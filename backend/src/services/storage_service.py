from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageService(ABC):

    @abstractmethod
    def upload_json(self, bucket: str, key: str, data: Dict[str, Any]) -> bool: ...

    @abstractmethod
    def download_file(self, bucket: str, key: str, local_path: str) -> bool: ...

    @abstractmethod
    def list_objects(self, bucket: str, prefix: Optional[str] = None) -> List[str]: ...
