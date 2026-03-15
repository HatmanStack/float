# Phase 2: [HYGIENIST] Critical & High Operational/Structural Fixes

## Phase Goal

Fix the remaining CRITICAL and HIGH findings that require more careful changes: S3 pagination, FFmpeg Popen timeout safety, frontend polling deduplication, and the unused lambda `c` variables. These are all subtractive or corrective changes -- no new abstractions, no new modules.

Items explicitly **deferred** (too large for health remediation, require dedicated feature work):
- HIGH #1: `lambda_handler.py` god module (681 lines) -- requires architectural refactor
- HIGH #3: `Colors.ts` (3888 lines) -- requires build-time generation or runtime computation
- HIGH #6: `job_service.py` S3 GET+PUT per segment -- requires caching layer design
- MEDIUM #6: `hls_service.py` leaky `StorageService` abstraction -- requires interface redesign

**Success criteria:**
- S3 `list_objects` uses pagination
- FFmpeg `Popen` in `process_stream_to_hls()` has a timeout mechanism
- Frontend polling functions are consolidated into one
- Unused `c` variables in lambda closures are replaced with `_`
- `npm run check` passes
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~25k

## Prerequisites

- Phase 1 completed and verified
- All Phase 1 checks passing

---

## Tasks

### Task 1: Add S3 pagination to `list_objects`

**Goal:** Fix CRITICAL architectural debt -- `list_objects_v2` returns max 1000 keys per response. Without pagination, music selection and job cleanup silently miss objects beyond that limit.

**Files to Modify:**
- `backend/src/services/s3_storage_service.py` - Add pagination loop to `list_objects()`

**Prerequisites:** Phase 1 complete

**Implementation Steps:**
1. Open `backend/src/services/s3_storage_service.py`
2. Modify the `list_objects()` method (lines 82-100) to use the `ContinuationToken` pagination pattern:

   Replace the current implementation with a paginated version:
   ```python
   def list_objects(self, bucket: str, prefix: Optional[str] = None) -> List[str]:
       try:
           kwargs = {"Bucket": bucket}
           if prefix:
               kwargs["Prefix"] = prefix
           keys = []
           while True:
               response = self.s3_client.list_objects_v2(**kwargs)
               if "Contents" in response:
                   keys.extend(obj["Key"] for obj in response["Contents"])
               if not response.get("IsTruncated"):
                   break
               kwargs["ContinuationToken"] = response["NextContinuationToken"]
           return keys
       except ClientError as e:
           logger.error(
               "Error listing objects",
               extra={"data": {"bucket": bucket, "error": str(e)}}
           )
           return []
       except Exception:
           logger.error("Unexpected error listing objects", exc_info=True)
           return []
   ```

3. The error handling structure stays the same -- just add the pagination loop inside the try block

**Verification Checklist:**
- [ ] `list_objects()` uses `IsTruncated` and `ContinuationToken` for pagination
- [ ] Error handling is preserved
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run existing backend tests: `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Search test files for `list_objects` to check if any tests mock the S3 response and need the mock updated to test pagination (add `IsTruncated: False` to existing mock responses if needed)

**Commit Message Template:**
```
fix(backend): add pagination to S3 list_objects

