from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIService(ABC):
    pass
    @abstractmethod
    def analyze_sentiment(self, audio_file: Optional[str], user_text: Optional[str]) -> str:
        pass
        pass
    @abstractmethod
    def generate_meditation(self, input_data: Dict[str, Any]) -> str:
        pass
        pass
