---
type: repo-health
date: 2026-04-08
scope: full-repo
deployment: serverless-lambda
---

## CODEBASE HEALTH AUDIT

### EXECUTIVE SUMMARY
- Overall health: **GOOD**
- Biggest structural risk: `LambdaHandler` is a dispatching god-object coupling to every service and re-implementing HTTP routing outside its own middleware pipeline.
- Biggest operational risk: The streaming HLS pipeline in `ffmpeg_audio_service.py` combines subprocess, pipe, and a polling watcher thread with shared mutable state and bare `Exception` raises — a class of bugs that tend to manifest only under production load.
- Total findings: 2 critical, 8 high, 12 medium, 6 low

### TECH DEBT LEDGER

#### CRITICAL

- **[Operational][CRITICAL]** `backend/src/handlers/lambda_handler.py:744-748` — `/token` endpoint returns the raw `GEMINI_API_KEY` to clients. Acknowledged in-code as MVP debt, but it is a live production security boundary violation that allows any caller to exfiltrate the backend's Gemini credentials. Mitigated only by an in-memory, single-Lambda-instance rate limiter (`_token_rate_limit`) at line 48 that resets on every cold start and is not shared across concurrent Lambda containers — effectively no rate limit in practice.
- **[Operational][CRITICAL]** `backend/requirements.txt` — `requests==2.32.3` has two known CVEs (`CVE-2024-47081`, `CVE-2026-25645`); `pip-audit` reports fixes in 2.32.4 / 2.33.0.

#### HIGH

- **[Structural][HIGH]** `backend/src/handlers/lambda_handler.py:68-604` — `LambdaHandler` is a god object (756 lines) that constructs 7 services in its constructor (`ai_service`, `storage_service`, `hls_service`, `download_service`, `audio_service`, `tts_provider`, `fallback_tts_provider`, `job_service`), performs HTTP-verb-and-path routing at the module level (`lambda_handler` at line 572 manually branches on `rawPath` / `http_method`), and duplicates auth checks across `_handle_job_status_request` and `_handle_download_request`. Middleware exists but is bypassed for three of four route types.
- **[Architectural][HIGH]** `backend/src/handlers/lambda_handler.py:589-598` — Routing is done by string matching on `rawPath` (`"/job/" in raw_path`, `"/download" in raw_path`, `"/token" in raw_path`). A path like `/download/job/x` matches both branches depending on ordering; brittle and not covered by the declarative middleware system that handles the main POST.
- **[Operational][HIGH]** `backend/src/services/ffmpeg_audio_service.py:670-784` — `process_stream_to_hls` uses a shared `state` dict across a main thread and watcher thread without locking; `state["segments_uploaded"]`, `state["segment_durations"]`, and `uploaded_segments` are mutated concurrently. Race window between the final `state["uploading"] = False` and `watcher_thread.join`.
- **[Operational][HIGH]** `backend/src/services/ffmpeg_audio_service.py:681` — watcher loop condition `while state["uploading"] or os.path.exists(hls_output_dir):` uses directory existence as a liveness signal; since `shutil.rmtree` happens only at line 803 after the thread join, this condition can spin indefinitely if the main thread is blocked.
- **[Operational][HIGH]** `backend/src/services/ffmpeg_audio_service.py:752-754` — `process.stdin.write(chunk)` inside a TTS generator loop has no backpressure handling beyond `process.poll()`; `BrokenPipeError` is caught but partial writes from the generator are not drained, leaking the generator and leaving TTS provider connections open.
- **[Operational][HIGH]** `backend/src/handlers/lambda_handler.py:418-434` — Retry logic self-invokes Lambda inside the exception handler of an already-self-invoked Lambda with no de-duplication beyond an S3-stored attempt counter. A failure during `increment_generation_attempt` can cause double-retries; a failure during `_invoke_async_meditation` logs and falls through to mark as failed, but the previously-enqueued async invocation may still execute.
- **[Operational][HIGH]** `backend/src/handlers/lambda_handler.py:237` — `raise Exception("Failed to encode combined audio")` and several similar raw `Exception` raises across `ffmpeg_audio_service.py` (lines 200, 220, 290, 751, 761, 773) obscure error categorization and bypass the custom `exceptions.py` taxonomy.
- **[Hygiene][HIGH]** `frontend/constants/Colors.ts` — 3888 lines of hand-enumerated hex color gradients (`angry.one`, etc.). Essentially a generated data asset committed as source; dwarfs every other frontend file and pollutes diffs, type-check time, and bundle size.

#### MEDIUM

