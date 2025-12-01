# HLS Streaming for Meditation Audio (Future)

Progressive audio playback using HLS to reduce perceived wait time from 2 minutes to ~20 seconds.

## Current Flow

```
POST /meditation → job_id → poll every 3s → wait 2 min → download 2MB audio
```

## Proposed Flow

```
POST /meditation → job_id
Lambda generates segments → S3:
  /jobs/{job_id}/playlist.m3u8
  /jobs/{job_id}/segment_000.ts  (ready in ~20s)
  /jobs/{job_id}/segment_001.ts
  ...
Client plays playlist.m3u8 → audio starts after first segment
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│ API Gateway │────▶│   Lambda    │
└─────────────┘     └─────────────┘     └──────┬──────┘
      │                                        │
      │                                        ▼
      │                               ┌─────────────┐
      │                               │   FFmpeg    │
      │                               │  (segment)  │
      │                               └──────┬──────┘
      │                                      │
      │         ┌────────────────────────────┘
      │         ▼
      │   ┌─────────────┐
      └──▶│     S3      │
          │  segments/  │
          │  playlist   │
          └─────────────┘
```

## Backend Changes

### FFmpeg Segmented Output

```python
# Current: single file output
ffmpeg -i input.mp3 -i music.mp3 ... output.mp3

# HLS: segmented output
ffmpeg -i input.mp3 -i music.mp3 ... \
  -f hls \
  -hls_time 10 \
  -hls_segment_filename 'segment_%03d.ts' \
  playlist.m3u8
```

### Lambda Flow

1. Generate meditation text (Gemini)
2. Generate voice (OpenAI TTS)
3. Start FFmpeg with HLS output, upload segments to S3 as created
4. Update playlist.m3u8 in S3 after each segment
5. Mark job complete when all segments uploaded

### S3 Structure

```
s3://float-data-bucket/
  jobs/
    {job_id}/
      playlist.m3u8      # HLS manifest
      segment_000.ts     # First 10 seconds
      segment_001.ts     # Next 10 seconds
      ...
```

### Cleanup

- S3 lifecycle rule: delete segments after 24 hours
- Or delete on meditation completion/skip

## Frontend Changes

### Web (HLS.js)

```typescript
import Hls from 'hls.js';

function playHLSAudio(playlistUrl: string) {
  const audio = document.createElement('audio');

  if (Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(playlistUrl);
    hls.attachMedia(audio);
    hls.on(Hls.Events.MANIFEST_PARSED, () => audio.play());
  } else if (audio.canPlayType('application/vnd.apple.mpegurl')) {
    // Safari native HLS
    audio.src = playlistUrl;
    audio.play();
  }

  return audio;
}
```

### React Native

- iOS: `expo-av` supports HLS natively
- Android: Use `react-native-video` for HLS support

## Cost Comparison

| Current | HLS/S3 |
|---------|--------|
| API Gateway: $3.50/million requests | S3 GET: $0.40/million requests |
| Lambda response bandwidth | S3/CloudFront bandwidth |
| Polling overhead | No polling needed |

HLS/S3 is cheaper for audio delivery.

## Implementation Steps

1. [ ] Modify FFmpeg service to output HLS segments
2. [ ] Add segment upload logic (stream to S3 during FFmpeg)
3. [ ] Create playlist.m3u8 generation
4. [ ] Add S3 lifecycle rule for cleanup
5. [ ] Create HLS player component for web
6. [ ] Test on iOS (native HLS via expo-av)
7. [ ] Add react-native-video for Android HLS
8. [ ] Update job status to include playlist URL
9. [ ] Add CloudFront distribution (optional, for caching)

## Open Questions

- Segment duration: 10s vs 5s (shorter = faster start, more requests)
- Keep base64 fallback for offline/download?
- Progress UI during segment generation?
