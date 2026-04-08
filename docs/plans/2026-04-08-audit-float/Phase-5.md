# Phase 5: Fortifier -- Lint, CI, Hooks, Type Guardrails [FORTIFIER]

## Phase Goal

Add guardrails that prevent regression of the work in Phases 1-4. This phase
introduces ZERO product-code changes -- it only adds lint rules, CI jobs,
pre-commit hooks, and type-checker configuration. Where a new lint rule
catches a violation, the fortifier fixes the lint surface (e.g. an
`# noqa` comment) but does NOT refactor the underlying code. If a guardrail
needs more than trivial fixes to pass, the fortifier raises feedback and the
plan iterates.

**Success criteria**

- A `pip-audit` CI job exists and runs against `backend/requirements.txt` on
  every PR
- A maximum-file-size lint rule (or CI assertion) prevents any backend
  Python file from exceeding **450 lines** (50 lines of slack over the
  Phase 4 targets to avoid spurious CI failures on incidental growth)
- Pre-commit hooks run `ruff check --fix` and a backend test smoke
- The CI workflow has an explicit job for the new pip-audit check
- Backend `mypy` config tightens for the modules touched in Phase 4
  (handlers and audio collaborators), without enabling strict mode globally
- A handful of `any` casts in `frontend/tests/unit/` are typed; no production
  code changes
- `npm run check` passes
- Estimated tokens: ~16000

## Prerequisites

- Phases 1-4 complete and merged
- `npm run check` passes on the merged tree

## Tasks

### Task 1: Add `pip-audit` CI job

**Goal:** The Phase 1 Task 2 dependency bump fixes the current CVEs, but
nothing prevents future drift. Add a CI job that runs `pip-audit` on every
PR.

**Files to Modify:**

- `.github/workflows/ci.yml` -- add a `pip-audit` job that depends on `changes`
  and runs only when the backend changed
- `backend/requirements-dev.txt` -- add `pip-audit` (pinned)

**Prerequisites:** Phase 1 Task 2 (dependency bump landed).

**Implementation Steps:**

- Add to `requirements-dev.txt`:
  ```text
  pip-audit==2.7.3
  ```
  (Pin to a known-good version; bump as needed.)
- Add a new job to `.github/workflows/ci.yml`:
  ```yaml
    pip-audit:
      name: Backend Dependency Audit
      runs-on: ubuntu-latest
      timeout-minutes: 10
      needs: changes
      if: needs.changes.outputs.backend == 'true'
      steps:
        - uses: actions/checkout@v6
        - uses: actions/setup-python@v6
          with:
            python-version: '3.13'
            cache: 'pip'
            cache-dependency-path: backend/requirements.txt
        - name: Install pip-audit
          run: pip install pip-audit
        - name: Audit
          working-directory: ./backend
          run: pip-audit -r requirements.txt
  ```
- Add `pip-audit` to the `status-check` job's `needs:` list so a failing
  audit blocks merges.
- Document in the workflow comments that the audit can be temporarily
  silenced via `--ignore-vuln <id>` for false positives, but only with a
  matching CHANGELOG entry.

**Verification Checklist:**

- [x] `.github/workflows/ci.yml` defines a `pip-audit` job
- [x] The `status-check` job lists `pip-audit` in `needs`
- [x] `requirements-dev.txt` pins `pip-audit`
- [x] Push the branch and verify the new job runs in CI; it should pass
      because Phase 1 Task 2 already bumped `requests`
- [x] `npm run check` passes locally (no functional change to existing checks)

**Testing Instructions:**

- This task ships in CI; local verification is `pip install pip-audit && cd
  backend && pip-audit -r requirements.txt`. Expect 0 vulnerabilities.

**Commit Message Template:**

```text
ci: add pip-audit job for backend dependency vulnerabilities

- Runs on every PR that touches backend/
- Blocks merge via status-check needs
- pip-audit pinned in requirements-dev.txt
```

---

### Task 2: Enforce maximum file size on backend Python sources

**Goal:** Phase 4 Task 1 and Task 2 reduced every backend `src/` file to under
400 lines. Add a guardrail that prevents new files from drifting past that
bound.

**Slack policy:** The guardrail is set to **450 lines**, not 400. Phase 4
targets 350-400 lines per extracted file (`meditation_handler.py < 400`,
`audio/*.py < 350`); a 50-line slack window prevents the guardrail from
firing on incidental growth from unrelated PRs (a docstring expansion, a
new method, a TypedDict definition). Files that approach 450 lines should
be split in a future plan, but the guardrail's job is to catch drift, not
to keep every file at the absolute floor. If the guardrail fires, the
correct response is "split this file in a follow-up plan", not "force the
unrelated PR to inline its work somewhere else".

The fortifier should choose between two equivalent approaches:

