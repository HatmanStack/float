# Phase 0: Foundation

This document captures architecture decisions, design patterns, and conventions shared across
all implementation phases.

## Architecture Decisions

### ADR-1: Gemini 2.5 Flash TTS as Primary Provider with OpenAI Fallback

The existing `GeminiTTSProvider` in `backend/src/providers/gemini_tts.py` uses the older
`generate_content` API with `response_modalities=["AUDIO"]` and outputs raw PCM. The new
implementation upgrades to the dedicated TTS model `gemini-2.5-flash-preview-tts` and requests
MP3 output directly. This avoids any PCM-to-MP3 conversion step and keeps the existing FFmpeg
HLS pipeline unchanged (it already expects MP3 voice input).

The `LambdaHandler.__init__` currently hardcodes `OpenAITTSProvider()` at line 68. This will
be changed to `GeminiTTSProvider()` as the primary, with OpenAI used as a fallback when the
Gemini circuit breaker trips. The fallback logic lives in `lambda_handler.py`, not inside the
provider itself.

**Decision:** Upgrade the existing `gemini_tts.py` in-place rather than creating a new file.
The old PCM-based implementation is not used in production (OpenAI is the current primary).

### ADR-2: Client-Side Gemini Live API Connection

The voice Q&A connects directly from the React Native frontend to the Gemini Live API via
WebSocket. This avoids new backend infrastructure (no ECS/Fargate/Cloud Run needed for
WebSocket proxying). The frontend obtains a short-lived token from the Lambda backend before
establishing the WebSocket connection, keeping the main Gemini API key server-side.

**Token exchange approach:** The backend provides a new `POST /token` endpoint that returns
a short-lived token. The frontend uses this token when connecting to the Gemini Live API.
Research during implementation will determine whether Google provides ephemeral API tokens
or whether a proxy pattern with a time-limited key is needed. The token endpoint is
lightweight to minimize Lambda cold-start impact.

### ADR-3: Inline Q&A UI in MeditationControls

The voice Q&A replaces the Generate button temporarily during the conversation. It renders
inline in the same location as `MeditationControls`, not in a full-screen overlay. The UI
shows a mic icon with visual feedback (pulsing animation during recording) and a brief
transcript display. After Q&A completes, the meditation generation flow proceeds normally.

### ADR-4: Text Fallback for Mic Denial

When microphone permission is denied, the Q&A falls back to text input. The same 2-3
exchange conversation happens via typed messages instead of voice. The system prompt and
transcript format remain identical regardless of input modality.

### ADR-5: Gemini 2.5 Flash Model Upgrade

Both `analyze_sentiment` and `generate_meditation` in `gemini_service.py` currently use
`gemini-2.0-flash`. These are upgraded to `gemini-2.5-flash`. This is a simple string
replacement in the model name, but tests must be updated to expect the new model name.

### ADR-6: Dual SDK Management

The backend currently uses `google-generativeai` (older SDK, imported as
`import google.generativeai as genai`) for `gemini_service.py` and `google-genai` (newer SDK,
imported as `from google import genai`) for `gemini_tts.py`. The TTS provider already uses
the newer SDK. The Live API token endpoint will also use the newer SDK. The AI service
(`gemini_service.py`) stays on the older SDK for now since it works and migration is risky.
`google-genai` must be added to `requirements.txt` since it is imported but not listed.

## Design Patterns

### TTS Provider Pattern

All TTS providers implement the `TTSService` abstract base class:

```python
class TTSService(ABC):
    def synthesize_speech(self, text: str, output_path: str) -> bool: ...
    def stream_speech(self, text: str) -> Iterator[bytes]: ...
    def get_provider_name(self) -> str: ...
```

The Gemini TTS provider follows the same pattern as `OpenAITTSProvider`:

- `stream_speech` is the primary method, decorated with `@with_circuit_breaker`
- `synthesize_speech` delegates to an internal streaming method (without circuit breaker)
- Errors raise `TTSError` for consistency

### TTS Fallback Pattern

The fallback logic in `lambda_handler.py` works as follows:

1. Try the primary provider (Gemini TTS)
1. If `TTSError` or `CircuitBreakerOpenError`, fall back to secondary (OpenAI TTS)
1. If secondary also fails, raise `TTSError` to the caller

This applies to both `_generate_meditation_audio` (batch mode) and `_process_meditation_hls`
(streaming mode, via `get_tts_provider()`).

### Q&A State Machine

The frontend voice Q&A goes through these states:

```text
IDLE -> CONNECTING -> LISTENING -> PROCESSING -> RESPONDING -> LISTENING -> ... -> COMPLETE
```

- `IDLE`: Generate button visible
- `CONNECTING`: Obtaining token, establishing WebSocket
- `LISTENING`: Mic active, user speaking
- `PROCESSING`: User finished speaking, waiting for model response
- `RESPONDING`: Model speaking (audio playback)
- `COMPLETE`: Q&A finished, transcript captured, meditation generation begins

### Transcript Format

The Q&A transcript is a simple array of exchange objects:

```json
[
  {"role": "assistant", "text": "I see you had a stressful moment at work..."},
  {"role": "user", "text": "Yes, my boss gave me unexpected feedback..."},
  {"role": "assistant", "text": "That sounds challenging. Let's address that in your meditation."}
]
```

This is passed as `qa_transcript` in the meditation request payload and appended to the
meditation generation prompt.

## Testing Strategy

### Backend Tests

- **Framework:** pytest with `@pytest.mark.unit` markers
- **Mocking:** `unittest.mock.patch` and `MagicMock` for external services
- **No live API calls:** All Gemini and OpenAI API calls are mocked in unit tests
- **Circuit breaker:** Test that `@with_circuit_breaker` decorator works with new provider
- **Run command:** `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- **CI command:** `pytest backend/tests` (runs all tests including integration)

### Frontend Tests

- **Framework:** Jest with React Testing Library
- **Mocking:** `jest.mock()` for modules, `jest.fn()` for functions
- **WebSocket mocking:** Mock the native WebSocket class for Live API tests
- **Audio mocking:** Mock `expo-av` Audio for mic permission tests
- **Run command:** `npm test`
- **Single file:** `npm test -- --testPathPattern="SomeTest"`

### Test File Locations

- Backend: `backend/tests/unit/test_*.py`
- Frontend unit: `frontend/tests/unit/*-test.tsx` or `*-test.ts`
- Frontend integration: `frontend/tests/integration/*-test.tsx`

## Commit Message Format

All commits use conventional commits:

```text
type(scope): brief description

- Detail 1
- Detail 2
```

Types: `feat`, `fix`, `test`, `refactor`, `chore`

Scopes: `backend`, `frontend`, `tts`, `qa`, `deps`

## Deployment Strategy

Deployment is NOT part of this plan. The `npm run deploy` command should NOT be run during
implementation. Changes are verified locally via tests and lint checks:

```bash
npm run check          # Runs lint + all tests
npm run lint           # Frontend ESLint + TypeScript
npm test               # Frontend Jest
npm run test:backend   # Backend pytest
npm run lint:backend   # Backend ruff
```
