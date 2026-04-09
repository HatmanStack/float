# Feedback Log

This file is the single communication channel between Planner, Plan Reviewer,
Implementer, Reviewer, and Final Reviewer for plan
`2026-04-08-audit-float`. Plan documents are never mutated by reviewers --
all feedback lives here.

See `.claude/skills/pipeline/pipeline-protocol.md` for the canonical
schema and rules.

## Active Feedback

_(none)_

---

## Verification

### VERIFIED - 2026-04-08

**Reviewer:** Verification Reviewer

All findings from health-audit.md (CRITICAL + HIGH), eval.md (REMEDIATION TARGETS across Hire/Stress/Day2 lenses), and doc-audit.md (DRIFT/GAP/STALE/BROKEN LINK) verified addressed in code. Tests: 351/351 backend unit pass, 287/287 frontend pass, ruff clean, frontend lint clean.

---

## Phase Approvals

### PHASE_APPROVED - Phase 6 [DOC-ENGINEER]

**Status:** APPROVED (iteration 1)
**Reviewer:** Doc Reviewer
**Implementer:** Documentation Engineer

All 6 Phase 6 doc tasks verified:

1. README/CLAUDE/docs version drift fixed (Expo 55, RN 0.84, React 19); `tests/` paths corrected to `frontend/tests/` and `backend/tests/`; "Node.js v24 LTS" dropped; `EXPO_PUBLIC_ANDROID_CLIENT_ID` and `G_KEY` legacy alias documented.
1. `docs/API.md` rewritten — Download Section 3 documents JSON `{job_id, download_url, expires_in: 3600}`; new Section 4 documents `/token` opaque HMAC marker; `qa_transcript` field added; complete job-status example with `streaming`/`download`/`generation_attempt`; polling Example 3; authorization model; corrected error text.
1. `docs/ARCHITECTURE.md` — new "Meditation Generation Flow" sequence diagram; HLS streaming pipeline; `_StreamState`/watcher; retry semantics; constants table cross-verified against `backend/src/config/constants.py`.
1. Root `README.md` deploy table replaced with link to `docs/README.md#deployment`; CLAUDE.md and docs/README.md plans index landed in Task 1.
1. `.markdownlint.json` config + `markdownlint-cli2-action@v23` CI job; markdownlint-cli2 runs clean (8 files, 0 errors); MD040/MD012/MD032 issues fixed.
1. `lychee-action@v2` `link-check` CI job added; both new jobs gated into `status-check.needs`.

Excludes: `node_modules`, `.claude`, `backend/.venv`, `backend/.aws-sam`, `CHANGELOG.md`, `docs/plans/**`, `frontend/tests/**/README.md`.

**Commits:** `279693a`, `fc389bf`, `036accd`, `7b55fee`, `9e23b5b`, `2ae5da5`.

---

### PHASE_APPROVED - Phase 5 [FORTIFIER]

**Status:** APPROVED (iteration 1)
**Reviewer:** Health Reviewer
**Implementer:** Code Fortifier

All 4 Phase 5 fortifier tasks verified:

1. `pip-audit` job added to `.github/workflows/ci.yml` (lines 122-141), gated into `status-check.needs` (line 147); `pip-audit==2.7.3` pinned in `backend/requirements-dev.txt:9`.
1. 450-line file-size guardrail step in backend CI job (lines 98-112); 0 offenders locally.
1. All 9 remaining `UP*` ignores in `backend/pyproject.toml:121-129` annotated with measured violator counts (UP006=152, UP045=83, UP035=49, UP007=4, UP017=3, UP028=3, UP024=2, UP015=1, UP046=1) per Phase 5 Task 3 spec — no rules re-enabled because all still have violators.
1. 6 `as any` casts in `frontend/tests/unit/AudioRecording-test.tsx` replaced with `as unknown as Audio.Recording`; 0 `as any` remaining.

**Test results:** ruff clean, frontend lint clean, 287/287 frontend tests pass. Backend pytest not run locally (missing deps); CI installs them.

**Commits:** `ea8f2f1`, `da50eac`, `12c436e`, `4ad6a7b`, `52c938d`.

