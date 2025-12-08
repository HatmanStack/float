# Phase 0: Foundation

This document establishes architecture decisions, patterns, and conventions that apply to all implementation phases. Engineers should read this document before starting any phase.

## Architecture Decision Records (ADRs)

### ADR-001: HLS Segment Duration - 5 Seconds

**Context**: HLS allows configurable segment duration. Shorter segments mean faster time-to-first-audio but more S3 operations and manifest updates.

**Decision**: Use 5-second segments.

**Rationale**:
- Achieves ~4 second time-to-first-audio (segment generation + upload + client fetch)
- For a 3-minute meditation: ~36 segments, ~72 S3 operations (PUT + GET each)
- S3 costs are negligible at this scale (~$0.0004 per meditation)
- User experience improvement outweighs operational overhead

**Consequences**:
- More frequent manifest updates during generation
- Slightly higher S3 request costs (still minimal)
- Better streaming experience on poor connections

---

### ADR-002: Pre-signed S3 URLs (No CloudFront)

**Context**: HLS segments need to be accessible to clients. Options: public bucket, pre-signed URLs, or CloudFront distribution.

**Decision**: Use pre-signed S3 URLs for MVP.

**Rationale**:
- No additional infrastructure to deploy/manage
- Works immediately with existing S3 bucket
- Security: URLs expire, segments are not permanently public
- Can add CloudFront later if performance/cost demands

**Consequences**:
- Pre-signed URLs must be generated for playlist AND each segment reference
- URLs have expiration (use 1 hour for segments, sufficient for meditation completion)
- Slightly higher latency than CloudFront edge delivery

---

### ADR-003: HLS.js Everywhere with WebView on Mobile

**Context**: Need unified player across web, iOS, and Android. Options: platform-specific native players, HLS.js on web + native on mobile, or HLS.js everywhere.

**Decision**: Use HLS.js on web natively, HLS.js in WebView on mobile.

**Rationale**:
- Single player implementation and behavior across platforms
- HLS.js is mature, well-maintained, handles live playlists well
- Simplifies testing and debugging
- Avoids dependency on `react-native-video` and its maintenance burden

**Consequences**:
- Mobile playback requires foreground (WebView limitation)
- No lock screen controls or background audio on mobile
- Can revisit with native players if these become requirements

**Accepted Limitations**:
- Users must keep app in foreground during meditation
- No system media controls integration on mobile

---

### ADR-004: Idempotent Regeneration for Fault Tolerance

**Context**: If Lambda times out or FFmpeg crashes mid-generation, we need recovery strategy. Options: checkpoint each segment, or cache TTS audio and restart FFmpeg.

**Decision**: Cache TTS audio in S3, restart FFmpeg from beginning on retry.

**Rationale**:
- TTS (OpenAI API) is the expensive/slow step (~80% of generation time)
- FFmpeg processing is fast (~5-10 seconds for full meditation)
- Simpler state management than segment-level checkpointing
- Job metadata tracks: `tts_audio_key` (cached), `generation_attempt` (retry count)

**Consequences**:
- On retry, FFmpeg re-generates all segments (fast, since TTS is cached)
- Need to clean up partial segments before retry
- Maximum 3 retry attempts before marking job failed

---

### ADR-005: Server-side MP3 Concatenation

**Context**: Users want downloadable MP3 after streaming. Options: generate MP3 in parallel, concatenate segments server-side, or concatenate client-side.

**Decision**: Concatenate HLS segments to MP3 server-side after streaming completes.

**Rationale**:
- Single FFmpeg pass during generation (HLS only)
- Concatenation is fast (remux, no re-encoding)
- Client doesn't need to handle segment concatenation
- MP3 created only when user requests download

**Consequences**:
- Additional Lambda invocation for MP3 creation
- Small delay (~2-3 seconds) when user clicks download
- Must retain segments until MP3 download or cleanup

---

### ADR-006: Segment Cleanup After MP3 Download

**Context**: When to delete HLS segments from S3. Options: immediate on completion, after download, TTL-based, or on next meditation.

