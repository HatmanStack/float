from abc import ABC, abstractmethod


class TTSService(ABC):
    pass

    @abstractmethod
    def synthesize_speech(self, text: str, output_path: str) -> bool: ...

    @abstractmethod
    def get_provider_name(self) -> str: ...
