# Phase 4: Implementer -- Architecture and Type Rigor [IMPLEMENTER]

## Phase Goal

Decompose the two largest files in the backend (`lambda_handler.py` at 756
lines and `ffmpeg_audio_service.py` at 805 lines) into smaller,
single-responsibility modules. Collapse the dual-validation pattern between
`request_validation_middleware` and the Pydantic models. Trim
`BackendMeditationCall.tsx` (427 lines). Tighten typing on the dictionary-based
job-state and Lambda-event surfaces. Centralize the module-level constants
that the audit calls out as scattered.

This phase is the largest in the plan because the architectural decomposition
unlocks the type-rigor and pragmatism gains the eval calls out, but it has no
new behavior -- only structural reshaping.

**Success criteria**

- No backend file in `src/` exceeds 400 lines (Architecture pillar 7 -> 9)
- `LambdaHandler` is split into a thin handler facade plus dedicated
  domain handlers in `src/handlers/`
- `FFmpegAudioService` is split into a small orchestrator plus
  `MusicSelector`, `AudioMixer`, and `HlsEncoder` collaborators
- Dual validation between `request_validation_middleware` and Pydantic is
  collapsed (the middleware delegates to Pydantic for `user_id` /
  `inference_type` checks)
- `BackendMeditationCall.tsx` is split into a hook plus a view; total file
  size for the original is under 200 lines
- Job-state dict has a `TypedDict` definition used everywhere
- Module-level constants in `lambda_handler.py:47-65` move to
  `src/config/constants.py`
- `npm run check` passes
- Estimated tokens: ~22000

## Prerequisites

- Phases 1, 2, 3 complete and merged
- `npm run check` passes on the merged tree

## Tasks

### Task 1: Decompose `LambdaHandler` god object

**Goal:** `LambdaHandler` (756 lines, 8 services) is the structural risk
called out by both the health audit and the eval. Split it into a thin
facade that constructs services and routes, plus dedicated domain
handlers for summary, meditation, job-status, and download.

**Files to Create:**

- `backend/src/handlers/summary_handler.py` -- `SummaryHandler` class with
  `handle(request: SummaryRequestModel) -> dict`. Owns
  `_store_summary_results`.
- `backend/src/handlers/meditation_handler.py` -- `MeditationHandler` class
  with `handle(request: MeditationRequestModel) -> dict`,
  `process_async(job_id, request_dict)`, `_process_base64`, `_process_hls`,
  `_mark_job_failed` (introduced in Phase 3 Task 4), and the retry logic.
  This is the largest extracted file.
- `backend/src/handlers/job_handler.py` -- `JobHandler` class with
  `handle_status(user_id, job_id)`, `handle_download(user_id, job_id)`,
  `_authorize` (already extracted in Phase 2 Task 2).
- `backend/src/handlers/router.py` -- the dispatch table from Phase 2 Task 3,
  the helper closures, and the top-level `lambda_handler(event, context)`
  entry point.

**Files to Modify:**

- `backend/src/handlers/lambda_handler.py` -- becomes a thin shim that
  re-exports `lambda_handler` from `router.py` and constructs the global
  `_handler` instance via `_get_handler()`. Total target: under 100 lines.
- `backend/lambda_function.py` -- already imports `lambda_handler` from
  `src.handlers.lambda_handler`; verify the re-export still works.
- `backend/tests/unit/test_lambda_handler.py` -- existing test names are kept
  for backward compatibility; tests that exercise extracted helpers move to
  `test_summary_handler.py`, `test_meditation_handler.py`, `test_job_handler.py`,
  `test_router.py`.

**Prerequisites:** Phase 2 Task 3 (dispatch table already exists; this task
moves it into a dedicated module).

**Implementation Steps:**

- Read `lambda_handler.py` end-to-end and identify the boundary lines for
  each extracted handler. Build a one-page mapping table of method ->
  destination file BEFORE making any cuts.