**Decision**: Keep segments until MP3 is downloaded, then cleanup. Fall back to 24h TTL.

**Rationale**:
- Segments needed for: replay (restart stream), MP3 generation
- After MP3 download, segments are redundant
- 24h TTL catches abandoned sessions
- Saves storage costs vs keeping indefinitely

**Consequences**:
- Job tracks: `mp3_downloaded: boolean`
- Cleanup triggered by: download completion OR 24h TTL
- S3 lifecycle rule as safety net

---

## Tech Stack

### Backend
- **Runtime**: Python 3.13 on AWS Lambda
- **FFmpeg**: v6.1 via Lambda layer (existing)
- **Storage**: S3 for segments, playlists, job metadata
- **API**: HTTP API Gateway (existing)

### Frontend
- **Framework**: React Native / Expo
- **HLS Player**: hls.js v1.5+ (web), WebView with hls.js (mobile)
- **HTTP**: Axios (existing)

### New Dependencies

**Frontend** (`package.json`):
```json
{
  "hls.js": "^1.5.0",
  "react-native-webview": "^13.0.0"
}
```

**Backend**: No new dependencies (uses existing boto3, subprocess for FFmpeg)

---

## S3 Structure

### Current Structure
```
s3://float-cust-data/
  {user_id}/
    jobs/{job_id}.json          # Job metadata
    meditation/{timestamp}.json  # Meditation results
    summary/{timestamp}.json     # Summary results
```

### New Structure (HLS additions)
```
s3://float-cust-data/
  {user_id}/
    jobs/{job_id}.json              # Job metadata (extended)
    hls/{job_id}/
      playlist.m3u8                 # HLS manifest
      segment_000.ts                # First 5 seconds
      segment_001.ts                # Next 5 seconds
      ...
      voice.mp3                     # Cached TTS audio (for retry)
    downloads/{job_id}.mp3          # Final downloadable MP3
```

### Job Metadata Extension

Current job structure:
```json
{
  "job_id": "uuid",
  "user_id": "user123",
  "job_type": "meditation",
  "status": "pending|processing|completed|failed",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "expires_at": "ISO8601",
  "result": { "base64": "..." },
  "error": null
}
```

Extended for HLS:
```json
{
  "job_id": "uuid",
  "user_id": "user123",
  "job_type": "meditation",
  "status": "pending|processing|streaming|completed|failed",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "expires_at": "ISO8601",
  "streaming": {
    "enabled": true,
    "playlist_url": "pre-signed URL",
    "segments_completed": 5,
    "segments_total": 36,
    "started_at": "ISO8601"
  },
  "download": {
    "available": false,
    "url": null,
    "downloaded": false
  },
  "tts_cache_key": "hls/{job_id}/voice.mp3",
  "generation_attempt": 1,
  "result": null,
  "error": null
}
```

---

## API Changes

### Existing Endpoints (unchanged)
- `POST /` - Create meditation/summary job
- `GET /job/{job_id}?user_id={userId}` - Poll job status

### New Endpoint
- `POST /job/{job_id}/download?user_id={userId}` - Request MP3 generation and get download URL

### Response Changes

**Job status response** (extended):
```json
{
  "job_id": "uuid",
  "status": "streaming",
  "streaming": {
    "playlist_url": "https://s3.../playlist.m3u8?signature=...",
    "segments_completed": 5,
    "segments_total": null
  },
  "download": {
    "available": false
  }
}
```

**Completed job response**:
```json
{
  "job_id": "uuid",
  "status": "completed",
  "streaming": {
    "playlist_url": "https://s3.../playlist.m3u8?signature=...",
    "segments_completed": 36,
    "segments_total": 36
  },
  "download": {
    "available": true,
    "url": null
  }
}
```

**Download response**:
```json
{
  "job_id": "uuid",
  "download_url": "https://s3.../downloads/{job_id}.mp3?signature=...",
  "expires_in": 3600
}
```

---

## Deployment Script Specifications

The existing deploy script at `backend/scripts/deploy.mjs` handles most requirements. Extensions needed:

