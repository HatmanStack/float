# Phase 1: Backend TTS Migration and Token Endpoint

## Phase Goal

Upgrade the Gemini TTS provider to use `gemini-2.5-flash-preview-tts` with MP3 output, swap
the default TTS provider from OpenAI to Gemini with circuit-breaker fallback, upgrade the AI
model from `gemini-2.0-flash` to `gemini-2.5-flash`, and add a token exchange endpoint for
the frontend voice Q&A. This phase is backend-only.

### Success Criteria

- Gemini TTS provider outputs MP3 audio via `stream_speech` and `synthesize_speech`
- Gemini TTS is the default provider in `LambdaHandler`
- OpenAI TTS is used as fallback when Gemini circuit breaker trips
- AI model is `gemini-2.5-flash` for both sentiment analysis and meditation generation
- `MeditationRequestModel` accepts optional `qa_transcript` field
- Meditation generation prompt incorporates Q&A transcript when present
- Token exchange endpoint returns a short-lived token for Gemini Live API
- `google-genai` is listed in `requirements.txt`
- `GEMINI_TTS_MODEL` is defined in `settings.py`
- All existing tests pass with necessary updates
- New tests cover Gemini TTS, fallback logic, token endpoint, and transcript integration

### Estimated Tokens

~40,000

## Prerequisites

- No previous phases required (Phase 0 is reference only)
- Backend dependencies installed: `cd backend && pip install -r requirements.txt`
- Gemini API key available in environment

## Tasks

### Task 1: Add google-genai to requirements.txt and GEMINI_TTS_MODEL to settings

**Goal:** Ensure the newer Google GenAI SDK is a declared dependency and the TTS model name
is configurable via settings, not hardcoded.

**Files to Modify:**

- `backend/requirements.txt` - Add `google-genai` package
- `backend/src/config/settings.py` - Add `GEMINI_TTS_MODEL` field

**Prerequisites:** None

**Implementation Steps:**

1. Add `google-genai>=1.0.0` to `backend/requirements.txt`. This package is already imported
   by `backend/src/providers/gemini_tts.py` (`from google import genai`) but is not listed as
   a dependency. Keep `google-generativeai>=0.8.5` (used by `gemini_service.py`).
1. Add a `GEMINI_TTS_MODEL` field to the `Settings` class in `backend/src/config/settings.py`
   with default value `"gemini-2.5-flash-preview-tts"`. This is a simple string field:
   `GEMINI_TTS_MODEL: str = "gemini-2.5-flash-preview-tts"`.
1. Run `cd backend && pip install -r requirements.txt` to verify the dependency installs.

**Verification Checklist:**

- [x] `google-genai>=1.0.0` appears in `backend/requirements.txt`
- [x] `google-generativeai>=0.8.5` still appears (not removed)
- [x] `settings.GEMINI_TTS_MODEL` returns `"gemini-2.5-flash-preview-tts"`
- [x] `pip install -r requirements.txt` succeeds without errors

**Testing Instructions:**

No new tests needed for this task. Existing tests should still pass:

```bash
cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
```

**Commit Message Template:**

```text
chore(deps): add google-genai to requirements, add GEMINI_TTS_MODEL setting

- Add google-genai>=1.0.0 to requirements.txt (already imported by gemini_tts.py)
- Add GEMINI_TTS_MODEL setting with default gemini-2.5-flash-preview-tts
```

---

### Task 2: Upgrade GeminiTTSProvider to 2.5 Flash with MP3 Output

**Goal:** Rewrite the existing `GeminiTTSProvider` to use the dedicated TTS model with MP3
output format, voice style instructions, and circuit breaker integration. The current
implementation outputs raw PCM and lacks error handling consistency with the OpenAI provider.

**Files to Modify:**

- `backend/src/providers/gemini_tts.py` - Rewrite provider implementation

**Prerequisites:** Task 1 (GEMINI_TTS_MODEL in settings)

**Implementation Steps:**

