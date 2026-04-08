# Phase 3: Implementer -- Streaming Pipeline and Job State [IMPLEMENTER]

## Phase Goal

Resolve the four HIGH operational findings in `ffmpeg_audio_service.py` and
`lambda_handler.py` that center on the streaming HLS pipeline:
shared mutable state across threads, the `os.path.exists` watcher liveness
signal, missing backpressure on the TTS-to-FFmpeg stdin pipe, and the
self-invoking retry loop that can ping-pong on `_save_job` failure. Also
replace the remaining raw `Exception` raises with domain-typed errors so the
middleware can categorize them.

**Success criteria**

- `process_stream_to_hls` uses a thread-safe state container (lock or
  thread-safe queue), no concurrent unsynchronized access to shared dicts
- The watcher loop terminates on a sentinel/event, not on directory existence
- The TTS streaming generator is fully drained (or explicitly closed) on
  `BrokenPipeError` and timeout paths
- The retry self-invoke does not fire when
  `increment_generation_attempt` raises
- All `raise Exception(...)` calls in product code (`lambda_handler.py:237,
  290` and `ffmpeg_audio_service.py:199, 220, 557, 751, 761, 773`) are
  replaced with `AudioProcessingError`, `TTSError`, or `ExternalServiceError`.
  The `grep -rn "raise Exception(" backend/src/` verification gate is
  authoritative; the line list is a planning aid that may drift slightly.
- New unit tests cover the thread-safety, retry, and exception-type changes
- `npm run check` passes
- Estimated tokens: ~24000

## Prerequisites

- Phases 1 and 2 complete (clean baseline, validators in place, dispatch table
  routing)
- `npm run check` passes on the merged tree

## Tasks

### Task 1: Thread-safe state in `process_stream_to_hls`

**Goal:** `process_stream_to_hls` (lines 568-805 in
`backend/src/services/ffmpeg_audio_service.py`) shares a `state` dict and
an `uploaded_segments` set between the main thread and a watcher thread with
no locking. `state["segments_uploaded"]`, `state["segment_durations"]`, and
`uploaded_segments` are mutated concurrently. Audit health-finding HIGH.

**Files to Modify:**

- `backend/src/services/ffmpeg_audio_service.py` -- replace the bare `state`
  dict with a class-scoped helper that wraps a `threading.Lock`
- `backend/tests/unit/test_services.py` -- add a thread-safety test that
  drives `process_stream_to_hls` with a synthetic generator and a fake
  `hls_service`. NOTE: there is no `test_ffmpeg_audio_service.py` file in
  this repo; the FFmpeg service tests live in `test_services.py` (the same
  1473-line file that the health audit calls out as a structural outlier).
  Add the new test class/function inline in `test_services.py`; do NOT
  create a new test file in this phase (that split is part of Phase 4
  Task 2).

**Prerequisites:** None inside this phase.

**Implementation Steps:**

- Introduce a small private dataclass at module scope:
  ```python
  @dataclass
  class _StreamState:
      lock: threading.Lock = field(default_factory=threading.Lock)
      uploading: bool = True
      segments_uploaded: int = 0
      segment_durations: List[float] = field(default_factory=list)
      uploaded_segments: Set[str] = field(default_factory=set)
      error: Optional[BaseException] = None
      done: threading.Event = field(default_factory=threading.Event)

      def stop(self) -> None:
          with self.lock:
              self.uploading = False
          self.done.set()
  ```
- Replace the local `state` dict and `uploaded_segments` set with a single
  `_StreamState` instance.
- Every read or write of mutable fields acquires `state.lock`. The
  `done` event is the cross-thread terminator -- the watcher waits on it
  with a short timeout instead of polling `os.path.exists`.
- The watcher's `if state["error"]` check becomes a locked read.
- The main thread calls `state.stop()` in `finally` (replacing the previous
  `state["uploading"] = False`).
- The watcher thread joins via `watcher_thread.join(timeout=30)` exactly as
  before.
