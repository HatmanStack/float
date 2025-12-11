from abc import ABC, abstractmethod
from typing import Iterator


class TTSService(ABC):

    @abstractmethod
    def synthesize_speech(self, text: str, output_path: str) -> bool: ...

    @abstractmethod
    def stream_speech(self, text: str) -> Iterator[bytes]: ...

    @abstractmethod
    def get_provider_name(self) -> str: ...
