"""Focused collaborators extracted from :mod:`ffmpeg_audio_service`.

Phase 4 Task 2 of the 2026-04-08-audit-float plan split the 800+ line
``FFmpegAudioService`` into single-responsibility modules. The service
in :mod:`ffmpeg_audio_service` is now a thin facade delegating into these
collaborators.
"""
