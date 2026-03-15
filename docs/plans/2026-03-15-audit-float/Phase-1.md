# Phase 1: [HYGIENIST] Quick Wins, Dead Code Removal, and Hygiene Fixes

## Phase Goal

Remove dead code, fix trivial operational bugs, and clean up hygiene issues identified in the health audit. This phase covers all CRITICAL quick wins, dead code flagged with high Vulture confidence, unused error codes/exceptions, and low-effort hygiene fixes. No new code or abstractions are introduced -- only removal and minimal fixes.

**Success criteria:**
- All 3 quick wins from the audit are resolved
- Dead code modules (`color_utils.py`, `domain.py`) are removed
- Unused exception classes and error codes are removed
- Frontend hygiene issues (empty useEffect, deprecated imports) are fixed
- `npm run check` passes (lint + all tests)
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~20k

## Prerequisites

- Phase 0 read and understood
- Repository cloned, `npm install --legacy-peer-deps` completed
- Python environment with `pytest` and `ruff` available

---

## Tasks

### Task 1: Add `timeout` to `combine_voice_and_music()` subprocess calls

**Goal:** Fix CRITICAL operational debt -- five `subprocess.run()` calls in `combine_voice_and_music()` have no timeout, risking Lambda hangs. The constant `FFMPEG_STEP_TIMEOUT` already exists at line 37 and is used in `_prepare_mixed_audio()`.

**Files to Modify:**
- `backend/src/services/ffmpeg_audio_service.py` - Add `timeout=FFMPEG_STEP_TIMEOUT` to 5 subprocess calls

**Prerequisites:** None

**Implementation Steps:**
1. Open `backend/src/services/ffmpeg_audio_service.py`
2. Locate the `combine_voice_and_music()` method (lines ~84-188)
3. Find the 5 `subprocess.run()` calls at lines ~115, ~127, ~141, ~153, ~165
4. Add `timeout=FFMPEG_STEP_TIMEOUT,` to each call's keyword arguments, matching the style in `_prepare_mixed_audio()` (lines 356-420)
5. Also add `capture_output=True,` to each call to match the style in `_prepare_mixed_audio()`. This ensures stderr is captured rather than printed to Lambda logs

**Verification Checklist:**
- [x] All 5 `subprocess.run()` calls in `combine_voice_and_music()` have `timeout=FFMPEG_STEP_TIMEOUT`
- [x] All 5 calls also have `capture_output=True`
- [x] No other changes to the method
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [x] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run existing backend tests: `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- If any test mocks `subprocess.run` for `combine_voice_and_music`, verify the mock still matches (check `tests/unit/` for `combine_voice` references)

**Commit Message Template:**
```
fix(backend): add timeout to combine_voice_and_music subprocess calls

Add timeout=FFMPEG_STEP_TIMEOUT and capture_output=True to all 5
subprocess.run() calls in combine_voice_and_music(), matching the
pattern already used in _prepare_mixed_audio(). Prevents FFmpeg hangs
from consuming the full Lambda timeout.
```

---

### Task 2: Remove `traceback.print_exc()` from OpenAI TTS provider

**Goal:** Fix MEDIUM operational debt -- `traceback.print_exc()` writes to stderr outside the structured logger. The structured logger on line 49 already captures the error, and the `raise TTSError(...)` on line 51 includes `traceback.format_exc()` in its details.

**Files to Modify:**
- `backend/src/providers/openai_tts.py` - Remove line 50 (`traceback.print_exc()`)

**Prerequisites:** None

**Implementation Steps:**
1. Open `backend/src/providers/openai_tts.py`
2. Remove line 50: `traceback.print_exc()`
3. Check if the `traceback` import at the top of the file is still needed (it is -- `traceback.format_exc()` is used on line 53)
4. Apply the same fix in `backend/src/providers/gemini_tts.py` line 44: remove `traceback.print_exc()`. Also remove the `import traceback` on line 2 if `traceback` is no longer used anywhere in that file

**Verification Checklist:**
- [x] `traceback.print_exc()` removed from `openai_tts.py`
- [x] `traceback` import retained in `openai_tts.py` (still used by `format_exc()`)
- [x] `traceback.print_exc()` removed from `gemini_tts.py`
- [x] `import traceback` removed from `gemini_tts.py` if no longer used
- [x] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`

