# Feedback: 2026-03-15-audit-float

## Active Feedback

### PLAN_REVIEW-2: Phase 5 Task 1 — `_save_job` callers mostly lack try/except

**Severity:** HIGH
**Phase:** 5, Task 1

The plan claims all `_save_job` callers are "inside try/except blocks that can handle this" and lists only 3 callers. In reality, `_save_job` is called from **10 different locations** (lines 103, 123, 157, 186, 212, 234, 245, 256, 267, and 365). Most callers (e.g., `mark_streaming_started`, `mark_streaming_complete`, `mark_download_ready`, `mark_download_completed`, `set_tts_cache_key`, `increment_generation_attempt`) do NOT have local try/except blocks. If `_save_job` starts raising `ExternalServiceError`, these callers will propagate unhandled exceptions to their own callers.

**Required fix:** The plan must either:
1. Enumerate ALL 10 call sites and verify the full call chain handles the exception, OR
2. Recommend wrapping certain callers (e.g., `update_streaming_progress`, `mark_download_completed`) where a failed S3 write is non-fatal and should be logged-and-continued rather than raised, OR
3. Add a `raise_on_failure: bool = True` parameter to `_save_job` so callers can opt in/out.

Without this, the change risks turning non-critical S3 hiccups (e.g., updating streaming progress) into unhandled exceptions that crash the Lambda invocation.

---

### PLAN_REVIEW-3: Phase 5 Task 3 — `toIncident` mapping is incomplete

**Severity:** MEDIUM
**Phase:** 5, Task 3

The proposed `toIncident` function maps 7 fields but is missing fields that `Incident` supports and `SummaryResponse` may carry:
- `SummaryResponse.color_key` has no mapping (the plan acknowledges this in the description but the mapping function silently drops it).
- `Incident.user_summary` and `Incident.user_short_summary` are used by `IncidentItem.tsx` for display. If the API response includes these fields, the mapping must carry them through.

**Required fix:** The plan should instruct the implementer to:
1. Verify which fields the API actually returns (check `lambda_handler.py` summary response construction).
2. Map ALL overlapping fields, not just the 7 listed.
3. Explicitly document which `SummaryResponse` fields are intentionally dropped (e.g., `color_key`) with a comment in the mapping function.

---

### PLAN_REVIEW-4: Phase 5 Task 4 — `pydantic-settings` not in requirements.txt

**Severity:** MEDIUM
**Phase:** 5, Task 4

`requirements.txt` contains `pydantic>=2.0` but NOT `pydantic-settings`. The plan mentions checking for it (Step 1) and adding it (Step 7), but the implementation steps between (Steps 2-6) provide code that imports from `pydantic_settings` before the dependency is installed. The plan should reorder to make adding the dependency Step 1, not Step 7.

Additionally, the plan provides contradictory guidance on `validation_alias` vs `AliasChoices` for the `G_KEY` env var mapping (Steps 3 vs 4). Step 3 provides a complete file replacement that does NOT include the alias. Step 4 then says "However, `validation_alias` only applies to input data" and provides a different approach. The implementer will be confused about which version to use.

**Required fix:**
1. Move `pydantic-settings` dependency installation to Step 1.
2. Provide a single, definitive `Settings` class definition that includes the `AliasChoices` pattern for `G_KEY`. Do not provide a "wrong" version first and then correct it.

---

### PLAN_REVIEW-5: Phase 7 Task 3 — Pre-commit hook approach is ambiguous

**Severity:** MEDIUM
**Phase:** 7, Task 3

The plan presents two competing approaches (Python `pre-commit` vs npm `husky`+`lint-staged`) and tells the implementer to "Choose ONE approach." This violates the zero-context engineer principle -- the implementer should not be making architectural decisions. No `.husky` directory or `husky` dependency exists in the repo currently.

Furthermore, Phase 8 Task 1 depends on the outcome of this decision (it provides different instructions for husky vs pre-commit). This creates a decision dependency chain that a zero-context engineer cannot resolve without context.

**Required fix:** Pick one approach in the plan. Given that Phase 8 installs `commitlint` (an npm tool) and the repo is npm-workspace-based, the plan should commit to `husky`+`lint-staged` as the single approach and remove the `pre-commit` alternative. Update Phase 8 Task 1 accordingly.

---

### PLAN_REVIEW-6: Phase 6 Task 3 — End-to-end test fixture assumes constructor API

**Severity:** LOW
**Phase:** 6, Task 3

The test fixture creates `LambdaHandler(ai_service=mock_ai_service, validate_config=False)` but the plan does not verify that `LambdaHandler.__init__` accepts these keyword arguments. If the constructor signature differs (e.g., uses positional args, or does not have a `validate_config` parameter), the test will fail at fixture creation.

**Required fix:** Add a step to inspect the `LambdaHandler.__init__` signature before writing the fixture. The implementer should adapt the fixture to match the actual constructor API.

---

### PLAN_REVIEW-7: Phase 6 Task 1 — Assertion replacement is speculative

**Severity:** LOW
**Phase:** 6, Task 1

The plan proposes `expect(result.current).toBeNull()` but immediately hedges: "If `result.current` is not `null` in the error case, use `expect(result.current).toBeDefined()`." The implementer is told to guess what the hook returns under error conditions.

**Required fix:** Add a concrete step: "Run the existing test first to see what `result.current` actually is when `AsyncStorage.getItem` rejects, then write the assertion to match the observed behavior." This is a test -- the implementer can run it and observe.

---

### PLAN_REVIEW-8: Phase 7 Task 2 — Docker verification cannot run in CI

**Severity:** LOW
**Phase:** 7, Task 2

The verification checklist requires `docker build` and `docker compose run`, but the testing instructions note "If Docker is not available in CI, this is a local-only verification." This means the Docker setup has no CI verification -- it could break silently. The plan should either:
1. Add a CI step that validates the Dockerfile (even just `docker build --check` or a hadolint lint step), OR
2. Explicitly state this is local-only and add a note to Phase 8 Task 3's final sweep that Docker verification is manual.

## Resolved Feedback

### PLAN_REVIEW-1: Phase 3 Task 1 — Missing `S101` per-file-ignores for test directory

**Resolution:** Addressed in Phase-3.md revision. Changes made:
1. Added explicit Step 4 with `[tool.ruff.lint.per-file-ignores]` section containing `"tests/**" = ["S101"]`, with explanation of why `S101` must not be globally ignored.
2. Replaced vague Step 5 with an enumerated list of specific rule codes the implementer will encounter: `S101` (tests, handled by per-file-ignores), `S108` (53 /tmp usages), `S311` (2 pseudo-random), `UP006` (122 instances), `UP045` (82 instances), `UP035` (31 instances), `B017` (6 instances), `B904` (4 instances, with guidance to optionally fix), `B023` (1 instance), and remaining minor UP codes. All are pre-added to the `ignore` list in the plan's config snippet with comments.
3. Added verification checklist items confirming `per-file-ignores` exists and `S101` is NOT in the global ignore list.
4. Updated commit message template to reflect per-file-ignores addition.