- Move methods one handler class at a time. After each move, run
  `pytest backend/tests/unit -v` and fix import errors before proceeding.
- The shared `_create_ai_service`, `get_tts_provider`,
  `_generate_meditation_audio`, `_ensure_input_data_is_dict` helpers belong on
  `MeditationHandler`. Keep `_handler` global facade but make it construct
  the four domain handlers and expose them as attributes:
  ```python
  class LambdaHandler:
      def __init__(self, ...):
          self.summary = SummaryHandler(self.ai_service, self.storage_service)
          self.meditation = MeditationHandler(...)
          self.jobs = JobHandler(self.job_service, self.hls_service, self.download_service)
  ```
- The legacy `LambdaHandler.handle_summary_request`,
  `LambdaHandler.handle_meditation_request` etc become thin delegations:
  ```python
  def handle_summary_request(self, request):
      return self.summary.handle(request)
  ```
  This preserves the public surface so existing tests don't break.
- Each extracted handler file MUST be under 400 lines. Verify with
  `wc -l backend/src/handlers/*.py` after the split.

**Verification Checklist:**

- [ ] `wc -l backend/src/handlers/lambda_handler.py` shows under 100 lines
- [ ] `wc -l backend/src/handlers/meditation_handler.py` shows under 400 lines
- [ ] `wc -l backend/src/handlers/summary_handler.py` shows under 200 lines
- [ ] `wc -l backend/src/handlers/job_handler.py` shows under 200 lines
- [ ] `wc -l backend/src/handlers/router.py` shows under 200 lines
- [ ] `pytest backend/tests/unit -v` passes
- [ ] `pytest backend/tests/integration -v` passes (if applicable in this env)
- [ ] `npm run check` passes
- [ ] `backend/lambda_function.py` still imports from
      `src.handlers.lambda_handler` and the import resolves

**Testing Instructions:**

- The existing tests should largely pass unchanged because the shim
  preserves the public surface. Where a test imports a private helper,
  update the import to the new module and add a comment explaining the move.
- Add a `test_router_dispatch.py` that asserts each route shape from Phase 2
  Task 3 still resolves correctly.

**Commit Message Template:**

```text
refactor(backend): split LambdaHandler god object into domain handlers

- summary_handler.py: SummaryHandler.handle()
- meditation_handler.py: MeditationHandler with sync/async/HLS variants
- job_handler.py: JobHandler with status and download
- router.py: dispatch table + lambda_handler entry point
- lambda_handler.py becomes a thin facade re-exporting the entry point
```

---

### Task 2: Decompose `FFmpegAudioService`

**Goal:** `ffmpeg_audio_service.py` (805 lines, post-Phase-3 deletions) mixes
FFmpeg CLI construction, temp-file lifecycle, S3 interaction, threading, music
selection, and duration probing. Split into:

- `MusicSelector` -- the existing `select_background_music` and
  `_extract_last_numeric_value` plus the cache integration
- `AudioMixer` -- `_prepare_mixed_audio` (the 5 subprocess steps) and
  `combine_voice_and_music`
- `HlsBatchEncoder` -- `combine_voice_and_music_hls` (cached-TTS path)
- `HlsStreamEncoder` -- `process_stream_to_hls` and `_append_fade_segments`
- `FFmpegAudioService` -- thin facade that constructs and delegates

**Files to Create:**

- `backend/src/services/audio/__init__.py`
- `backend/src/services/audio/music_selector.py`
- `backend/src/services/audio/audio_mixer.py`
- `backend/src/services/audio/hls_batch_encoder.py`
- `backend/src/services/audio/hls_stream_encoder.py`
- `backend/src/services/audio/duration_probe.py` -- `get_audio_duration`
  helper, called by all four

**Files to Modify:**

- `backend/src/services/ffmpeg_audio_service.py` -- becomes a thin facade
  under 150 lines that constructs the four collaborators and delegates the
  public methods (so the rest of the app keeps importing
  `FFmpegAudioService`)
