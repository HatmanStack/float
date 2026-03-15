---
type: repo-health
date: 2026-03-15
scope: full-monorepo
goal: general-health-check
---

## CODEBASE HEALTH AUDIT

### EXECUTIVE SUMMARY
- **Overall health:** FAIR
- **Biggest structural risk:** `lambda_handler.py` (681 lines) is a god module orchestrating all business logic, routing, authorization, async invocation, and retry logic in a single class without clear separation.
- **Biggest operational risk:** Five `subprocess.run()` calls in `combine_voice_and_music()` have no timeout, risking Lambda hangs that consume billing and block resources.
- **Total findings:** 2 critical, 7 high, 9 medium, 6 low

### TECH DEBT LEDGER

#### CRITICAL

1. **[Operational Debt]** `backend/src/services/ffmpeg_audio_service.py:115-177`
   - **The Debt:** Five sequential `subprocess.run()` calls in `combine_voice_and_music()` have no `timeout` parameter. The refactored `_prepare_mixed_audio()` (lines 356-420) correctly adds `timeout=FFMPEG_STEP_TIMEOUT`, but this legacy method does not. This method is still actively called via `_process_meditation_base64()`.
   - **The Risk:** A hanging FFmpeg process in Lambda will consume the full Lambda timeout (up to 15 minutes), billing for idle compute and potentially blocking the user's job permanently. Lambda has no external watchdog for child processes.

2. **[Architectural Debt]** `backend/src/services/s3_storage_service.py:82-100`
   - **The Debt:** `list_objects_v2` is called without pagination. The S3 API returns a maximum of 1000 keys per response. If a user or the music bucket accumulates more than 1000 objects, results will be silently truncated.
   - **The Risk:** Music selection (`select_background_music`) will silently miss available tracks once the audio bucket exceeds 1000 objects. Job cleanup (`cleanup_expired_jobs`) will miss expired jobs beyond 1000 per user prefix. Data loss is silent -- no error, no log.

#### HIGH

1. **[Structural Debt]** `backend/src/handlers/lambda_handler.py:1-681`
   - **The Debt:** Single 681-line file containing the `LambdaHandler` class (all business orchestration), plus three module-level routing functions (`lambda_handler`, `_handle_job_status_request`, `_handle_download_request`). The class handles: service initialization, summary requests, meditation requests (sync + async), audio generation, HLS streaming, retries, job status, download requests, S3 storage of results, and authorization checks.
   - **The Risk:** Any change to routing, authorization, or a single business flow risks regressions in all other flows. Testing requires mocking the entire service graph.

2. **[Operational Debt]** `backend/src/services/ffmpeg_audio_service.py:668-800`
   - **The Debt:** `process_stream_to_hls()` spawns an FFmpeg `Popen` process with stdin piping and a background `upload_watcher` thread. The Popen process has no explicit timeout. If the TTS generator stalls, FFmpeg and the watcher thread will hang indefinitely. The `watcher_thread.join(timeout=30)` protects the join but not the FFmpeg process itself.
   - **The Risk:** A stalled TTS stream or FFmpeg hang will consume the Lambda timeout, and the watcher thread may leak if `join(timeout=30)` fires before FFmpeg terminates, leaving orphaned threads in warm Lambda containers.

3. **[Structural Debt]** `frontend/constants/Colors.ts:1-3888`
   - **The Debt:** A single 3,888-line file containing hardcoded color gradient arrays for every emotion/intensity combination. These are massive literal arrays of hex strings (e.g., 25+ color values per gradient entry, 5 intensity levels per 7 emotions).
   - **The Risk:** This file is untestable, unmaintainable, and likely should be computed at build time or runtime. Any color change requires editing hundreds of lines. File size impacts bundle and IDE performance.

4. **[Architectural Debt]** `backend/src/handlers/lambda_handler.py:586-629` and `632-681`
   - **The Debt:** Authorization logic (user_id ownership check) is duplicated in both `_handle_job_status_request` and `_handle_download_request` as inline code, outside the middleware pipeline. These functions also duplicate CORS wrapping via `cors_middleware(lambda e, c: response)(event, None)` pattern repeated 10 times.
   - **The Risk:** Authorization inconsistency if one path is updated but not the other. The ad-hoc CORS wrapping bypasses the middleware chain used for POST requests, creating two different response pipelines.

5. **[Structural Debt]** `frontend/components/BackendMeditationCall.tsx:107-312`
   - **The Debt:** Three nearly identical polling functions (`pollJobStatusForStreaming`, `pollUntilComplete`, `pollJobStatus`) that share the same URL construction, fetch logic, error handling, and backoff pattern. ~200 lines of duplicated logic with minor behavioral differences.
   - **The Risk:** Bug fixes or changes to polling behavior (e.g., auth headers, error codes) must be applied to three places. Missed updates lead to inconsistent behavior between streaming and legacy modes.

