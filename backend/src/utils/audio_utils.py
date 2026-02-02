import base64
import os
import tempfile
from typing import Optional


def decode_audio_base64(audio_base64: str, suffix: str = ".mp3") -> str:
    """Decode a base64-encoded audio string and save to a temporary file.

    Args:
        audio_base64: Base64-encoded audio data as a string.
        suffix: File extension for the temporary file (default: ".mp3").

    Returns:
        str: Path to the created temporary file containing the decoded audio.

    Note:
        The caller is responsible for cleaning up the temporary file using cleanup_temp_file().
    """
    audio_bytes = base64.b64decode(audio_base64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(audio_bytes)
        return temp_file.name


def cleanup_temp_file(file_path: str) -> bool:
    """Remove a temporary file from the filesystem.

    Args:
        file_path: Path to the file to be removed.

    Returns:
        bool: True if the file was removed or doesn't exist, False if removal failed.

    Note:
        Errors during removal are logged to stdout but don't raise exceptions.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return True
    except Exception as e:
        print(f"Error removing temporary file {file_path}: {e}")
        return False


def encode_audio_to_base64_streaming(
    file_path: str, chunk_size: int = 3 * 1024 * 1024
) -> Optional[str]:
    """Encode an audio file to base64 in chunks to reduce peak memory usage.

    For a 24MB file, this uses ~6MB peak memory instead of ~48MB
    (file content + base64 string when loaded all at once).

    Args:
        file_path: Path to the audio file to encode.
        chunk_size: Size of chunks to read. Must be divisible by 3 for correct
                   base64 concatenation. Default: 3MB.

    Returns:
        Optional[str]: Base64-encoded string representation of the audio file,
                      or None if encoding fails.

    Note:
        Base64 encoding expands data by ~33%, so a 3MB chunk becomes ~4MB encoded.
        Using 3MB chunks keeps peak memory around 6MB for arbitrarily large files.
    """
    try:
        chunks: list[str] = []
        with open(file_path, "rb") as audio_file:
            while True:
                chunk = audio_file.read(chunk_size)
                if not chunk:
                    break
                chunks.append(base64.b64encode(chunk).decode("utf-8"))
        return "".join(chunks)
    except Exception as e:
        print(f"Error encoding audio file {file_path}: {e}")
        return None


def encode_audio_to_base64(file_path: str) -> Optional[str]:
    """Encode an audio file to a base64 string.

    This function uses streaming encoding internally to reduce memory pressure
    for large files (20-minute meditations can be ~24MB).

    Args:
        file_path: Path to the audio file to encode.

    Returns:
        Optional[str]: Base64-encoded string representation of the audio file,
                      or None if encoding fails.

    Note:
        Errors during encoding are logged to stdout but don't raise exceptions.
    """
    return encode_audio_to_base64_streaming(file_path)


def validate_audio_file(file_path: str) -> bool:
    """Validate that an audio file exists and is not empty.

    Args:
        file_path: Path to the audio file to validate.

    Returns:
        bool: True if the file exists and has non-zero size, False otherwise.

    Note:
        Any exceptions during validation (e.g., permission errors) return False.
    """
    try:
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except Exception:
        return False
