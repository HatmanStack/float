# Roadmap

Tracked work that was identified during the 2026-04-08 audit
(`docs/plans/2026-04-08-audit-float/`) but explicitly deferred from the
remediation pipeline. Each item links back to the audit finding or ADR
that justifies the deferral.

## Backend — Operational and Resiliency

### 1. DynamoDB migration for job state and rate limiting

- **Source:** Stress Eval Performance pillar (5/10), `eval.md`; ADR-3 in
  `docs/plans/2026-04-08-audit-float/Phase-0.md:133-165`
- **Why deferred:** Out of scope for audit remediation. Requires new
  infrastructure (table provisioning, IAM, SAM template changes).
- **Scope:**
  - Replace S3-backed `JobService` with a DynamoDB table keyed by
    `(user_id, job_id)`.
  - Replace the per-container in-memory `/token` rate limiter with a
    DynamoDB atomic counter (or ElastiCache).
  - Use TTL attribute for job cleanup instead of `list_objects` sweeps.

### 2. ETag-aware conditional writes on `S3StorageService`

- **Source:** Stress Eval critical failure point #3; ADR-3
- **Why deferred:** Superseded by item 1 (DynamoDB migration removes the
  read-modify-write pattern entirely). If DynamoDB is rejected, this is
  the in-place fix.
- **Scope:** Add `If-Match` ETag handling to `_save_job` and
  `update_streaming_progress` so concurrent progress callbacks cannot
  stomp each other.

### 3. Per-service narrowing of `except Exception` clauses

- **Source:** `health-audit.md` MEDIUM hygiene finding (~57 clauses);
  Phase-0 Out of Scope item 4
- **Why deferred:** Multi-day refactor requiring per-service exception
  taxonomy decisions.
- **Scope (by file, with current counts):**
  - `backend/src/services/hls_service.py` — 11 catches
  - `backend/src/services/job_service.py` — 8 catches
  - `backend/src/services/ffmpeg_audio_service.py` — 7 catches
  - Remaining ~28 catches across `s3_storage_service.py`,
    `download_service.py`, `gemini_service.py`, providers
- **Approach:** Define per-service domain exceptions, narrow each catch
  to the specific exception types it can actually receive, let unknown
  exceptions propagate to the middleware.

### 4. Server-issued opaque `user_id` (auth overhaul)

- **Source:** Stress Eval critical failure point #4; Phase-0 Out of
  Scope item 3
- **Why deferred:** Belongs to a separate auth plan; current Phase 2
  regex validator already blocks path-traversal as a stopgap.
- **Scope:** Server-minted UUIDs or JWTs replacing
  client-controlled `user_id` strings. Migration plan for existing
  S3-stored jobs keyed by current `user_id` values.

### 5. Shared circuit-breaker state

- **Source:** Stress Eval critical failure point #5
- **Why deferred:** Same infrastructure dependency as item 1 (needs
  DynamoDB or Redis for cross-container state).
- **Scope:** `circuit_breaker.py` currently keeps state in module
  globals — 1000 warm Lambdas means 1000 independent breakers and no
  collective backoff. Move state to a shared store.

### 6. Async path for `handle_summary_request`

- **Source:** Stress Eval critical failure point #6
- **Why deferred:** Audit scope was remediation, not new pipelines.
- **Scope:** Base64-decoding audio inside the synchronous request
  handler saturates Lambda concurrency at high load. Either move
  decoding off the request path or impose stricter input-size limits
  ahead of decode.

## Backend — Code Modernization

### 7. Modernize legacy `typing.List`/`Dict`/`Union` imports

- **Source:** Phase-0 Out of Scope item 6; tracked via annotated
  ignores in `backend/pyproject.toml:121-129`
- **Why deferred:** Phase 1 was subtractive only; Phase 4 added
  TypedDicts in new files but did not sweep legacy modules.
- **Scope:** Single sweep that replaces `List/Dict/Optional/Union`
  imports with PEP 585/604 syntax across `backend/src/handlers/` and
  `backend/src/services/`. Re-enable `UP006`, `UP007`, `UP035`,
  `UP045` in `pyproject.toml` once violator counts hit zero.
- **Current violator counts (2026-04-08):** UP006=152, UP045=83,
  UP035=49, UP007=4

## Frontend

### 8. `BackendMeditationCall.tsx` state-management redesign

- **Source:** Phase-0 Out of Scope item 5
- **Why deferred:** Phase 4 Task 4 split helpers into a hook/helpers
  module, but the underlying state machine was untouched.
- **Scope:** Replace ad-hoc polling state with a typed state machine
  (XState or a discriminated-union reducer).

## Developer Experience and Onboarding

### 9. FFmpeg Lambda layer build documentation

