import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from ..config.constants import InferenceType


@dataclass
class BaseResponse:
    """Base class for all API responses."""

    request_id: int
    user_id: str
    inference_type: InferenceType

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        data = asdict(self)
        # Convert enum to string for JSON serialization
        data["inference_type"] = self.inference_type.value
        return data

    def to_json(self) -> str:
        """Convert response to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class SummaryResponse(BaseResponse):
    """Response model for sentiment analysis/summary."""

    sentiment_label: str
    intensity: str
    speech_to_text: str
    added_text: str
    summary: str
    user_summary: str
    user_short_summary: str

    def __post_init__(self):
        self.inference_type = InferenceType.SUMMARY


@dataclass
class MeditationResponse(BaseResponse):
    """Response model for meditation generation."""

    music_list: List[str]
    base64: str  # Base64 encoded combined audio

    def __post_init__(self):
        self.inference_type = InferenceType.MEDITATION


@dataclass
class ErrorResponse:
    """Response model for errors."""

    error: str
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert error response to JSON string."""
        return json.dumps(self.to_dict())


def create_summary_response(request_id: int, user_id: str, summary_result: str) -> SummaryResponse:
    """
    Create summary response from AI service result.

    Args:
        request_id: Request identifier
        user_id: User identifier
        summary_result: JSON string from AI service

    Returns:
        SummaryResponse object

    Raises:
        ValueError: If summary_result cannot be parsed
    """
    try:
        # Extract JSON from the result string
        json_start = summary_result.find("{")
        json_end = summary_result.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in summary result")

        json_str = summary_result[json_start:json_end]
        data = json.loads(json_str)

        return SummaryResponse(
            request_id=request_id,
            user_id=user_id,
            inference_type=InferenceType.SUMMARY,
            sentiment_label=data.get("sentiment_label", ""),
            intensity=data.get("intensity", ""),
            speech_to_text=data.get("speech_to_text", "NotAvailable"),
            added_text=data.get("added_text", "NotAvailable"),
            summary=data.get("summary", ""),
            user_summary=data.get("user_summary", ""),
            user_short_summary=data.get("user_short_summary", ""),
        )

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise ValueError(f"Failed to parse summary result: {e}")


def create_meditation_response(
    request_id: int, user_id: str, music_list: List[str], base64_audio: str
) -> MeditationResponse:
    """
    Create meditation response.

    Args:
        request_id: Request identifier
        user_id: User identifier
        music_list: Updated list of used music tracks
        base64_audio: Base64 encoded combined audio

    Returns:
        MeditationResponse object
    """
    return MeditationResponse(
        request_id=request_id,
        user_id=user_id,
        inference_type=InferenceType.MEDITATION,
        music_list=music_list,
        base64=base64_audio,
    )