**Commit Message Template:**
```
chore(backend): remove traceback.print_exc() from TTS providers

Remove redundant traceback.print_exc() calls that bypass structured
logging. The structured logger already captures errors and the TTSError
includes the formatted traceback in its details.
```

---

### Task 3: Delete `backend/src/utils/color_utils.py`

**Goal:** Remove dead code module. All functions are flagged unused by Vulture. The module depends on `numpy` and `scipy` which are not in the Lambda deployment. No file in the backend imports `color_utils`.

**Files to Modify:**
- `backend/src/utils/color_utils.py` - DELETE this file

**Prerequisites:** None

**Implementation Steps:**
1. Verify no imports exist: search the entire `backend/` directory for `color_utils` (should find nothing)
2. Delete `backend/src/utils/color_utils.py`
3. Check if `backend/src/utils/__init__.py` re-exports anything from `color_utils` and remove if so

**Verification Checklist:**
- [x] No file in `backend/` imports from `color_utils`
- [x] `backend/src/utils/color_utils.py` is deleted
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [x] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`

**Commit Message Template:**
```
chore(backend): remove dead color_utils module

Delete color_utils.py which contains unused functions (confirmed by
Vulture) depending on numpy/scipy (not deployed to Lambda). No imports
of this module exist anywhere in the backend.
```

---

### Task 4: Delete `backend/src/models/domain.py`

**Goal:** Remove unused domain model layer. Vulture flags nearly every class/method as unused at 60% confidence. Verified: no file in `backend/` imports from `domain.py`. The codebase uses raw dicts throughout `lambda_handler.py` and `job_service.py`.

**Files to Modify:**
- `backend/src/models/domain.py` - DELETE this file

**Prerequisites:** None

**Implementation Steps:**
1. Verify no imports exist: search `backend/` for `from.*domain import` and `import.*domain` (should find nothing in production code)
2. Check if any test file imports from `domain.py` and handle accordingly
3. Delete `backend/src/models/domain.py`
4. Check if `backend/src/models/__init__.py` re-exports anything from `domain` and remove if so

**Verification Checklist:**
- [x] No file imports from `domain.py`
- [x] `backend/src/models/domain.py` is deleted
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [x] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`

**Commit Message Template:**
```
chore(backend): remove unused domain model layer

Delete domain.py which defines UserIncident, MeditationSession,
ProcessingJob and other models that are never imported or instantiated.
The codebase uses raw dicts for all data flow.
```

---

### Task 5: Remove unused exception classes and error codes

**Goal:** Clean up dead exception taxonomy entries. `StorageError` and `EncodingError` are defined but never raised. `MUSIC_LIST_TOO_LARGE` and `INVALID_DURATION` error codes are defined but never used.

**Files to Modify:**
- `backend/src/exceptions.py` - Remove unused classes and enum values

**Prerequisites:** None

**Implementation Steps:**
1. Search `backend/` for `StorageError` -- confirm it is only defined in `exceptions.py` and never raised/caught elsewhere
2. Search `backend/` for `EncodingError` -- confirm same
3. Search `backend/` for `MUSIC_LIST_TOO_LARGE` and `INVALID_DURATION` -- confirm only defined in the enum
4. Remove the `StorageError` class (lines 121-125)
5. Remove the `EncodingError` class (lines 149-155)
6. Remove `MUSIC_LIST_TOO_LARGE` and `INVALID_DURATION` from the `ErrorCode` enum (lines 23-24)

**Verification Checklist:**
- [x] `StorageError` class removed
- [x] `EncodingError` class removed
- [x] `MUSIC_LIST_TOO_LARGE` and `INVALID_DURATION` enum values removed
- [x] No remaining references to these names in `backend/`
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [x] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Search test files for references to the removed names in case tests import them

**Commit Message Template:**
```
chore(backend): remove unused exception classes and error codes

Remove StorageError and EncodingError (never raised) and
MUSIC_LIST_TOO_LARGE/INVALID_DURATION error codes (never referenced).
```

---

### Task 6: Remove empty `useEffect` and lint suppression in `explore.tsx`

**Goal:** Remove the no-op `useEffect` that tracks `width`/`height` changes with an empty body, and fix the adjacent `eslint-disable` suppression.