Use ContinuationToken pagination loop in list_objects() to handle
buckets with more than 1000 objects. Previously, results were silently
truncated at the S3 API limit.
```

---

### Task 2: Add timeout to FFmpeg Popen in `process_stream_to_hls()`

**Goal:** Fix HIGH operational debt -- the `Popen` process spawned in `process_stream_to_hls()` has no timeout. If the TTS generator stalls, FFmpeg hangs indefinitely, consuming the Lambda timeout.

**Files to Modify:**
- `backend/src/services/ffmpeg_audio_service.py` - Add timeout to `process.wait()` and kill on timeout

**Prerequisites:** Phase 1 complete

**Implementation Steps:**
1. Open `backend/src/services/ffmpeg_audio_service.py`
2. Locate `process_stream_to_hls()` -- find the `process.wait()` call (around line 759)
3. Add a timeout to `process.wait()`. The `FFMPEG_STEP_TIMEOUT` constant (120s) is too short for streaming which can take minutes. Use a longer timeout:

   At the top of the file near the other constants (around line 37), check if there's already a streaming timeout constant. If not, add one after `FFMPEG_STEP_TIMEOUT`:
   ```python
   FFMPEG_STREAM_TIMEOUT = 600  # 10 minutes for full streaming pipeline
   ```

4. Replace the bare `process.wait()` at line 759 with:
   ```python
   process.wait(timeout=FFMPEG_STREAM_TIMEOUT)
   ```

5. In the `except` block that handles exceptions (around lines 769-773), ensure `process.kill()` is called when the process is still running. The existing code already does `if process.poll() is None: process.kill()` -- verify this covers the `subprocess.TimeoutExpired` exception that `wait(timeout=...)` raises.

6. Add `subprocess.TimeoutExpired` to the except clause or ensure it's caught by the general `except Exception` block. Since `TimeoutExpired` is a subclass of `SubprocessError` which is a subclass of `Exception`, the existing `except Exception` block will catch it. But add a specific log message:

   Before the general `except Exception` block (line 769), add:
   ```python
   except subprocess.TimeoutExpired:
       logger.error(f"FFmpeg streaming process timed out after {FFMPEG_STREAM_TIMEOUT}s")
       process.kill()
       process.wait()  # Reap the process
       raise AudioProcessingError(f"FFmpeg streaming timed out after {FFMPEG_STREAM_TIMEOUT}s")
   ```

**Verification Checklist:**
- [ ] `FFMPEG_STREAM_TIMEOUT` constant defined
- [ ] `process.wait()` has `timeout=FFMPEG_STREAM_TIMEOUT`
- [ ] `subprocess.TimeoutExpired` is caught with a clear error message
- [ ] Process is killed and reaped on timeout
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Search test files for `process_stream_to_hls` to check if any tests need updating

**Commit Message Template:**
```
fix(backend): add timeout to FFmpeg streaming Popen process