- Add a unit test:
  ```python
  def test_process_stream_to_hls_handles_concurrent_segment_uploads(
      ffmpeg_service, mock_hls_service, tmp_path
  ):
      """Drive process_stream_to_hls with a fake generator and a fake hls_service
      that records upload calls. Assert no AssertionError or KeyError, and
      that uploaded segment count matches what the watcher saw."""
  ```
- Mock `subprocess.Popen` to return a fake process whose
  `stdin.write` accepts bytes and whose `stdout`/`stderr` are queues.
- The test does not need a real FFmpeg; simulate segment file appearance by
  having the fake process create files in the tmp directory at intervals.

**Verification Checklist:**

- [ ] No bare `state["..."]` accesses remain inside `process_stream_to_hls`
- [ ] Every shared-state access is inside `with state.lock:`
- [ ] The watcher loop terminates on `state.done.wait(timeout=...)` not on
      `os.path.exists(hls_output_dir)`
- [ ] New thread-safety test passes
- [ ] `npm run check` passes

**Testing Instructions:**

- Run `pytest backend/tests/unit/test_services.py -v -k stream`.

**Commit Message Template:**

```text
fix(backend): make process_stream_to_hls state thread-safe

- Replace shared state dict with locked _StreamState dataclass
- Watcher terminates on threading.Event, not os.path.exists polling
- Add thread-safety unit test using a synthetic voice generator
```

---

### Task 2: Replace watcher liveness signal

**Goal:** The watcher loop condition
`while state["uploading"] or os.path.exists(hls_output_dir):` (line 681) uses
directory existence as a liveness signal. Since `shutil.rmtree` only happens
at line 803 after `watcher_thread.join`, the condition can spin indefinitely
if the main thread is blocked. This task is the runtime-loop counterpart of
Task 1's state-container change.

**Files to Modify:**

- `backend/src/services/ffmpeg_audio_service.py` -- adjust the
  `upload_watcher` loop to use `state.done.wait(timeout=0.3)`
  instead of `time.sleep(0.3)` and `os.path.exists`

**Prerequisites:** Task 1 (the `_StreamState` dataclass with `done` event must
exist).

**Implementation Steps:**

- Rewrite the loop body:
  ```python
  while True:
      try:
          # ... existing scan/upload logic, with locked state access ...
          if state.done.wait(timeout=0.3):
              # Final pass to drain any segments that landed after stop()
              ...
              break
      except Exception as e:
          with state.lock:
              state.error = e
          break
  ```
- After the watcher exits, the main thread proceeds to the fade-segment
  append. No `os.path.exists` check on `hls_output_dir` is necessary -- the
  directory is owned by this function and only deleted at the very end.

**Verification Checklist:**

- [ ] `os.path.exists(hls_output_dir)` no longer appears in the watcher loop
      condition
- [ ] `time.sleep(0.3)` is replaced by `state.done.wait(timeout=0.3)`
- [ ] The Task 1 thread-safety test still passes after this change
- [ ] `npm run check` passes

**Testing Instructions:**

- Existing test from Task 1 covers this. Add an explicit assertion that the
  watcher exits within (timeout + small grace) once `state.stop()` is called.

**Commit Message Template:**

```text
fix(backend): use threading.Event to terminate HLS upload watcher

- Watcher previously polled os.path.exists which spun indefinitely if the
  main thread blocked before rmtree
- Replace with state.done.wait(timeout=0.3) and a final drain pass
```

---

### Task 3: Drain TTS generator on `BrokenPipeError`

**Goal:** `process.stdin.write(chunk)` inside the TTS generator loop has no
backpressure handling beyond `process.poll()`. `BrokenPipeError` is caught
but partial writes from the generator are not drained, leaving the TTS
provider connection open and leaking the iterator (lines 752-754, 770-773).

**Files to Modify:**

