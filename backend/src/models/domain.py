from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ..config.constants import SentimentLabel, TTSProvider


@dataclass
class SentimentAnalysis:
    sentiment_label: SentimentLabel
    intensity: int  # 1-5 scale
    confidence: Optional[float] = None
    summary: Optional[str] = None

    def validate(self) -> bool:
        return (
            isinstance(self.sentiment_label, SentimentLabel)
            and 1 <= self.intensity <= 5
        )


@dataclass
class AudioTrack:
    key: str
    duration: Optional[float] = None
    format: Optional[str] = None
    size_bytes: Optional[int] = None

    def __post_init__(self):
        if self.format is None and "." in self.key:
            self.format = self.key.split(".")[-1].lower()


@dataclass
class UserIncident:
    user_id: str
    timestamp: datetime
    sentiment: SentimentAnalysis
    speech_text: Optional[str] = None
    added_text: Optional[str] = None
    user_summary: Optional[str] = None
    short_summary: Optional[str] = None

    def to_meditation_data(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "sentiment_label": [self.sentiment.sentiment_label.value],
            "intensity": [str(self.sentiment.intensity)],
            "speech_to_text": [self.speech_text or "NotAvailable"],
            "added_text": [self.added_text or "NotAvailable"],
            "summary": [self.sentiment.summary or ""],
            "user_summary": [self.user_summary or ""],
            "user_short_summary": [self.short_summary or ""],
        }


@dataclass
class MeditationSession:
    user_id: str
    transcript: str
    audio_path: Optional[str] = None
    background_music: Optional[AudioTrack] = None
    duration: Optional[float] = None
    tts_provider: Optional[TTSProvider] = None

    def validate(self) -> bool:
        return bool(self.user_id and self.transcript)


@dataclass
class ProcessingJob:
    job_id: str
    user_id: str
    job_type: str  # 'summary', 'meditation', etc.
    status: str  # 'pending', 'processing', 'completed', 'failed'
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None

    def mark_completed(self, result: Dict[str, Any]):
        self.status = "completed"
        self.completed_at = datetime.now()
        self.result_data = result

    def mark_failed(self, error: str):
        self.status = "failed"
        self.completed_at = datetime.now()
        self.error_message = error
