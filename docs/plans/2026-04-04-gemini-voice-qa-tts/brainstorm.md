# Feature: Gemini Voice Q&A + TTS Migration

## Overview
Replace OpenAI TTS with Gemini 2.5 Flash TTS for meditation audio generation and introduce a pre-meditation voice Q&A powered by the Gemini Live API. When a user clicks Generate, instead of immediately kicking off meditation generation, the app initiates a short real-time voice conversation (2-3 exchanges) between the user and a Gemini-powered agent. The agent uses the selected floats' sentiment data to ask targeted questions — e.g., "I see you had a stressful moment at work — is that still weighing on you?" — giving the model richer context for a more personalized meditation.

The voice Q&A connects directly from the React Native client to the Gemini Live API via WebSocket. A short-lived token is obtained from the existing Lambda backend before the connection is established, keeping the main Gemini API key server-side. After the Q&A completes, the conversation transcript is appended to the existing float sentiment data and sent to the current Lambda meditation endpoint. The backend meditation pipeline (script generation → TTS → FFmpeg → HLS streaming) remains intact, with the TTS provider swapped from OpenAI gpt-4o-mini-tts to Gemini 2.5 Flash TTS.

This migration dramatically reduces cost — Gemini 2.5 Flash TTS is ~$0.12/1M chars vs OpenAI's ~$12/1M audio tokens — while adding a personalization layer that improves meditation quality. OpenAI TTS is retained as a circuit-breaker fallback until Gemini TTS proves stable in production. The AI text generation model is also upgraded from Gemini 2.0 Flash to 2.5 Flash across the board.

## Decisions
1. **Voice Q&A via Gemini Live API** — Real-time spoken back-and-forth conversation using WebSocket, not text-based. Provides the richest user experience for a meditation app.
2. **Client-side Live API connection** — Frontend connects directly to Gemini Live API. Avoids new backend infrastructure (no ECS/Fargate needed), keeps the architecture simple for MVP.
3. **Short-lived token exchange for auth** — Frontend calls existing Lambda endpoint to get a scoped/short-lived token before connecting to Gemini. Main API key stays server-side.
4. **Quick check-in (2-3 exchanges)** — Model asks 1-2 targeted questions based on float sentiment data, user responds, then meditation generates. ~30-60 seconds. Not an open-ended therapy session.
5. **Transcript appended to existing flow** — Q&A transcript is sent alongside existing float sentiment data to the Lambda meditation endpoint. Meditation prompt is enriched but the generation pipeline stays the same.
6. **Gemini 2.5 Flash TTS replaces OpenAI** — Dedicated TTS model (`gemini-2.5-flash-preview-tts`) with voice style instructions, requesting MP3 output directly for drop-in compatibility with the HLS pipeline.
7. **MP3 output from Gemini TTS** — Request MP3 format directly from the API to avoid PCM-to-MP3 conversion. Existing FFmpeg pipeline works unchanged.
8. **Inline Q&A UI** — Conversation happens where the Generate button was, with minimal UI (mic icon, visual feedback). No full-screen overlay. Low friction.
9. **Text fallback for mic denial** — If microphone permission is denied, Q&A falls back to text input. Meditation still generates normally.
10. **OpenAI kept as fallback** — Gemini TTS is primary provider. OpenAI remains behind circuit breaker for reliability. Full removal deferred.
11. **Upgrade AI model to Gemini 2.5 Flash** — Sentiment analysis and meditation script generation both move from 2.0 Flash to 2.5 Flash. Cheaper and better quality.

## Scope: In
- New Lambda endpoint (or extension of existing) to issue short-lived Gemini API tokens for the Live API
- Client-side Gemini Live API WebSocket integration in React Native
- Inline voice Q&A UI in the explore tab (mic icon, visual feedback, transcript display)
- System prompt for the Q&A agent that receives float sentiment data and conducts a 2-3 exchange check-in
- Text-based Q&A fallback when microphone permission is denied
- Transcript capture and transmission to Lambda meditation endpoint
- Update `MeditationRequestModel` to accept optional Q&A transcript field
- Update meditation generation prompt in `gemini_service.py` to incorporate Q&A transcript
- New Gemini 2.5 Flash TTS provider implementation (or update existing `gemini_tts.py`)
- MP3 output format from Gemini TTS
- Swap default TTS provider from OpenAI to Gemini in `lambda_handler.py`
- Circuit breaker fallback: Gemini TTS primary → OpenAI TTS secondary
- Upgrade `gemini_service.py` model from `gemini-2.0-flash` to `gemini-2.5-flash`
- Update `settings.py` to add Gemini TTS model config (already has `GEMINI_TTS_MODEL`)
- Frontend microphone permission handling (may already exist via RecordButton)
- Unit tests for new TTS provider, token exchange endpoint, Q&A transcript integration
- Update existing tests that reference OpenAI as primary provider

## Scope: Out
- Full removal of OpenAI dependency (deferred until Gemini TTS is proven stable)
- New backend infrastructure (ECS, Fargate, Cloud Run) for WebSocket proxying
- Full-screen conversation UI / dedicated Q&A screen
- Open-ended/long-form therapy conversations (capped at 2-3 exchanges)
- Video input via Live API (audio only)
- Multi-language Q&A support (English first)
- Changes to the float submission / sentiment analysis flow (that stays as-is)
- Changes to HLS streaming, S3 storage, background music mixing, or download pipeline
- User-configurable Q&A preferences or settings

