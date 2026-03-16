# Phase 6: [STRUCTURAL] Test Value & Creativity

## Phase Goal

Improve test quality and address creativity findings. Address Test Value (7 -> 9) and Creativity (8 -> 9) pillar findings: replace the placeholder test, audit and trim conftest fixtures, add an end-to-end handler test, extract the magic TTS duration constant, and document the music selection logic.

**Success criteria:**
- Placeholder `expect(true).toBe(true)` replaced with real assertion
- Conftest fixtures audited — unused fixtures removed or justified
- One new handler integration test exercises `handle_request` without mocking the destination method
- Magic number `80` (words/min) extracted to a named constant
- `npm run check` passes
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~25k

## Prerequisites

- Phases 0-5 completed and verified
- All checks passing

---

## Tasks

### Task 1: Replace placeholder test with real assertion

**Goal:** `tests/frontend/unit/LocalFileLoadAndSave-test.tsx:63` contains `expect(true).toBe(true)` — a placeholder that tests nothing. The test is supposed to verify graceful error handling when `AsyncStorage.getItem` rejects. Replace it with a meaningful assertion.

**Files to Modify:**
- `tests/frontend/unit/LocalFileLoadAndSave-test.tsx` — Replace placeholder assertion

**Prerequisites:** None

**Implementation Steps:**

1. Open `tests/frontend/unit/LocalFileLoadAndSave-test.tsx`
2. Read the test at line 56-64:
   ```tsx
   it('should handle load errors gracefully', async () => {
     (AsyncStorage.getItem as jest.Mock).mockRejectedValue(new Error('Load failed'));

     renderHook(() => IncidentSave());

     await new Promise((resolve) => setTimeout(resolve, 100));
     // Should not crash
     expect(true).toBe(true);
   });
   ```
3. The test verifies that `IncidentSave()` doesn't throw when `AsyncStorage.getItem` fails. Before writing a replacement assertion, first determine what the hook actually returns under error conditions:

   a. Check what `IncidentSave` returns:
      ```bash
      grep -n "IncidentSave\|export" frontend/hooks/ --include="*.ts" --include="*.tsx" -r | head -10
      ```

   b. **Run the existing test** to see the current behavior:
      ```bash
      npm test -- --testPathPattern="LocalFileLoadAndSave" --verbose
      ```
      The test should pass (since `expect(true).toBe(true)` always passes). This confirms the test infrastructure works.

   c. **Temporarily modify the test** to observe `result.current` by adding a `console.log`:
      ```tsx
      it('should handle load errors gracefully', async () => {
        (AsyncStorage.getItem as jest.Mock).mockRejectedValue(new Error('Load failed'));
        const { result } = renderHook(() => IncidentSave());
        await new Promise((resolve) => setTimeout(resolve, 100));
        console.log('result.current under error:', result.current);
        expect(true).toBe(true); // temporary, will be replaced
      });
      ```
      Run the test again:
      ```bash
      npm test -- --testPathPattern="LocalFileLoadAndSave" --verbose
      ```
      Observe the logged value of `result.current`.

   d. **Write the assertion based on the observed value:**
      - If `result.current` is `null`, use `expect(result.current).toBeNull()`
      - If `result.current` is `undefined`, use `expect(result.current).toBeUndefined()`
      - If `result.current` is an object (e.g., with default/empty state), assert on its shape: `expect(result.current).toEqual(expectedDefaultValue)`
      - If `result.current` is a function or tuple, assert it is defined: `expect(result.current).toBeDefined()`

   e. Remove the `console.log` and replace the placeholder with the correct assertion. The key requirement: **no `expect(true).toBe(true)`**.

4. Run the test one final time to confirm it passes with the real assertion:
   ```bash
   npm test -- --testPathPattern="LocalFileLoadAndSave" --verbose
   ```

**Verification Checklist:**
- [ ] No `expect(true).toBe(true)` in the file
- [ ] Test asserts something meaningful about the hook's behavior under error
- [ ] `npm test -- --testPathPattern="LocalFileLoadAndSave"` passes
- [ ] `npm test` passes

**Testing Instructions:**
- Run `npm test -- --testPathPattern="LocalFileLoadAndSave"` to verify the specific test
- Run `npm test` to verify all tests pass

**Commit Message Template:**
```
test(frontend): replace placeholder assertion in LocalFileLoadAndSave test

Replace expect(true).toBe(true) with a real assertion that verifies
the hook returns null when AsyncStorage.getItem rejects, confirming
graceful error handling behavior.
```