- **Option A:** A custom CI step using `find` + `wc -l` that fails if any
  `src/**.py` file exceeds **450 lines**. Cheap, no dependency.
- **Option B:** Add `flake8-max-file-length` or `pylint --max-module-lines`
  via a small additional dev dep. Heavier, more configurable.

Option A is preferred for simplicity. The fortifier MUST add the check and an
explanatory comment naming this plan ID.

**Files to Modify:**

- `.github/workflows/ci.yml` -- add a step in the `backend` job:
  ```yaml
        - name: File-size guardrail
          working-directory: ./backend
          run: |
            # Plan 2026-04-08-audit-float: no backend src file >450 lines
            # Phase 4 targets <400 lines; the 50-line slack prevents incidental
            # growth from firing the guardrail. See Phase 5 Task 2 for the
            # rationale and Phase 4 Task 1/2 for the underlying targets.
            offenders=$(find src -name '*.py' -print0 \
              | xargs -0 wc -l \
              | awk '$1 > 450 && $2 != "total" { print $2, $1 }')
            if [ -n "$offenders" ]; then
              echo "Files exceeding 450 lines:"
              echo "$offenders"
              exit 1
            fi
  ```

**Prerequisites:** Phases 1-4 complete (so no current file violates the
limit).

**Implementation Steps:**

- Verify locally first: `find backend/src -name '*.py' -print0 | xargs -0 wc
  -l | awk '$1 > 450 && $2 != "total"'`. The output must be empty.
- Add the step to the backend job in CI.
- Run the workflow on a feature branch to confirm it passes.

**Verification Checklist:**

- [x] Local `find ... | xargs wc -l | awk '$1 > 450'` is empty
- [x] CI step is in place and passes
- [x] A deliberate test (add a temporary 500-line file, push, see it fail,
      then revert) confirms the guardrail bites.

**Commit Message Template:**

```text
ci: enforce max 450-line backend Python files

- Phase 4 of plan 2026-04-08-audit-float decomposed two god objects to <400
- Guardrail set at 450 lines (50-line slack over Phase 4 targets)
- Prevents regression by failing CI if any src/**/*.py drifts past 450
```

---

### Task 3: Tighten ruff rules and pre-commit hooks

**Goal:** The current `pyproject.toml` ruff config has a long `ignore` list of
`UP*` rules that suppress modern-Python migrations. Phase 1 Task 6 cleaned the
logging convention; this task **measures** which `UP*` rules have zero
violators after Phases 1-4 and re-enables only those.

**Expected outcome (do not be surprised):** The most-cited rules
(`UP006`, `UP007`, `UP035`) WILL still have violators after Phase 4,
because the legacy `from typing import List, Dict, Optional, Union` imports
in `backend/src/handlers/lambda_handler.py:5` and several other files are
NOT modernized by any phase in this plan (see Phase 0 "Out of Scope" item
6 -- modernization is a separate plan). The Phase 4 TypedDict additions
use modern syntax in NEW files only; they do not touch the legacy generics
in existing files.

The realistic deliverable for this task is therefore one of:

1. Annotate every remaining `UP*` ignore in `pyproject.toml` with a
   one-line comment naming the rule and the violator count, e.g.
   `"UP006",  # 47 violators in lambda_handler.py and friends; defer to
   modernization plan`. This is the EXPECTED diff.
1. If by some chance a previously-ignored rule has zero violators
   (perhaps a small/obscure UP rule), remove it from the ignore list. Do
   not force this.

The reviewer should NOT expect a meaningful re-enable diff; the value of
this task is the documentation of the deferred work and the verification
that the husky pre-commit hook still runs ruff on the new Phase 4 files.

**Files to Modify:**

- `backend/pyproject.toml` -- annotate every remaining `UP*` ignore with a
  one-line comment naming the rule and the current violator count. Re-enable
  any rule whose count is zero (do not force the count down via refactor in
  this phase -- that violates ADR-1 fortifier scope).
  - `UP006` (use builtin `list`/`dict` over `List`/`Dict`) -- expected: still
    has dozens of violators in `lambda_handler.py` and other legacy files.
    Leave ignored, annotate with the count.
  - `UP007` (use `X | Y` over `Union[X, Y]`) -- expected: still has
    violators. Leave ignored, annotate.
  - `UP035` (deprecated typing imports) -- expected: still has violators.
    Leave ignored, annotate.
- `.husky/pre-commit` -- already runs `lint-staged`. Verify
  `package.json:lint-staged` covers `backend/**/*.py` and includes
  `ruff check --fix` (it does today). No change unless coverage is missing.
- `package.json` lint-staged section -- if a glob does not cover the new
  `backend/src/services/audio/` directory (it does, via `backend/**/*.py`),
  no change.

