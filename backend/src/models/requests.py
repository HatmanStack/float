import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ..config.constants import InferenceType


@dataclass
class BaseRequest:
    user_id: str
    inference_type: InferenceType


@dataclass
class SummaryRequest(BaseRequest):
    """Request model for sentiment analysis/summary.
    Represents a request to analyze sentiment from audio and/or text input.
    At least one of audio or prompt must be provided and not be "NotAvailable".
    """

    audio: Optional[str] = None  # Base64 encoded audio or "NotAvailable"
    prompt: Optional[str] = None  # Text prompt or "NotAvailable"

    def __post_init__(self) -> None:
        self.inference_type = InferenceType.SUMMARY

    def validate(self) -> bool:
        audio_available: bool = bool(self.audio and self.audio != "NotAvailable")
        prompt_available: bool = bool(self.prompt and self.prompt != "NotAvailable")
        return audio_available or prompt_available


@dataclass
class MeditationRequest(BaseRequest):
    input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    music_list: List[str]
    duration_minutes: int = 5  # Target meditation duration: 3, 5, 10, 15, or 20 minutes

    def __post_init__(self) -> None:
        self.inference_type = InferenceType.MEDITATION
        # Validate duration is one of the allowed values
        allowed_durations = [3, 5, 10, 15, 20]
        if self.duration_minutes not in allowed_durations:
            self.duration_minutes = 5  # Default to 5 if invalid

    def validate(self) -> bool:
        print(f"[MEDITATION_VALIDATION] input_data type: {type(self.input_data)}")
        print(f"[MEDITATION_VALIDATION] input_data: {self.input_data}")
        print(f"[MEDITATION_VALIDATION] music_list type: {type(self.music_list)}")
        print(f"[MEDITATION_VALIDATION] music_list: {self.music_list}")
        input_data_valid = isinstance(self.input_data, (dict, list)) and bool(
            self.input_data
        )
        music_list_valid = isinstance(self.music_list, list)
        print(f"[MEDITATION_VALIDATION] input_data_valid: {input_data_valid}")
        print(f"[MEDITATION_VALIDATION] music_list_valid: {music_list_valid}")
        result = input_data_valid and music_list_valid
        print(f"[MEDITATION_VALIDATION] validation result: {result}")
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "inference_type": self.inference_type.value,
            "input_data": self.input_data,
            "music_list": self.music_list,
            "duration_minutes": self.duration_minutes,
        }


def _parse_json_field(value: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            print(f"[PARSE_REQUEST] Failed to parse {field_name} JSON: {value}")
            return default if default is not None else {}
    return value


def _validate_request_fields(body: Dict[str, Any]) -> tuple[str, InferenceType]:
    user_id = body.get("user_id")
    if not user_id:
        raise ValueError("user_id is required")
    inference_type = body.get("inference_type")
    if not inference_type:
        raise ValueError("inference_type is required")
    try:
        inference_enum = InferenceType(inference_type)
    except ValueError:
        raise ValueError(f"Invalid inference_type: {inference_type}")
    return user_id, inference_enum


def parse_request_body(body: Dict[str, Any]) -> BaseRequest:
    user_id, inference_enum = _validate_request_fields(body)
    request: BaseRequest
    if inference_enum == InferenceType.SUMMARY:
        request = SummaryRequest(
            user_id=user_id,
            inference_type=inference_enum,
            audio=body.get("audio"),
            prompt=body.get("prompt"),
        )
    elif inference_enum == InferenceType.MEDITATION:
        input_data = _parse_json_field(body.get("input_data", {}), "input_data")
        music_list = _parse_json_field(body.get("music_list", []), "music_list", [])
        duration_minutes = body.get("duration_minutes", 5)
        print(f"[MEDITATION_REQUEST] Raw duration_minutes from body: {body.get('duration_minutes')} -> parsed: {duration_minutes}")
        if isinstance(duration_minutes, str):
            try:
                duration_minutes = int(duration_minutes)
            except ValueError:
                duration_minutes = 5
        print(f"[MEDITATION_REQUEST] Final duration_minutes: {duration_minutes}")
        request = MeditationRequest(
            user_id=user_id,
            inference_type=inference_enum,
            input_data=input_data,
            music_list=music_list,
            duration_minutes=duration_minutes,
        )
    else:
        raise ValueError(f"Unsupported inference type: {inference_enum.value}")
    if not request.validate():
        raise ValueError(f"Invalid request data for {inference_enum.value}")
    return request
