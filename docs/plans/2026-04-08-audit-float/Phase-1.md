# Phase 1: Hygienist -- Quick Wins and Dead Data [HYGIENIST]

## Phase Goal

Subtractive cleanup of the largest, lowest-risk debt items that can land
without behavior change. This phase removes a 3888-line generated data file,
patches a known-CVE dependency, deletes debug `console.log` calls in shipped
code, consolidates duplicated helpers, and corrects minor logging-convention
violators.

**Success criteria**

- `frontend/constants/Colors.ts` is shrunk to a hand-written palette and
  consumers compile unchanged
- `backend/requirements.txt` and `backend/pyproject.toml` no longer report
  vulnerabilities under `pip-audit`
- No `console.log` calls remain in `frontend/components/HLSPlayer/` or
  `frontend/scripts/inject-seo.js`
- `gemini_service.py` and `ffmpeg_audio_service.py` use the project logging
  convention exclusively
- `_get_audio_duration_from_file` is removed; callers use `get_audio_duration`
- `boto3.client("lambda")` is reused at module scope instead of constructed per
  invocation
- `npm run check` passes
- Estimated tokens: ~18000

## Prerequisites

- Phase 0 read and understood (no implementation work)
- A clean working tree on the working branch
- `npm install --legacy-peer-deps` succeeds
- `cd backend && pip install -r requirements.txt -r requirements-dev.txt`
  succeeds

## Tasks

### Task 1: Replace generated `Colors.ts` with a hand-written palette

**Goal:** Eliminate the 3888-line `frontend/constants/Colors.ts`. The file is
a hand-enumerated array of hex gradients per emotion class. It dwarfs every
other source file in the repo, slows TypeScript compilation, and pollutes
diffs.

**Files to Modify:**

- `frontend/constants/Colors.ts` -- rewrite to a small file
- `frontend/components/IncidentColoring.tsx` -- consumer; verify it still
  compiles. Read it first, then preserve every public symbol it depends on.
- `frontend/tests/unit/IncidentColoring-test.tsx` (or whichever existing test
  imports `Colors.angry.one[0]`-style accessors, if any) -- update tests to
  match the new shape

**Prerequisites:** None inside this phase.

**Implementation Steps:**

- Read `Colors.ts` to enumerate the keys it currently exports (`Colors.angry`,
  `Colors.sad`, `Colors.happy`, `Colors.fearful`, `Colors.neutral`,
  `Colors.disgusted`, `Colors.surprised`, plus `Colors.light`/`Colors.dark`
  and the standalone tint constants).
- Read every consumer of `Colors`:
  ```bash
  grep -rn "from.*constants/Colors" frontend/
  grep -rn "Colors\." frontend/components frontend/app frontend/hooks
  ```
- Identify which gradient slots are actually consumed at runtime. Most consumers
  read `Colors.<emotion>.one[idx]` for a single index. Reduce each emotion to a
  short palette (3-7 colors) covering only the indices in use, with a single
  named array (e.g. `angry: { one: [...] }` may collapse to `angry: ['#...']`)
  IF the consumers permit; otherwise preserve the `.one` nesting and only trim
  the array length.
- Pick visually equivalent colors by sampling the original gradient at evenly
  spaced points. The goal is to keep the output looking the same; match within
  a small visual tolerance, not pixel-perfect.
- Add a top-of-file comment explaining the rewrite and pointing at this plan
  ID.
- Run the existing snapshot tests; update any baselines that change.

**Verification Checklist:**

- [x] `frontend/constants/Colors.ts` is under 200 lines
- [x] Every existing import of `Colors` resolves and compiles
- [x] `npm run lint` passes
- [x] `npm test` passes (snapshots may need updating)
- [x] No new `eslint-disable` comments introduced
- [x] Visually inspect at least one screen using `IncidentColoring` (note in PR
      description; do not gate on the manual check)

**Testing Instructions:**

- Existing snapshot/unit tests cover most consumers. Update snapshots only if
  they capture explicit hex strings.
- No new tests required; this is a data-shape preservation refactor.

**Commit Message Template:**

```text
chore(frontend): replace generated Colors.ts with hand-written palette

- Shrink frontend/constants/Colors.ts from 3888 to <200 lines
- Preserve the public Colors.<emotion>.one[] shape for compatibility
- Remove unused gradient stops; consumers read at most a few indices
```