6. **[Operational Debt]** `backend/src/services/job_service.py:106-157`
   - **The Debt:** Every call to `update_streaming_progress()` performs a full S3 GET + S3 PUT cycle. During streaming, this is called once per HLS segment (every ~5 seconds). For a 20-minute meditation (~240 segments), this produces ~480 S3 API calls just for progress tracking.
   - **The Risk:** S3 is eventually consistent for overwrites, meaning rapid PUT-then-GET cycles may return stale data. This also adds latency to each segment upload cycle and incurs non-trivial S3 cost at scale.

7. **[Architectural Debt]** `backend/src/models/domain.py:1-150`
   - **The Debt:** The entire `domain.py` module defines rich domain models (`UserIncident`, `MeditationSession`, `ProcessingJob`) with methods like `to_meditation_data()`, `mark_completed()`, and `from_dict()`. Vulture reports nearly every class and method as unused (60% confidence). The actual codebase uses raw dicts throughout `lambda_handler.py` and `job_service.py`.
   - **The Risk:** These domain models represent a parallel type system that is not integrated with the actual data flow. They provide a false sense of type safety. Any developer relying on these models for understanding the code will be misled about how data actually moves through the system.

#### MEDIUM

1. **[Hygiene Debt]** `backend/src/handlers/lambda_handler.py:596-681`
   - **The Debt:** Vulture identified 10 unused variable assignments (`c`) at lines 596, 601, 626, 629, 655, 661, 668, 674, 678, 681 (100% confidence). These are lambda closures like `cors_middleware(lambda e, c: response)` where `c` (context) is captured but never used.
   - **The Risk:** Minor noise, but Vulture's 100% confidence flag means this will perpetually clutter dead code reports.

2. **[Hygiene Debt]** `backend/src/utils/color_utils.py:1-101`
   - **The Debt:** This module has an unused import (`NDArray` at line 10, 90% confidence), and Vulture flags nearly every function as unused: `modified_sigmoid`, `tanh`, `triangular_weights`, `gaussian_weights`, `custom_weights`, `generate_color_mapping`. The module conditionally imports `numpy` and `scipy` which are not in the Lambda deployment requirements.
   - **The Risk:** Dead code that inflates the codebase and confuses contributors. The numpy/scipy dependency is optional and would fail at runtime in Lambda if these functions were called.

3. **[Operational Debt]** `frontend/components/Notifications.tsx:4,49-53`
   - **The Debt:** Imports deprecated `expo-permissions` API (`Permissions.getAsync`, `Permissions.askAsync`). The `expo-permissions` package was deprecated in SDK 41 and replaced with per-module permission methods.
   - **The Risk:** Will break on future Expo SDK upgrades. The `alert()` call on line 57 is a bare browser alert that provides poor UX on mobile.

4. **[Hygiene Debt]** `backend/src/config/settings.py:8-34`
   - **The Debt:** `Settings` class uses class-level attributes with `os.getenv()` evaluated at import time, not instance time. All settings are class attributes, not instance attributes, so `settings = Settings()` creates an instance but all values come from class scope. The `validate` method is a `@classmethod` but accesses class attributes, making the instance meaningless.
   - **The Risk:** Settings cannot be overridden per-instance for testing without monkeypatching the class itself. The `validate(cls)` pattern means you cannot create an isolated test configuration.

5. **[Structural Debt]** `backend/src/services/ffmpeg_audio_service.py:84-188` vs `323-432`
   - **The Debt:** `combine_voice_and_music()` (lines 84-188) and `_prepare_mixed_audio()` (lines 323-432) contain near-identical FFmpeg pipelines (5 steps each: volume reduction, silence generation, concatenation, length trimming, mixing). The only differences are: timeouts present/absent, `capture_output` present/absent, and the return type.
   - **The Risk:** Two copies of the same audio pipeline with different operational characteristics. Bug fixes in one path (e.g., adding timeout) are not applied to the other.

6. **[Architectural Debt]** `backend/src/services/hls_service.py:44-46`
   - **The Debt:** `HLSService.generate_presigned_url()` directly accesses `self.storage_service.s3_client` to call `generate_presigned_url()`, bypassing the `StorageService` abstraction. Similarly, `upload_segment` (line 72), `upload_segment_from_file` (line 96), `upload_playlist` (line 118), and `download_service.py` all directly access `s3_client` on the storage service.
   - **The Risk:** The `StorageService` abstraction is leaky -- 6+ call sites reach through it to the underlying boto3 client. Testing requires mocking at the boto3 level rather than the service interface level.

7. **[Hygiene Debt]** `backend/src/exceptions.py:121,149`
   - **The Debt:** `StorageError` and `EncodingError` exception classes are defined but never raised anywhere in the codebase (Vulture: 60% confidence). Additionally, error code enum values `MUSIC_LIST_TOO_LARGE` and `INVALID_DURATION` (lines 23-24) are unused.
   - **The Risk:** Dead exception classes create confusion about the error handling taxonomy.

