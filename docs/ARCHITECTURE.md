# Float Architecture

This document describes the system architecture, component interactions, and design decisions behind Float.

## System Overview

Float is a serverless meditation app with clear separation between frontend (React Native/Expo) and backend (AWS Lambda).

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                       │
│  iOS / Android / Web (React Native + Expo)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/HTTPS
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  AWS Lambda Function                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Middleware (CORS, Auth, Validation, Error Handling)   ││
│  └──────────────────────┬──────────────────────────────────┘│
│  ┌──────────────────────▼──────────────────────────────────┐│
│  │           Handler (Routes to Services)                  ││
│  └──────────────────────┬──────────────────────────────────┘│
│  ┌──────────────────────▼──────────────────────────────────┐│
│  │  Services (AI, TTS, Audio, Storage)                     ││
│  └──────────────────────────────────────────────────────────┘│
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┬──────────────┐
     │               │               │              │
┌────▼──┐    ┌──────▼─────┐   ┌────▼──┐    ┌─────▼──┐
│Google │    │  OpenAI    │   │  AWS  │    │ User  │
│Gemini │    │   TTS      │   │  S3   │    │ Data  │
└────────┘    └────────────┘   └───────┘    └────────┘
```

## Frontend Architecture

### Overview

The frontend is a cross-platform React Native app built with Expo and Expo Router for file-based navigation.

### Technology Stack

- **Framework**: React Native 0.74
- **Build Tool**: Expo 52
- **Language**: TypeScript (strict mode)
- **Routing**: Expo Router (file-based)
- **State Management**: React Context API
- **Testing**: Jest + React Native Testing Library

### Directory Structure

```
app/                    # Expo Router navigation (file-based routing)
├── (tabs)/             # Tab-based navigation
│   ├── _layout.tsx     # Tab layout
│   ├── index.tsx       # Home tab
│   └── explore.tsx     # Explore tab
├── _layout.tsx         # Root layout
└── +not-found.tsx      # 404 page

components/            # React Native components
├── AudioRecording.tsx  # Record audio floats
├── AuthScreen.tsx      # Authentication
├── IncidentItem.tsx    # Display float items
├── MeditationControls.tsx # Play controls
├── ThemedView.tsx      # Themed container
└── __tests__/          # Component tests

context/               # State management
├── AuthContext.tsx    # Authentication state
└── IncidentContext.tsx # Floats state

constants/             # Constants and utilities
├── Colors.ts          # Color scheme
├── StylesConstants.tsx # Styling constants
└── util.ts            # Utility functions

hooks/                 # Custom React hooks (if used)
└── useAudio.ts        # Audio playback hook (example)
```

### State Management

Uses React Context API for simple state sharing:

- **AuthContext**: User authentication and session
- **IncidentContext**: List of floats and current selection
- Components consume contexts via hooks

### Data Flow

1. User opens app → Home screen shows list of floats
2. User records/creates a float → Sent to Lambda
3. Lambda analyzes emotion → Returns sentiment analysis
4. Float stored locally and in S3
5. User selects floats → Sent to meditation endpoint
6. Lambda generates meditation + audio → Downloaded to device
7. User plays meditation

## Backend Architecture

### Overview

Backend is a Python-based AWS Lambda function handling AI processing, TTS synthesis, and audio storage.

### Technology Stack

- **Language**: Python 3.12+
- **Framework**: AWS Lambda
- **Validation**: Pydantic models
- **AI**: Google Gemini API
- **TTS**: OpenAI TTS API
- **Storage**: AWS S3
- **Testing**: pytest

### Directory Structure

```
backend/
├── src/
│   ├── handlers/
│   │   ├── lambda_handler.py    # Entry point, routes requests
│   │   └── middleware.py         # Middleware chain (CORS, auth, etc.)
│   │
│   ├── services/
│   │   ├── ai_service.py        # Abstract AI interface
│   │   ├── gemini_service.py    # Google Gemini implementation
│   │   ├── tts_service.py       # Text-to-speech interface
│   │   ├── audio_service.py     # Audio processing
│   │   └── s3_storage_service.py # S3 operations
│   │
│   ├── models/
│   │   ├── requests.py           # Request validation (Pydantic)
│   │   └── responses.py          # Response formatting
│   │
│   ├── providers/
│   │   └── openai_tts.py        # OpenAI TTS provider
│   │
│   ├── config/
│   │   ├── settings.py           # Environment config
│   │   └── constants.py          # Constants
│   │
│   └── utils/
│       ├── audio_utils.py        # Audio encoding/decoding
│       └── file_utils.py         # File operations
│
├── tests/
│   ├── unit/                     # Unit tests
│   ├── mocks/                    # Mock objects
│   ├── fixtures/                 # Test data
│   └── conftest.py              # Pytest configuration
│
├── pyproject.toml               # Project config
├── requirements.txt             # Production dependencies
└── Makefile                     # Quality check commands
```

### Request Processing Pipeline

```
HTTP Request
    ↓
