# Feedback Log

This file is the single communication channel between Planner, Plan Reviewer,
Implementer, Reviewer, and Final Reviewer for plan
`2026-04-08-audit-float`. Plan documents are never mutated by reviewers --
all feedback lives here.

See `.claude/skills/pipeline/pipeline-protocol.md` for the canonical
schema and rules.

## Active Feedback

### PLAN_REVIEW - Iteration 1 - README.md and Phase coverage

Status: OPEN
Reviewer: Plan Reviewer (Tech Lead)

The plan is well structured, tagged correctly (HYGIENIST -> IMPLEMENTER ->
FORTIFIER -> DOC-ENGINEER), and the overall scope matches the three intake
docs. However, several cross-reference and coverage issues will confuse a
zero-context implementer and at least one intake finding is effectively
uncovered. The issues are grouped from most to least severe.

1. Health Audit coverage table (`README.md:69-96`) has two wrong
   task numbers that send the implementer to the wrong task file.

   - `README.md:74` maps "Routing via `rawPath` string matching" to
     Phase 2 Task 2, but Phase 2 Task 2 is "Add `user_id` validator and
     tighten authorization" (`Phase-2.md:135`). The dispatch-table work
     is actually Phase 2 Task 3 (`Phase-2.md:220`).
   - `README.md:84` maps "Middleware `except Exception` swallows taxonomy"
     to Phase 4 Task 3, but Phase 4 Task 3 is "Collapse dual validation
     and tighten event/job typing" (`Phase-4.md:233`). The middleware
     narrowing work is actually Phase 2 Task 4 (`Phase-2.md:304`).

   Consider: if an implementer grepped the README for their finding and
   went straight to the referenced task, would they find the work or get
   lost?

1. `README.md:89` claims "Backend ~57 `except Exception` clauses" is
   covered by Phase 4 Task 3. Phase 4 Task 3 (`Phase-4.md:233-347`) only
   removes `request_validation_middleware` from the middleware stack and
   adds TypedDicts. It does not address the 57 catch-all clauses across
   `backend/src/` (verified: 57 hits spread across 13 files, including
   8 in `job_service.py`, 11 in `hls_service.py`, 7 in
   `ffmpeg_audio_service.py`). No other phase addresses them either.

   Consider: is this finding actually in scope, or should the coverage
   table move it to "Out of Scope" with a justification? If in scope,
   which phase/task owns the narrowing work and how does the verifier
   confirm it landed?

1. Phase 0 ADR-3 (`Phase-0.md:135-137`) promises Phase 3 will "extend
   [`S3StorageService`] with conditional-write helpers" and the README
   Performance pillar row (`README.md:103`) claims Phase 3 covers
   "ETag/race". Phase 3 has no task for conditional writes. Phase 3
   Task 1 addresses *in-memory* thread safety in `process_stream_to_hls`
   but does not touch `job_service.update_streaming_progress`. Phase 3's
   own Known Limitations section (`Phase-3.md:449-451`) admits the race
   still exists. The Stress eval critical failure #3
   (`eval.md:58`) is therefore not mitigated.

   Consider: does the Performance pillar move from 5 to 9 without the
   ETag work? If ETag writes are in scope, where is the task? If they
   are out of scope, should ADR-3 and the coverage table be corrected
   so the claim matches reality?

1. `backend/tests/unit/test_ffmpeg_audio_service.py` is referenced as
   "Modify" in Phase 1 Task 4 (`Phase-1.md:222`), Phase 3 Task 1
   (`Phase-3.md:50`), and Phase 3 Task 3 (`Phase-3.md:204`). The file
   does not exist in the repo. Actual backend unit tests are in
   `backend/tests/unit/test_services.py` (1473 lines per the health
   audit), `test_lambda_handler.py`, `test_middleware.py`,
   `test_hls_service.py`, `test_request_validation.py`, etc.

   Similarly, `backend/tests/unit/test_job_service.py` is referenced in
   Phase 4 Task 3 verification (`Phase-4.md:335`) but does not exist.
   Job service tests also live in `test_services.py`.

   Consider: should the "Files to Modify" lines say "Create" (adding a
   new focused test file) or "Modify" (adding tests to the existing
   `test_services.py`)? The ambiguity will either produce a new file in
   the wrong location or leave tests in an oversized file. Pick one and
   be explicit.

