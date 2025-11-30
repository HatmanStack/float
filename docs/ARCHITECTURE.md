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
  - TTS: OpenAI/ElevenLabs for speech synthesis
  - Audio: FFmpeg processing
  - Storage: AWS S3 upload/download

**Endpoints**:

- `POST /` - Summary inference (emotion analysis)
- `POST /` - Meditation generation

## Database & Storage

- **S3**: User meditations and audio files
- **Local Context**: Float history in app

## Technology Stack

| Layer    | Technology                             |
| -------- | -------------------------------------- |
| Frontend | React Native 0.74, Expo 52, TypeScript |
| Backend  | Python 3.13, AWS Lambda, Pydantic      |
| AI       | Google Gemini                          |
| TTS      | OpenAI                                 |
| Storage  | AWS S3                                 |

## Deployment

```bash
cd backend && sam build && sam deploy
```

See `backend/samconfig.toml` for configuration.