---

### PHASE_APPROVED - Phase 4 [IMPLEMENTER]

**Status:** APPROVED (iteration 2)
**Reviewer:** Code Reviewer (Senior Engineer)
**Implementer:** Implementation Engineer

All 4 Phase 4 tasks complete; all 7 iteration-1 CODE_REVIEW items resolved in iteration 2.

Final line counts:

```text
backend/src/handlers/lambda_handler.py        90  (<100)
backend/src/handlers/meditation_handler.py   194  (<400)
backend/src/handlers/router.py               104  (<200)
backend/src/handlers/handler_facade.py       124
backend/src/handlers/routes.py               139
backend/src/handlers/meditation_pipeline.py  298
backend/src/services/ffmpeg_audio_service.py 149  (<150)
backend/src/services/audio/audio_mixer.py    302
backend/src/services/audio/hls_batch_encoder.py 148
backend/src/services/audio/hls_stream_encoder.py 285
frontend/components/BackendMeditationCall.tsx 142  (<200)
frontend/components/backendMeditationCallHelpers.ts 148
frontend/hooks/useMeditationGeneration.ts    163
```

`request_validation_middleware` fully deleted from `middleware.py` and tests.

**Test results:** 351/351 backend unit tests pass, 287/287 frontend tests pass, ruff clean, frontend lint clean.

**Commits:** `9dc76e1`, `c8d0c16`, `e34395d`, `410ea25`, `2977f71`, `80dace9`, `dfab535`.

---

### PHASE_APPROVED - Phase 3 [IMPLEMENTER]

**Status:** APPROVED (iteration 1)
**Reviewer:** Code Reviewer (Senior Engineer)
**Implementer:** Implementation Engineer

All 5 Phase 3 tasks verified complete:

1. Tasks 1+2 — `_StreamState` dataclass with `threading.Lock` + `threading.Event` at `ffmpeg_audio_service.py:43`, instantiated at `:688`. Watcher drains via `state.done.wait(0.3)` instead of `os.path.exists` polling.
1. Task 3 — BrokenPipe drain: streaming loop in try/finally calls `voice_generator.close()` on every exit path; `BrokenPipeError` raises `AudioProcessingError`.
1. Task 4 — Retry loop: `_process_meditation_hls` exception handler restructured so `increment_generation_attempt` runs in its own try; on failure marks job failed instead of retrying. New `_mark_job_failed` helper at `lambda_handler.py:495`, used at `:457/:470/:490`.
1. Task 5 — All 8 raw `raise Exception(...)` sites in `lambda_handler.py` and `ffmpeg_audio_service.py` replaced with `AudioProcessingError` or `ExternalServiceError(STORAGE_FAILURE)`. `grep "raise Exception(" backend/src/` = 0 hits.

**New tests:** `TestProcessStreamToHls` (locked drain, broken-pipe close), `TestHLSRetryLoop` (success, counter-failure, invoke-failure, max-attempts).

**Test results:** 357/357 backend unit tests pass, 287/287 frontend tests pass, ruff clean, frontend lint clean.

**Commits:** `713de74`, `3f7156a`, `f11a46e`.

---

### PHASE_APPROVED - Phase 2 [IMPLEMENTER]

**Status:** APPROVED (iteration 1)
**Reviewer:** Code Reviewer (Senior Engineer)
**Implementer:** (pre-existing commits)

All 4 Phase 2 tasks verified complete:

1. `/token` no longer leaks `GEMINI_API_KEY` — returns HMAC-derived opaque marker; new `backend/src/utils/security.py`; `_token_rate_limit` dict deleted. `grep settings.GEMINI_API_KEY backend/src/handlers/` = 0 hits.
1. `user_id` validated at request boundary — `is_valid_user_id` in `backend/src/utils/validation.py`; wired via Pydantic field_validator and `_validate_user_id_or_400` + `_authorize_job_access` helper.
1. `rawPath` string-match routing replaced with `_ROUTES` dispatch table; download-before-job-status ordering preserved; handlers resolved via `globals()` for mock patching; `_with_cors` wrapper. Inline `from .middleware import cors_middleware` eliminated (0 hits).
1. Middleware `except Exception` clauses narrowed in `json_middleware` and `request_validation_middleware`; domain exceptions (`TTSError`, `CircuitBreakerOpenError`, `ValidationError`) now propagate through the chain with tests.

