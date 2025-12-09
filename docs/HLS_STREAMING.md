# HLS Streaming for Meditation Audio

Progressive audio playback using HLS to reduce perceived wait time from ~2 minutes to ~4 seconds.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│ API Gateway │────▶│   Lambda    │
└─────────────┘     └─────────────┘     └──────┬──────┘
      │                                        │
      │                                        ▼
      │                               ┌─────────────┐
      │                               │   FFmpeg    │
      │                               │  (HLS out)  │
      │                               └──────┬──────┘
      │                                      │
      │         ┌────────────────────────────┘
      │         ▼
      │   ┌─────────────┐
      └──▶│     S3      │
          │  hls/       │
          │  downloads/ │
          └─────────────┘
```

## Flow

1. **Client** sends `POST /meditation` with `streaming: true`
2. **Lambda** returns `job_id` immediately, invokes async processing
3. **Async Lambda** generates TTS, creates HLS segments via FFmpeg
4. **Segments** uploaded to S3 progressively with live playlist updates
5. **Client** polls `/job/{job_id}`, receives `playlist_url` when first segment ready
6. **Client** plays HLS stream (starts in ~4 seconds, full audio ~2 minutes)
7. **Download** available after completion via `/job/{job_id}/download`

## S3 Key Structure

```
s3://float-cust-data/
  hls/{user_id}/{job_id}/
    playlist.m3u8      # HLS manifest (live, then finalized)
    segment_000.ts     # First 5 seconds
    segment_001.ts     # Next 5 seconds
    ...
    voice.mp3          # Cached TTS for retry
  downloads/{user_id}/{job_id}.mp3   # Full MP3 for offline
  jobs/{user_id}/{job_id}.json       # Job metadata
```

## Backend Components

- **HLSService** (`hls_service.py`): Segment upload, playlist generation, pre-signed URLs
- **DownloadService** (`download_service.py`): MP3 concatenation from segments
- **FFmpegAudioService** (`ffmpeg_audio_service.py`): `combine_voice_and_music_hls()` for HLS output
- **JobService** (`job_service.py`): Streaming status tracking

## Frontend Components

- **HLSPlayer** (`HLSPlayer.tsx`): WebView-based player for mobile
- **useHLSPlayer** (`useHLSPlayer.web.ts`): HLS.js hook for web browsers
- **MeditationControls**: Integrates streaming playback with download button

## Configuration

- Segment duration: 5 seconds
- Pre-signed URL expiry: 1 hour
- S3 lifecycle: 7 days for HLS/downloads, 30 days for job metadata
- Retry attempts: 3 (with TTS caching)
- FFmpeg timeout: 2 minutes per step, 5 minutes for HLS generation

## Download Flow

After streaming completes:
1. User taps download button
2. `POST /job/{job_id}/download` triggers MP3 generation
3. Backend concatenates segments to single MP3, uploads to S3
4. Returns pre-signed download URL (1 hour expiry)
