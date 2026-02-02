"""Request models with Pydantic validation and discriminated unions.

This module provides type-safe request parsing using Pydantic's discriminated
union pattern. The inference_type field determines which model is used for
validation, enabling proper type narrowing in handlers.
"""

from typing import Annotated, Any, Dict, List, Literal, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from ..config.constants import InferenceType


class SummaryRequestModel(BaseModel):
    """Request model for sentiment analysis/summary.

    At least one of audio or prompt must be provided and not be "NotAvailable".
    """

    inference_type: Literal["summary"]
    user_id: str = Field(min_length=1, max_length=256)
    audio: str | None = None  # Base64 encoded audio or "NotAvailable"
    prompt: str | None = None  # Text prompt or "NotAvailable"

    @model_validator(mode="after")
    def validate_input_present(self) -> "SummaryRequestModel":
        """Ensure at least one valid input is provided."""
        audio_available = self.audio and self.audio != "NotAvailable"
        prompt_available = self.prompt and self.prompt != "NotAvailable"
        if not audio_available and not prompt_available:
            raise ValueError("At least one of audio or prompt must be provided")
        return self

    def to_inference_type(self) -> InferenceType:
        """Return the InferenceType enum value."""
        return InferenceType.SUMMARY


class MeditationRequestModel(BaseModel):
    """Request model for meditation generation."""

    inference_type: Literal["meditation"]
    user_id: str = Field(min_length=1, max_length=256)
    input_data: Dict[str, Any] | List[Dict[str, Any]]
    music_list: List[str] = Field(default_factory=list)
    duration_minutes: Literal[3, 5, 10, 15, 20] = 5

    @field_validator("input_data", mode="before")
    @classmethod
    def parse_input_data(cls, v: Any) -> Dict[str, Any] | List[Dict[str, Any]]:
        """Parse input_data from string if necessary."""
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @field_validator("music_list", mode="before")
    @classmethod
    def parse_music_list(cls, v: Any) -> List[str]:
        """Parse music_list from string if necessary."""
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @model_validator(mode="after")
    def validate_input_data(self) -> "MeditationRequestModel":
        """Ensure input_data is not empty."""
        if not self.input_data:
            raise ValueError("input_data cannot be empty")
        return self

    def to_inference_type(self) -> InferenceType:
        """Return the InferenceType enum value."""
        return InferenceType.MEDITATION

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "inference_type": self.inference_type,
            "input_data": self.input_data,
            "music_list": self.music_list,
            "duration_minutes": self.duration_minutes,
        }


# Discriminated union - Pydantic picks correct model based on inference_type
RequestBody = Annotated[
    Union[SummaryRequestModel, MeditationRequestModel],
    Field(discriminator="inference_type"),
]


# =============================================================================
# Legacy compatibility layer
# =============================================================================
# The following classes and functions maintain backward compatibility with
# existing code that uses the dataclass-based interface.


class BaseRequest:
    """Legacy base request class for backward compatibility."""

    user_id: str
    inference_type: InferenceType


class SummaryRequest(BaseRequest):
    """Legacy summary request wrapper.

    Wraps SummaryRequestModel to maintain existing interface.
    """

    def __init__(
        self,
        user_id: str,
        inference_type: InferenceType,
        audio: str | None = None,
        prompt: str | None = None,
    ):
        self.user_id = user_id
        self.inference_type = inference_type
        self.audio = audio
        self.prompt = prompt

    def validate(self) -> bool:
        """Validate that at least one input is available."""
        audio_available = bool(self.audio and self.audio != "NotAvailable")
        prompt_available = bool(self.prompt and self.prompt != "NotAvailable")
        return audio_available or prompt_available


class MeditationRequest(BaseRequest):
    """Legacy meditation request wrapper.

    Wraps MeditationRequestModel to maintain existing interface.
    """

    def __init__(
        self,
        user_id: str,
        inference_type: InferenceType,
        input_data: Dict[str, Any] | List[Dict[str, Any]],
        music_list: List[str],
        duration_minutes: int = 5,
    ):
        self.user_id = user_id
        self.inference_type = inference_type
        self.input_data = input_data
        self.music_list = music_list
        # Validate duration
        allowed_durations = [3, 5, 10, 15, 20]
        self.duration_minutes = duration_minutes if duration_minutes in allowed_durations else 5

    def validate(self) -> bool:
        """Validate input data and music list."""
        input_data_valid = isinstance(self.input_data, (dict, list)) and bool(self.input_data)
        music_list_valid = isinstance(self.music_list, list)
        return input_data_valid and music_list_valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "inference_type": self.inference_type.value,
            "input_data": self.input_data,
            "music_list": self.music_list,
            "duration_minutes": self.duration_minutes,
        }


def _parse_json_field(value: Any, field_name: str, default: Any = None) -> Any:
    """Parse a JSON string field, returning default on failure."""
    if isinstance(value, str):
        import json

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default if default is not None else {}
    return value


def _validate_request_fields(body: Dict[str, Any]) -> tuple[str, InferenceType]:
    """Validate required fields and return parsed values."""
    from ..exceptions import ErrorCode, ValidationError

    user_id = body.get("user_id")
    if not user_id:
        raise ValidationError("user_id is required", ErrorCode.MISSING_FIELD)

    inference_type = body.get("inference_type")
    if not inference_type:
        raise ValidationError("inference_type is required", ErrorCode.MISSING_FIELD)

    try:
        inference_enum = InferenceType(inference_type)
    except ValueError:
        raise ValidationError(
            f"Invalid inference_type: {inference_type}",
            ErrorCode.INVALID_INFERENCE_TYPE,
        )

    return user_id, inference_enum


def parse_request_body(body: Dict[str, Any]) -> BaseRequest:
    """Parse and validate request body.

    This function maintains backward compatibility with existing handlers
    while using Pydantic validation internally where possible.

    Args:
        body: Raw request body dictionary.

    Returns:
        SummaryRequest or MeditationRequest based on inference_type.

    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    from ..exceptions import ErrorCode, ValidationError

    user_id, inference_enum = _validate_request_fields(body)

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
        if isinstance(duration_minutes, str):
            try:
                duration_minutes = int(duration_minutes)
            except ValueError:
                duration_minutes = 5

        request = MeditationRequest(
            user_id=user_id,
            inference_type=inference_enum,
            input_data=input_data,
            music_list=music_list,
            duration_minutes=duration_minutes,
        )
    else:
        raise ValidationError(
            f"Unsupported inference type: {inference_enum.value}",
            ErrorCode.INVALID_INFERENCE_TYPE,
        )

    if not request.validate():
        raise ValidationError(
            f"Invalid request data for {inference_enum.value}",
            ErrorCode.INVALID_REQUEST,
        )

    return request