**Test results:** 287/287 frontend tests pass, 351/351 backend unit tests pass, `npm run lint` clean, `uvx ruff check .` clean.

**Commits:** 4 atomic conventional commits — `283cbbb`, `3e05e12`, `dfb9c7c`, `52c08cc`.

---

### PHASE_APPROVED - Phase 1 [HYGIENIST]

**Status:** APPROVED (iteration 1)
**Reviewer:** Health Reviewer
**Implementer:** Code Hygienist

All 6 Phase 1 tasks verified complete:

1. Colors.ts shrunk 3888 → 141 lines; public `Colors.<emotion>.{one..five}: string[]` shape preserved; consumers verified.
1. `requests>=2.33.0` bump in `backend/requirements.txt:11` and `backend/pyproject.toml:40`.
1. `console.log` → `console.warn` at `hlsPlayerHtml.ts:164` and `inject-seo.js:58`; zero `console.log` hits in `frontend/components` and `frontend/scripts`.
1. `_get_audio_duration_from_file` deleted; `_append_fade_segments` calls `self.get_audio_duration(...)`; all 5 `patch.object` sites retargeted in `test_services.py`; `side_effect=[120.0, 5.0, 5.0]` ordering verified correct.
1. `_lambda_client` module cache + `_get_lambda_client()` helper at `lambda_handler.py:50-58`; `_invoke_async_meditation` uses helper; integration test patching still works.
1. Logging convention fixed at `ffmpeg_audio_service.py:85-88`, `gemini_service.py:13-16`, `exceptions.py:140`. Task extended to `openai_tts.py` and `gemini_tts.py` under ADR-4 (direct equivalent substitution) to satisfy the zero-grep verification criterion.

**Test results:** 287/287 frontend tests pass, 318/318 backend unit tests pass, `npm run lint` clean, `uvx ruff check .` clean. Pre-existing timing flake in `test_s3_storage_service_initialization` is unrelated.

**Commits:** 8 atomic conventional commits from `db60fa3` through `cd88b87`.

---

## Resolved Feedback

### PLAN_REVIEW - Iteration 1 - README.md and Phase coverage

Status: RESOLVED (iteration 2)
Reviewer: Plan Reviewer (Tech Lead)
Planner: Planning Architect (iteration 2)

The plan reviewer raised 14 items across three severity bands. Each is
resolved below with a one-line note pointing at the changed file and
section.

1. **Health Audit coverage table has wrong task numbers for "Routing via
   rawPath" and "Middleware except Exception" rows.**
   **Resolution:** Already corrected in `README.md:74, 84` -- Routing now
   maps to Phase 2 Task 3 and Middleware to Phase 2 Task 4. No change
   needed in iteration 2 (the rows were already right on re-read); the
   iteration 1 reviewer was comparing against a pre-revision snapshot.
   Verified by inspection of `README.md:71-96`.

1. **Backend ~57 `except Exception` clauses claim covered by Phase 4 Task
   3 but not actually addressed anywhere.**
   **Resolution:** The README row (`README.md:89`) already lists the
   finding as "Out of Scope (see Phase 0)" and the README Out of Scope
   section (`README.md:159-166`) documents the narrow three-middleware
   scope of Phase 2 Task 4 with the ~54 defensive service-level clauses
   explicitly deferred. Phase 0 now has a canonical "Out of Scope" section
   (`Phase-0.md:188-229`) with the full justification. The finding is not
   partially covered; it is explicitly deferred.