- `backend/tests/unit/test_ffmpeg_audio_service.py` -- split into
  `test_music_selector.py`, `test_audio_mixer.py`, `test_hls_batch_encoder.py`,
  `test_hls_stream_encoder.py`. Existing tests move where their target moved.

**Prerequisites:** Phase 3 Tasks 1-3 (the streaming code is in its
post-thread-safety shape).

**Implementation Steps:**

- Read `ffmpeg_audio_service.py` and group methods by collaborator.
- The temp-file cleanup pattern (3 near-identical `try/except OSError: pass`
  blocks) collapses into a single helper in `audio_mixer.py`:
  ```python
  def _cleanup_paths(*paths: str) -> None:
      for path in paths:
          if path and os.path.exists(path):
              try:
                  os.remove(path)
              except OSError as e:
                  logger.debug("Failed to clean temp file", extra={"data": {"path": path, "error": str(e)}})
  ```
- Each new module imports `get_audio_duration` from `duration_probe.py`.
- The thread-safe `_StreamState` dataclass introduced in Phase 3 Task 1 moves
  into `hls_stream_encoder.py`.
- The facade keeps the existing constructor signature
  (`FFmpegAudioService(storage_service, hls_service)`) so the rest of the app
  is unchanged.
- Verify `wc -l` on every new file.

**Verification Checklist:**

- [ ] `wc -l backend/src/services/audio/*.py` shows every file under 350 lines
- [ ] `wc -l backend/src/services/ffmpeg_audio_service.py` shows under 150
- [ ] All existing tests pass
- [ ] No new public API surface added; the facade keeps the same method names
- [ ] Three duplicated `try/except OSError: pass` blocks collapse to one
- [ ] `npm run check` passes

**Testing Instructions:**

- `pytest backend/tests/unit/test_audio_mixer.py -v`
- `pytest backend/tests/unit/test_music_selector.py -v`
- `pytest backend/tests/unit/test_hls_*.py -v`

**Commit Message Template:**

```text
refactor(backend): split FFmpegAudioService into focused collaborators

- audio/music_selector.py: background music pick + cache
- audio/audio_mixer.py: combine_voice_and_music + _prepare_mixed_audio
- audio/hls_batch_encoder.py: cached-TTS HLS path
- audio/hls_stream_encoder.py: streaming TTS-to-HLS pipeline
- audio/duration_probe.py: shared get_audio_duration helper
- ffmpeg_audio_service.py becomes a thin facade
```

---

### Task 3: Collapse dual validation and tighten event/job typing

**Goal:** The eval and the audit both call out two related issues:

1. `request_validation_middleware` (lines 118-147 in
   `backend/src/handlers/middleware.py`) checks for `user_id` and
   `inference_type` *before* Pydantic validates them. Pydantic re-checks
   the same fields. The two checks have subtly different error messages.
2. `Dict[str, Any]` job state and untyped `event: Dict[str, Any]` make every
   `job_data.get("streaming", {}).get(...)` call a typing escape hatch.

This task collapses (1) into a single Pydantic-only check and adds
`TypedDict` definitions for (2).

**Files to Create:**

- `backend/src/models/job_state.py` -- `TypedDict` definitions for
  `JobData`, `StreamingState`, `DownloadState`. Used by `JobService` and the
  meditation handler.
- `backend/src/models/lambda_event.py` -- `TypedDict` for the AWS Lambda Function
  URL event shape (only the fields the code reads:
  `rawPath`, `requestContext.http.method`, `queryStringParameters`,
  `pathParameters`, `body`, `_async_meditation`, `job_id`, `request`).

**Files to Modify:**

- `backend/src/handlers/middleware.py` -- `request_validation_middleware`
  becomes a no-op delegation OR is removed entirely. The Pydantic
  `parse_request_body` already raises `ValidationError` with `MISSING_FIELD`
  codes, which `error_handling_middleware` already converts to 400.
