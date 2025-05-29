from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
import json
from ..config.constants import InferenceType

@dataclass
class BaseRequest:
    """Base class for all API requests."""
    user_id: str
    inference_type: InferenceType

@dataclass 
class SummaryRequest(BaseRequest):
    """Request model for sentiment analysis/summary."""
    audio: Optional[str] = None  # Base64 encoded audio or "NotAvailable"
    prompt: Optional[str] = None  # Text prompt or "NotAvailable"
    
    def __post_init__(self):
        self.inference_type = InferenceType.SUMMARY
    
    def validate(self) -> bool:
        """Validate that at least one input (audio or prompt) is provided."""
        audio_available = self.audio and self.audio != "NotAvailable"
        prompt_available = self.prompt and self.prompt != "NotAvailable"
        return audio_available or prompt_available

@dataclass
class MeditationRequest(BaseRequest):
    """Request model for meditation generation."""
    input_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    music_list: List[str]
    
    def __post_init__(self):
        self.inference_type = InferenceType.MEDITATION
    
    def validate(self) -> bool:
        """Validate meditation request data."""
        print(f"[MEDITATION_VALIDATION] input_data type: {type(self.input_data)}")
        print(f"[MEDITATION_VALIDATION] input_data: {self.input_data}")
        print(f"[MEDITATION_VALIDATION] music_list type: {type(self.music_list)}")
        print(f"[MEDITATION_VALIDATION] music_list: {self.music_list}")
        
        input_data_valid = isinstance(self.input_data, (dict, list)) and bool(self.input_data)
        music_list_valid = isinstance(self.music_list, list)
        
        print(f"[MEDITATION_VALIDATION] input_data_valid: {input_data_valid}")
        print(f"[MEDITATION_VALIDATION] music_list_valid: {music_list_valid}")
        
        result = input_data_valid and music_list_valid
        print(f"[MEDITATION_VALIDATION] validation result: {result}")
        
        return result

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
    inference_type = body.get('inference_type')
    user_id = body.get('user_id')
    
    if not user_id:
        raise ValueError("user_id is required")
    
    if not inference_type:
        raise ValueError("inference_type is required")
    
    try:
        inference_enum = InferenceType(inference_type)
    except ValueError:
        raise ValueError(f"Invalid inference_type: {inference_type}")
    
    if inference_enum == InferenceType.SUMMARY:
        request = SummaryRequest(
            user_id=user_id,
            inference_type=inference_enum,
            audio=body.get('audio'),
            prompt=body.get('prompt')
        )
    elif inference_enum == InferenceType.MEDITATION:
        # Parse input_data if it's a JSON string
        input_data = body.get('input_data', {})
        if isinstance(input_data, str):
            try:
                input_data = json.loads(input_data)
            except json.JSONDecodeError:
                print(f"[PARSE_REQUEST] Failed to parse input_data JSON: {input_data}")
                input_data = {}
        
        # Parse music_list if it's a JSON string
        music_list = body.get('music_list', [])
        if isinstance(music_list, str):
            try:
                music_list = json.loads(music_list)
            except json.JSONDecodeError:
                print(f"[PARSE_REQUEST] Failed to parse music_list JSON: {music_list}")
                music_list = []
        
        request = MeditationRequest(
            user_id=user_id,
            inference_type=inference_enum,
            input_data=input_data,
            music_list=music_list
        )
    else:
        raise ValueError(f"Unsupported inference type: {inference_type}")
    
    if not request.validate():
        raise ValueError(f"Invalid request data for {inference_type}")
    
    return request