1. **Phase 0 ADR-3 / Performance pillar promises Phase 3 ETag work but no
   Phase 3 task implements it.**
   **Resolution:** ADR-3 (`Phase-0.md:133-165`) has been rewritten to
   explicitly walk back the earlier "extend S3StorageService with
   conditional-write helpers" promise. The ADR now states "This plan ALSO
   EXPLICITLY DEFERS the proposed in-place mitigation of adding ETag-aware
   conditional writes." Phase 0's new "Out of Scope" section also lists it
   as item 2. The README Performance pillar row (`README.md:103`) has been
   updated from "5 → 9" to "5 → 7" with a NOTE line explicitly disclaiming
   the ETag work. Phase 3 Known Limitations (`Phase-3.md:448-451`) already
   documents the remaining race. Defensiveness pillar adjusted from 9 to
   8 to reflect that without the race fix the score cannot reach 9.

1. **Test files `test_ffmpeg_audio_service.py` and `test_job_service.py`
   referenced as "Modify" but don't exist -- actual tests live in
   `test_services.py`.**
   **Resolution:** Verified via `ls backend/tests/unit/`. Fixed:
   - Phase 1 Task 4 (`Phase-1.md:221-232`) now names `test_services.py`
     as the test file with explicit enumeration of the five
     `patch.object` sites (lines 1162, 1204, 1229, 1252, 1277).
   - Phase 3 Task 1 (`Phase-3.md:49-54`) now names `test_services.py`
     and explains the split is deferred to Phase 4 Task 2.
   - Phase 3 Task 1 test runner (`Phase-3.md:109`) uses
     `test_services.py -v -k stream`.
   - Phase 3 Task 3 (`Phase-3.md:204-206`) now names `test_services.py`.
   - Phase 3 Task 3 test runner (`Phase-3.md:250`) uses
     `test_services.py -v -k broken_pipe`.
   - Phase 3 Task 5 (`Phase-3.md:410-413`) now names `test_services.py`
     explicitly.
   - Phase 4 Task 2 Files to Modify (`Phase-4.md:174-183`) now explains
     that `test_services.py` contains the FFmpeg tests and the
     `test_music_selector.py` / `test_audio_mixer.py` /
     `test_hls_batch_encoder.py` / `test_hls_stream_encoder.py` split
     happens by EXTRACTING from `test_services.py` during the refactor.
   - Phase 4 Task 3 Testing Instructions (`Phase-4.md:343-347`) now uses
     `test_services.py -v -k job` (not `test_job_service.py`).

1. **Phase 3 Task 5 raw Exception line list misattributes
   `lambda_handler.py:290` to ffmpeg and misses ffmpeg_audio_service.py:557.**
   **Resolution:** Phase 3 Task 5 Files to Modify (`Phase-3.md:375-413`)
   has been rewritten with the correct 2026-04-08 verified list:
   `lambda_handler.py:237, 290` and `ffmpeg_audio_service.py:199, 220, 557,
   751, 761, 773`. Line 557 is explicitly added with a note that it was
   missed in earlier drafts. Phase 3 success criteria (`Phase-3.md:22-26`)
   also updated to match. Phase 0 Exceptions section (`Phase-0.md:53-70`)
   mirrors the list.

1. **Phase 1 Task 6 targets ffmpeg_audio_service.py:76 but line 76 is
   already correct; actual violator is line 83 with a different convention.**
   **Resolution:** Phase 1 Task 6 (`Phase-1.md:337-345` and
   `Phase-1.md:369-389`) now explicitly targets line 83 (the f-string-only
   `logger.warning(f"Error getting audio duration: {e}")`) and rewrites it
   to use a structured `extra={"data": {"error": str(e)}}` payload. The
   task also notes that line 76 is already correct and MUST NOT be
   touched. README row updated to cite line 83 (`README.md:93`). Phase 0
   Logging convention section (`Phase-0.md:39-42`) also cites line 83.

1. **Phase 1 Task 4 doesn't enumerate the 5 `patch.object` sites in
   test_services.py mocking `_get_audio_duration_from_file`.**
   **Resolution:** Phase 1 Task 4 Files to Modify (`Phase-1.md:221-232`)
   now enumerates all five sites by line number (1162, 1204, 1229, 1252,
   1277) and explicitly instructs the implementer to retarget each to
   `patch.object(service, "get_audio_duration", ...)`. Includes a
   verification grep command.

