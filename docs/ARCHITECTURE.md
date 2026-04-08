# Float Architecture

Float is a serverless meditation app with clear separation between frontend and backend.

## System Overview

```
┌─────────────────────────┐
│ Frontend (Expo)         │
│ iOS/Android/Web         │
└────────────┬────────────┘
             │ HTTP
┌────────────▼────────────┐
│ AWS Lambda              │
│ - Handler               │
│ - Services (AI, TTS)    │
│ - Storage               │
└────────────┬────────────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼──┐ ┌──▼──┐ ┌───▼──┐
│Google│ │OpenAI│ │AWS S3│
│Gemini│ │ TTS  │ └──────┘
└──────┘ └──────┘
```

## Frontend (React Native/Expo)

- **Location**: `frontend/`
- **Routing**: Expo Router (file-based)
- **State**: React Context API
- **Testing**: Jest

**Key Components**:

- Audio recording and float submission
- Float list and meditation controls
- Authentication context

**Data Flow**:

1. User submits float → Sent to Lambda
2. Lambda analyzes sentiment → Returns analysis
3. User selects floats → Generate meditation endpoint
4. Meditation + audio downloaded and played

## Backend (AWS Lambda)

- **Location**: `backend/`
- **Entry**: `lambda_function.py`
- **Language**: Python 3.13

**Layers**:

- **Middleware**: CORS, validation, error handling
- **Handler**: Routes requests to services
- **Services**:
  - AI: Google Gemini for sentiment & meditation generation
  - TTS: OpenAI for speech synthesis
  - Audio: FFmpeg processing (via Lambda layer)
  - Storage: AWS S3 upload/download
  - Jobs: Async job tracking for long-running tasks
- **Config** (`src/config/`): Application settings (`settings.py` via Pydantic BaseSettings) and constants (`constants.py`)
- **Models** (`src/models/`): Pydantic request/response validation models
- **Utils** (`src/utils/`): Circuit breaker, caching, structured logging, audio utilities
- **Exceptions** (`src/exceptions.py`): Custom exception hierarchy (FloatException, ValidationError, ExternalServiceError, TTSError)

**Endpoints**:

- `POST /` - Summary inference (emotion analysis)
- `POST /` - Meditation generation (async, returns job_id)
- `GET /job/{job_id}` - Poll job status
- `POST /job/{job_id}/download` - Download completed meditation audio

**Async Meditation Flow**:

1. Client submits meditation request
2. Lambda creates job in S3, invokes itself asynchronously
3. Returns job_id immediately (~1 second)
4. Async Lambda processes meditation (1-2 minutes)
5. Client polls `/job/{job_id}` until `status: completed`
6. Result includes base64 audio

## Database & Storage

- **S3**: User meditations and audio files
- **Local Context**: Float history in app

## Technology Stack

| Layer    | Technology                             |
| -------- | -------------------------------------- |
| Frontend | React Native 0.84, Expo 55, React 19, TypeScript |
| Backend  | Python 3.13, AWS Lambda, Pydantic      |
| AI       | Google Gemini                          |
| TTS      | OpenAI                                 |
| Storage  | AWS S3                                 |

## Meditation Generation Flow

Meditation generation is the long-running pipeline in the backend and is
implemented as a self-invoking Lambda plus an HLS streaming writer.
This section is the canonical description; API.md only documents the
wire contract.

### Async self-invocation

```text
Client                  Lambda (sync)                 Lambda (async)              S3
  |  POST / (meditation)      |                              |                    |
  |-------------------------->|                              |                    |
  |                           | create_job(user_id, job_id)  |                    |
  |                           |----------------------------->|-------------------->|
  |                           | lambda_client.invoke(        |                    |
  |                           |   InvocationType="Event")    |                    |
  |                           |----------------------------->|                    |
  | 200 {job_id, streaming:{  |                              |                    |
  |   enabled:true,           |                              |                    |
  |   playlist_url:null}}     |                              |                    |
  |<--------------------------|                              |                    |
  |                           |                              | Gemini prompt ->   |
  |                           |                              | TTS (OpenAI or     |
  |                           |                              |   Gemini fallback) |
  |                           |                              | FFmpeg mix + HLS   |
  |                           |                              |------------------->|
  |  GET /job/{job_id}        |                              |                    |
  |-------------------------->|                              |                    |
  | 200 {status,              |                              |                    |
  |   streaming.playlist_url, |                              |                    |
  |   download.available}     |                              |                    |
  |<--------------------------|                              |                    |
```

