from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
class AIService(ABC):
    """Abstract base class for AI services."""

    @abstractmethod
    def analyze_sentiment(self, audio_file: Optional[str], user_text: Optional[str]) -> str:
        """
        Analyze sentiment from audio and/or text input.

        Args:
            audio_file: Path to audio file or None if not available
            user_text: Text input or None if not available

        Returns:
            JSON string containing sentiment analysis results
        """
        pass

    @abstractmethod
    def generate_meditation(self, input_data: Dict[str, Any]) -> str:
        """
        Generate meditation transcript based on input data.

        Args:
            input_data: Dictionary containing user data for meditation generation

        Returns:
            Meditation transcript text
        """
        pass