1. Open `backend/src/providers/gemini_tts.py`. The current implementation uses
   `self.client.models.generate_content()` with `response_modalities=["AUDIO"]` and voice
   name "Kore", yielding raw PCM bytes from `part.inline_data.data`.

1. Rewrite `stream_speech` to use the Gemini 2.5 Flash TTS model with these changes:
   - Keep the existing `genai.Client` initialization (newer SDK, `from google import genai`)
   - Use `self.model_name` from `settings.GEMINI_TTS_MODEL` (already set in `__init__`)
   - Add voice style instructions similar to `MEDITATION_VOICE_INSTRUCTIONS` from the OpenAI
     provider. Define a module-level constant `MEDITATION_VOICE_INSTRUCTIONS` with the same
     content as the one in `openai_tts.py`
   - Configure the API call to request MP3 output format. Use the `generate_content` API with
     the TTS model, setting the output modality to audio with MP3 format. The exact parameter
     names depend on the `google-genai` SDK version -- check the SDK docs or source for
     `types.GenerateContentConfig` to find the MP3 output option. If the SDK does not support
     MP3 directly, output PCM and note this as a finding (the plan will need revision)
   - Choose voice "Kore" for the meditation voice (warm, calm tone). This can be changed later
     after voice evaluation
   - Extract audio bytes from the response and yield them as chunks

1. Add the `@with_circuit_breaker(gemini_tts_circuit)` decorator to `stream_speech`. Import
   `with_circuit_breaker` from `..utils.circuit_breaker`. A new `gemini_tts_circuit` breaker
   will be created in Task 3.

1. Rewrite `synthesize_speech` to follow the OpenAI provider pattern: delegate to an internal
   `_stream_speech_internal` method (without circuit breaker), write chunks to file, return
   bool. Wrap in try/except, log errors, return False on failure.

1. Wrap errors in `TTSError` for consistency. Import from `..exceptions`.

1. Add logging consistent with the OpenAI provider (log text length on entry, log success/error).

**Verification Checklist:**

- [x] `GeminiTTSProvider.stream_speech()` yields MP3 audio bytes (or PCM with noted finding)
- [x] `GeminiTTSProvider.synthesize_speech()` writes audio to file and returns bool
- [x] `GeminiTTSProvider.get_provider_name()` returns `"gemini"`
- [x] `stream_speech` is decorated with `@with_circuit_breaker`
- [x] Errors raise `TTSError`
- [x] Voice style instructions are defined as a module-level constant

**Testing Instructions:**

Write tests in `backend/tests/unit/test_services.py` (append to existing file) under a new
`TestGeminiTTSProvider` class:

1. `test_provider_name` - Assert `get_provider_name()` returns `"gemini"`
1. `test_synthesize_speech_success` - Mock `genai.Client` and its `models.generate_content`
   method to return a response with audio data. Assert `synthesize_speech` returns True and
   the file is written. Follow the existing `TestOpenAITTSProvider.test_synthesize_speech_success`
   pattern.
1. `test_synthesize_speech_api_error` - Mock API to raise exception. Assert returns False.
1. `test_stream_speech_yields_chunks` - Mock API response with audio data. Assert
   `stream_speech` yields bytes.
1. `test_stream_speech_raises_tts_error` - Mock API to raise exception. Assert `TTSError`
   is raised.

Mock the `genai.Client` class at `src.providers.gemini_tts.genai.Client`. The mock response
structure should match the Gemini generate_content response:
`response.candidates[0].content.parts[0].inline_data.data` returning bytes.

```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_services.py -v --tb=short -k "Gemini"
```

**Commit Message Template:**

```text
feat(tts): upgrade GeminiTTSProvider to 2.5 Flash with MP3 output

- Rewrite gemini_tts.py for gemini-2.5-flash-preview-tts model
- Add meditation voice instructions and circuit breaker
- Request MP3 output format for HLS pipeline compatibility
- Add unit tests for Gemini TTS provider
```

---

### Task 3: Add Gemini TTS Circuit Breaker and TTS Fallback Logic

