from abc import ABC, abstractmethod


class TTSService(ABC):
    """Abstract base class for Text-to-Speech services."""

    @abstractmethod
    def synthesize_speech(self, text: str, output_path: str) -> bool:
        """
        Convert text to speech and save to file.

        Args:
            text: Text content to convert to speech
            output_path: Path where the audio file should be saved

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the TTS provider.

        Returns:
            Provider name string
        """
        pass