- `backend/src/services/ffmpeg_audio_service.py` -- update the streaming loop
  to:
  - Wrap the generator in a contextmanager that calls `.close()` (Python
    generators have a `.close()` method that triggers `GeneratorExit`)
  - On `BrokenPipeError` and on timeout, drain the remaining chunks (or
    explicitly close the generator) before raising
  - Replace raw `raise Exception(...)` with `AudioProcessingError` or
    `TTSError` (Task 5 covers the broader cleanup; this task does the
    streaming-specific ones)
- `backend/tests/unit/test_services.py` -- add a test that the generator is
  closed on simulated `BrokenPipeError`. (No `test_ffmpeg_audio_service.py`
  exists; tests live in `test_services.py`.)

**Prerequisites:** Tasks 1 and 2 (state container and watcher fix).

**Implementation Steps:**

- Use a try/finally around the streaming loop:
  ```python
  try:
      for chunk in voice_generator:
          if process.poll() is not None:
              ...
              raise AudioProcessingError("FFmpeg exited unexpectedly: ...")
          try:
              process.stdin.write(chunk)
              process.stdin.flush()
          except BrokenPipeError as e:
              # Stop pulling more chunks; the pipe is dead.
              raise AudioProcessingError("FFmpeg pipe closed mid-stream") from e
          voice_file.write(chunk)
  finally:
      # Best-effort generator cleanup (idempotent)
      close = getattr(voice_generator, "close", None)
      if callable(close):
          try:
              close()
          except Exception:
              logger.debug("voice_generator.close() raised; ignoring")
  ```
- The TTS provider implementations (`backend/src/providers/openai_tts.py`,
  `backend/src/providers/gemini_tts.py`) yield bytes from a `requests` stream;
  calling `.close()` on the generator releases the underlying HTTP connection.
- Add a test that constructs a generator that yields a few chunks then waits
  on a sentinel, simulates a `BrokenPipeError` from the fake `process.stdin`,
  and asserts that the generator's `close()` is called exactly once.

**Verification Checklist:**

- [ ] The streaming loop has a `finally:` block that closes the generator
- [ ] `BrokenPipeError` produces an `AudioProcessingError` (not raw `Exception`)
- [ ] New unit test confirms generator close on broken pipe
- [ ] `npm run check` passes

**Testing Instructions:**

- `pytest backend/tests/unit/test_services.py -v -k broken_pipe`.

**Commit Message Template:**

```text
fix(backend): drain TTS generator on BrokenPipeError in HLS stream

- voice_generator was leaked on broken-pipe and timeout paths
- Add try/finally closing the generator regardless of exception path
- Replace raw Exception with AudioProcessingError on stream failures
```

---

### Task 4: Tighten retry self-invoke loop

**Goal:** The retry block at `lambda_handler.py:407-442` self-invokes the
Lambda inside the exception handler of an already-self-invoked Lambda. A
failure during `increment_generation_attempt` can cause double-retries; a
failure during `_invoke_async_meditation` logs and falls through to mark as
failed, but the previously-enqueued async invocation may still execute.

**Files to Modify:**

- `backend/src/handlers/lambda_handler.py` -- restructure the retry block so
  that `increment_generation_attempt` is called BEFORE deciding whether to
  retry, and `_invoke_async_meditation` is the LAST thing in the try (so a
  failure cleanly falls through to the fail path)
- `backend/tests/unit/test_lambda_handler.py` -- add tests for:
  - retry succeeds when both `increment_generation_attempt` and
    `_invoke_async_meditation` succeed
  - retry does NOT fire when `increment_generation_attempt` raises
    `ExternalServiceError`
  - retry does NOT double-fire when `_invoke_async_meditation` raises after
    the counter increments

**Prerequisites:** None (independent of Task 1-3).

**Implementation Steps:**

- The current code (lines 414-434):
  ```python
  if current_attempt < MAX_GENERATION_ATTEMPTS:
      self.job_service.increment_generation_attempt(...)  # may raise
      logger.info("Retrying ...")
      try:
          self._invoke_async_meditation(request, job_id)
          return
      except Exception as invoke_error:
          logger.error(...)
          # Fall through to mark as failed
  ```