### No Changes Required
- Script already prompts for missing config and saves to `.deploy-config.json`
- Script already generates `samconfig.toml` programmatically
- Script already updates frontend `.env` with API URL

### Verification Steps
Before implementing HLS, verify deploy script works:
1. Run `npm run deploy` from project root
2. Confirm it prompts for missing values
3. Confirm it creates `samconfig.toml`
4. Confirm it updates `frontend/.env`
5. Confirm stack deploys successfully

---

## Testing Strategy

### Unit Tests
- **Backend**: pytest with mocked boto3, subprocess
- **Frontend**: Jest with mocked fetch, WebView

### Integration Tests (Mocked)
- **Backend**: LocalStack or moto for S3 operations
- **Frontend**: MSW (Mock Service Worker) for API responses

### CI Pipeline
- Linting (ruff for Python, ESLint for JS)
- Unit tests (pytest, Jest)
- Mocked integration tests
- **No live AWS deployment in CI**

### Testing HLS Specifically

**Backend unit tests**:
- FFmpeg command generation (verify HLS flags)
- Segment upload sequencing
- Playlist generation and updates
- Pre-signed URL generation
- MP3 concatenation logic

**Frontend unit tests**:
- HLS.js initialization
- Playlist URL handling
- Playback state management
- Error state handling
- Download button behavior

**Integration tests**:
- Mock S3 responses for playlist/segments
- Mock HLS.js events
- Full job polling → streaming → download flow

### Mocking Patterns

**Backend S3 mocking** (pytest):
```python
@pytest.fixture
def mock_s3(mocker):
    mock_client = mocker.MagicMock()
    mocker.patch('boto3.client', return_value=mock_client)
    return mock_client
```

**Frontend fetch mocking** (Jest):
```typescript
jest.mock('global', () => ({
  fetch: jest.fn()
}));
```

---

## Conventions

### Commit Message Format
```
type(scope): brief description

Detail 1
Detail 2
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Scopes: `backend`, `frontend`, `deploy`, `hls`

### File Naming
- Python: `snake_case.py`
- TypeScript: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Tests: `test_*.py` (Python), `*-test.tsx` (TypeScript)

### Code Style
- Python: ruff formatting, type hints
- TypeScript: Prettier, strict TypeScript

### Branch Strategy
- Work on feature branch
- PR to main with squash merge
- Run `npm run check` before committing

---

## Error Handling

### Backend Errors
- FFmpeg failure: Log error, increment `generation_attempt`, retry up to 3 times
- S3 upload failure: Retry with exponential backoff (boto3 handles this)
- Lambda timeout: Next poll triggers retry via idempotent regeneration

### Frontend Errors
- HLS.js fatal error: Show error message, offer retry button
- Network error during streaming: HLS.js handles retry automatically
- Download failure: Show error, allow retry

### Error Response Format
```json
{
  "error": {
    "code": "GENERATION_FAILED",
    "message": "Audio generation failed after 3 attempts",
    "retriable": false
  }
}
```

---

## Security Considerations

### Pre-signed URLs
- Segment URLs expire in 1 hour
- Download URLs expire in 1 hour
- URLs are user-specific (job owned by user)

### Input Validation
- Job ID must be valid UUID
- User ID must match authenticated user
- No path traversal in S3 keys

### Rate Limiting
- Existing API Gateway throttling applies
- No additional rate limiting needed for HLS

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Time to first audio | < 5 seconds | ~120 seconds |
| Segment upload latency | < 1 second | N/A |
| MP3 generation time | < 5 seconds | N/A |
| Playlist update frequency | Every 5 seconds | N/A |

---

## Rollback Strategy

If HLS causes issues in production:

1. **Feature flag**: Add `ENABLE_HLS_STREAMING` environment variable
2. **Fallback**: If disabled, use existing base64 response
3. **Client detection**: Frontend checks job response for `streaming` field
4. **No streaming field**: Falls back to existing base64 playback

This allows gradual rollout and instant rollback without code changes.