8. **[Operational Debt]** `backend/src/providers/openai_tts.py:49-50`
   - **The Debt:** `traceback.print_exc()` is called on line 50 inside the `stream_speech` exception handler, writing to stderr independently of the structured logger used everywhere else.
   - **The Risk:** In Lambda, stderr goes to CloudWatch but outside the structured log format, making these error traces harder to search, filter, and correlate with request IDs.

9. **[Hygiene Debt]** `backend/src/providers/gemini_tts.py:13`
   - **The Debt:** Vulture flags `GeminiTTSProvider` as an unused class (60% confidence). This is a TTS provider alternative to OpenAI that appears to be defined but never instantiated anywhere in the handler or service factory.
   - **The Risk:** Dead provider code that may drift out of sync with the TTSService interface.

#### LOW

1. **[Hygiene Debt]** Frontend: ~40 `console.error` statements across production components
   - **The Debt:** `console.error` is used liberally in production code paths (AuthScreen, BackendMeditationCall, HLSPlayer, MeditationControls, DownloadButton) rather than a structured error reporting system.
   - **The Risk:** No aggregation, filtering, or alerting on frontend errors in production.

2. **[Hygiene Debt]** `frontend/app/(tabs)/explore.tsx:284-286`
   - **The Debt:** Empty `useEffect` that tracks `width`/height changes with a comment "This effect is intentionally empty." An effect with dependencies but no body is a no-op.
   - **The Risk:** Triggers unnecessary re-renders or is confusing to future developers.

3. **[Hygiene Debt]** `frontend/app/(tabs)/explore.tsx:289-291`
   - **The Debt:** `eslint-disable-next-line react-hooks/exhaustive-deps` suppression for `setRenderKey` effect that triggers on `colorChangeArrayOfArrays` changes. The exhaustive-deps rule is being silenced rather than addressed.
   - **The Risk:** Missing dependency could cause stale closure bugs.

4. **[Hygiene Debt]** Test files: pervasive use of `as any` casts
   - **The Debt:** E2E tests (`error-scenarios.e2e.ts`) use `as any` on 15+ lines. Unit test utilities (`testUtils.tsx`) accept `any[]` and `any` parameters. This erodes type safety in tests.
   - **The Risk:** Tests may pass with wrong types, missing regressions that TypeScript would otherwise catch.

5. **[Hygiene Debt]** `backend/src/services/gemini_service.py:31-148`
   - **The Debt:** Three large prompt strings (~120 lines total) embedded as string literals inside `_setup_prompts()`. These contain detailed instruction formatting that is untestable and hard to diff in code review.
   - **The Risk:** Prompt engineering changes are buried in code changes. No way to A/B test or version prompts independently.

6. **[Operational Debt]** `backend/src/config/settings.py:11`
   - **The Debt:** The Gemini API key environment variable is named `G_KEY` rather than following the project's naming convention (e.g., `GEMINI_API_KEY`).
   - **The Risk:** Inconsistent naming between the code (`GEMINI_API_KEY` attribute) and the environment variable (`G_KEY`) creates confusion during deployment configuration.

### QUICK WINS

1. `backend/src/services/ffmpeg_audio_service.py:115-177` — Add `timeout=FFMPEG_STEP_TIMEOUT` to all 5 `subprocess.run()` calls in `combine_voice_and_music()`, matching `_prepare_mixed_audio()` (estimated effort: < 30 minutes)
2. `backend/src/providers/openai_tts.py:50` — Remove `traceback.print_exc()` since the structured logger on line 49 already captures the stack via the subsequent `raise` (estimated effort: < 15 minutes)
3. `backend/src/utils/color_utils.py:1-101` — Delete or move behind a feature flag; all functions are flagged unused by Vulture and the numpy/scipy dependencies are not deployed (estimated effort: < 30 minutes)

### AUTOMATED SCAN RESULTS

**Dead Code (Python - `uvx vulture .`):**
- 80+ findings across backend/src. High-confidence findings (100%): 10 unused lambda variables `c` in `lambda_handler.py`, 1 unused `peak_index` variable in `color_utils.py`, 1 unused `field_name` in `requests.py`. Low-confidence findings (60%): entire `domain.py` model layer, `GeminiTTSProvider`, `cleanup_expired_jobs`, `service_factory`, multiple constants.

**Vulnerability Scan (npm audit):**
- 13 vulnerabilities in `undici` dependency (3 moderate, 9 high, 1 critical) — all in transitive dependencies, fixable via `npm audit fix`. Skipped per constraint (third-party dependency).

**Vulnerability Scan (pip-audit):**
- 1 known vulnerability in `requests==2.32.3` (CVE-2024-47081), fix available in 2.32.4. Third-party dependency, noted but skipped per constraint.

**Secrets Scan:**
- No committed `.env`, credentials, or secret files found. `.gitignore` properly excludes `.env`, `samconfig.toml`, and `*.env.deploy`. The `.gitignore` includes a helpful comment about `samconfig.toml` containing API keys.

**Git Hygiene:**
- Clean: no untracked files, recent commit history shows regular feature work with PRs and code review. CI runs on all PRs (frontend-lint, frontend-tests, backend-tests).
