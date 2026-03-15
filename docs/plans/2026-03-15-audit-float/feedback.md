# Feedback: 2026-03-15-audit-float

## Active Feedback

### PLAN_REVIEW-1: Phase 3 Task 1 — Missing `S101` per-file-ignores for test directory

**Severity:** Blocking — implementer will encounter 279+ `S101` (use of `assert`) violations across 5 test files when enabling the `S` (bandit) ruleset.

**Problem:** The plan says to add `S` rules and then "add specific rule codes to the `ignore` list" for pre-existing violations. However, `S101` should NOT be globally ignored — `assert` in production code is a legitimate bandit finding. The correct fix is a `per-file-ignores` configuration that exempts the `tests/` directory from `S101`.

**Required change to Phase 3 Task 1, Step 3:** After the `ignore` list, add a `per-file-ignores` section:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]  # assert is expected in test files
```

Also add this to the implementation steps explicitly so the implementer does not waste time debugging hundreds of false positives or globally suppressing a useful rule.

**Additionally:** Step 5 says "If there are new violations from `UP`, `B`, or `S` rules that are pre-existing issues outside the scope of this remediation, add specific rule codes to the `ignore` list with a comment explaining why." This instruction is too vague for a zero-context implementer. It should enumerate the most likely rule codes that will fire (at minimum `S101` for tests, possibly `B904` for bare `raise` in exception handlers, `UP` style suggestions) so the implementer can distinguish expected noise from real issues introduced by their changes.

## Resolved Feedback

_No resolved feedback._