**Goal:** Add a dedicated circuit breaker for Gemini TTS (separate from the existing
`gemini_circuit` used by the AI service) and implement fallback logic in `LambdaHandler`
that tries Gemini TTS first and falls back to OpenAI TTS on failure.

**Files to Modify:**

- `backend/src/utils/circuit_breaker.py` - Add `gemini_tts_circuit` instance
- `backend/src/handlers/lambda_handler.py` - Change default TTS provider and add fallback

**Prerequisites:** Task 2 (Gemini TTS provider is updated)

**Implementation Steps:**

1. In `backend/src/utils/circuit_breaker.py`, add a new module-level circuit breaker after
   the existing `gemini_circuit`:

   ```python
   gemini_tts_circuit = CircuitBreaker(
       name="gemini_tts",
       failure_threshold=3,
       recovery_timeout=60.0,
   )
   ```

1. In `backend/src/handlers/lambda_handler.py`:
   - Add import for `GeminiTTSProvider`: `from ..providers.gemini_tts import GeminiTTSProvider`
   - Add import for `CircuitBreakerOpenError`: `from ..exceptions import CircuitBreakerOpenError, TTSError`
     (TTSError is already imported)
   - Change `__init__` line 68 from `self.tts_provider = OpenAITTSProvider()` to
     `self.tts_provider = GeminiTTSProvider()`
   - Add a `self.fallback_tts_provider = OpenAITTSProvider()` on the next line
   - Modify `get_tts_provider` to return the primary provider (no change needed, it already
     returns `self.tts_provider`)
   - Modify `_generate_meditation_audio` (used by base64 mode) to add fallback. After the
     existing `tts_provider.synthesize_speech` call fails (returns False), try
     `self.fallback_tts_provider.synthesize_speech`. If both fail, raise `TTSError`.
   - Modify `_process_meditation_hls` streaming mode: wrap the `tts_provider.stream_speech`
     call (around line 339) in a try/except for `(TTSError, CircuitBreakerOpenError)`. On
     catch, log a warning and retry with `self.fallback_tts_provider.stream_speech`.

**Verification Checklist:**

- [x] `gemini_tts_circuit` exists in `circuit_breaker.py` with name `"gemini_tts"`
- [x] `LambdaHandler.tts_provider` is `GeminiTTSProvider` by default
- [x] `LambdaHandler.fallback_tts_provider` is `OpenAITTSProvider`
- [x] Base64 mode falls back to OpenAI when Gemini TTS fails
- [x] HLS streaming mode falls back to OpenAI when Gemini TTS fails
- [x] Fallback is logged at warning level

**Testing Instructions:**

Add tests in `backend/tests/unit/test_lambda_handler.py`:

1. `test_default_tts_provider_is_gemini` - Create handler with `validate_config=False` and
   mock AI service. Assert `handler.tts_provider.get_provider_name() == "gemini"`.
1. `test_fallback_tts_provider_is_openai` - Assert
   `handler.fallback_tts_provider.get_provider_name() == "openai"`.
1. `test_tts_fallback_on_gemini_failure` - Mock `GeminiTTSProvider.synthesize_speech` to
   return False, mock `OpenAITTSProvider.synthesize_speech` to return True. Call
   `_generate_meditation_audio`. Assert OpenAI provider was called.
1. `test_tts_fallback_on_circuit_breaker_open` - Mock Gemini `stream_speech` to raise
   `CircuitBreakerOpenError("gemini_tts")`. Assert fallback provider's `stream_speech` is
   called.

These tests require patching the provider constructors since `LambdaHandler.__init__`
instantiates them. Patch `src.handlers.lambda_handler.GeminiTTSProvider` and
`src.handlers.lambda_handler.OpenAITTSProvider` to return mock objects.

```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_lambda_handler.py -v --tb=short -k "tts"
```

**Commit Message Template:**

```text
feat(tts): add Gemini TTS circuit breaker and OpenAI fallback

- Add gemini_tts_circuit to circuit_breaker.py
- Set GeminiTTSProvider as default in LambdaHandler
- Add OpenAI fallback for both batch and streaming modes
- Add tests for TTS fallback logic
```