- **Source:** Day 2 Eval red flag
- **Why deferred:** Out of audit scope.
- **Scope:** Document or script the FFmpeg Lambda layer build so a new
  contributor can deploy end-to-end. Currently `template.yaml` requires
  an externally-supplied `FfmpegLayerArn` with no build instructions.

### 10. `--legacy-peer-deps` rationale and exit criteria

- **Source:** Day 2 Eval red flag
- **Why deferred:** Out of audit scope.
- **Scope:** Document why `npm install --legacy-peer-deps` is required,
  which dependency creates the conflict, and the criteria for dropping
  the flag.

### 11. "First PR" contributor walkthrough

- **Source:** Day 2 Eval Onboarding pillar (8 → 9 remediation target)
- **Why deferred:** Phase 6 prioritized doc accuracy over new doc
  authoring.
- **Scope:** Add a short walkthrough to `CONTRIBUTING.md`: pick a
  good-first-issue, run `npm run check`, open a PR, what CI gates
  expect.

## Post-Audit Code Review Findings (2026-04-08)

Items raised after the pipeline closed that are too large to land as
drive-by fixes.

### 12. GEMINI_API_KEY reused as HMAC signing key

- **Source:** `backend/src/utils/security.py:34-38`
- **Why deferred:** Stop-gap until the native Gemini ephemeral token
  path is available.
- **Risk:** If the Gemini key is rotated, all outstanding token markers
  immediately become unverifiable (no migration window). Acceptable for
  short-lived advisory markers, but tracked toward replacement.
- **Scope:** Use a dedicated `TOKEN_SIGNING_KEY` env var (rotated
  independently from the Gemini key), or migrate to the native Gemini
  ephemeral token API once available.

### 13. Move `user_id` out of query parameters into a request header

- **Source:** `frontend/hooks/useMeditationGeneration.ts:56` and the
  matching backend route handlers
- **Why deferred:** Touches both sides of the contract and every
  in-flight client; safer as a planned migration than a drive-by edit.
- **Risk:** Query parameters appear in server access logs, CDN logs,
  and browser history.
- **Scope:**
  - Backend: read `user_id` from `X-User-Id` header in
    `_handle_job_status_request` / `_handle_download_request`, with
    fallback to query param during migration.
  - Frontend: send `X-User-Id` header in `pollJobStatus` and
    `fetchDownloadUrl` instead of inlining into the URL.
  - Update `docs/API.md` and remove the query-param fallback once all
    clients are updated.

### 14. Replace hardcoded music fallback with a real "no music" path

- **Source:** `backend/src/services/audio/music_selector.py:65-70`
- **Why deferred:** Removing the hardcoded `Hopeful-Elegant-LaidBack_120.wav`
  sentinel breaks 7 unit tests in `test_services.py` that mock
  `list_objects` with auto-mocks (truthy `MagicMock` whose `list(...)` is
  empty). A clean fix needs both the production-code raise and a
  test-fixture sweep.
- **Risk:** If the sentinel filename does not exist in the deployed S3
  bucket, `select_background_music` raises `AudioProcessingError` only at
  download time instead of failing fast at the selection step.
- **Scope:**
  - In `MusicSelector.select`, raise `AudioProcessingError("No background
    music available")` when both `filtered_keys` and `existing_keys` are
    empty (or when the cache holds an empty list).
  - Update the affected `TestFFmpegAudioService` tests to seed
    `mock_storage_service.list_objects.return_value` with a real list
    matching the requested duration tier.
  - Consider adding a startup probe that pre-warms the
    `music_list_cache` so a missing bucket is caught at cold start
    instead of first request.

### 15. Sign Gemini Live tokens with `iat`/`exp` timestamps

- **Source:** Phase-2.md remediation note; ties into ROADMAP item 12.
- **Why deferred:** The Phase 2 implementation signed only `user_id`, so
  tokens never expire on their own (only via the advisory
  `TOKEN_MARKER_TTL_SECONDS` field returned to the client). The fix
  needs a new validator path on the consuming side and a coordinated
  Gemini Live client update.
- **Scope:**
  - Sign `f"{user_id}|{iat}|{exp}"` instead of just `user_id` in
    `derive_token_marker`.
  - Add `validate_token_marker(token, user_id)` that recomputes the HMAC
    and rejects expired or mismatched tokens.
  - Move the helpers into a dedicated `gemini_token` utility module so
    no handler imports `settings.GEMINI_API_KEY` directly.

## Score Movements Locked Behind These Items

The following eval scores were intentionally *not* taken to 9/10
because the work above was deferred. They are tracked here so the next
audit cycle knows what is blocking each pillar.

| Pillar | Achieved | Original Target | Blocking Item(s) |
|--------|----------|-----------------|-------------------|
| Stress: Performance | 7 | 9 | Items 1, 5 |
| Stress: Defensiveness | 8 | 9 | Item 2 |
| Day 2: Onboarding | 8 | 9 | Items 9, 10, 11 |
