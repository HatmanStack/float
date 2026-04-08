"""Placeholder for the cached-TTS batch HLS encoder.

Phase 4 Task 2 introduced this module as the future home of
``combine_voice_and_music_hls`` (the cached-TTS / non-streaming path).
Moving the body requires retargeting ``src.services.ffmpeg_audio_service``
patch points in the unit test suite; that follow-up work is tracked so
the initial split could land without a mass test rewrite.

The real logic currently lives on :class:`FFmpegAudioService` in
:mod:`ffmpeg_audio_service`. This module is intentionally empty and
serves only to document the module boundary so follow-up work has a
clear landing pad.
"""