---

### Task 4: Upgrade AI Model to Gemini 2.5 Flash

**Goal:** Change the model used for sentiment analysis and meditation generation from
`gemini-2.0-flash` to `gemini-2.5-flash` in `gemini_service.py`.

**Files to Modify:**

- `backend/src/services/gemini_service.py` - Update model name strings

**Prerequisites:** None (independent of TTS tasks)

**Implementation Steps:**

1. In `backend/src/services/gemini_service.py`, find the two places where
   `model_name="gemini-2.0-flash"` is used:
   - Line 179 in `analyze_sentiment`: `genai.GenerativeModel(model_name="gemini-2.0-flash", ...)`
   - Line 283 in `generate_meditation`: `genai.GenerativeModel(model_name="gemini-2.0-flash", ...)`
1. Change both to `model_name="gemini-2.5-flash"`.
1. Consider extracting the model name to a class-level constant or setting for easier future
   changes. If you do, add a `GEMINI_AI_MODEL` field to `settings.py` with default
   `"gemini-2.5-flash"` and use `settings.GEMINI_AI_MODEL` in the service. This is optional
   but recommended.

**Verification Checklist:**

- [x] No occurrences of `gemini-2.0-flash` remain in `gemini_service.py`
- [x] `analyze_sentiment` uses `gemini-2.5-flash`
- [x] `generate_meditation` uses `gemini-2.5-flash`
- [x] All existing tests pass (tests mock the model, so model name change is transparent)

**Testing Instructions:**

Existing tests in `backend/tests/unit/test_services.py` and `test_lambda_handler.py` should
continue to pass since they mock the Gemini API calls. No new tests needed, but verify:

```bash
cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
```

If you extracted the model name to settings, add a simple test:

```python
def test_gemini_ai_model_setting():
    assert settings.GEMINI_AI_MODEL == "gemini-2.5-flash"
```

**Commit Message Template:**

```text
feat(backend): upgrade AI model from gemini-2.0-flash to gemini-2.5-flash

- Update model name in analyze_sentiment and generate_meditation
- Optionally extract to GEMINI_AI_MODEL setting for configurability
```

---

### Task 5: Add qa_transcript to MeditationRequestModel and Meditation Prompt

**Goal:** Extend the meditation request model to accept an optional Q&A transcript and
update the meditation generation prompt to incorporate it when present.

**Files to Modify:**

- `backend/src/models/requests.py` - Add `qa_transcript` field to `MeditationRequestModel`
- `backend/src/services/gemini_service.py` - Update meditation prompt template
- `backend/src/handlers/lambda_handler.py` - Pass transcript through to AI service

**Prerequisites:** None (independent of TTS tasks)

**Implementation Steps:**

1. In `backend/src/models/requests.py`, add an optional field to `MeditationRequestModel`:

   ```python
   qa_transcript: List[Dict[str, str]] | None = None
   ```

   This field accepts an array of `{"role": "...", "text": "..."}` objects or None. Add it
   after the `duration_minutes` field.

1. Update `MeditationRequestModel.to_dict()` to include `qa_transcript` when present:

   ```python
   def to_dict(self) -> Dict[str, Any]:
       result = {
           "user_id": self.user_id,
           "inference_type": self.inference_type,
           "input_data": self.input_data,
           "music_list": self.music_list,
           "duration_minutes": self.duration_minutes,
       }
       if self.qa_transcript:
           result["qa_transcript"] = self.qa_transcript
       return result
   ```

1. In `backend/src/services/gemini_service.py`, update `prompt_meditation_template` to include
   a conditional section for Q&A transcript. Add the following text before the final
   "Data for meditation transcript:" line:

   ```text
   {qa_transcript_section}
   ```

   Then in `generate_meditation`, build the `qa_transcript_section` string:
   - If `input_data` contains a `"qa_transcript"` key with a non-empty list, format it as:

     ```text
     Additionally, the user participated in a brief check-in conversation before this
     meditation. Use the insights from this conversation to make the meditation more
     personal and targeted:

     Check-in transcript:
     [formatted transcript exchanges]
     ```

   - If no transcript, use an empty string for `qa_transcript_section`