---

### Task 2: Audit conftest for unused fixtures

**Goal:** The backend `conftest.py` has 20 fixtures. The eval notes "fixture bloat." Audit each fixture for usage and remove or relocate unused ones.

**Files to Modify:**
- `backend/tests/conftest.py` — Remove unused fixtures, relocate test-specific fixtures

**Prerequisites:** Phase 5 Task 2 complete (legacy request classes removed — fixtures using old classes need updating)

**Implementation Steps:**

1. For each fixture in `conftest.py`, search for usage in test files:
   ```bash
   for fixture in test_user_id mock_ai_service mock_storage_service mock_audio_service mock_tts_provider valid_summary_request valid_meditation_request invalid_summary_request mock_event_factory mock_lambda_context request_factory sample_sentiment_response sample_meditation_response sample_audio_data mock_s3_response mock_ffmpeg_output test_music_list test_input_data parametrized_requests mock_gemini_model; do
     count=$(grep -rn "$fixture" backend/tests/ --include="*.py" | grep -v conftest.py | wc -l)
     echo "$fixture: $count references"
   done
   ```

2. For fixtures with 0 references — delete them from conftest.py

3. For fixtures used by only 1 test file — move the fixture into that test file. This reduces conftest size and makes test dependencies explicit.

4. Keep in conftest only fixtures used by 2+ test files (these are genuinely shared)

5. **Note:** After Phase 5 Task 2, `SummaryRequest` and `MeditationRequest` imports will have changed. The `valid_summary_request` and `valid_meditation_request` fixtures must be updated to use the new Pydantic model classes. If they are unused, delete them instead.

6. Update the imports at the top of `conftest.py` to remove references to deleted classes.

**Verification Checklist:**
- [ ] Every remaining fixture in `conftest.py` is used by 2+ test files
- [ ] Single-use fixtures moved to their respective test files
- [ ] Unused fixtures deleted
- [ ] Imports updated (no `SummaryRequest`/`MeditationRequest` from legacy layer)
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Run `cd backend && PYTHONPATH=. pytest tests/ -v --tb=short` (include integration tests to catch fixture moves)

**Commit Message Template:**
```
test(backend): audit conftest fixtures, remove unused and relocate single-use

Remove N unused fixtures from conftest.py and move M single-use
fixtures to their respective test files. Reduces conftest from 20
fixtures to K shared fixtures.
```

---

### Task 3: Add end-to-end handler test

**Goal:** The eval notes that backend routing tests mock the handler method itself (`handle_summary_request`/`handle_meditation_request`) rather than testing through the full `handle_request` path. Add one test that exercises the full path from `handle_request` through middleware to actual handler logic (mocking only external services, not handler methods).

**Files to Modify:**
- `backend/tests/unit/test_lambda_handler.py` — Add end-to-end handler test

**Prerequisites:** Phase 5 Task 2 complete (request models updated)

**Implementation Steps:**

1. Open `backend/tests/unit/test_lambda_handler.py`
2. Read the existing test structure to understand the test class hierarchy and fixtures used

3. **Inspect the `LambdaHandler.__init__` signature** before writing the fixture. Run:
   ```bash
   grep -A 15 "class LambdaHandler" backend/src/handlers/lambda_handler.py | head -20
   ```
   As of this writing, the constructor is:
   ```python
   def __init__(self, ai_service: Optional[AIService] = None, validate_config: bool = True):
   ```
   This confirms it accepts `ai_service` and `validate_config` as keyword arguments. If the signature has changed since this plan was written, adapt the fixture below to match the actual constructor API.

4. Add a new test class at the end of the file:

   ```python
   class TestEndToEndSummaryFlow:
       """Test the full handle_request -> middleware -> handler path.

       Unlike other tests that mock handle_summary_request, these tests
       mock only external services (AI, storage) and let the full
       request flow execute.
       """

       @pytest.fixture
       def handler_with_mock_services(self, mock_ai_service):
           """Create handler with mocked external services but real routing."""
           # NOTE: Verify LambdaHandler.__init__ accepts these kwargs.
           # If the constructor signature differs, adapt accordingly.
           handler = LambdaHandler(ai_service=mock_ai_service, validate_config=False)
           handler.storage_service = MagicMock()
           handler.storage_service.upload_json.return_value = True
           return handler

       def test_summary_request_full_flow(self, handler_with_mock_services, mock_lambda_context):
           """Exercise the full handle_request path for a summary request."""
           event = {
               "httpMethod": "POST",
               "headers": {
                   "Content-Type": "application/json",
                   "Origin": "https://float-app.fun",
               },
               "body": json.dumps({
                   "inference_type": "summary",
                   "user_id": "test-user-e2e",
                   "prompt": "I had a stressful day",
                   "audio": "NotAvailable",
               }),
           }

           response = handler_with_mock_services.handle_request(event, mock_lambda_context)

           assert response["statusCode"] == 200
           body = json.loads(response["body"])
           assert "sentiment_label" in body
           assert "intensity" in body
           # Verify AI service was actually called (not mocked at handler level)
           handler_with_mock_services.ai_service.analyze_sentiment.assert_called_once()
   ```