Add FFMPEG_STREAM_TIMEOUT (600s) to process.wait() in
process_stream_to_hls(). Catches subprocess.TimeoutExpired to kill
and reap the process, preventing indefinite Lambda hangs from stalled
TTS streams.
```

---

### Task 3: Consolidate frontend polling functions

**Goal:** Fix HIGH structural debt -- three nearly identical polling functions (`pollJobStatusForStreaming`, `pollUntilComplete`, `pollJobStatus`) share ~200 lines of duplicated polling/fetch/error/backoff logic with minor behavioral differences.

**Files to Modify:**
- `frontend/components/BackendMeditationCall.tsx` - Consolidate into one generic poller

**Prerequisites:** Phase 1 complete

**Implementation Steps:**

1. Open `frontend/components/BackendMeditationCall.tsx`
2. Analyze the three polling functions (lines 107-312) to identify their differences:

   | Feature | `pollJobStatusForStreaming` | `pollUntilComplete` | `pollJobStatus` |
   |---------|---------------------------|--------------------|--------------------|
   | Abort signal | Yes | Yes | No |
   | onStatusUpdate callback | Yes | Yes | No |
   | Returns early on streaming | Yes (playlist_url) | No | No |
   | Returns on completed | Yes | Yes | Yes |
   | Returns on failed | Throws | Throws | Throws |

3. Create ONE private function that accepts configuration options:

   ```typescript
   interface PollOptions {
     jobId: string;
     userId: string;
     lambdaUrl: string;
     onStatusUpdate?: (status: JobStatusResponse) => void;
     signal?: AbortSignal;
     /** Return early when streaming playlist_url is available */
     returnOnStreaming?: boolean;
   }

   async function pollJobStatus(options: PollOptions): Promise<JobStatusResponse> {
     const { jobId, userId, lambdaUrl, onStatusUpdate, signal, returnOnStreaming = false } = options;
     const baseUrl = lambdaUrl.replace(/\/$/, '');
     const statusUrl = `${baseUrl}/job/${jobId}?user_id=${encodeURIComponent(userId)}`;

     const startTime = Date.now();
     let pollInterval = INITIAL_POLL_INTERVAL_MS;

     while (Date.now() - startTime < MAX_TOTAL_WAIT_MS) {
       if (signal?.aborted) {
         throw new DOMException('Polling cancelled', 'AbortError');
       }

       const fetchOptions: RequestInit = {
         method: 'GET',
         headers: { 'Content-Type': 'application/json' },
       };
       if (signal) {
         fetchOptions.signal = signal;
       }

       const response = await fetch(statusUrl, fetchOptions);

       if (!response.ok) {
         throw new Error(`Job status check failed with status ${response.status}`);
       }

       const jobData: JobStatusResponse = await response.json();
       onStatusUpdate?.(jobData);

       if (returnOnStreaming && jobData.streaming?.playlist_url) {
         return jobData;
       }

       if (jobData.status === 'completed') {
         return jobData;
       }

       if (jobData.status === 'failed') {
         const errorMsg = typeof jobData.error === 'string'
           ? jobData.error
           : jobData.error?.message || 'Meditation generation failed';
         throw new Error(errorMsg);
       }

       const elapsed = Date.now() - startTime;
       pollInterval = getNextPollInterval(elapsed);
       await new Promise<void>((resolve, reject) => {
         const timeout = setTimeout(resolve, pollInterval);
         if (signal) {
           signal.addEventListener('abort', () => {
             clearTimeout(timeout);
             reject(new DOMException('Polling cancelled', 'AbortError'));
           }, { once: true });
         }
       });
     }

     throw new Error('Meditation generation timed out');
   }
   ```

4. Delete `pollJobStatusForStreaming` (lines 107-169), `pollUntilComplete` (lines 177-233), and the old `pollJobStatus` (lines 270-312)

5. Update all call sites in the same file. Search for where these functions are called:
   - `pollJobStatusForStreaming(...)` calls become `pollJobStatus({ ..., returnOnStreaming: true })`
   - `pollUntilComplete(...)` calls become `pollJobStatus({ ... })` (no `returnOnStreaming`)
   - `pollJobStatus(...)` calls become `pollJobStatus({ ... })` (no signal, no callback)

6. Also delete `fetchDownloadUrl` only if it's unused -- search for its call sites first

**Verification Checklist:**
- [ ] Only ONE `pollJobStatus` function exists
- [ ] All three original call sites updated
- [ ] Abort signal support works for callers that pass it
- [ ] `returnOnStreaming` flag controls early return on playlist_url
- [ ] `npm run lint` passes
- [ ] `npm test` passes

**Testing Instructions:**
- Run `npm run lint`
- Run `npm test`
- Search test files for `pollJobStatus`, `pollUntilComplete`, `pollJobStatusForStreaming` to verify no test directly references the deleted functions

**Commit Message Template:**
```
chore(frontend): consolidate three polling functions into one

Replace pollJobStatusForStreaming, pollUntilComplete, and pollJobStatus
with a single pollJobStatus function that accepts a PollOptions object.
The returnOnStreaming flag controls early return behavior. Eliminates
~200 lines of duplicated fetch/error/backoff logic.
```

---

### Task 4: Replace unused `c` variables with `_` in lambda closures

**Goal:** Fix MEDIUM hygiene debt -- 10 lambda closures in `lambda_handler.py` use `c` (context) which is captured but never used. Vulture flags these at 100% confidence.

**Files to Modify:**
- `backend/src/handlers/lambda_handler.py` - Replace `lambda e, c:` with `lambda e, _:`

**Prerequisites:** Phase 1 complete

**Implementation Steps:**
1. Open `backend/src/handlers/lambda_handler.py`
2. Find all occurrences of the pattern `lambda e, c:` (approximately 10 occurrences around lines 596, 601, 626, 629, 655, 661, 668, 674, 678, 681)
3. Replace each `lambda e, c:` with `lambda e, _:` -- the underscore convention signals an intentionally unused parameter
4. Do a find-and-replace across the file. The pattern is consistent: `cors_middleware(lambda e, c: response)` becomes `cors_middleware(lambda e, _: response)`

**Verification Checklist:**
- [ ] No remaining `lambda e, c:` patterns in the file
- [ ] All replacements use `lambda e, _:`
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`