1. In `lambda_handler.py`, update `_process_meditation_base64` and `_process_meditation_hls`
   to include the Q&A transcript in `input_data` when present on the request. After the
   `input_data = self._ensure_input_data_is_dict(request.input_data)` line, add:

   ```python
   if request.qa_transcript:
       input_data["qa_transcript"] = request.qa_transcript
   ```

**Verification Checklist:**

- [x] `MeditationRequestModel` accepts `qa_transcript` as optional field
- [x] Requests without `qa_transcript` still validate correctly
- [x] `to_dict()` includes `qa_transcript` when present, omits when None
- [x] Meditation prompt includes transcript section when provided
- [x] Meditation prompt is unchanged when no transcript provided
- [x] `input_data` dict passed to `generate_meditation` includes transcript when present

**Testing Instructions:**

Add tests in `backend/tests/unit/test_models.py`:

1. `test_meditation_request_with_qa_transcript` - Create a `MeditationRequestModel` with
   `qa_transcript=[{"role": "assistant", "text": "How are you?"}]`. Assert it validates.
1. `test_meditation_request_without_qa_transcript` - Create without the field. Assert
   `qa_transcript` is None.
1. `test_meditation_request_to_dict_with_transcript` - Assert `to_dict()` includes
   `qa_transcript` when present.
1. `test_meditation_request_to_dict_without_transcript` - Assert `to_dict()` does not
   include `qa_transcript` key when None.

Add tests in `backend/tests/unit/test_services.py` or create a new test class:

1. `test_meditation_prompt_includes_transcript` - Mock `genai.GenerativeModel` and capture
   the prompt passed to `generate_content`. Provide `input_data` with a `qa_transcript` key.
   Assert the prompt contains "Check-in transcript".
1. `test_meditation_prompt_without_transcript` - Same but without `qa_transcript` in
   `input_data`. Assert the prompt does not contain "Check-in transcript".

```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_models.py tests/unit/test_services.py -v --tb=short -k "transcript"
```

**Commit Message Template:**

```text
feat(backend): add qa_transcript support to meditation request and prompt

- Add optional qa_transcript field to MeditationRequestModel
- Update meditation prompt to incorporate Q&A transcript when present
- Pass transcript through lambda_handler to AI service
- Add tests for transcript model validation and prompt integration
```

---

### Task 6: Add Token Exchange Endpoint

**Goal:** Add a `POST /token` endpoint to the Lambda function that returns a short-lived
token for the frontend to connect to the Gemini Live API. This keeps the Gemini API key
server-side while allowing direct client-to-Gemini WebSocket connections.

**Files to Modify:**

- `backend/src/handlers/lambda_handler.py` - Add routing for `/token` endpoint and handler
- `backend/src/config/settings.py` - No changes needed (GEMINI_API_KEY already available)

**Prerequisites:** Task 1 (google-genai dependency)

**Implementation Steps:**

1. Research the Gemini Live API authentication model. The options are:
   - **Ephemeral token:** Google may provide a way to generate short-lived tokens from an
     API key. Check the `google-genai` SDK for token generation methods.
   - **Proxy pattern:** If no ephemeral token exists, the endpoint returns the API key
     directly but wrapped with metadata (expiry timestamp). The frontend uses it for one
     session only. This is less secure but acceptable for MVP since the key is already
     scoped to the Gemini API.

   The implementation should prefer ephemeral tokens if available. If not, return the API
   key with a timestamp and document the security limitation.

1. In `backend/src/handlers/lambda_handler.py`, add a new function `_handle_token_request`
   after the existing `_handle_download_request` function. Follow the same pattern:
   - Extract `user_id` from query params (for logging/rate limiting later)
   - Return a JSON response with the token, expiry, and endpoint URL
   - Apply CORS middleware

1. Add routing in the `lambda_handler` function. After the download request check
   (around line 572), add:

   ```python
   if http_method == "POST" and "/token" in raw_path:
       return _handle_token_request(handler, event)
   ```