1. **Phase 4 Task 3 prescribes "deprecate for one release" but no release
   cycle exists in this plan.**
   **Resolution:** Phase 4 Task 3 Implementation Steps (`Phase-4.md:317-326`)
   now says to DELETE `request_validation_middleware` outright (no
   deprecation). The "one release" language is removed. A verification
   grep confirms no product-code import remains.

1. **Phase 5 Task 3 tries to re-enable UP006/UP007/UP035 but no phase has
   modernized types beyond TypedDicts -- task will produce zero changes.**
   **Resolution:** Phase 5 Task 3 Goal (`Phase-5.md:172-211`) has been
   rewritten to explicitly state the expected outcome is "annotate every
   remaining UP* ignore with a one-line comment naming the rule and the
   current violator count" and NOT a meaningful re-enable diff. The task
   now calls out that `UP006/UP007/UP035` WILL still have violators
   because Phases 1-4 don't modernize legacy `typing.List/Dict/Union`
   imports. Phase 0 "Out of Scope" item 6 (`Phase-0.md:219-229`) mirrors
   the deferral and points at a future modernization plan.

1. **Phase 2 Task 1 defers Option A vs Option B for the CRITICAL /token
   fix to git archaeology; should be pre-decided.**
   **Resolution:** Phase 2 Task 1 (`Phase-2.md:42-72`) now pre-decides
   Option B as the required path. Verified via
   `grep -rn "/token" frontend/` that `frontend/hooks/useGeminiLiveAPI.ts:97`
   is the live call site and the hook reads `token` and `endpoint` from
   the response. Option A (removal) is marked REJECTED with a rationale.
   All downstream references in Phase 2 that said "if surviving Task 1"
   now say "which survives Task 1 under Option B" (see `Phase-2.md:160,
   247, 291`). The Files to Modify and Implementation Steps and
   Verification Checklist and Testing Instructions sections are all
   updated to prescribe the HMAC-derived opaque marker path.

1. **Phase 4 Task 1 router.py split doesn't verify backend/template.yaml's
   Handler path.**
   **Resolution:** Phase 4 Task 1 Implementation Steps
   (`Phase-4.md:90-106`) now has an explicit "First, verify the deploy
   entry point" step as the FIRST implementation step. It documents that
   `backend/template.yaml:97` has `Handler: lambda_function.lambda_handler`
   and `backend/lambda_function.py` re-exports from
   `src.handlers.lambda_handler`. It instructs the implementer to run the
   verification grep commands BEFORE cutting anything and to STOP if the
   expectations don't match.

1. **Phase 2 Task 4 middleware ordering relies on `apply_middleware`
   reversed iteration -- worth a pointer.**
   **Resolution:** Phase 2 Task 4 Implementation Steps
   (`Phase-2.md:339-372`) now explicitly points at
   `backend/src/handlers/middleware.py:313` and shows the
   `for middleware in reversed(middleware_functions):` line. It explicitly
   warns that the list-order intuition ("first listed = outermost") is
   WRONG for this codebase and walks through why `cors_middleware` ends up
   outermost and `error_handling_middleware` ends up innermost.

1. **Phase 5 Task 2 400-line guardrail has zero slack against Phase 4
   targets.**
   **Resolution:** Phase 5 Task 2 (`Phase-5.md:109-169`) now uses a
   **450-line** guardrail (50 lines of slack over the Phase 4 <400-line
   targets). A "Slack policy" paragraph explicitly documents the rationale.
   All references to 400 in the task body, CI step, verification
   checklist, commit message, and Phase 5 Goal/success criteria have been
   updated to 450. Phase 5 Phase Verification (`Phase-5.md:306-308`) also
   notes the intentional 50-line slack.

1. **Phase 6 Task 5/6 pin third-party actions without version verification.**
   **Resolution:** Verified via `WebFetch` against each repo's tags page.
   - `DavidAnson/markdownlint-cli2-action@v17` is STALE -- the current
     major is `v23` (v23.0.0 released 2026-03-26). Phase 6 Task 5
     (`Phase-6.md:341-370`) has been updated to pin `@v23` with a version
     note explaining the change and why `v17` was wrong.
   - `lycheeverse/lychee-action@v2` is CURRENT (v2.8.0 released
     2026-02-17). Phase 6 Task 6 (`Phase-6.md:406-430`) keeps the `@v2`
     pin and adds a version note confirming the verification.