---

### Task 2: Bump `requests` to address CVE-2024-47081 / CVE-2026-25645

**Goal:** Eliminate the two known vulnerabilities reported by `pip-audit`
against `requests==2.32.3`. The fix is in 2.33.0 per the audit report.

**Files to Modify:**

- `backend/requirements.txt` -- bump `requests`
- `backend/pyproject.toml` -- already pins `requests>=2.32.4`; tighten the
  floor to `>=2.33.0` to match CVE guidance
- `backend/uv.lock` -- regenerate if `uv` is in use locally; otherwise leave
  for the orchestrator

**Prerequisites:** None.

**Implementation Steps:**

- In `backend/requirements.txt`, change `requests>=2.32.0` to `requests>=2.33.0`.
- In `backend/pyproject.toml`, change `requests>=2.32.4` to `requests>=2.33.0`.
- Run `pip install -r backend/requirements.txt` locally to verify the upgrade
  resolves.
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` -- expected
  to pass; `requests` is used by HTTP clients and any test mocks should be
  unaffected by the patch bump.
- If `pip-audit` is installed locally, run it against
  `backend/requirements.txt` and confirm 0 vulnerabilities. (The Phase 5
  fortifier work adds this to CI; this task does not.)

**Verification Checklist:**

- [x] `backend/requirements.txt` lists `requests>=2.33.0`
- [x] `backend/pyproject.toml` lists `requests>=2.33.0`
- [x] `pip install -r backend/requirements.txt` succeeds
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes

**Testing Instructions:**

- Run the existing backend test suite. No new tests.

**Commit Message Template:**

```text
fix(backend): bump requests to >=2.33.0 to address CVE-2024-47081

- requests==2.32.3 has CVE-2024-47081 and CVE-2026-25645
- pip-audit reports both fixed in 2.33.0
- Update both requirements.txt and pyproject.toml floors
```

---

### Task 3: Remove `console.log` calls from shipped frontend code

**Goal:** Two `console.log` calls survive in shipped code paths
(`frontend/components/HLSPlayer/hlsPlayerHtml.ts:164` and
`frontend/scripts/inject-seo.js:61`). Convert them to warn/error or delete
them. Both are flagged by the project ESLint config (`no-console: ['warn',
{ allow: ['warn', 'error'] }]`).

**Files to Modify:**

- `frontend/components/HLSPlayer/hlsPlayerHtml.ts` -- remove or convert the
  network-retry log to `console.warn` (it is debugging output for an injected
  WebView script)
- `frontend/scripts/inject-seo.js` -- convert to `console.warn` or delete
  (this is a build-time script; `console.warn` is acceptable per ESLint config)

**Prerequisites:** None.

**Implementation Steps:**

- Read both files to confirm the call sites and surrounding intent.
- For `hlsPlayerHtml.ts`: this string is embedded in HTML injected into a
  WebView. Convert to `console.warn` (allowed) or delete.
- For `inject-seo.js`: convert the success message to `console.warn` so it
  remains visible during build. Confirm `inject-seo.js` is invoked by
  `frontend/package.json`'s `build:web` script.
- Run `npm run lint` to confirm the lint warning is gone.

**Verification Checklist:**

- [x] `grep -rn "console.log" frontend/` returns no hits in shipped paths
      (test fixtures may still contain logs and are out of scope)
- [x] `npm run lint` reports no `no-console` warnings on these files
- [x] `npm test` passes
- [x] HLS playback test (`useHLSPlayer-test.ts` or equivalent) still passes

**Testing Instructions:**

- Existing HLS player tests cover the injected script paths.
- No new tests required.

**Commit Message Template:**

```text
chore(frontend): remove debug console.log from shipped code