5. Add the necessary imports at the top of the test file if not already present:
   ```python
   import json
   from unittest.mock import MagicMock
   ```

6. Verify the test passes by running it specifically:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit/test_lambda_handler.py::TestEndToEndSummaryFlow -v --tb=short
   ```

**Verification Checklist:**
- [ ] New test class `TestEndToEndSummaryFlow` added
- [ ] Test mocks only external services (AI, storage), not handler methods
- [ ] Test calls `handle_request` (the entry point) not `handle_summary_request`
- [ ] Test verifies response structure AND that the AI service was called
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit/test_lambda_handler.py -v --tb=short`

**Commit Message Template:**
```
test(backend): add end-to-end handler test for summary flow

Add TestEndToEndSummaryFlow that exercises the full handle_request ->
middleware -> handle_summary_request path, mocking only external
services (AI, storage). Verifies the request routing and response
structure without mocking handler methods themselves.
```

---

### Task 4: Extract magic TTS duration constant

**Goal:** The eval flags `word_count / 80` as a magic number in `lambda_handler.py:323`. Extract it to a named constant with documentation.

**Files to Modify:**
- `backend/src/handlers/lambda_handler.py` — Extract constant

**Prerequisites:** None

**Implementation Steps:**

1. Open `backend/src/handlers/lambda_handler.py`
2. Find line ~323:
   ```python
   estimated_tts_duration = (word_count / 80) * 60  # seconds
   ```
3. Add a named constant near the top of the file, after the existing constants (`ENABLE_HLS_STREAMING`, `MAX_GENERATION_ATTEMPTS`):
   ```python
   # Estimated TTS speaking rate for calm meditation voice with pauses.
   # Based on observation: meditation TTS averages ~80 words/minute
   # (slower than conversational ~150 wpm due to intentional pauses).
   TTS_WORDS_PER_MINUTE = 80
   ```
4. Replace line ~323:
   ```python
   # Before:
   estimated_tts_duration = (word_count / 80) * 60  # seconds
   # After:
   estimated_tts_duration = (word_count / TTS_WORDS_PER_MINUTE) * 60  # seconds
   ```

5. Also extract the `90` second buffer on the next line if present:
   ```python
   # Before:
   music_duration = estimated_tts_duration + 90  # Add 90s buffer for trailing music
   # After:
   MUSIC_TRAILING_BUFFER_SECONDS = 90
   music_duration = estimated_tts_duration + MUSIC_TRAILING_BUFFER_SECONDS
   ```
   Add `MUSIC_TRAILING_BUFFER_SECONDS` near `TTS_WORDS_PER_MINUTE`.

**Verification Checklist:**
- [ ] `TTS_WORDS_PER_MINUTE = 80` constant defined
- [ ] `MUSIC_TRAILING_BUFFER_SECONDS = 90` constant defined
- [ ] Magic numbers replaced with constants
- [ ] Constants have descriptive comments
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`

**Commit Message Template:**
```
chore(backend): extract magic TTS duration constants

Extract word_count/80 to TTS_WORDS_PER_MINUTE and 90s buffer to
MUSIC_TRAILING_BUFFER_SECONDS with documentation explaining the
values. Makes the meditation duration estimation logic self-documenting.
```

---

## Phase Verification

After completing all 4 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```

2. Run backend checks:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   cd backend && uvx ruff check .
   ```

3. Verify no placeholder tests:
   ```bash
   grep -rn "expect(true)" tests/ --include="*.tsx" --include="*.ts"
   # Should return nothing
   ```

4. Verify constants exist:
   ```bash
   grep -n "TTS_WORDS_PER_MINUTE\|MUSIC_TRAILING_BUFFER" backend/src/handlers/lambda_handler.py
   ```

All checks must pass before proceeding to Phase 7.
