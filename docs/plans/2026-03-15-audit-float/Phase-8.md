# Phase 8: [FORTIFIER] Git Hygiene & Final Guardrails

## Phase Goal

Enforce commit quality and add final guardrails. Address Git Hygiene (6 -> 9) with commitlint, add a backend lint CI step, and perform a final sweep to ensure all 12 pillars reach 9/10.

**Success criteria:**
- `commitlint` installed with conventional commits preset
- Commit-msg hook validates commit messages
- CI workflow includes backend ruff lint as a named step (already done in Phase 3 — verify)
- All 12 eval pillar targets met
- `npm run check` passes
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~15k

## Prerequisites

- Phases 0-7 completed and verified
- All checks passing

---

## Tasks

### Task 1: Install commitlint with conventional commits

**Goal:** Enforce commit message format. The eval flags vague commits (`"ordering"`, `"SEO"`) under Git Hygiene (Day 2: 6/10). Adding commitlint prevents future vague messages.

**Files to Create/Modify:**
- `commitlint.config.js` (at repo root)
- `package.json` (add devDependencies)
- `.husky/commit-msg` (commit-msg hook)

**Prerequisites:** Phase 7 Task 3 complete (husky installed)

**Implementation Steps:**

1. Install commitlint:
   ```bash
   npm install --save-dev @commitlint/cli @commitlint/config-conventional --legacy-peer-deps
   ```

2. Create `commitlint.config.js` at repo root:
   ```js
   module.exports = {
     extends: ['@commitlint/config-conventional'],
     rules: {
       'type-enum': [
         2,
         'always',
         [
           'feat',
           'fix',
           'chore',
           'docs',
           'test',
           'ci',
           'refactor',
           'perf',
           'style',
           'build',
           'revert',
         ],
       ],
       'scope-enum': [
         1,
         'always',
         ['frontend', 'backend'],
       ],
       'subject-max-length': [2, 'always', 72],
       'body-max-line-length': [1, 'always', 100],
     },
   };
   ```
   Note: `scope-enum` is set to level `1` (warning) not `2` (error), allowing scope-less commits like `ci: add push trigger`.

3. Set up the commit-msg hook using husky (installed in Phase 7 Task 3). Create `.husky/commit-msg`:
   ```bash
   npx --no -- commitlint --edit "$1"
   ```
   If `npx husky add` is available in your husky version, you can also run:
   ```bash
   npx husky add .husky/commit-msg 'npx --no -- commitlint --edit "$1"'
   ```

4. Verify the hook works:
   ```bash
   echo "bad message" | npx commitlint
   # Should fail

   echo "chore: valid message" | npx commitlint
   # Should pass
   ```

**Verification Checklist:**
- [ ] `commitlint.config.js` exists at repo root
- [ ] `@commitlint/cli` and `@commitlint/config-conventional` in devDependencies
- [ ] Commit-msg hook is installed (`.husky/commit-msg` exists)
- [ ] Valid messages pass: `echo "chore(backend): test" | npx commitlint`
- [ ] Invalid messages fail: `echo "ordering" | npx commitlint`

**Testing Instructions:**
- Test valid: `echo "feat(frontend): add dark mode" | npx commitlint`
- Test invalid: `echo "SEO" | npx commitlint`
- Make a test commit and verify the hook runs

**Commit Message Template:**
```
chore: add commitlint with conventional commits enforcement

Install @commitlint/cli and @commitlint/config-conventional with a
commit-msg hook. Enforces conventional commit format (type(scope):
subject) to prevent vague commit messages.
```

---

### Task 2: Add PR template

**Goal:** Standardize pull request descriptions. Part of Onboarding (Day 2: 7/10) improvements.

**Files to Create:**
- `.github/pull_request_template.md`

**Prerequisites:** None

**Implementation Steps:**