- `backend/src/handlers/lambda_handler.py` (post-Task 1: now `router.py` etc) --
  remove `request_validation_middleware` from the middleware stack at line
  536-543
- `backend/src/services/job_service.py` -- annotate
  `Dict[str, Any]` returns as `JobData`
- `backend/src/handlers/meditation_handler.py` (post-Task 1) -- type
  `job_data` parameters as `JobData`, narrowing the chained `.get` calls
- `backend/tests/unit/test_middleware.py` -- update tests that asserted on
  the deprecated `request_validation_middleware` error messages

**Prerequisites:** Tasks 1 and 2 (handler decomposition complete).

**Implementation Steps:**

- Define the TypedDicts:
  ```python
  from typing import TypedDict, NotRequired, Optional, List

  class StreamingState(TypedDict, total=False):
      enabled: bool
      playlist_url: Optional[str]
      segments_completed: int
      segments_total: Optional[int]
      started_at: Optional[str]

  class DownloadState(TypedDict, total=False):
      available: bool
      url: Optional[str]
      downloaded: bool

  class JobData(TypedDict, total=False):
      job_id: str
      user_id: str
      job_type: str
      status: str
      created_at: str
      updated_at: str
      expires_at: str
      result: Optional[dict]
      error: Optional[str]
      streaming: StreamingState
      download: DownloadState
      tts_cache_key: Optional[str]
      generation_attempt: int
  ```
- The Lambda event TypedDict is a `total=False` shape covering only the
  read paths.
- For the middleware change, prove the Pydantic path covers every existing
  validation case by adding tests asserting:
  - missing `user_id` -> 400 with code `MISSING_FIELD`
  - missing `inference_type` -> 400 with code `MISSING_FIELD`
  - invalid `inference_type` value -> 400 with code `INVALID_INFERENCE_TYPE`
- Remove `request_validation_middleware` from the middleware decorator stack.
  Keep the function exported (deprecate via docstring) for one release in case
  any test or external caller imports it. A subsequent plan can delete it.
- Update `job_service.py` return annotations: `def get_job(...) -> Optional[JobData]:`.
- Update the meditation handler to read `job_data["streaming"]["started_at"]`
  via `Optional` checks once instead of chained `.get({}).get()`.

**Verification Checklist:**

- [ ] `request_validation_middleware` is no longer in the middleware stack
- [ ] All existing 400 tests still pass with the new error messages
- [ ] `JobData` TypedDict is imported and used in `JobService` and the
      meditation handler
- [ ] `mypy backend/src/services/job_service.py` (if mypy is run) reports no
      new errors
- [ ] `npm run check` passes

**Testing Instructions:**

- `pytest backend/tests/unit/test_middleware.py -v`
- `pytest backend/tests/unit/test_job_service.py -v`

**Commit Message Template:**

```text
refactor(backend): collapse dual validation; add TypedDicts for job state

- request_validation_middleware duplicated Pydantic checks; remove from stack
- Pydantic now owns user_id / inference_type validation end-to-end
- Add JobData / StreamingState / DownloadState TypedDicts
- Type job_service and meditation handler return annotations
```

---

### Task 4: Trim `BackendMeditationCall.tsx` and centralize backend constants

**Goal:** Two unrelated cleanups bundled because they are small:

1. `frontend/components/BackendMeditationCall.tsx` is 427 lines -- the eval
   calls it out as a code-quality concern. Extract polling and lifecycle into
   a `useMeditationGeneration` hook; keep the component as a thin view.
2. `lambda_handler.py:47-65` (now in `router.py` post-Task 1) holds a
   mix of rate-limit state, feature flags, retry constants, and domain
   constants at module scope. Move all constants to
   `backend/src/config/constants.py` (where they belong per ADR-5 and the
   existing project pattern).

**Files to Create:**

