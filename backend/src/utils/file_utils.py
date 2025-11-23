import os
import random
from datetime import datetime
from typing import Optional


def generate_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def generate_request_id() -> int:
    return random.randint(1, 10000000)


def ensure_directory_exists(directory_path: str) -> bool:
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def is_audio_file(filename: str) -> bool:
    audio_extensions = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
    return get_file_extension(filename) in audio_extensions


def safe_filename(filename: str) -> str:
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, "_")
    safe_name = safe_name.strip(" .")
    if not safe_name:
        safe_name = "untitled"
    return safe_name


def get_temp_file_path(
    prefix: str = "", suffix: str = "", directory: Optional[str] = None
) -> str:
    if directory is None:
        directory = "/tmp"
    timestamp = generate_timestamp()
    filename = f"{prefix}{timestamp}{suffix}"
    return os.path.join(directory, filename)