1. The response format should be:

   ```json
   {
     "token": "<api_key_or_ephemeral_token>",
     "expires_in": 300,
     "endpoint": "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
   }
   ```

**Verification Checklist:**

- [x] `POST /token?user_id=xxx` returns 200 with token payload
- [x] Response includes `token`, `expires_in`, and `endpoint` fields
- [x] CORS headers are present on the response
- [x] Missing `user_id` returns 400 error
- [x] Token value is non-empty

**Testing Instructions:**

Add tests in `backend/tests/unit/test_lambda_handler.py`:

1. `test_token_request_returns_token` - Create a mock event with
   `rawPath="/production/token"`, `method="POST"`, and `queryStringParameters={"user_id": "test"}`.
   Call `lambda_handler(event, context)`. Assert response status is 200 and body contains
   `token` and `endpoint` keys.
1. `test_token_request_missing_user_id` - Same but without `user_id` in query params.
   Assert 400 response.
1. `test_token_request_cors_headers` - Assert CORS headers are present on the response.

Mock `settings.GEMINI_API_KEY` to a test value like `"test-gemini-key"`.

```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_lambda_handler.py -v --tb=short -k "token"
```

**Commit Message Template:**

```text
feat(backend): add token exchange endpoint for Gemini Live API

- Add POST /token endpoint returning short-lived Gemini API token
- Include WebSocket endpoint URL in response
- Add CORS support and user_id validation
- Add unit tests for token endpoint
```

---

### Task 7: Update Existing Tests for Provider Swap

**Goal:** Update existing tests that assume OpenAI is the default TTS provider to account
for the Gemini-first provider configuration.

**Files to Modify:**

- `backend/tests/unit/test_lambda_handler.py` - Update provider expectations
- `backend/tests/unit/test_services.py` - Update if any tests reference default provider

**Prerequisites:** Tasks 2, 3 (Gemini is now default)

**Implementation Steps:**

1. Search `backend/tests/unit/` for any test that asserts the default TTS provider is OpenAI
   or creates a `LambdaHandler` and checks `tts_provider`. Update these to expect Gemini
   as the default.

1. The existing `test_handler_get_tts_provider` test in `test_lambda_handler.py` creates a
   handler and calls `get_tts_provider()`. This should still pass since it only checks
   `provider is not None`, but verify.

1. Any test that patches `OpenAITTSProvider` in `lambda_handler` imports will need to also
   patch `GeminiTTSProvider` since the handler now creates both providers in `__init__`.

1. Run the full test suite and fix any failures:

   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   ```

**Verification Checklist:**

- [x] All tests in `test_lambda_handler.py` pass
- [x] All tests in `test_services.py` pass
- [x] No test assumes OpenAI is the default TTS provider

**Testing Instructions:**

Run the full backend test suite:

```bash
cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
```

Also run lint to catch any import issues:

```bash
cd backend && uvx ruff check .
```

**Commit Message Template:**

```text
test(backend): update tests for Gemini-first TTS provider

- Update provider assertions for Gemini as default
- Patch both GeminiTTSProvider and OpenAITTSProvider in handler tests
- Ensure all existing tests pass with new provider configuration
```

## Phase Verification

After completing all tasks, verify the entire phase:

1. **All backend tests pass:**

   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   ```

1. **Backend lint passes:**

   ```bash
   cd backend && uvx ruff check .
   ```

1. **Full check passes:**

   ```bash
   npm run check
   ```

1. **No regressions:** The frontend tests should be unaffected by backend-only changes.

### Known Limitations

- The Gemini TTS model `gemini-2.5-flash-preview-tts` is in preview and may change
- If Gemini TTS does not support MP3 output directly, a PCM-to-MP3 conversion step will
  be needed (document this finding and update the plan)
- The token endpoint security model depends on what Google provides for ephemeral tokens.
  If only raw API key forwarding is possible, this is a known security limitation for MVP
- The voice choice ("Kore") is a starting point; voice evaluation is deferred
