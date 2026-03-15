# Feedback: 2026-03-15-audit-float

## Active Feedback

_No open items._

## Resolved Feedback

### PLAN_REVIEW-2: Phase 5 Task 1 — `_save_job` callers mostly lack try/except

**Resolution:** Addressed in Phase-5.md revision. The plan already enumerated all 9 call sites (lines 103, 123, 157, 186, 212, 234, 245, 256, 267; line 365 is the definition, not a caller). Changes verified/confirmed:
1. Step 4 classifies all 9 callers as **fatal** (3: `create_job`, `update_job_status`, `mark_streaming_complete`) or **non-fatal** (6: `update_streaming_progress`, `mark_streaming_started`, `mark_download_ready`, `mark_download_completed`, `set_tts_cache_key`, `increment_generation_attempt`).
2. Step 5 provides a try/except wrapper pattern for all 6 non-fatal callers with explicit method names.
3. Step 6 confirms fatal callers need no change -- `ExternalServiceError` propagates to existing try/except in `lambda_handler.py`.

---

### PLAN_REVIEW-3: Phase 5 Task 3 — `toIncident` mapping is incomplete

**Resolution:** Addressed in Phase-5.md revision. Changes made:
1. Added new Step 3 that instructs implementer to update `SummaryResponse` interface to include `user_summary` and `user_short_summary` fields (returned by backend `SummaryResponse` dataclass and used by `IncidentItem.tsx`).
2. Expanded `toIncident` mapping to include all 9 overlapping fields: `timestamp`, `sentiment_label`, `intensity`, `summary`, `speech_to_text`, `added_text`, `notificationId` (mapped from `notification_id`), `user_summary`, `user_short_summary`.
3. Added detailed JSDoc comment to `toIncident` documenting which fields are intentionally dropped (`color_key` -- not part of `Incident` type) and why.
4. Updated verification checklist to include `user_summary`/`user_short_summary` mapping and `color_key` drop comment.

---

### PLAN_REVIEW-4: Phase 5 Task 4 — `pydantic-settings` not in requirements.txt

**Resolution:** Addressed in Phase-5.md revision. Changes made:
1. Moved `pydantic-settings` dependency installation to Step 1 (was Step 7). Step 1 now explicitly states "This MUST be done first, before any code changes."
2. Removed the contradictory two-version approach. Step 3 now provides a single, definitive `Settings` class that includes `AliasChoices("GEMINI_API_KEY", "G_KEY")` on the `GEMINI_API_KEY` field. The old Step 4 (which presented a wrong version then corrected it) has been eliminated entirely.
3. Reduced total steps from 7 to 5 by consolidating.

---

### PLAN_REVIEW-5: Phase 7 Task 3 — Pre-commit hook approach is ambiguous

**Resolution:** Addressed in Phase-7.md and Phase-8.md revisions. Changes made:
1. Phase 7 Task 3 now commits exclusively to `husky` + `lint-staged`. The Python `pre-commit` alternative has been removed entirely. Task title changed to "Add pre-commit hooks with husky + lint-staged." Rationale documented: npm-workspace-based repo, Phase 8 uses commitlint (npm), keeps all hooks in one ecosystem.
2. Phase 7 Task 4 (CONTRIBUTING.md) updated to reference `npm run prepare` instead of `pip install pre-commit`.
3. Phase 7 Task 5 (setup script) updated to remove pre-commit conditional.
4. Phase 7 verification updated to check `.husky/pre-commit` instead of `.pre-commit-config.yaml`.
5. Phase 8 Task 1 updated: removed `pre-commit` YAML alternative for commitlint, now only provides husky `.husky/commit-msg` instructions. Prerequisite updated to "(husky installed)" instead of "(pre-commit or husky installed)".
6. Phase 8 Task 3 verification table updated to check `.husky/pre-commit` instead of `.pre-commit-config.yaml`.
7. Phase 8 final file inventory updated accordingly.

---

### PLAN_REVIEW-6: Phase 6 Task 3 — End-to-end test fixture assumes constructor API

**Resolution:** Addressed in Phase-6.md revision. Changes made:
1. Added new Step 3 before writing the fixture: "Inspect the `LambdaHandler.__init__` signature" with a grep command and the expected output showing `ai_service` and `validate_config` kwargs.
2. Added an explicit note in the fixture docstring: "NOTE: Verify LambdaHandler.__init__ accepts these kwargs. If the constructor signature differs, adapt accordingly."
3. Renumbered subsequent steps (old 4->5, old 5->6).

---

### PLAN_REVIEW-7: Phase 6 Task 1 — Assertion replacement is speculative

**Resolution:** Addressed in Phase-6.md revision. Changes made:
1. Replaced the speculative "use toBeNull or toBeDefined" guidance with a concrete multi-step observation process: (a) run existing test to confirm infrastructure works, (b) temporarily add `console.log` to observe `result.current`, (c) run again and read output, (d) write assertion matching observed behavior.
2. Provided a decision matrix: null -> `toBeNull()`, undefined -> `toBeUndefined()`, object -> `toEqual(expected)`, function/tuple -> `toBeDefined()`.
3. Added explicit "remove console.log" cleanup step.
4. The implementer no longer guesses -- they observe and then assert.

---

### PLAN_REVIEW-8: Phase 7 Task 2 — Docker verification cannot run in CI

**Resolution:** Addressed in Phase-7.md and Phase-8.md revisions. Changes made:
1. Added Step 5 to Phase 7 Task 2: add a `dockerfile-lint` CI job using `hadolint/hadolint-action@v3.1.0` to lint `backend/Dockerfile` on every push/PR.
2. Instructions include adding `dockerfile-lint` to the `status-check` job's `needs` array and its conditional check.
3. Updated verification checklist to include "`dockerfile-lint` job added to CI" and "`status-check` includes `dockerfile-lint`."
4. Testing instructions clarify: Docker build/run is local-only; CI validates Dockerfile syntax via hadolint.
5. Phase 8 Task 3 Reproducibility verification updated to check for `dockerfile-lint` in CI config.

---

### PLAN_REVIEW-1: Phase 3 Task 1 — Missing `S101` per-file-ignores for test directory

**Resolution:** Addressed in Phase-3.md revision. Changes made:
1. Added explicit Step 4 with `[tool.ruff.lint.per-file-ignores]` section containing `"tests/**" = ["S101"]`, with explanation of why `S101` must not be globally ignored.
2. Replaced vague Step 5 with an enumerated list of specific rule codes the implementer will encounter: `S101` (tests, handled by per-file-ignores), `S108` (53 /tmp usages), `S311` (2 pseudo-random), `UP006` (122 instances), `UP045` (82 instances), `UP035` (31 instances), `B017` (6 instances), `B904` (4 instances, with guidance to optionally fix), `B023` (1 instance), and remaining minor UP codes. All are pre-added to the `ignore` list in the plan's config snippet with comments.
3. Added verification checklist items confirming `per-file-ignores` exists and `S101` is NOT in the global ignore list.
4. Updated commit message template to reflect per-file-ignores addition.
