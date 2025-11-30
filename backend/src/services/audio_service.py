from abc import ABC, abstractmethod
from typing import List
class AudioService(ABC):
    """Abstract base class for audio processing services."""

    @abstractmethod
    def get_audio_duration(self, file_path: str) -> float:
        """
        Get duration of audio file in seconds.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds
        """
        pass

    @abstractmethod
    def combine_voice_and_music(
        self, voice_path: str, music_list: List[str], timestamp: str, output_path: str
    ) -> List[str]:
        """
        Combine voice recording with background music.

        Args:
            voice_path: Path to voice audio file
            music_list: List of previously used music tracks
            timestamp: Timestamp for temporary file naming
            output_path: Path for combined output file

        Returns:
            Updated list of used music tracks
        """
        pass

    @abstractmethod
    def select_background_music(
        self, used_music: List[str], duration: float, output_path: str
    ) -> List[str]:
        """
        Select and download appropriate background music.

        Args:
            used_music: List of previously used music tracks
            duration: Required duration in seconds
            output_path: Path to save selected music

        Returns:
            Updated list of used music tracks
        """
        pass
