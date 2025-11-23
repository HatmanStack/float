from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageService(ABC):
    pass
    @abstractmethod
    def upload_json(self, bucket: str, key: str, data: Dict[str, Any]) -> bool:
        pass
        pass
    @abstractmethod
    def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        pass
        pass
    @abstractmethod
    def list_objects(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
        pass
        pass
