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

## Deployment

```bash
npm run deploy
```

This runs a custom deploy script (`backend/scripts/deploy.mjs`) that builds and deploys via AWS SAM. See `backend/samconfig.toml` for configuration (gitignored — create your own with `sam deploy --guided`).