The sync Lambda returns within ~1 second; the async Lambda processes
the job for 1-2 minutes. The client polls `GET /job/{job_id}` and can
start playback as soon as `streaming.playlist_url` is non-null.

### HLS streaming pipeline

Streaming is the default path (`ENABLE_HLS_STREAMING=true`). The
writer lives in `backend/src/services/audio/hls_stream_encoder.py` and
is invoked via `process_stream_to_hls`:

1. A `_StreamState` dataclass carries a `threading.Lock` and a
   `threading.Event` (`done`) that coordinate the TTS producer and the
   segment-upload watcher thread.
2. The watcher thread drains completed FFmpeg segments from a shared
   temp directory and uploads each to S3 under
   `user/<user_id>/job/<job_id>/segment-NNN.ts`, updating the HLS
   playlist after each upload.
3. On the last segment, fade-out segments are appended via
   `hls_batch_encoder.append_fade_segments` to avoid an abrupt cut
   (total fade length = `HLS_FADE_DURATION_SECONDS = 10` seconds).
4. A BrokenPipe on the TTS stream triggers a clean generator
   `.close()` and raises `AudioProcessingError`; partial uploads stay
   in place because the next retry uses the same deterministic keys.
5. TTS results are cached under `tts_cache/<hash>` so a retry of the
   same script reuses prior audio without re-invoking the provider.

Key constants (in `backend/src/config/constants.py` and
`backend/src/services/hls_service.py`):

| Constant | Value | Meaning |
|---|---|---|
| `MAX_GENERATION_ATTEMPTS` | `3` | Hard cap on meditation retries per job_id |
| `SEGMENT_DURATION` | `5` (seconds) | HLS target segment length |
| `HLS_FADE_DURATION_SECONDS` | `10` | Fade-out tail appended to the final playlist |
| `TTS_WORDS_PER_MINUTE` | `80` | Used to estimate script length vs target duration |
| `TOKEN_MARKER_TTL_SECONDS` | `60` | Lifetime of the opaque `/token` marker |

### Retry semantics

`MAX_GENERATION_ATTEMPTS = 3` governs meditation retries. The retry
loop lives in the async meditation handler
(`backend/src/handlers/meditation_pipeline.py`):

- Each attempt increments `generation_attempt` via
  `JobService.increment_generation_attempt` *before* self-invoking the
  next async Lambda.
- If incrementing the counter raises, the loop does **not** self-fire
  (this is the Phase 3 Task 4 fix — previously a counter failure could
  retry indefinitely). Instead the job is marked `failed`.
- Job status exposes `generation_attempt` so the frontend can surface
  "retrying (2/3)" style feedback.

A known limitation after the 2026-04-08 audit: the cross-invocation
read-modify-write race in
`S3StorageService.update_streaming_progress` remains. The in-process
race in `process_stream_to_hls` is mitigated by the `_StreamState`
lock. See Phase 0 ADR-3 of `docs/plans/2026-04-08-audit-float/` for the
justification and the deferred DynamoDB migration scope.

### Gemini Live token endpoint

The `/token` endpoint backs the optional Gemini Live voice Q&A flow in
the frontend (`frontend/hooks/useGeminiLiveAPI.ts`). As of Phase 2
Task 1 of the 2026-04-08 audit remediation, the endpoint returns an
HMAC-derived opaque marker keyed on `(user_id, server GEMINI_API_KEY)`
with a 60-second TTL, not the raw Gemini API key. See API.md Section 4
for the wire contract.

## Deployment

```bash
npm run deploy
```

This runs a custom deploy script (`backend/scripts/deploy.mjs`) that builds and deploys via AWS SAM. See `backend/samconfig.toml` for configuration (gitignored — create your own with `sam deploy --guided`).