- **[Structural][MEDIUM]** `backend/src/services/ffmpeg_audio_service.py:1-805` — 805-line class mixing FFmpeg CLI construction, temp-file lifecycle, S3 interaction (via `hls_service`), threading, music selection, and duration probing. Multiple responsibilities; `_prepare_mixed_audio` alone runs 5 sequential subprocesses with ad-hoc temp file management.
- **[Operational][MEDIUM]** `backend/src/services/ffmpeg_audio_service.py:446-465` — `_get_audio_duration_from_file` duplicates `get_audio_duration` (lines 65-84) with different timeout value (30s vs 120s) and subtly different error handling.
- **[Operational][MEDIUM]** `backend/src/services/ffmpeg_audio_service.py:75-84` — ffmpeg duration parsing via string manipulation on stderr; fragile and hard-codes English-locale format `"Duration:"`.
- **[Operational][MEDIUM]** `backend/src/handlers/lambda_handler.py:48-50` — Module-level `_token_rate_limit` dict grows unbounded per user; only pruned on access. Cold Lambda container can accumulate memory from stale users.
- **[Operational][MEDIUM]** `backend/src/handlers/middleware.py:80-85, 140-145, 274` — Three `except Exception:` clauses in middleware return generic 500s and swallow the original error type; couples to the logger for diagnosis and hides `CircuitBreakerOpenError` / `TTSError` taxonomies from HTTP clients.
- **[Architectural][MEDIUM]** `backend/src/handlers/lambda_handler.py:609, 658, 706` — Inline `from .middleware import cors_middleware` inside handler functions (repeated 3x) suggests an unresolved circular-import concern, and each handler wraps a response with `cors_middleware(lambda e, _: response)(event, None)` — a CORS hack that bypasses the decorator pipeline.
- **[Architectural][MEDIUM]** `backend/src/services/ffmpeg_audio_service.py:86-100, 114-249` — `combine_voice_and_music` and `combine_voice_and_music_hls` share ~90% of setup via `_prepare_mixed_audio` but branch at output stage; duplication in timeout handling and cleanup patterns.
- **[Operational][MEDIUM]** `backend/src/handlers/lambda_handler.py:162-178` — `_invoke_async_meditation` creates a new boto3 `lambda_client` on every invocation rather than caching at module scope (defeats AWS SDK connection reuse inside a warm Lambda).
- **[Hygiene][MEDIUM]** `backend/src/services/ffmpeg_audio_service.py:101-112, 251-260, 380-387` — Three near-identical `try/except OSError: pass` temp-file cleanup blocks; silent failures and no metric on leaked files.
- **[Hygiene][MEDIUM]** `backend/src/handlers/lambda_handler.py:237` — `Exception("Failed to encode combined audio")` after `if not base64_audio:`; should be a domain error.
- **[Hygiene][MEDIUM]** Backend ~57 `except Exception` / bare excepts across `src/` — excessive catch-all handling obscures fault isolation even though most re-log.
- **[Hygiene][MEDIUM]** `frontend/tests/unit/AuthScreen-test.tsx`, `tests/unit/history-test.tsx`, `tests/unit/AudioRecording-test.tsx`, etc. — multiple test files using `any`; limited to tests but indicates weak typing in mocks.

#### LOW

- **[Hygiene][LOW]** `backend/src/handlers/lambda_handler.py:5` — `from typing import Any, Dict, List, Optional, Union` uses legacy capitalized generics on a Python 3.13 runtime.
- **[Hygiene][LOW]** `backend/src/services/gemini_service.py:16` — Uses `logging.getLogger(__name__)` directly instead of `get_logger(__name__)` (project convention used everywhere else).
- **[Hygiene][LOW]** `backend/src/services/ffmpeg_audio_service.py:76` — f-string in a `logger.warning` that also passes `extra={"data":...}`, mixing two logging conventions.
- **[Hygiene][LOW]** `backend/src/exceptions.py:143` — bare `pass` inside an exception class; likely missing docstring or members.
- **[Hygiene][LOW]** `frontend/components/HLSPlayer/hlsPlayerHtml.ts:1`, `frontend/scripts/inject-seo.js:1` — `console.log` in shipped code path.
- **[Hygiene][LOW]** `backend/src/handlers/lambda_handler.py:47, 52, 55, 61, 65` — Module-level mix of rate-limit state, feature flags, retry constants, and domain constants; should live in `config/constants.py`.

### QUICK WINS

1. Replace the `/token` endpoint's rate-limit store with a shared DynamoDB / S3 counter (or remove the endpoint until ephemeral tokens exist).
2. Bump `requests` to `>=2.33.0` in `backend/requirements.txt`.
3. Delete or generate `frontend/constants/Colors.ts` from a small palette file.
4. Extract `_handle_job_status_request`, `_handle_download_request`, `_handle_token_request` in `lambda_handler.py` into a proper router and apply the existing middleware chain.
5. Consolidate `get_audio_duration` and `_get_audio_duration_from_file`.
6. Module-level `boto3.client("lambda")` in `lambda_handler.py` for warm-container reuse.
7. Replace raw `raise Exception(...)` calls with the domain exceptions in `exceptions.py`.

### AUTOMATED SCAN RESULTS

- **npm audit (prod):** 0 vulnerabilities.
- **pip-audit (backend/requirements.txt):** 2 vulnerabilities in `requests==2.32.3` (CVE-2024-47081, CVE-2026-25645).
- **Secrets grep:** No hardcoded API keys/secrets in source; all flow through `settings`. Note the deliberate leak of `GEMINI_API_KEY` via `/token` (see CRITICAL).
- **Git hygiene:** Single-branch repo on `main`, 372 commits, clean working tree, `.aws-sam` build artifacts correctly untracked.
- **Dead code scan:** Not run. Largest structural outliers: `constants/Colors.ts` (3888), `test_services.py` (1473), `ffmpeg_audio_service.py` (805), `lambda_handler.py` (756).
- **Type escape hatches:** 23 `any`-type occurrences in frontend (majority in tests), 7 Python `# type: ignore` in backend src — within acceptable bounds.
- **TODO/FIXME:** No stray `TODO`/`FIXME` in source code.
- **Debug artifacts:** 2 `console.log` in shipped frontend (`HLSPlayer/hlsPlayerHtml.ts`, `scripts/inject-seo.js`).
