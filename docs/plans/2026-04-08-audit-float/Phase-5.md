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
  Python file from exceeding 400 lines
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

- [ ] `.github/workflows/ci.yml` defines a `pip-audit` job
- [ ] The `status-check` job lists `pip-audit` in `needs`
- [ ] `requirements-dev.txt` pins `pip-audit`
- [ ] Push the branch and verify the new job runs in CI; it should pass
      because Phase 1 Task 2 already bumped `requests`
- [ ] `npm run check` passes locally (no functional change to existing checks)

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
400 lines. Add a guardrail that prevents new files from exceeding that bound.

The fortifier should choose between two equivalent approaches:

- **Option A:** A custom CI step using `find` + `wc -l` that fails if any
  `src/**.py` file exceeds 400 lines. Cheap, no dependency.
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
            # Plan 2026-04-08-audit-float: no backend src file >400 lines
            # See docs/plans/2026-04-08-audit-float/Phase-4.md
            offenders=$(find src -name '*.py' -print0 \
              | xargs -0 wc -l \
              | awk '$1 > 400 && $2 != "total" { print $2, $1 }')
            if [ -n "$offenders" ]; then
              echo "Files exceeding 400 lines:"
              echo "$offenders"
              exit 1
            fi
  ```

**Prerequisites:** Phases 1-4 complete (so no current file violates the
limit).

**Implementation Steps:**

- Verify locally first: `find backend/src -name '*.py' -print0 | xargs -0 wc
  -l | awk '$1 > 400 && $2 != "total"'`. The output must be empty.
- Add the step to the backend job in CI.
- Run the workflow on a feature branch to confirm it passes.

**Verification Checklist:**

- [ ] Local `find ... | xargs wc -l | awk '$1 > 400'` is empty
- [ ] CI step is in place and passes
- [ ] A deliberate test (add a temporary 500-line file, push, see it fail,
      then revert) confirms the guardrail bites. The implementer MAY skip the
      deliberate test if Phase 4 already produced a tight margin.

**Commit Message Template:**

```text
ci: enforce max 400-line backend Python files

- Phase 4 of plan 2026-04-08-audit-float decomposed two god objects
- Guardrail prevents regression by failing CI if any src/**/*.py grows
```

---

### Task 3: Tighten ruff rules and pre-commit hooks

**Goal:** The current `pyproject.toml` ruff config has a long `ignore` list of
`UP*` rules that suppress modern-Python migrations. Phase 1 Task 6 cleaned the
logging convention; this task enables the rules whose violators have all been
fixed (so the rules are guardrails, not new work). Also ensure the existing
husky `pre-commit` hook runs `ruff check --fix` on staged files; today it
runs via `lint-staged` which is correct, but verify the configuration covers
the new files added in Phase 4.

**Files to Modify:**

- `backend/pyproject.toml` -- remove from the `ignore` list any rule whose
  violators are now zero. Specifically check:
  - `UP006` (use builtin `list`/`dict` over `List`/`Dict`) -- Phase 4 Task 1
    added new modules with modern typing. Re-enable IF and only if the
    existing modules also pass. If they do not, leave `UP006` ignored and
    note the remaining violators in the commit body.
  - `UP007` (use `X | Y` over `Union[X, Y]`) -- same approach
  - `UP035` (deprecated typing imports) -- same approach
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

- [ ] `cd backend && uvx ruff check .` passes
- [ ] `pyproject.toml` ignore list has comments explaining every remaining
      `UP*` ignore
- [ ] Husky pre-commit fires `ruff check --fix` on a staged `.py` file
- [ ] `npm run check` passes

**Commit Message Template:**

```text
chore(backend): tighten ruff rules with zero remaining violators

- Re-enable UP006/UP007/UP035 if the audit modules now satisfy them
- Annotate remaining UP* ignores with violator counts for future cleanup
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

- [ ] At least half of the previously-counted `as any` occurrences in
      `frontend/tests/unit/` are typed
- [ ] `npm test` still passes
- [ ] `npm run lint` still passes
- [ ] No new `// TODO type` comments without a tracking note

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

- [ ] CI passes (frontend, backend, dockerfile-lint, pip-audit, status-check)
- [ ] `find backend/src -name '*.py' -exec wc -l {} + | sort -n | tail` --
      no file over 400 lines
- [ ] `cd backend && pip-audit -r requirements.txt` -- 0 vulnerabilities
- [ ] `cd backend && uvx ruff check .` -- 0 errors
- [ ] `npm run check` passes
- [ ] No product-code refactors landed in this phase

Known limitations after this phase:

- A handful of `any` casts in test files remain (intentional)
- The `UP*` ignore list still has some entries; a future plan can complete
  the modernization
- The fortifier did NOT add markdown lint or link checking -- those belong to
  Phase 6 (doc-engineer) per ADR-1
