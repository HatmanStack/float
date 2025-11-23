from abc import ABC, abstractmethod
from typing import List


class AudioService(ABC):
    pass

    @abstractmethod
    def get_audio_duration(self, file_path: str) -> float: ...

    @abstractmethod
    def combine_voice_and_music(
        self, voice_path: str, music_list: List[str], timestamp: str, output_path: str
    ) -> List[str]: ...

    @abstractmethod
    def select_background_music(
        self, used_music: List[str], duration: float, output_path: str
    ) -> List[str]: ...