- `frontend/hooks/useMeditationGeneration.ts` -- new hook that owns:
  - The polling loop (currently inline in `BackendMeditationCall.tsx`)
  - Job state transitions
  - Error handling and retry
  - Returns `{ status, jobId, playlistUrl, error, start, cancel }`

**Files to Modify:**

- `frontend/components/BackendMeditationCall.tsx` -- becomes a thin view that
  consumes the hook. Target: under 200 lines.
- `frontend/tests/unit/BackendMeditationCall-test.tsx` (if exists) -- update
  for the new shape; the polling tests move to a new hook test file
- `frontend/tests/unit/useMeditationGeneration-test.ts` -- new test file
- `backend/src/config/constants.py` -- add the migrated constants:
  - `ENABLE_HLS_STREAMING` (env-driven; this is currently in lambda_handler at
    line 53)
  - `MAX_GENERATION_ATTEMPTS = 3`
  - `TTS_WORDS_PER_MINUTE = 80`
  - `MUSIC_TRAILING_BUFFER_SECONDS = 90`
- `backend/src/handlers/router.py` (or wherever they end up after Task 1) --
  import the constants from `..config.constants` instead of redefining

**Prerequisites:** Task 1 (so `lambda_handler.py`/`router.py` boundary is
final) and Task 3 (so the type-rigor work is done).

**Implementation Steps:**

- Read `BackendMeditationCall.tsx` and identify which state lives in the
  component vs which is local-only. Polling, jobId tracking, playlistUrl,
  error -- these all belong in the hook.
- Extract step-by-step using the React Hook extraction pattern:
  - Move all `useState`/`useEffect`/`useCallback` blocks related to the
    backend call into the new hook
  - Return a typed object with the public surface
  - The component imports the hook and renders based on hook state
- For the backend constants, add them to `constants.py` and remove the
  module-level definitions in the handler. Update every import.
- The `_token_rate_limit` dict, if it survived Phase 2 Task 1, stays where it
  is (it is state, not a constant).
- Run `npm run check`.

**Verification Checklist:**

- [ ] `wc -l frontend/components/BackendMeditationCall.tsx` shows under 200
- [ ] `frontend/hooks/useMeditationGeneration.ts` exists and is tested
- [ ] `grep -n "TTS_WORDS_PER_MINUTE" backend/src/handlers/` returns import
      hits, not definition hits
- [ ] `grep -n "MAX_GENERATION_ATTEMPTS" backend/src/handlers/` shows the
      definition only in `constants.py`
- [ ] `npm run check` passes

**Testing Instructions:**

- `npm test -- --testPathPattern="useMeditationGeneration"`
- `npm test -- --testPathPattern="BackendMeditationCall"`
- `pytest backend/tests/unit -v`

**Commit Message Template:**

```text
refactor: extract useMeditationGeneration hook and centralize constants

- frontend: BackendMeditationCall splits into hook + view (427 -> <200 lines)
- backend: TTS_WORDS_PER_MINUTE, MUSIC_TRAILING_BUFFER_SECONDS,
  MAX_GENERATION_ATTEMPTS, ENABLE_HLS_STREAMING move to constants.py
```

---

## Phase Verification

After all four tasks land:

- [ ] No backend file in `backend/src/` exceeds 400 lines
      (`find backend/src -name '*.py' -exec wc -l {} + | sort -n | tail`)
- [ ] No frontend component file in `frontend/components/` exceeds 250 lines
      (excluding `Colors.ts`-style data files)
- [ ] `npm run check` passes
- [ ] All four CI jobs are green
- [ ] No regression in any existing test
- [ ] The public API surface (`POST /`, `GET /job/{id}`, `POST /job/{id}/download`)
      is unchanged

Known limitations after this phase:

- The S3-backed job state still has read-modify-write race risk on concurrent
  `update_streaming_progress` calls. Mitigation deferred to a DynamoDB plan.
- The fortifier guardrails to prevent regression of these splits do not exist
  yet -- Phase 5 adds them (max-file-size lint rule, mypy strict scoped to
  the new modules).
