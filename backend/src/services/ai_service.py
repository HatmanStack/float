from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIService(ABC):

    @abstractmethod
    def analyze_sentiment(
        self, audio_file: Optional[str], user_text: Optional[str]
    ) -> str: ...

    @abstractmethod
    def generate_meditation(self, input_data: Dict[str, Any], duration_minutes: int = 5) -> str: ...