[CORS Middleware] → Check origin
    ↓
[JSON Middleware] → Parse body
    ↓
[Method Validation] → POST only
    ↓
[Request Validation] → Check required fields
    ↓
[Error Handling] → Catch exceptions
    ↓
[Handler Logic]
├─ Summary Request → analyze_sentiment → return analysis
└─ Meditation Request → generate_meditation → synthesize → return audio
    ↓
Response (JSON or error)
```

### Key Services

#### AIService (Abstract)
- `analyze_sentiment(audio, text)` → SentimentResult
- `generate_meditation(floats)` → meditation text

#### GeminiAIService (Implementation)
- Uses Google Gemini API
- Analyzes emotion from audio/text
- Generates meditation scripts

#### TTSService (Abstract)
- `synthesize_speech(text, output_path)` → bool

#### OpenAI TTS Provider
- Converts meditation text to speech
- Saves MP3 file
- Supports different voices and speeds

#### AudioService
- Combines voice narration with background music
- Audio processing with FFmpeg
- WAV/MP3 conversion

#### StorageService
- Upload/download from S3
- Organize by user ID and request type
- Track generated meditations

### Error Handling

All endpoints return structured error responses:

```python
{
    "statusCode": 400,
    "body": {
        "error": "Validation error",
        "details": "user_id is required"
    }
}
```

HTTP Status Codes:
- `200 OK`: Success
- `400 Bad Request`: Validation error
- `500 Internal Server Error`: Server error

### Configuration

Environment variables in `.env`:

**Required (Backend)**
```
G_KEY=<google-gemini-api-key>
OPENAI_API_KEY=<openai-api-key>
AWS_S3_BUCKET=<bucket-name>
AWS_ACCESS_KEY_ID=<aws-key>
AWS_SECRET_ACCESS_KEY=<aws-secret>
```

**Optional**
```
TEMP_DIR=/tmp  # Temp file location
LOG_LEVEL=INFO
```

## Data Models

### Request Models (Pydantic)

**SummaryRequest**
- `user_id`: str (required)
- `audio`: str or "NotAvailable" (optional, base64 encoded)
- `prompt`: str or "NotAvailable" (optional)

**MeditationRequest**
- `user_id`: str (required)
- `input_data`: dict or list of dicts (float data)
- `music_list`: list of strings (music file paths)

### Response Models

**SummaryResponse**
- `request_id`: str (unique request ID)
- `user_id`: str
- `sentiment`: str (emotion analysis)
- `intensity`: float (0-1 intensity score)
- `reasoning`: str (why this emotion was detected)

**MeditationResponse**
- `request_id`: str
- `user_id`: str
- `base64_audio`: str (base64 encoded MP3)
- `duration`: int (seconds)
- `music_list`: list (used music files)

## Data Flow (Detailed)

### Summary Request Flow

```
1. User submits float (audio/text)
2. Frontend encodes audio to base64
3. POST /summary with:
   - user_id
   - audio (base64)
   - prompt (text)
4. Backend:
   - Validate request
   - Decode audio if provided
   - Call AI service: analyze_sentiment()
   - Store results in S3
   - Return SummaryResponse
5. Frontend displays sentiment analysis
6. User reviews before creating meditation
```

### Meditation Request Flow

```
1. User selects floats and music
2. Frontend collects float data and music list
3. POST /meditate with:
   - user_id
   - input_data (float details)
   - music_list (music files)
4. Backend:
   - Validate request
   - Call AI service: generate_meditation()
   - Call TTS provider: synthesize_speech()
   - Combine voice + music with audio_service
   - Encode result to base64
   - Store in S3
   - Return MeditationResponse
5. Frontend receives base64 audio
6. User plays meditation
```

## Design Decisions

### Serverless (AWS Lambda)

**Why**: Scales automatically, pay-per-use, no server management

**Trade-offs**:
- Cold starts (15s first call)
- Max 15-minute execution time
- Stateless (no caching)

### Google Gemini for AI

**Why**: Excellent at emotion detection from audio, good cost, API-first

**Alternative**: OpenAI GPT (more expensive, no audio native)

### OpenAI TTS

**Why**: High-quality voice synthesis, affordable

**Alternative**: Google TTS (more voices, more expensive)

### AWS S3 for Storage

**Why**: Durable, scalable, integrates with Lambda

**Usage**: Store generated meditations by user for replay

### React Context for Frontend State

**Why**: Simple for medium-sized app, no external dependencies

**Trade-offs**: Prop drilling at depth, not optimized for frequent updates

## Future Scaling Considerations

### Frontend
- Add Redux/MobX if state management becomes complex
- Implement local caching of meditations
- Add offline support with local database

### Backend
- Add database (DynamoDB) for user history
- Implement caching layer (Redis/ElastiCache)
- Add ML model optimization for cold starts
- Separate Lambda functions by endpoint type

### Data
- Implement batch processing for meditation generation
- Add CDN for audio distribution
- Implement versioning for meditation templates

---

**Questions?** See [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue.