## Open Questions
- **Gemini Live API token scoping:** What token format does Google support for short-lived client access? May need to use Google Cloud service account with limited scopes or Gemini API's built-in ephemeral token mechanism. Planner should research `generateContent` vs Live API auth patterns.
- **Gemini 2.5 Flash TTS MP3 support:** Confirm that `gemini-2.5-flash-preview-tts` supports direct MP3 output (vs only PCM/WAV). If not, a lightweight PCM→MP3 conversion step will be needed client-side or server-side.
- **Live API React Native WebSocket compatibility:** Verify that React Native's WebSocket implementation works with Gemini Live API's protocol. May need a polyfill or native module.
- **Voice selection for TTS:** Current OpenAI uses "sage" voice with meditation-specific instructions. Need to evaluate Gemini TTS voices (Kore, Puck, Charon, Leda, etc.) for best meditation quality and confirm style instruction support.
- **Audio output format from Live API Q&A:** The Q&A audio doesn't need to be stored, but the transcript does. Confirm that the Live API provides text transcripts of both sides of the conversation.
- **Rate limits:** Gemini Live API and TTS have different rate limits than the standard `generateContent` API. Verify limits are sufficient for expected traffic.

## Relevant Codebase Context
- `backend/src/providers/openai_tts.py` — Current TTS provider using `gpt-4o-mini-tts-2025-12-15`, voice "sage", with `MEDITATION_VOICE_INSTRUCTIONS`. This is the primary replacement target.
- `backend/src/providers/gemini_tts.py` — Existing Gemini TTS provider using older `generate_content` API with `response_modalities=["AUDIO"]` and voice "Kore". Outputs raw PCM. Needs upgrade to 2.5 Flash TTS with MP3 output.
- `backend/src/services/gemini_service.py` — AI service using `gemini-2.0-flash` for sentiment analysis and meditation generation. Model to be upgraded to `gemini-2.5-flash`. Meditation prompt template at line 112 needs to incorporate Q&A transcript.
- `backend/src/services/tts_service.py` — Abstract `TTSService` base class with `synthesize_speech`, `stream_speech`, `get_provider_name`. New provider must implement this interface.
- `backend/src/services/ai_service.py` — Abstract `AIService` base class. `generate_meditation` signature accepts `input_data: Dict` — transcript can be added to this dict.
- `backend/src/handlers/lambda_handler.py` — `LambdaHandler.__init__` hardcodes `OpenAITTSProvider()` at line 68. Needs to be swapped to Gemini with OpenAI fallback. Token exchange endpoint needs to be added to routing.
- `backend/src/config/settings.py` — Has `GEMINI_API_KEY`, `OPENAI_API_KEY`, and `GEMINI_TTS_MODEL` (via existing gemini_tts usage). `validate_keys()` requires both keys.
- `backend/src/utils/circuit_breaker.py` — Has `gemini_circuit` and `openai_circuit`. TTS fallback logic will use these.
- `backend/src/models/requests.py` — `MeditationRequestModel` needs a new optional `qa_transcript` field.
- `frontend/components/BackendMeditationCall.tsx` — Meditation request payload construction at line 241. Needs to include Q&A transcript.
- `frontend/app/(tabs)/explore.tsx` — `useMeditation` hook and `MeditationControls` component. Q&A UI will be added inline here.
- `frontend/components/ScreenComponents/MeditationControls.tsx` — Generate button and loading states. Q&A interaction replaces/precedes the loading state.
- `frontend/components/ScreenComponents/RecordButton.tsx` — Existing microphone usage pattern. Reference for audio permissions handling.
- `frontend/context/IncidentContext.tsx` — Incident (float) data structure with sentiment analysis results.
- `backend/requirements.txt` — Has `google-generativeai>=0.8.5` and `openai`. May need `google-genai` (newer SDK) for Live API / 2.5 Flash TTS.
- `frontend/.env` — `EXPO_PUBLIC_LAMBDA_FUNCTION_URL`. May need new env var for Gemini Live API endpoint if not proxied through Lambda.

## Technical Constraints
- **Lambda 15-minute timeout:** Not a concern for the Q&A (client-side) but remains the constraint for meditation generation. Current async self-invocation pattern handles this.
- **Lambda cold starts:** Token exchange endpoint should be lightweight to minimize latency when user clicks Generate.
- **React Native WebSocket:** Standard WebSocket API is available in React Native but may have platform-specific quirks with binary audio data. Expo's managed workflow may impose additional constraints.
- **Gemini Live API session limits:** Audio-only sessions are limited (15 min on free tier). The 30-60 second Q&A is well within limits, but rate limiting per-user should be considered.
- **Gemini 2.5 Flash TTS is in preview:** The model ID `gemini-2.5-flash-preview-tts` suggests it's not yet GA. Stability and API changes are possible — another reason to keep OpenAI as fallback.
- **Dual SDK concern:** The backend currently uses `google-generativeai` (older SDK) for the AI service and `google-genai` (newer SDK) for the existing Gemini TTS provider. May need to consolidate or manage both.
- **HLS pipeline dependency on MP3:** The FFmpeg audio service expects MP3 voice input. If Gemini TTS cannot output MP3 directly, a conversion step is required before the existing pipeline.
- **Cost estimation:** For a 5-minute meditation (~750 words, ~3800 chars), Gemini TTS cost is ~$0.000000456 per meditation. OpenAI cost for equivalent is significantly higher. Q&A adds ~$0.001-0.005 per session for Live API usage.