- Refactor so `increment_generation_attempt` is inside its own try, and a
  failure marks the job as failed without triggering retry:
  ```python
  if current_attempt >= MAX_GENERATION_ATTEMPTS:
      self._mark_job_failed(request, job_id, e, MAX_GENERATION_ATTEMPTS)
      return

  try:
      self.job_service.increment_generation_attempt(request.user_id, job_id)
  except Exception as inc_error:
      logger.error("Failed to increment generation attempt; not retrying",
                   extra={"data": {"job_id": job_id, "error": str(inc_error)}})
      self._mark_job_failed(request, job_id, e, current_attempt)
      return

  try:
      self._invoke_async_meditation(request, job_id)
  except Exception as invoke_error:
      logger.error("Failed to invoke retry; marking failed",
                   extra={"data": {"job_id": job_id, "error": str(invoke_error)}})
      self._mark_job_failed(request, job_id, e, current_attempt + 1)
  ```
- Extract `_mark_job_failed` as a private helper to deduplicate the failure
  paths.
- The original concern (`_invoke_async_meditation` enqueues an async call that
  still executes after the local mark-as-failed) cannot be fully prevented
  without idempotency on the async side. Document this in a code comment and
  rely on the consumer-side check that the job already exists. This is the
  best mitigation without a queue redesign.
- Add tests using `mock.patch` on `JobService.increment_generation_attempt`
  and `_invoke_async_meditation`.

**Verification Checklist:**

- [ ] `_mark_job_failed` exists as a single helper used by all failure paths
- [ ] No retry fires when `increment_generation_attempt` raises
- [ ] Test `test_retry_does_not_fire_on_increment_failure` passes
- [ ] Test `test_retry_marks_failed_on_invoke_failure` passes
- [ ] Existing retry tests still pass
- [ ] `npm run check` passes

**Testing Instructions:**

- `pytest backend/tests/unit/test_lambda_handler.py -v -k retry`.

**Commit Message Template:**

```text
fix(backend): never retry HLS generation when counter increment fails

- Previously, if increment_generation_attempt raised, retry still fired
- Restructure retry so increment is checked first; on failure, mark failed
- Extract _mark_job_failed helper for deduplicated failure paths
```

---

### Task 5: Replace raw `Exception` raises with domain types

**Goal:** Audit health-finding HIGH calls out raw `raise Exception(...)` calls
that bypass the `exceptions.py` taxonomy. Convert each one and ensure the
middleware exception handler routes them correctly.

**Files to Modify:**

The full list of `raise Exception(...)` sites across `backend/src/` (verified
2026-04-08 via `grep -rn "raise Exception(" backend/src/`) is enumerated
below. The grep MUST return zero hits in product code after this task; treat
the grep as the source of truth and the explicit list as the planning aid.

- `backend/src/handlers/lambda_handler.py:237` -- replace
  `raise Exception("Failed to encode combined audio")` with
  `raise AudioProcessingError("Failed to encode combined audio", details=...)`
- `backend/src/handlers/lambda_handler.py:290` -- replace
  `raise Exception("Failed to download cached TTS audio")` with
  `raise ExternalServiceError("Failed to download cached TTS audio",
  ErrorCode.STORAGE_FAILURE, ...)`
- `backend/src/services/ffmpeg_audio_service.py:199` -- replace the wrapped
  multi-line `raise Exception(...)` (the FFmpeg HLS timeout site) with
  `raise AudioProcessingError("FFmpeg HLS generation timed out ...") from e`
- `backend/src/services/ffmpeg_audio_service.py:220` -- replace
  `raise Exception(f"Failed to upload segment {i}")` with
  `raise ExternalServiceError(f"Failed to upload segment {i}",
  ErrorCode.STORAGE_FAILURE, ...)`
- `backend/src/services/ffmpeg_audio_service.py:557` -- replace
  `raise Exception(f"Failed to upload fade segment {segment_index}")` with
  `raise ExternalServiceError(f"Failed to upload fade segment
  {segment_index}", ErrorCode.STORAGE_FAILURE, ...)`. (This site lives in
  `_append_fade_segments` and was missed in earlier drafts of this task.)
