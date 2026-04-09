from abc import ABC, abstractmethod
from typing import Iterator


class TTSService(ABC):
    @abstractmethod
    def synthesize_speech(self, text: str, output_path: str) -> bool: ...

    @abstractmethod
    def stream_speech(self, text: str) -> Iterator[bytes]: ...

    @abstractmethod
    def get_provider_name(self) -> str: ...

    def get_stream_format(self) -> list[str]:
        """Return FFmpeg input format flags for the audio produced by stream_speech.

        Subclasses override this to declare their output encoding so that
        downstream consumers (e.g. the HLS stream encoder) can configure
        FFmpeg's input demuxer correctly.

        Returns a list of FFmpeg CLI args (e.g. ["-f", "mp3"]).
        """
        return ["-f", "mp3"]
