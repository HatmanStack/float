import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ..config.constants import InferenceType
@dataclass
class BaseRequest:
    """Base class for all API requests."""

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
        """Set inference type to SUMMARY."""
        self.inference_type = InferenceType.SUMMARY

    def validate(self) -> bool:
        """Validate that at least one input (audio or prompt) is provided.

        Returns:
            True if at least one valid input is provided, False otherwise
        """
        audio_available: bool = bool(self.audio and self.audio != "NotAvailable")
        prompt_available: bool = bool(self.prompt and self.prompt != "NotAvailable")
        return audio_available or prompt_available
@dataclass
class MeditationRequest(BaseRequest):
    """Request model for meditation generation.

    Represents a request to generate a personalized meditation from user floats
    and background music selections.
    """

    input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    music_list: List[str]

    def __post_init__(self) -> None:
        """Set inference type to MEDITATION."""
        self.inference_type = InferenceType.MEDITATION

    def validate(self) -> bool:
        """Validate meditation request data.

        Checks that input_data and music_list are valid and non-empty.

        Returns:
            True if all fields are valid, False otherwise
        """
}")
input_data_valid = isinstance(self.input_data, (dict, list)) and bool(self.input_data)
        music_list_valid = isinstance(self.music_list, list)

        result = input_data_valid and music_list_valid
return result
def _parse_json_field(value: Any, field_name: str, default: Any = None) -> Any:
    """
    Parse a field that might be a JSON string.

    Args:
        value: The value to parse
        field_name: Name of field for logging
        default: Default value if parsing fails

    Returns:
        Parsed value or default
    """
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
return default if default is not None else {}
    return value
def _validate_request_fields(body: Dict[str, Any]) -> tuple[str, InferenceType]:
    """
    Validate and extract required request fields.

    Args:
        body: Request body dictionary

    Returns:
        Tuple of (user_id, inference_enum)

    Raises:
        ValueError: If required fields are missing or invalid
    """
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
    """
    Parse request body into appropriate request model.

    Args:
        body: Raw request body dictionary

    Returns:
        Parsed request object

    Raises:
        ValueError: If request type is invalid or required fields are missing
    """
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

        request = MeditationRequest(
            user_id=user_id,
            inference_type=inference_enum,
            input_data=input_data,
            music_list=music_list,
        )
    else:
        raise ValueError(f"Unsupported inference type: {inference_enum.value}")

    if not request.validate():
        raise ValueError(f"Invalid request data for {inference_enum.value}")

    return request