- `backend/src/services/ffmpeg_audio_service.py:751` -- replace
  `raise Exception(f"FFmpeg exited unexpectedly: {stderr}")` with
  `raise AudioProcessingError(f"FFmpeg exited unexpectedly: {stderr}")`
- `backend/src/services/ffmpeg_audio_service.py:761` -- replace
  `raise Exception(f"FFmpeg failed: {stderr}")` with
  `raise AudioProcessingError(f"FFmpeg failed: {stderr}")`
- `backend/src/services/ffmpeg_audio_service.py:773` -- covered by Task 3
  (`BrokenPipeError` handler) which already raises `AudioProcessingError`.
  Verify this site is no longer a `raise Exception` after Task 3 lands.
- `backend/src/services/hls_service.py` -- if any raw exceptions remain after
  the grep verification, fix them too
- `backend/tests/unit/test_lambda_handler.py` and
  `backend/tests/unit/test_services.py` (the FFmpeg service tests live here;
  there is NO `test_ffmpeg_audio_service.py` in this repo) -- update tests
  that catch bare `Exception` to assert the domain type

**Prerequisites:** Tasks 1-4 (so the touched files are in their final shape
for this phase).

**Implementation Steps:**

- Grep all `raise Exception(` in `backend/src/`:
  ```bash
  grep -rn "raise Exception(" backend/src/
  ```
- For each hit, choose:
  - Storage failure (S3 upload/download): `ExternalServiceError(...,
    ErrorCode.STORAGE_FAILURE, ...)`
  - FFmpeg subprocess failure: `AudioProcessingError(...)`
  - TTS provider failure: `TTSError(...)` (already handled in some places)
- Update the existing `try/except Exception` blocks where they catch the now-typed
  exceptions: most of them re-raise or log-and-fail, so behavior is preserved.
- Run the test suite. If a test asserts `with pytest.raises(Exception)`, narrow
  it to the new type.

**Verification Checklist:**

- [ ] `grep -rn "raise Exception(" backend/src/` returns 0 hits in product
      code (test files may still have `raise Exception` for fixtures and that
      is acceptable)
- [ ] Every replaced exception is a subclass of `FloatException`
- [ ] All existing tests pass after type updates
- [ ] `npm run check` passes
- [ ] `error_handling_middleware` (Phase 2 Task 4) routes the new exceptions
      to the correct status code

**Testing Instructions:**

- `pytest backend/tests/unit -v` -- the existing test suite should catch
  any regressions.

**Commit Message Template:**

```text
refactor(backend): replace raw Exception raises with domain types

- lambda_handler.py:237 base64 encode failure -> AudioProcessingError
- ffmpeg_audio_service.py: 5 raw Exception sites -> AudioProcessingError
- hls_service.py: storage failures -> ExternalServiceError(STORAGE_FAILURE)
- Update tests that asserted on bare Exception
```

---

## Phase Verification

After all five tasks land:

- [ ] `grep -rn "raise Exception(" backend/src/` returns 0 hits
- [ ] `grep -rn 'state\["' backend/src/services/ffmpeg_audio_service.py`
      returns 0 hits inside `process_stream_to_hls`
- [ ] `grep -n "os.path.exists(hls_output_dir)" backend/src/services/ffmpeg_audio_service.py`
      returns no hits inside the watcher loop
- [ ] `_mark_job_failed` exists in `lambda_handler.py`
- [ ] All new tests pass
- [ ] `npm run check` passes

Known limitations after this phase:

- Job state is still S3-backed; race conditions on `update_streaming_progress`
  remain possible across concurrent retries. Mitigated but not eliminated.
- The `LambdaHandler` god object still exists -- Phase 4 splits it
- The `_prepare_mixed_audio` 5-subprocess pipeline is still monolithic --
  Phase 4 decomposes it
