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

---
