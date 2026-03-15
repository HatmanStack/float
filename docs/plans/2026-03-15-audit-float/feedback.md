# Feedback: 2026-03-15-audit-float

## Active Feedback

_No active feedback._

## Resolved Feedback

### PLAN_REVIEW-1: Phase 3 Task 1 — Missing `S101` per-file-ignores for test directory

**Resolution:** Addressed in Phase-3.md revision. Changes made:
1. Added explicit Step 4 with `[tool.ruff.lint.per-file-ignores]` section containing `"tests/**" = ["S101"]`, with explanation of why `S101` must not be globally ignored.
2. Replaced vague Step 5 with an enumerated list of specific rule codes the implementer will encounter: `S101` (tests, handled by per-file-ignores), `S108` (53 /tmp usages), `S311` (2 pseudo-random), `UP006` (122 instances), `UP045` (82 instances), `UP035` (31 instances), `B017` (6 instances), `B904` (4 instances, with guidance to optionally fix), `B023` (1 instance), and remaining minor UP codes. All are pre-added to the `ignore` list in the plan's config snippet with comments.
3. Added verification checklist items confirming `per-file-ignores` exists and `S101` is NOT in the global ignore list.
4. Updated commit message template to reflect per-file-ignores addition.