**Prerequisites:** Phase 1 Task 6 (logging convention) and Phase 4 Task 3
(typing updates).

**Implementation Steps:**

- Run `cd backend && uvx ruff check --select UP006 .` to count UP006
  violations. If 0, remove `UP006` from the ignore list.
- Repeat for UP007, UP035, UP015, UP017, UP024, UP028, UP045, UP046.
- For every rule with non-zero violators, leave it in the ignore list and
  add a one-line comment naming the rule and the file count, e.g.
  `"UP007",  # 12 violators in legacy modules; defer to a UP cleanup plan`.
- Run `cd backend && uvx ruff check .` after each change to confirm the
  baseline holds.
- Verify `pre-commit` runs by making a no-op change to a `.py` file and
  running `git add` + `git commit --no-verify=false` on a throwaway branch
  (use `git stash` to undo).

**Verification Checklist:**

- [x] `cd backend && uvx ruff check .` passes
- [x] `pyproject.toml` ignore list has comments explaining every remaining
      `UP*` ignore
- [x] Husky pre-commit fires `ruff check --fix` on a staged `.py` file
- [x] `npm run check` passes

**Commit Message Template:**

```text
chore(backend): annotate ruff UP* ignore list with violator counts

- Measure each UP* ignore: UP006/UP007/UP035 still have violators in
  lambda_handler.py and other legacy files; modernization is deferred
  to a separate plan (see Phase 0 "Out of Scope")
- Re-enable any UP* rule whose count is now zero (expected: none)
- Verify lint-staged still runs ruff on backend/**/*.py
```

---

### Task 4: Type a small set of `any` casts in `frontend/tests/unit/`

**Goal:** The audit identified ~23 `any` occurrences in frontend code, mostly
in test mocks (`AuthScreen-test.tsx`, `history-test.tsx`,
`AudioRecording-test.tsx`, `Notifications-test.tsx`). The
`@typescript-eslint/no-explicit-any` rule is *off* for `**/tests/**`, so
these are not lint failures -- they are correctness debt.

Type the test mocks where doing so is mechanical. Do NOT undertake a full
test rewrite.

**Files to Modify:**

- `frontend/tests/unit/AuthScreen-test.tsx` -- replace `as any` casts on
  Google sign-in mocks with the actual `GoogleSignin` mock type
- `frontend/tests/unit/history-test.tsx` -- type `AsyncStorage` mocks
- `frontend/tests/unit/AudioRecording-test.tsx` -- type `expo-av` mocks
- `frontend/tests/unit/Notifications-test.tsx` -- type the Notifications
  permission mock
- `frontend/tests/unit/utils/testUtils.tsx` -- if there is a shared mock
  factory, type its return value once and let consumers reuse it

**Prerequisites:** None (this is independent).

**Implementation Steps:**

- For each file, identify the imports being mocked. Use the actual TypeScript
  types from those imports as the cast target:
  ```typescript
  // before
  (GoogleSignin.signIn as any).mockResolvedValue(fakeUser);
  // after
  (GoogleSignin.signIn as jest.Mock<typeof GoogleSignin.signIn>).mockResolvedValue(fakeUser);
  ```
- The fortifier MUST NOT change test behavior. If a `any` cast cannot be
  cleanly typed in five minutes, leave it and add a `// TODO type` comment.
- The eslint rule for tests is OFF, so this is correctness-only -- the
  guardrail is the new pattern, not a lint enforcement.

**Verification Checklist:**

- [x] At least half of the previously-counted `as any` occurrences in
      `frontend/tests/unit/` are typed
- [x] `npm test` still passes
- [x] `npm run lint` still passes
- [x] No new `// TODO type` comments without a tracking note

**Commit Message Template:**

```text
test(frontend): type `any` casts in unit test mocks

- AuthScreen-test, history-test, AudioRecording-test, Notifications-test
- Use jest.Mock<typeof X> instead of `as any`
- testUtils.tsx: shared typed mock factory
```

---

## Phase Verification

After all four tasks land:

- [x] CI passes (frontend, backend, dockerfile-lint, pip-audit, status-check)
- [x] `find backend/src -name '*.py' -exec wc -l {} + | sort -n | tail` --
      no file over 450 lines (Phase 4 targets are <400; the 50-line slack
      is intentional)
- [x] `cd backend && pip-audit -r requirements.txt` -- 0 vulnerabilities
- [x] `cd backend && uvx ruff check .` -- 0 errors
- [x] `npm run check` passes
- [x] No product-code refactors landed in this phase

Known limitations after this phase:

- A handful of `any` casts in test files remain (intentional)
- The `UP*` ignore list still has some entries; a future plan can complete
  the modernization
- The fortifier did NOT add markdown lint or link checking -- those belong to
  Phase 6 (doc-engineer) per ADR-1
