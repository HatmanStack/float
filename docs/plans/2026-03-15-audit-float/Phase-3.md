# Phase 3: [FORTIFIER] Guardrails and CI Hardening

## Phase Goal

Add automated guardrails that enforce the clean state achieved by Phases 1-2. This phase does NOT fix existing code -- it only adds linting rules, CI checks, and configuration that prevent regressions. After this phase, the issues remediated in Phases 1-2 cannot silently recur.

**Success criteria:**
- Ruff rules expanded to catch unused variables and imports
- CI workflow includes a backend lint step that catches dead code patterns
- `subprocess.run` calls without `timeout` are flagged by a ruff rule
- `npm run check` passes
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~15k

## Prerequisites

- Phase 1 and Phase 2 completed and verified
- All checks passing

---

## Tasks

### Task 1: Expand ruff lint rules to catch dead code and unused variables

**Goal:** Add ruff rules that would have caught several of the audit findings: unused variables, unused imports, and unused exception classes.

**Files to Modify:**
- `backend/pyproject.toml` - Add ruff rule selections

**Prerequisites:** Phase 2 complete (dead code already removed)

**Implementation Steps:**
1. Open `backend/pyproject.toml`
2. Locate the `[tool.ruff.lint]` section (line 100-102):
   ```toml
   [tool.ruff.lint]
   select = ["E", "F", "W", "I"]
   ignore = ["E501"]  # Line too long (handled by black)
   ```
3. Expand the `select` list to include additional rule sets:
   ```toml
   [tool.ruff.lint]
   select = [
       "E",    # pycodestyle errors
       "F",    # pyflakes (includes F841 unused variables)
       "W",    # pycodestyle warnings
       "I",    # isort
       "UP",   # pyupgrade (modernize Python syntax)
       "B",    # flake8-bugbear (catches common bugs)
       "S",    # flake8-bandit (basic security checks like subprocess without timeout)
   ]
   ignore = [
       "E501",   # Line too long (handled by black)
       "S603",   # subprocess call - check for execution of untrusted input (too noisy for FFmpeg)
       "S607",   # starting a process with a partial executable path
   ]
   ```

4. Run `cd backend && uvx ruff check .` and review output
5. If there are new violations from `UP`, `B`, or `S` rules that are **pre-existing** issues outside the scope of this remediation, add specific rule codes to the `ignore` list with a comment explaining why. Do NOT fix existing code in this phase -- only suppress pre-existing violations that are outside scope.
6. The key rule to verify works: `S603` / `S607` for subprocess -- these should be intentionally suppressed since the FFmpeg calls use controlled inputs, BUT `S603` would flag subprocess calls, making future reviewers aware. If the team prefers to keep `S603` active with per-line `# noqa: S603` on the FFmpeg calls, that's an alternative approach. Choose the suppress-globally approach for simplicity.

**Verification Checklist:**
- [ ] `select` includes `"UP"`, `"B"`, `"S"` rules
- [ ] `cd backend && uvx ruff check .` passes with zero violations
- [ ] Any new `ignore` entries have comments explaining the reason
- [ ] No code changes -- only `pyproject.toml` config changes

**Testing Instructions:**
- Run `cd backend && uvx ruff check .` -- must return 0 violations
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` -- must pass (config change should not affect tests)

**Commit Message Template:**
```
ci(backend): expand ruff rules to catch dead code and security patterns

Add UP (pyupgrade), B (bugbear), and S (bandit) rule sets to ruff
configuration. Suppresses S603/S607 globally for controlled FFmpeg
subprocess calls.
```

---

### Task 2: Add `push` trigger to CI workflow

**Goal:** The CI workflow currently only triggers on `pull_request`. Add `push` trigger for the `main` branch so that direct pushes (e.g., merge commits) are also validated.

**Files to Modify:**
- `.github/workflows/ci.yml` - Add push trigger

**Prerequisites:** None

**Implementation Steps:**
1. Open `.github/workflows/ci.yml`
2. Modify the `on:` trigger section (lines 3-5):

   **Before:**
   ```yaml
   on:
     pull_request:
       branches: [main]
   ```

   **After:**
   ```yaml
   on:
     push:
       branches: [main]
     pull_request:
       branches: [main]
   ```

3. No other changes to the workflow

**Verification Checklist:**
- [ ] `push` trigger added for `main` branch
- [ ] `pull_request` trigger unchanged
- [ ] YAML is valid (proper indentation)

**Testing Instructions:**
- Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
- No tests to run -- this is a CI config change

**Commit Message Template:**
```
ci: add push trigger for main branch to CI workflow

Ensure direct pushes to main (e.g., merge commits) are also validated
by the CI pipeline, not just pull requests.
```

---

### Task 3: Add `no-console` enforcement notes and verify `eslint-disable` count

**Goal:** Verify the frontend ESLint config already catches `console.log` (the `no-console` rule exists at line 29 of `.eslintrc.json` with `warn` level, allowing `console.warn` and `console.error`). Document the current count of `eslint-disable` comments in the codebase for future tracking -- do NOT add or remove any.

This is a verification-only task. The existing config is correct. The audit flagged ~40 `console.error` statements but these are ALLOWED by the current rule (which permits `warn` and `error`). No change needed.

**Files to Modify:** None

**Prerequisites:** Phase 2 complete

**Implementation Steps:**
1. Verify the `no-console` rule in `frontend/.eslintrc.json`:
   ```json
   "no-console": ["warn", { "allow": ["warn", "error"] }]
   ```
   This is correct -- `console.log` will trigger warnings, `console.warn`/`console.error` are allowed.

2. Count remaining `eslint-disable` comments in frontend code:
   ```bash
   grep -r "eslint-disable" frontend/ --include="*.tsx" --include="*.ts" | grep -v node_modules | wc -l
   ```
   Record this count for the phase verification section below.

3. Run `npm run lint` to confirm zero lint errors.

**Verification Checklist:**
- [ ] `no-console` rule is `["warn", { "allow": ["warn", "error"] }]`
- [ ] `npm run lint` passes with zero errors
- [ ] `eslint-disable` comment count recorded

**Testing Instructions:**
- Run `npm run lint`

**Commit Message Template:**
No commit -- this is a verification-only task.

---

## Phase Verification

After completing all 3 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```

2. Run backend checks with expanded ruff rules:
   ```bash
   cd backend && uvx ruff check .
   ```

3. Verify CI config:
   ```bash
   grep -A3 "^on:" .github/workflows/ci.yml
   ```

4. Verify ruff config includes new rules:
   ```bash
   grep -A8 "\[tool.ruff.lint\]" backend/pyproject.toml
   ```

5. Run frontend lint:
   ```bash
   npm run lint
   ```

All checks must pass. The repo is now in a clean state with guardrails preventing regression of the fixed issues.
