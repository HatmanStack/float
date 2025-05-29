import os
import random
from datetime import datetime
from typing import Optional

def generate_timestamp() -> str:
    """Generate timestamp string for file naming."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def generate_request_id() -> int:
    """Generate random request ID."""
    return random.randint(1, 10000000)

def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        True if directory exists or was created, False on error
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Name of file
        
    Returns:
        File extension including dot (e.g., '.mp3')
    """
    return os.path.splitext(filename)[1].lower()

def is_audio_file(filename: str) -> bool:
    """
    Check if filename has audio file extension.
    
    Args:
        filename: Name of file
        
    Returns:
        True if file appears to be audio format
    """
    audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
    return get_file_extension(filename) in audio_extensions

def safe_filename(filename: str) -> str:
    """
    Create safe filename by removing/replacing unsafe characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename for filesystem use
    """
    # Replace unsafe characters with underscores
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    # Ensure filename is not empty
    if not safe_name:
        safe_name = 'untitled'
    
    return safe_name

def get_temp_file_path(prefix: str = '', suffix: str = '', directory: Optional[str] = None) -> str:
    """
    Generate temporary file path.
    
    Args:
        prefix: Prefix for filename
        suffix: Suffix/extension for filename
        directory: Directory for temp file (defaults to /tmp)
        
    Returns:
        Full path to temporary file
    """
    if directory is None:
        directory = '/tmp'
    
    timestamp = generate_timestamp()
    filename = f"{prefix}{timestamp}{suffix}"
    return os.path.join(directory, filename)