**Commit Message Template:**
```
chore(backend): replace unused lambda parameter c with _ in handler

Rename unused context parameter c to _ in 10 cors_middleware lambda
closures. Clears Vulture dead code findings at 100% confidence.
```

---

### Task 5: Remove duplicate FFmpeg pipeline (`combine_voice_and_music`)

**Goal:** Fix MEDIUM structural debt -- `combine_voice_and_music()` (lines 84-188) and `_prepare_mixed_audio()` (lines 323-432) contain near-identical FFmpeg pipelines. Now that Task 1 in Phase 1 added timeouts to `combine_voice_and_music()`, the only remaining difference is the return type and cleanup approach.

**Files to Modify:**
- `backend/src/services/ffmpeg_audio_service.py` - Make `combine_voice_and_music()` delegate to `_prepare_mixed_audio()`

**Prerequisites:** Phase 1 Task 1 (timeout addition) must be complete

**Implementation Steps:**
1. Open `backend/src/services/ffmpeg_audio_service.py`
2. Understand how `combine_voice_and_music()` is called -- search for call sites to understand what callers expect as return value
3. Read `_prepare_mixed_audio()` return signature: it returns `tuple[str, List[str]]` (mixed audio path, updated music list)
4. Read `combine_voice_and_music()` to understand what it returns and what additional work it does beyond the 5 FFmpeg steps (cleanup, base64 encoding, etc.)
5. Refactor `combine_voice_and_music()` to:
   - Call `_prepare_mixed_audio()` for the 5-step FFmpeg pipeline
   - Keep only the post-processing logic that differs (e.g., reading output, cleanup, return format)
   - Remove the duplicated 5 `subprocess.run()` calls

6. **Important**: The `_prepare_mixed_audio()` method already handles intermediate file cleanup in its `finally` block. Verify that `combine_voice_and_music()` cleanup logic is compatible -- it may need to clean up the mixed output file that `_prepare_mixed_audio()` returns.

7. Pay close attention to the method signatures and temp file naming. Both methods use `timestamp` for unique file names but `combine_voice_and_music` receives file paths as parameters while `_prepare_mixed_audio` constructs them internally. You may need to pass the voice path through.

**Verification Checklist:**
- [ ] `combine_voice_and_music()` delegates FFmpeg steps to `_prepare_mixed_audio()`
- [ ] No duplicated subprocess calls remain
- [ ] Return value of `combine_voice_and_music()` is unchanged for callers
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Search tests for `combine_voice_and_music` and `_prepare_mixed_audio` to verify mocking still works

**Commit Message Template:**
```
chore(backend): deduplicate FFmpeg pipeline in combine_voice_and_music

Refactor combine_voice_and_music() to delegate the 5-step FFmpeg
pipeline to _prepare_mixed_audio(), eliminating ~100 lines of
duplicated subprocess calls.
```

---

## Phase Verification

After completing all 5 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```

2. Run backend checks:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   cd backend && uvx ruff check .
   ```

3. Verify the S3 pagination works by reviewing the code:
   ```bash
   grep -n "IsTruncated\|ContinuationToken" backend/src/services/s3_storage_service.py
   ```

4. Verify the FFmpeg timeout:
   ```bash
   grep -n "FFMPEG_STREAM_TIMEOUT\|TimeoutExpired" backend/src/services/ffmpeg_audio_service.py
   ```

5. Verify polling consolidation:
   ```bash
   grep -c "async function poll" frontend/components/BackendMeditationCall.tsx
   # Should return 1
   ```

6. Verify no unused `c` variables:
   ```bash
   grep "lambda e, c:" backend/src/handlers/lambda_handler.py
   # Should return nothing
   ```

All checks must pass before proceeding to Phase 3.