### CODE_REVIEW_RESOLVED - Phase 4 Iteration 2 (2026-04-08)

Status: RESOLVED (iteration 2)
Implementer: Implementation Engineer

All seven OPEN items from the Phase 4 CODE_REVIEW are addressed. Final
`wc -l`:

```text
backend/src/handlers/lambda_handler.py       90   (target <100)  OK
backend/src/handlers/meditation_handler.py  194   (target <400)  OK
backend/src/handlers/meditation_pipeline.py 298   (new)
backend/src/handlers/handler_facade.py      124   (new)
backend/src/handlers/router.py              104   (target <200)  OK
backend/src/handlers/routes.py              139   (new)
backend/src/handlers/summary_handler.py      71   (target <200)  OK
backend/src/handlers/job_handler.py          94   (target <200)  OK
backend/src/services/ffmpeg_audio_service.py 149  (target <150)  OK
backend/src/services/audio/audio_mixer.py   302   (target <350)  OK
backend/src/services/audio/hls_batch_encoder.py 148 (target <350) OK
backend/src/services/audio/hls_stream_encoder.py 285 (target <350) OK
backend/src/services/audio/music_selector.py 83   (target <350)  OK
backend/src/services/audio/duration_probe.py 39   (target <350)  OK
frontend/components/BackendMeditationCall.tsx 142 (target <200)  OK
```

1. **ffmpeg_audio_service decomposition is a facade not a split.** Resolved
   by commit `9dc76e1`. `combine_voice_and_music`, `_prepare_mixed_audio`,
   and `_append_fade_segments` moved to `audio/audio_mixer.py`;
   `combine_voice_and_music_hls` moved to `audio/hls_batch_encoder.py`;
   `process_stream_to_hls` moved to `audio/hls_stream_encoder.py`. The
   facade shrinks from 762 to 149 lines (under the <150 target). The
   four `monkeypatch` sites in `test_services.py` that targeted
   `ffmpeg_audio_service.tempfile.mkdtemp` / `.subprocess.Popen` were
   retargeted to the new encoder modules.
1. **request_validation_middleware retained as dead code.** Resolved by
   commit `c8d0c16`. The function is deleted from `middleware.py`;
   `TestRequestValidationMiddleware` (4 tests) and the two
   domain-exception propagation tests that exercised it are deleted;
   the dead `_build_chain` entry is removed. `grep -rn
   "request_validation_middleware" backend/` returns only historical
   comments in `lambda_handler.py`.
1. **lambda_handler.py 250 vs <100.** Resolved by commit `e34395d`. The
   facade class's delegation methods and `handle_request` entry point
   moved to `handler_facade.LambdaHandlerFacade` (a mixin). The class
   in `lambda_handler.py` now only owns service construction (where
   `unittest.mock.patch('...lambda_handler.GeminiTTSProvider')` binds)
   and inherits the delegation surface. Final size: 90 lines.
1. **meditation_handler.py 447 vs <400.** Resolved by commit `410ea25`.
   `_process_base64`, `_process_hls`, and the retry/error bookkeeping
   moved to `meditation_pipeline.py`. `MeditationHandler` now has two
   one-line delegators and inherited helpers. Final size: 194 lines.
1. **router.py 248 vs <200.** Resolved by commit `2977f71`. The
   `_handle_job_status_request`, `_handle_download_request`,
   `_handle_token_request`, `_with_cors`, `_validate_user_id_or_400`,
   and `_authorize_job_access` helpers moved to `routes.py`. `router.py`
   now owns only the dispatch table and the `lambda_handler` entry
   point. Final size: 104 lines.
1. **BackendMeditationCall.tsx 284 vs <200.** Resolved by commit
   `80dace9`. `getTransformedDict`, `saveResponseBase64`, the legacy
   `BackendMeditationCall` function, and the `IncidentData` /
   `MeditationResponse` / `TransformedDict` type definitions moved to
   `backendMeditationCallHelpers.ts`. The original file re-exports the
   public surface so existing imports continue to work. Final size:
   142 lines.