- HLSPlayer/hlsPlayerHtml.ts: convert network-retry log to console.warn
- scripts/inject-seo.js: convert success log to console.warn
- Both already flagged by ESLint no-console rule (allows warn/error)
```

---

### Task 4: Consolidate `_get_audio_duration_from_file` into `get_audio_duration`

**Goal:** Two near-identical helpers parse FFmpeg `Duration:` lines from
stderr. They differ only in timeout (120s vs 30s) and a trivial branch in
error handling. Keep the public method, delete the private duplicate.

**Files to Modify:**

- `backend/src/services/ffmpeg_audio_service.py` -- delete
  `_get_audio_duration_from_file` (lines 446-465); update the one caller in
  `_append_fade_segments` (line 486) to use `self.get_audio_duration(...)`.
- `backend/tests/unit/test_services.py` -- existing test file (this is where
  the FFmpeg service tests live; there is NO `test_ffmpeg_audio_service.py`
  in this repo). Update the FIVE `patch.object(service,
  "_get_audio_duration_from_file", ...)` sites at lines 1162, 1204, 1229,
  1252, and 1277. Each call must be retargeted to
  `patch.object(service, "get_audio_duration", ...)` (the public method).
  Verify with: `grep -n "_get_audio_duration_from_file"
  backend/tests/unit/test_services.py` -- this MUST return 0 hits after the
  edit.

**Prerequisites:** None.

**Implementation Steps:**

- Confirm the only caller of `_get_audio_duration_from_file` is line 486 in
  `_append_fade_segments`. Use grep:
  ```bash
  grep -rn "_get_audio_duration_from_file" backend/
  ```
- Replace the call with `self.get_audio_duration(music_path)`. The public
  method already returns `0.0` on failure, so the calling code's
  `if music_file_duration <= 0` guard still works.
- Delete the private method.
- The existing public method has a 120s timeout; the deleted private one had
  30s. Document this change in the commit message: the consolidated method
  uses the longer timeout, which is safe (probing is short in practice).
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`.

**Verification Checklist:**

- [x] `grep -rn "_get_audio_duration_from_file" backend/` returns 0 hits
- [x] `cd backend && uvx ruff check .` passes
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [x] No new test failures

**Testing Instructions:**

- Existing unit tests for `FFmpegAudioService` cover this code path indirectly
  via fade-segment tests.
- No new tests required.

**Commit Message Template:**

```text
chore(backend): consolidate audio-duration helpers in FFmpegAudioService

- Delete _get_audio_duration_from_file (duplicate of get_audio_duration)
- Update _append_fade_segments to call the public method
- Consolidated timeout is 120s (safe; probing is short)
```

---

### Task 5: Cache `boto3.client("lambda")` at module scope

**Goal:** `_invoke_async_meditation` constructs a fresh `boto3` client on every
invocation. AWS SDK clients are designed to be reused inside a warm Lambda --
each construction is dozens of ms and defeats connection pooling. Move the
client to module scope.

**Files to Modify:**

- `backend/src/handlers/lambda_handler.py` -- add module-level
  `_lambda_client = boto3.client("lambda")` (lazy via a helper if needed for
  test isolation), use it in `_invoke_async_meditation`
- `backend/tests/unit/test_lambda_handler.py` (or wherever
  `_invoke_async_meditation` is mocked) -- adjust mock target if necessary

**Prerequisites:** None.

**Implementation Steps:**

- Add a private helper `_get_lambda_client()` that lazily constructs the
  client on first call and caches it on the module:
  ```python
  _lambda_client = None
  def _get_lambda_client():
      global _lambda_client
      if _lambda_client is None:
          _lambda_client = boto3.client("lambda")
      return _lambda_client
  ```
- In `_invoke_async_meditation`, call `_get_lambda_client()` instead of
  `boto3.client("lambda")`.
- Update existing tests that mock `boto3.client` to mock `_get_lambda_client`
  or `_lambda_client` instead. If the existing tests use
  `mock.patch("boto3.client")`, leave them; the lazy init will still call
  `boto3.client` on first use.
- DO NOT change the call shape of `_invoke_async_meditation` -- this task
  preserves behavior.

**Verification Checklist:**

- [x] `_invoke_async_meditation` no longer calls `boto3.client(...)` directly
- [x] All existing `lambda_handler` tests pass
- [x] No new boto3 imports added at function scope

**Testing Instructions:**

- Existing tests must pass. If a test imports `lambda_handler` and inspects
  module attributes, ensure the lazy init does not break import.
- Optional: add one new unit test asserting `_get_lambda_client()` returns the
  same instance across calls.