1. Create `.github/pull_request_template.md`:
   ```markdown
   ## Summary

   Brief description of what this PR does and why.

   ## Changes

   - Change 1
   - Change 2

   ## Testing

   - [ ] `npm run check` passes
   - [ ] Manual testing done (describe below)

   ## Notes

   Any additional context for reviewers.
   ```

**Verification Checklist:**
- [ ] `.github/pull_request_template.md` exists
- [ ] Template includes summary, changes, testing sections

**Testing Instructions:**
- No automated tests — verify file contents

**Commit Message Template:**
```
docs: add pull request template

Create .github/pull_request_template.md with summary, changes,
testing checklist, and notes sections.
```

---

### Task 3: Final verification sweep

**Goal:** Verify all 12 eval pillars have been addressed. This is a verification-only task — no code changes unless a gap is found.

**Files to Modify:** None (unless gaps found)

**Prerequisites:** Tasks 1-2 complete

**Implementation Steps:**

1. Run the complete check suite:
   ```bash
   npm run check
   ```

2. Run backend checks:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   cd backend && uvx ruff check .
   ```

3. Verify each pillar's remediation:

   | Pillar | Verification Command | Expected |
   |--------|---------------------|----------|
   | Problem-Solution Fit (8->9) | `grep "TODO" frontend/components/Notifications.tsx` | No TODO |
   | Architecture (8->9) | `grep "TTS_WORDS_PER_MINUTE" backend/src/handlers/lambda_handler.py` | Found |
   | Code Quality (7->9) | `grep -rn "print(" backend/src/ --include="*.py"` | Nothing |
   | Creativity (8->9) | `grep "TTS_WORDS_PER_MINUTE" backend/src/handlers/lambda_handler.py` | Found |
   | Pragmatism (8->9) | `ls backend/src/services/service_factory.py` | Not found |
   | Defensiveness (7->9) | `grep "raise.*ExternalServiceError" backend/src/services/job_service.py` | Found |
   | Performance (7->9) | `grep "FFMPEG_STEP_TIMEOUT\|FFMPEG_STREAM_TIMEOUT" backend/src/services/ffmpeg_audio_service.py` | Found |
   | Type Rigor (7->9) | `grep "class BaseRequest" backend/src/models/requests.py` | Not found |
   | Test Value (7->9) | `grep "expect(true)" tests/frontend/unit/LocalFileLoadAndSave-test.tsx` | Not found |
   | Reproducibility (6->9) | `ls frontend/.env.example backend/.env.example .husky/pre-commit docker-compose.yml` and `grep dockerfile-lint .github/workflows/ci.yml` | All exist; hadolint CI job present |
   | Git Hygiene (6->9) | `echo "bad" \| npx commitlint` | Fails |
   | Onboarding (7->9) | `ls CONTRIBUTING.md .github/pull_request_template.md` | Both exist |

4. If any verification fails, create a follow-up task in this phase to address it.

**Verification Checklist:**
- [ ] All 12 verification commands produce expected results
- [ ] `npm run check` passes
- [ ] `cd backend && uvx ruff check .` passes
- [ ] All new files are committed

**Testing Instructions:**
- Run full suite: `npm run check`
- Run all verifications from the table above

**Commit Message Template:**
No commit — this is a verification-only task. If fixes are needed, each fix gets its own commit.

---

## Phase Verification

After completing all 3 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```

2. Run backend checks:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   cd backend && uvx ruff check .
   ```

3. Verify commitlint:
   ```bash
   echo "chore: test" | npx commitlint && echo "PASS" || echo "FAIL"
   echo "bad" | npx commitlint && echo "SHOULD FAIL" || echo "CORRECTLY REJECTED"
   ```

4. Final file inventory:
   ```bash
   ls -la frontend/.env.example backend/.env.example \
          CONTRIBUTING.md .husky/pre-commit \
          docker-compose.yml backend/Dockerfile \
          commitlint.config.js .github/pull_request_template.md
   ```

All checks must pass. The remediation is complete.