1. Phase 3 Task 5 (`Phase-3.md:359-431`) lists raw `Exception` sites as
   `ffmpeg_audio_service.py:200, 220, 290, 751, 761, 773` but:

   - Line 200 is actually line 199 in current source (minor drift).
   - Line 290 is in `lambda_handler.py`, not `ffmpeg_audio_service.py`
     (verified via `grep -rn "raise Exception(" backend/src/`). The
     message "Failed to download cached TTS audio" lives in
     `lambda_handler.py:290`.
   - `ffmpeg_audio_service.py:557` also has
     `raise Exception(f"Failed to upload fade segment {segment_index}")`
     in `_append_fade_segments` and is not listed in the task.

   The task's grep-based verification (`Phase-3.md:408`) would still
   catch line 557, so the Phase Verification gate is not broken. But the
   explicit list is misleading.

   Consider: update the enumerated list to match actual code, or rely
   solely on the grep and drop the explicit line numbers. Mixing the two
   invites confusion.

1. Phase 1 Task 6 (`Phase-1.md:363-372`) instructs the implementer to
   re-check `ffmpeg_audio_service.py:76` for an f-string + `extra=` mix,
   then admits the line is already correct on inspection and tells the
   implementer to "document the discrepancy in the commit message and
   skip". The actual f-string log (without `extra=`) occurs at line 83:
   `logger.warning(f"Error getting audio duration: {e}")`. This is a
   different convention violation (f-string-only, no structured data)
   than what Phase 0 forbids (mixed f-string + `extra=`).

   Consider: does this sub-task have any concrete work for the
   implementer? If the target line is 83 and the actual issue is the
   absence of structured logging, say so. If it should be dropped,
   remove the sub-item and the commit-message bullet. As written the
   implementer is told to do nothing and write a commit message about
   doing nothing.

1. Phase 1 Task 4 (`Phase-1.md:211-264`) removes
   `_get_audio_duration_from_file`. Five tests in `test_services.py`
   currently mock this private method (lines 1162, 1204, 1229, 1252,
   1277 per `grep -rn "_get_audio_duration_from_file"`). Task 4 mentions
   "`backend/tests/unit/test_services.py` (or whichever test covers the
   helper) -- update if it references the private method" but the
   implementer will not know how many sites to update without re-running
   the grep.

   Consider: list the five mock sites explicitly, or say "`patch.object`
   calls on `_get_audio_duration_from_file` must be retargeted to
   `get_audio_duration`" so the implementer knows the scope.

1. Phase 4 Task 3 (`Phase-4.md:315-317`) removes
   `request_validation_middleware` from the decorator stack but says to
   "Keep the function exported (deprecate via docstring) for one release
   in case any test or external caller imports it." There is no external
   release cycle in scope for this plan; the phase sequence is one merge
   per phase. Once Phase 4 ships the plan is complete and no "next
   release" exists.

   Consider: is the deprecation comment prescribing behavior that
   matches this plan, or is it leftover boilerplate from a longer-lived
   deprecation process? If the function can be deleted outright, do so;
   if it must stay, cite the specific downstream importer that requires
   it.

1. Phase 5 Task 3 (`Phase-5.md:204-211`) instructs the fortifier to run
   `uvx ruff check --select UP006 .` and re-enable rules whose violators
   are zero. This tries to flip rules in the same phase the fortifier
   *measures* them, but if any module still has `List`/`Dict` imports
   the rule stays in the ignore list. Phase 0's ADR-4 forbids Phase 1
   from modernizing legacy imports, and Phase 4 Task 3 only adds
   TypedDicts without touching the legacy generics in
   `lambda_handler.py:5` (listed in the LOW section of the health audit).
   So the predictable outcome is that UP006/UP007/UP035 stay ignored
   and Task 3 produces no net change beyond adding comments.

   Consider: is this task intended to produce zero rule changes in the
   common case? If so, say so explicitly so the reviewer does not expect
   a meaningful diff. If modernization is expected, which phase
   actually modernizes the legacy typing imports in `lambda_handler.py`
   so UP006 becomes achievable?