**Commit Message Template:**

```text
perf(backend): cache boto3 lambda client at module scope

- _invoke_async_meditation constructed a fresh boto3 client every call
- Move to a lazy module-level _get_lambda_client() helper
- Preserves connection pooling across warm Lambda invocations
```

---

### Task 6: Logging-convention cleanups

**Goal:** Three small logging-convention violators that are pure hygiene:

1. `backend/src/services/gemini_service.py:16` uses
   `logging.getLogger(__name__)` directly instead of the project
   `get_logger(__name__)` helper.
2. `backend/src/services/ffmpeg_audio_service.py:83` uses an f-string log
   message with NO structured `extra={"data": ...}` payload. The project
   convention is `logger.warning("Error getting audio duration",
   extra={"data": {"error": str(e)}})`. The audit originally cited line 76,
   but on re-inspection line 76 (`logger.warning("No Duration line in ffmpeg
   output", extra={"data": {"file": file_path}})`) is already correct. The
   actual violator is line 83 (`logger.warning(f"Error getting audio
   duration: {e}")`), which must be rewritten to lift the `e` into a
   structured `extra={"data": ...}` payload.
3. `backend/src/exceptions.py:143` has a bare `pass` inside the `JobError`
   class (it should be a docstring).

**Files to Modify:**

- `backend/src/services/gemini_service.py` -- swap import
- `backend/src/services/ffmpeg_audio_service.py` -- pick one log style
- `backend/src/exceptions.py` -- replace `pass` with a docstring

**Prerequisites:** None.

**Implementation Steps:**

- In `gemini_service.py`:
  ```python
  # before
  import logging
  logger = logging.getLogger(__name__)
  # after
  from ..utils.logging_utils import get_logger
  logger = get_logger(__name__)
  ```
- In `ffmpeg_audio_service.py:83`, the existing call is:
  ```python
  except Exception as e:
      logger.warning(f"Error getting audio duration: {e}")
      return 0.0
  ```
  Rewrite to lift `e` into a structured payload (no f-string, use `extra=`):
  ```python
  except Exception as e:
      logger.warning(
          "Error getting audio duration",
          extra={"data": {"error": str(e)}},
      )
      return 0.0
  ```
  Note: line 76 of the same file (`logger.warning("No Duration line in
  ffmpeg output", extra={"data": {"file": file_path}})`) is already correct
  and MUST NOT be touched. The audit's original "line 76" citation is a
  drift artifact corrected here.
- In `exceptions.py:143`, replace:
  ```python
  class JobError(FloatException):
      """Base class for job-related errors."""

      pass
  ```
  with:
  ```python
  class JobError(FloatException):
      """Base class for job-related errors."""
  ```
  (The `pass` is unnecessary when a docstring is present.)

**Verification Checklist:**

- [x] `grep -n "logging.getLogger" backend/src/` returns 0 hits in product
      code (test code is allowed to use stdlib logging)
- [x] `cd backend && uvx ruff check .` passes
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes

**Testing Instructions:**

- Existing tests cover both modules. No new tests required.

**Commit Message Template:**

```text
chore(backend): align logging convention and tidy exceptions

- gemini_service.py: use get_logger() instead of logging.getLogger()
- exceptions.py: drop redundant pass inside docstring'd JobError
- (Optional) ffmpeg_audio_service.py: harmonise duration log
```

---

## Phase Verification

After all six tasks land:

- [x] `npm run check` passes (frontend lint + tests, backend ruff + pytest)
- [x] `pip-audit` against `backend/requirements.txt` reports 0 vulnerabilities
- [x] `frontend/constants/Colors.ts` is under 200 lines
- [x] `grep -rn "console.log" frontend/components frontend/scripts` returns 0
      hits
- [x] `grep -rn "_get_audio_duration_from_file" backend/` returns 0 hits
- [x] `grep -n "logging.getLogger" backend/src/` returns 0 hits
- [x] No behavior change observable in any existing test

Known limitations after this phase:

- The `LambdaHandler` god object remains -- Phase 4 addresses it
- The `/token` endpoint still leaks the API key -- Phase 2 Task 1 addresses it
- The streaming HLS pipeline still has thread-safety issues -- Phase 3
  addresses them
