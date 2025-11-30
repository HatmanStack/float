import base64
import os
import tempfile
from typing import Optional
def decode_audio_base64(audio_base64: str, suffix: str = ".mp3") -> str:
    """
    Decode base64 audio data and save to temporary file.

    Args:
        audio_base64: Base64 encoded audio data
        suffix: File extension for temporary file

    Returns:
        Path to temporary audio file
    """
    audio_bytes = base64.b64decode(audio_base64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(audio_bytes)
        return temp_file.name
def cleanup_temp_file(file_path: str) -> bool:
    """
    Remove temporary file if it exists.

    Args:
        file_path: Path to file to remove

    Returns:
        True if file was removed or didn't exist, False on error
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return True
    except Exception as e:
return False
def encode_audio_to_base64(file_path: str) -> Optional[str]:
    """
    Encode audio file to base64 string.

    Args:
        file_path: Path to audio file

    Returns:
        Base64 encoded string or None on error
    """
    try:
        with open(file_path, "rb") as audio_file:
            encoded_string = base64.b64encode(audio_file.read()).decode("utf-8")
            return encoded_string
    except Exception as e:
return None
def validate_audio_file(file_path: str) -> bool:
    """
    Validate that audio file exists and is accessible.

    Args:
        file_path: Path to audio file

    Returns:
        True if file is valid, False otherwise
    """
    try:
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except Exception:
        return False