1. Phase 2 Task 1 (`Phase-2.md:56-59`) tells the implementer to
   "Consult `git log --oneline -- frontend/components/AuthScreen.tsx`
   and `frontend/components/AudioRecording.tsx` to determine the call
   site status" before picking Option A vs Option B. Leaving a
   CRITICAL security fix on a git-archaeology decision introduces
   ambiguity: two implementers might reach opposite conclusions. The
   actual call site can be verified in under a minute with
   `grep -rn "/token" frontend/`.

   Consider: run the grep now, document the current call-site status in
   the task (e.g., "as of 2026-04-08, `AuthScreen.tsx:XXX` calls
   `/token` via fetch; the frontend counterpart lives in component X"),
   and explicitly name Option A or B as the required path. Leaving the
   choice open for a security-critical endpoint invites scope creep.

1. Phase 4 Task 1 (`Phase-4.md:42-141`) creates
   `backend/src/handlers/router.py` that holds the top-level
   `lambda_handler(event, context)` entry point while the existing
   `backend/lambda_function.py` (per `Phase-0.md:227`) imports
   `lambda_handler` from `src.handlers.lambda_handler`. Phase 4 Task 1
   instructs the implementer to turn `lambda_handler.py` into a "thin
   shim that re-exports `lambda_handler` from `router.py`." The SAM
   template's `Handler:` entry point is not verified in the plan --
   if `backend/template.yaml` points at
   `src.handlers.lambda_handler.lambda_handler` the re-export works; if
   it points at the new `router` module the plan would need to update
   SAM.

   Consider: verify `backend/template.yaml`'s `Handler:` path before
   committing to the re-export shim. Add the verification step
   explicitly to Task 1's Implementation Steps so the implementer
   cannot skip it and break the deploy target.

1. Phase 2 Task 4 (`Phase-2.md:340-357`) correctly notes middleware
   wrapping order but the claim hinges on the `apply_middleware` helper
   reversing its arguments. A zero-context implementer reading the
   decorator list at `lambda_handler.py:536-543` will intuitively assume
   the first-listed middleware is outermost. The task tells them "CORS
   is the outermost" which is correct under the reversed-iteration
   wrapper (`middleware.py:313` uses `for middleware in reversed(...)`).
   But they may not trust the assertion without verifying.

   Consider: add a one-line pointer to `middleware.py:313` showing the
   `reversed(...)` iteration so the implementer can verify the claim
   themselves instead of taking it on faith.

1. Phase 5 Task 2 (`Phase-5.md:109-168`) adds a 400-line guardrail on
   `backend/src/**/*.py`. Phase 4 Task 2 (`Phase-4.md:205`) asserts
   "`wc -l backend/src/services/audio/*.py` shows every file under 350
   lines" and Phase 4 Task 1 verification asserts `meditation_handler.py
   < 400`. The guardrail's cutoff matches the Phase 4 target exactly,
   leaving no slack. If Phase 4 produces a 398-line file that later
   grows to 402 the guardrail fires on an unrelated PR.

   Consider: set the guardrail to 450 or 500 lines to provide breathing
   room, or explicitly document the zero-slack policy in Phase 5 so
   reviewers know to expect CI failures on incidental growth.

1. Phase 6 Task 5 (`Phase-6.md:347`) pins
   `DavidAnson/markdownlint-cli2-action@v17` and Phase 6 Task 6
   (`Phase-6.md:406`) pins `lycheeverse/lychee-action@v2`. The rest of
   the CI uses `actions/setup-node@v6`, `actions/checkout@v6`, etc.
   These are third-party actions; verify the versions exist before
   merging.

   Consider: cite the tag/release that currently exists on each action
   or pin to a SHA to prevent the CI from failing with
   "action not found" on the very first run of the new job.

---

## Resolved Feedback

_(none yet)_

---
