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
    qa_transcript: List[Dict[str, str]] | None = None

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
        result = {
            "user_id": self.user_id,
            "inference_type": self.inference_type,
            "input_data": self.input_data,
            "music_list": self.music_list,
            "duration_minutes": self.duration_minutes,
        }
        if self.qa_transcript:
            result["qa_transcript"] = self.qa_transcript
        return result


# Discriminated union - Pydantic picks correct model based on inference_type
RequestBody = Annotated[
    Union[SummaryRequestModel, MeditationRequestModel],
    Field(discriminator="inference_type"),
]


def parse_request_body(body: Dict[str, Any]) -> Union[SummaryRequestModel, MeditationRequestModel]:
    """Parse and validate request body using Pydantic discriminated union.

    Args:
        body: Raw request body dictionary.

    Returns:
        SummaryRequestModel or MeditationRequestModel based on inference_type.

    Raises:
        ValidationError: If required fields are missing or invalid.
    """
    from pydantic import TypeAdapter
    from pydantic import ValidationError as PydanticValidationError

    from ..exceptions import ErrorCode, ValidationError

    # Reject non-dict payloads (e.g. list, string, null from json.loads)
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object", ErrorCode.INVALID_REQUEST)

    # Pre-validate required fields for clear error messages
    if not body.get("user_id"):
        raise ValidationError("user_id is required", ErrorCode.MISSING_FIELD)

    inference_type = body.get("inference_type")
    if not inference_type:
        raise ValidationError("inference_type is required", ErrorCode.MISSING_FIELD)

    # Validate inference_type is a known value
    try:
        InferenceType(inference_type)
    except ValueError as err:
        raise ValidationError(
            f"Invalid inference_type: {inference_type}",
            ErrorCode.INVALID_INFERENCE_TYPE,
        ) from err

    try:
        # Pydantic discriminated union handles type routing automatically
        adapter = TypeAdapter(RequestBody)
        return adapter.validate_python(body)
    except PydanticValidationError as e:
        # Convert Pydantic validation errors to domain errors
        first_error = e.errors()[0] if e.errors() else {"msg": "Validation failed"}
        raise ValidationError(
            first_error.get("msg", "Invalid request data"),
            ErrorCode.INVALID_REQUEST,
            details=str(e),
        ) from e