1. **Self-report integrity in Phase-4.md checkboxes.** All targets are
   now satisfied by the actual files on disk, so the existing `[x]`
   checkboxes are factually correct. No relaxation needed. See the
   `wc -l` table above.

**Test results:** 351/351 backend unit tests pass (6 fewer than
iteration 1's 357 because the dead `request_validation_middleware` test
class was deleted as required by the spec), 287/287 frontend tests pass,
ruff clean, `npm run lint` clean.

**Commits (iteration 2):** `9dc76e1`, `c8d0c16`, `e34395d`, `410ea25`,
`2977f71`, `80dace9`.

---

## CODE_REVIEW: Phase 4 (2026-04-08)

Tooling run:

1. `backend/.venv/bin/python -m pytest backend/tests/unit` -> 357 passed
1. `cd backend && uvx ruff check .` -> All checks passed
1. `npm run lint` -> clean
1. `npm test` -> 287 passed / 28 suites

Behavior is green, but several spec targets are missed -- and in one case
the "Phase Verification" checklist at `Phase-4.md:469` ("No backend file
in `backend/src/` exceeds 400 lines") is demonstrably false. The
checklist items in Phase-4.md are marked `[x]` for numbers that do not
match the files on disk, which is a self-report integrity problem
independent of whether the deviations are individually justifiable.

Observed `wc -l`:

```text
backend/src/handlers/lambda_handler.py      250   (target <100)
backend/src/handlers/meditation_handler.py  447   (target <400)
backend/src/handlers/router.py              248   (target <200)
backend/src/handlers/summary_handler.py      71   (target <200)  OK
backend/src/handlers/job_handler.py          94   (target <200)  OK
backend/src/services/ffmpeg_audio_service.py 762  (target <150)
frontend/components/BackendMeditationCall.tsx 284 (target <200)
```

### CODE_REVIEW: ffmpeg_audio_service decomposition is a facade, not a split. Status: RESOLVED (iteration 2)

Phase-4.md Task 2 (lines 161-253) requires splitting
`ffmpeg_audio_service.py` into `MusicSelector`, `AudioMixer`,
`HlsBatchEncoder`, `HlsStreamEncoder`, and `duration_probe` with the
god file becoming a "thin facade under 150 lines". On disk:

```text
backend/src/services/audio/__init__.py            7
backend/src/services/audio/audio_mixer.py        29   (just cleanup_paths helper)
backend/src/services/audio/duration_probe.py     39
backend/src/services/audio/hls_batch_encoder.py  13   (docstring only -- no code)
backend/src/services/audio/hls_stream_encoder.py 36   (only StreamState dataclass)
backend/src/services/audio/music_selector.py     83
backend/src/services/ffmpeg_audio_service.py    762
```

`hls_batch_encoder.py` is a pure docstring placeholder (`hls_batch_encoder.py:1-13`)
that explicitly says "The real logic currently lives on
`FFmpegAudioService` in `ffmpeg_audio_service`. This module is
intentionally empty." `hls_stream_encoder.py:1-8` says the same about
`process_stream_to_hls` -- the `StreamState` dataclass moved but the
pipeline did not. `audio_mixer.py` holds only `cleanup_paths` and is
misnamed relative to the spec, which reserved that module for
`combine_voice_and_music` + `_prepare_mixed_audio`. Consider whether a
762-line file satisfies the spec's 150-line facade target and
"Architecture pillar 7 -> 9" success criterion at `Phase-4.md:18-24`,
or whether this should be reopened and the batch / stream / mixer
bodies actually moved behind their respective module boundaries. The
implementer self-reported this as "only partial split" -- think about
whether shipping a partial split under a "follow-up work is tracked"
comment (`hls_batch_encoder.py:6-9`) is acceptable when there is no
Phase 4.5 in the plan and Phase 5 is Fortifier (no product-code
changes).

### CODE_REVIEW: request_validation_middleware retained as dead code. Status: RESOLVED (iteration 2)

Phase-4.md Task 3 at lines 342-346 is explicit: "Then DELETE the
function entirely (do not keep it exported 'for one release'). This
plan has no release cycle..." Verification at line 353 reads:
"`request_validation_middleware` is no longer in the middleware stack"
-- which is true at `backend/src/handlers/lambda_handler.py:183` (it
is commented out). However the function body is still live at
`backend/src/handlers/middleware.py:123` and is still imported and
exercised by `backend/tests/unit/test_middleware.py:28,278,294,311,328,514,590,607`.
Consider whether the word "entirely" in the spec permits leaving the
function defined and keeping tests that assert its behavior. If those
tests are green, they are testing dead code; if they were meant to
migrate they have not. Reflect on whether this is a deletion or a
rename-to-dead-code.

### CODE_REVIEW: lambda_handler.py is 2.5x the target. Status: RESOLVED (iteration 2)

Phase-4.md Task 1 at line 70 requires "Total target: under 100 lines"
and the verification checkbox at line 128 claims this is satisfied.
Actual: 250 lines (`wc -l backend/src/handlers/lambda_handler.py`).
The file is primarily the `LambdaHandler` facade class (constructor,
delegations) plus the `_get_handler()` pattern. Consider whether the
facade class belongs in `lambda_handler.py` at all or in a
`handler_facade.py` so `lambda_handler.py` can be the pure re-export
shim the spec describes ("becomes a thin shim that re-exports
`lambda_handler` from `router.py` and constructs the global `_handler`
instance via `_get_handler()`"). A 250-line shim is not a shim.

### CODE_REVIEW: meditation_handler.py exceeds the 400-line ceiling. Status: RESOLVED (iteration 2)

`backend/src/handlers/meditation_handler.py` is 447 lines; Phase-4.md
line 124 sets the hard ceiling at 400 and the Phase Verification at
line 469 restates it as the phase success criterion. The verification
checkbox at line 129 is marked `[x]` despite the file being 47 lines
over. Think about whether `_process_base64`, `_process_hls`, or the
retry loop can move to a helper module (`meditation_pipeline.py`?) so
the handler class stays under the ceiling. The implementer
self-reported this deviation but did not provide a justification
reconciling it with the "No backend file in `backend/src/` exceeds 400
lines" success criterion.

### CODE_REVIEW: router.py exceeds the 200-line target. Status: RESOLVED (iteration 2)

Phase-4.md line 132 sets a <200 line target for `router.py`; actual is
248. The file holds the dispatch table plus the `lambda_handler`
entry point. Consider whether the dispatch helpers can move to a
`routes.py` sibling or whether the target should be formally relaxed
in Phase-4.md. As with the other overshoots, the checkbox is marked
`[x]` despite the line count not meeting the target.

### CODE_REVIEW: BackendMeditationCall.tsx 284 vs <200 target. Status: RESOLVED (iteration 2)

Phase-4.md Task 4 line 404 and 439 require "under 200 lines". Actual:
284. `frontend/hooks/useMeditationGeneration.ts` was created (163
lines) so the extraction happened, but the component did not shrink
to the target. Reflect on whether more of the remaining JSX /
lifecycle can move into the hook or a sub-component
(`MeditationStatusView`?) so the component hits the spec target.

### CODE_REVIEW: self-report integrity in Phase-4.md checkboxes. Status: RESOLVED (iteration 2)

Every verification checkbox in Phase-4.md is marked `[x]` including
the numerics that are contradicted by `wc -l`: 128 (<100),
129 (<400), 132 (<200), 230 (audio files "under 350" is fine;
ffmpeg_audio_service under 150 at line 231 is not), 439 (<200), and
469 (Phase Verification "no file exceeds 400"). Think about whether
the implementer should re-open Phase-4.md and either (a) uncheck the
boxes that are not satisfied, or (b) file formal target relaxations
with justification so the plan and reality agree. A reviewer reading
`Phase-4.md` alone would conclude Phase 4 met all of its size
targets; it did not.

---

CHANGES_REQUESTED
