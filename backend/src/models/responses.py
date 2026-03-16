import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, ValidationError

from ..config.constants import InferenceType


@dataclass
class BaseResponse:
    request_id: int
    user_id: str
    inference_type: InferenceType

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["inference_type"] = self.inference_type.value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class SummaryResponse(BaseModel):
    """Pydantic model for summary responses — validates AI output fields."""

    model_config = ConfigDict(use_enum_values=True)

    request_id: int
    user_id: str
    inference_type: InferenceType = InferenceType.SUMMARY
    sentiment_label: str
    intensity: int
    speech_to_text: str = "NotAvailable"
    added_text: str = "NotAvailable"
    summary: str
    user_summary: str
    user_short_summary: str

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        # Ensure enum values are serialized as strings
        if isinstance(data.get("inference_type"), InferenceType):
            data["inference_type"] = data["inference_type"].value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class MeditationResponse(BaseResponse):
    music_list: List[str]
    base64: str  # Base64 encoded combined audio

    def __post_init__(self):
        self.inference_type = InferenceType.MEDITATION


@dataclass
class ErrorResponse:
    error: str
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def create_summary_response(request_id: int, user_id: str, summary_result: str) -> SummaryResponse:
    try:
        json_start = summary_result.find("{")
        json_end = summary_result.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in summary result")
        json_str = summary_result[json_start:json_end]
        data = json.loads(json_str)
        # Inject request metadata, then let Pydantic validate the AI fields.
        # Missing required fields (sentiment_label, intensity, summary,
        # user_summary, user_short_summary) will raise ValidationError.
        data["request_id"] = request_id
        data["user_id"] = user_id
        return SummaryResponse.model_validate(data)
    except (json.JSONDecodeError, KeyError, IndexError, ValidationError) as e:
        raise ValueError(f"Failed to parse summary result: {e}") from e


def create_meditation_response(
    request_id: int, user_id: str, music_list: List[str], base64_audio: str
) -> MeditationResponse:
    return MeditationResponse(
        request_id=request_id,
        user_id=user_id,
        inference_type=InferenceType.MEDITATION,
        music_list=music_list,
        base64=base64_audio,
    )