**Files to Modify:**
- `frontend/app/(tabs)/explore.tsx` - Remove empty useEffect, fix lint suppression

**Prerequisites:** None

**Implementation Steps:**
1. Open `frontend/app/(tabs)/explore.tsx`
2. Remove the empty useEffect at lines 284-286:
   ```tsx
   useEffect(() => {
     // This effect is intentionally empty to track width/height changes
   }, [width, height]);
   ```
3. For the adjacent effect (lines 288-291), remove the `eslint-disable-next-line` comment and add `colorChangeArrayOfArrays` awareness:
   ```tsx
   useEffect(() => {
     setRenderKey((prevKey) => prevKey + 1);
   }, [colorChangeArrayOfArrays]);
   ```
   The `setRenderKey` function from `useState` is a stable reference, so the exhaustive-deps rule should be satisfied with just `colorChangeArrayOfArrays`.

**Verification Checklist:**
- [x] Empty `useEffect` removed
- [x] `eslint-disable-next-line` comment removed
- [x] `npm run lint` passes
- [x] `npm test` passes

**Testing Instructions:**
- Run `npm run lint`
- Run `npm test`

**Commit Message Template:**
```
chore(frontend): remove empty useEffect and lint suppression in explore.tsx

Remove no-op useEffect that tracked width/height with an empty body.
Remove eslint-disable suppression for setRenderKey effect -- the
function reference is stable so exhaustive-deps is satisfied.
```

---

### Task 7: Fix deprecated `expo-permissions` in Notifications.tsx

**Goal:** Replace deprecated `expo-permissions` API with the per-module permission methods from `expo-notifications`. The `expo-permissions` package was deprecated in SDK 41.

**Files to Modify:**
- `frontend/components/Notifications.tsx` - Replace permission calls

**Prerequisites:** None

**Implementation Steps:**
1. Open `frontend/components/Notifications.tsx`
2. Remove the import: `import * as Permissions from 'expo-permissions';`
3. Replace the permission logic in `registerForPushNotificationsAsync()` (lines 49-53):

   **Before:**
   ```tsx
   const { status: existingStatus } = await Permissions.getAsync(Permissions.NOTIFICATIONS);
   let finalStatus = existingStatus;
   if (existingStatus !== 'granted') {
     const { status } = await Permissions.askAsync(Permissions.NOTIFICATIONS);
     finalStatus = status;
   }
   ```

   **After:**
   ```tsx
   const { status: existingStatus } = await Notifications.getPermissionsAsync();
   let finalStatus = existingStatus;
   if (existingStatus !== 'granted') {
     const { status } = await Notifications.requestPermissionsAsync();
     finalStatus = status;
   }
   ```

4. Replace `alert(...)` on line 56 with `console.warn(...)` since `alert()` provides poor UX on mobile and this is a non-critical notification. (Do NOT add a new UI component -- that would be additive. `console.warn` is the minimal fix.)

**Verification Checklist:**
- [x] `expo-permissions` import removed
- [x] Permission calls use `Notifications.getPermissionsAsync()` and `Notifications.requestPermissionsAsync()`
- [x] `alert()` replaced with `console.warn()`
- [x] `npm run lint` passes
- [x] `npm test` passes

**Testing Instructions:**
- Run `npm run lint`
- Run `npm test`
- Check `package.json` -- if `expo-permissions` is listed as a dependency, note it but do NOT remove it in this task (other files may use it; removal is a separate concern)

**Commit Message Template:**
```
chore(frontend): replace deprecated expo-permissions with expo-notifications API

Use Notifications.getPermissionsAsync() and requestPermissionsAsync()
instead of the deprecated Permissions.getAsync/askAsync from
expo-permissions (deprecated since SDK 41). Replace bare alert() with
console.warn().
```

---

## Phase Verification

After completing all 7 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```
   This runs frontend lint + TypeScript check + all Jest tests.

2. Run backend checks:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   cd backend && uvx ruff check .
   ```

3. Verify deleted files are gone:
   ```bash
   # These should return "No such file or directory"
   ls backend/src/utils/color_utils.py
   ls backend/src/models/domain.py
   ```

4. Verify no broken imports:
   ```bash
   cd backend && python -c "from src.handlers.lambda_handler import LambdaHandler; print('OK')"
   ```

All checks must pass before proceeding to Phase 2.
