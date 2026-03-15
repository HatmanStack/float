# Phase 7: [FORTIFIER] Reproducibility & Onboarding

## Phase Goal

Make the repo self-service for new contributors. Address Reproducibility (6 -> 9) and Onboarding (7 -> 9) pillar findings: create `.env.example` files, add `docker-compose.yml`, add pre-commit hooks, create `CONTRIBUTING.md`, and add a setup script.

**Success criteria:**
- `.env.example` files exist for frontend and backend
- `docker-compose.yml` defines backend service with Python 3.13 + FFmpeg
- `.pre-commit-config.yaml` with ruff, eslint, prettier hooks
- `CONTRIBUTING.md` with local setup, branch naming, PR template
- `npm run setup` or Makefile target for one-command setup
- `npm run check` passes
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~25k

## Prerequisites

- Phases 0-6 completed and verified
- All checks passing

---

## Tasks

### Task 1: Create `.env.example` files

**Goal:** New contributors have no idea which env vars are needed. The eval flags this under Reproducibility (Day 2: 6/10) as the top issue.

**Files to Create:**
- `frontend/.env.example`
- `backend/.env.example`

**Prerequisites:** None

**Implementation Steps:**

1. Create `frontend/.env.example` by examining which `EXPO_PUBLIC_*` vars are used:
   ```bash
   grep -rn "process.env.EXPO_PUBLIC" frontend/ --include="*.ts" --include="*.tsx" | grep -v node_modules
   ```
   Based on current usage, create:
   ```env
   # Frontend environment variables
   # Copy this file to .env and fill in the values

   # Lambda function URL for API calls
   EXPO_PUBLIC_LAMBDA_FUNCTION_URL=https://your-lambda-url.lambda-url.us-east-1.on.aws/

   # Google OAuth Web Client ID (from Google Cloud Console)
   EXPO_PUBLIC_WEB_CLIENT_ID=your-web-client-id.apps.googleusercontent.com

   # Google OAuth Android Client ID (optional, for Android builds)
   EXPO_PUBLIC_ANDROID_CLIENT_ID=your-android-client-id.apps.googleusercontent.com
   ```

2. Create `backend/.env.example` by examining `settings.py`:
   ```env
   # Backend environment variables
   # Copy this file to .env and fill in the values

   # Google Gemini API key for AI service
   G_KEY=your-gemini-api-key

   # OpenAI API key for TTS
   OPENAI_API_KEY=your-openai-api-key

   # AWS S3 buckets (defaults shown — override for local development)
   AWS_S3_BUCKET=float-cust-data
   AWS_AUDIO_BUCKET=audio-er-lambda

   # FFmpeg path (default: /opt/bin/ffmpeg for Lambda layer)
   # For local development with system FFmpeg:
   # FFMPEG_PATH=/usr/bin/ffmpeg
   ```

3. Add both `.env.example` files to git tracking (they should NOT be in `.gitignore`)

4. Verify `.env` is in `.gitignore`:
   ```bash
   grep "\.env$\|\.env " .gitignore
   ```
   If not, add `.env` to `.gitignore` in both `frontend/` and `backend/` directories (or root if using a root `.gitignore`).

**Verification Checklist:**
- [ ] `frontend/.env.example` exists with all `EXPO_PUBLIC_*` vars
- [ ] `backend/.env.example` exists with all required env vars
- [ ] Neither file contains real credentials
- [ ] `.env` files are in `.gitignore`

**Testing Instructions:**
- Verify files are not accidentally ignored: `git status --porcelain frontend/.env.example backend/.env.example`

**Commit Message Template:**
```
docs: add .env.example files for frontend and backend

Create .env.example files documenting required environment variables
for both frontend (Expo) and backend (Lambda). New contributors can
copy these files and fill in their credentials.
```

---

### Task 2: Add `docker-compose.yml` for backend

**Goal:** Provide a containerized backend development environment. The eval flags this under Reproducibility (Day 2: 6/10).

**Files to Create:**
- `docker-compose.yml` (at repo root)
- `backend/Dockerfile`

**Prerequisites:** None

**Implementation Steps:**

1. Create `backend/Dockerfile`:
   ```dockerfile
   FROM python:3.13-slim

   # Install FFmpeg
   RUN apt-get update && \
       apt-get install -y --no-install-recommends ffmpeg && \
       rm -rf /var/lib/apt/lists/*

   WORKDIR /app

   # Install Python dependencies
   COPY requirements.txt requirements-dev.txt ./
   RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

   # Copy source
   COPY . .

   ENV PYTHONPATH=/app
   ENV FFMPEG_PATH=/usr/bin/ffmpeg

   CMD ["python", "-m", "pytest", "tests/unit", "-v", "--tb=short"]
   ```

2. Create `docker-compose.yml` at repo root:
   ```yaml
   version: "3.8"

   services:
     backend:
       build:
         context: ./backend
         dockerfile: Dockerfile
       env_file:
         - ./backend/.env
       volumes:
         - ./backend:/app
       working_dir: /app
       command: python -m pytest tests/unit -v --tb=short
   ```

3. Add a `docker-compose.override.yml.example` is NOT needed — keep it simple.

4. Add to root `package.json` scripts (optional, but helpful):
   ```json
   "test:backend:docker": "docker compose run --rm backend"
   ```

5. Add a hadolint CI step to `.github/workflows/ci.yml` to lint the Dockerfile in CI. This ensures the Dockerfile does not silently break. Add a new job after `backend-tests`:
   ```yaml
   dockerfile-lint:
     name: Dockerfile Lint
     runs-on: ubuntu-latest

     steps:
       - uses: actions/checkout@v4

       - name: Lint Dockerfile with hadolint
         uses: hadolint/hadolint-action@v3.1.0
         with:
           dockerfile: backend/Dockerfile
   ```
   Also add `dockerfile-lint` to the `needs` array of the `status-check` job:
   ```yaml
   needs: [frontend-lint, frontend-tests, backend-tests, dockerfile-lint]
   ```
   And update the status-check script to include the new job:
   ```yaml
   if [ "${{ needs.dockerfile-lint.result }}" != "success" ] || ...
   ```

**Verification Checklist:**
- [ ] `backend/Dockerfile` builds successfully: `docker build -t float-backend ./backend`
- [ ] `docker-compose.yml` is valid YAML
- [ ] Container runs tests: `docker compose run --rm backend`
- [ ] FFmpeg is available in the container
- [ ] `dockerfile-lint` job added to `.github/workflows/ci.yml`
- [ ] `status-check` job includes `dockerfile-lint` in its `needs` array

**Testing Instructions:**
- Local: `docker compose build backend && docker compose run --rm backend` (Docker required locally)
- CI: The `dockerfile-lint` job runs hadolint automatically on every push/PR. Docker build/run is NOT executed in CI (too slow); only the Dockerfile syntax is validated.

**Commit Message Template:**
```
chore: add Docker setup for backend development

Add Dockerfile (Python 3.13 + FFmpeg) and docker-compose.yml for
containerized backend development. Add hadolint CI job to validate
Dockerfile syntax on every push/PR. New contributors can run tests
without installing Python or FFmpeg locally.
```

---

### Task 3: Add pre-commit hooks with husky + lint-staged

**Goal:** Enforce code quality checks before commit. The eval flags this under Reproducibility (Day 2: 6/10).

**Approach:** Use `husky` + `lint-staged` (npm-native). This is the correct choice for this repo because:
- The repo is npm-workspace-based with `package.json` at root
- Phase 8 Task 1 installs `commitlint` (an npm tool) with a `.husky/commit-msg` hook
- No `.husky` directory or `pre-commit` config exists currently -- this is a fresh setup
- Keeps all git hooks in one ecosystem (npm) rather than mixing Python `pre-commit` with npm tooling

**Files to Create/Modify:**
- `.husky/pre-commit` (hook script)
- `package.json` (root) — add `lint-staged` config and devDependencies

**Prerequisites:** None

**Implementation Steps:**

1. Install husky and lint-staged:
   ```bash
   npm install --save-dev husky lint-staged --legacy-peer-deps
   ```

2. Initialize husky:
   ```bash
   npx husky init
   ```
   This creates the `.husky/` directory and adds a `prepare` script to `package.json`.

3. Create `.husky/pre-commit` with the following content:
   ```bash
   npx lint-staged
   ```

4. Add `lint-staged` configuration to root `package.json`:
   ```json
   "lint-staged": {
     "frontend/**/*.{ts,tsx}": ["eslint --fix", "prettier --write"],
     "backend/**/*.py": ["ruff check --fix", "ruff format"]
   }
   ```

5. Verify the hooks work by staging a file and running lint-staged:
   ```bash
   npx lint-staged
   ```

**Verification Checklist:**
- [ ] `.husky/pre-commit` exists and contains `npx lint-staged`
- [ ] `husky` and `lint-staged` are in `devDependencies`
- [ ] `lint-staged` config in `package.json` covers both frontend (eslint/prettier) and backend (ruff)
- [ ] `npx lint-staged` runs without errors on staged files

**Testing Instructions:**
- Stage a Python file and a TypeScript file, then run `npx lint-staged` to verify both linters execute
- Make a test commit to verify the pre-commit hook fires

**Commit Message Template:**
```
chore: add husky + lint-staged pre-commit hooks

Install husky and lint-staged with pre-commit hooks for ruff
(backend Python linting/formatting) and eslint/prettier (frontend
TypeScript). Enforces code quality checks before every commit.
```

---

### Task 4: Create `CONTRIBUTING.md`

**Goal:** Provide contributor guidelines. The eval flags this under Onboarding (Day 2: 7/10).

**Files to Create:**
- `CONTRIBUTING.md` (at repo root)

**Prerequisites:** Tasks 1-3 complete (so we can reference .env.example and pre-commit)

**Implementation Steps:**

1. Create `CONTRIBUTING.md` at repo root:

   ```markdown
   # Contributing to Float

   ## Prerequisites

   - Node.js 24+
   - Python 3.13+
   - FFmpeg (for audio processing)
   - AWS CLI (for deployment only)

   ## Quick Start

   ```bash
   # Clone and install
   git clone <repo-url>
   cd float
   npm install --legacy-peer-deps

   # Set up environment
   cp frontend/.env.example frontend/.env
   cp backend/.env.example backend/.env
   # Edit .env files with your API keys

   # Backend setup
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt -r requirements-dev.txt
   cd ..

   # Install git hooks (husky)
   npm run prepare

   # Verify everything works
   npm run check
   ```

   ## Running Tests

   ```bash
   # All checks (lint + tests)
   npm run check

   # Frontend only
   npm run lint          # ESLint + TypeScript
   npm test              # Jest

   # Backend only
   npm run lint:backend  # ruff
   npm run test:backend  # pytest
   ```

   ## Branch Naming

   Use descriptive branch names with a type prefix:
   - `feat/add-meditation-timer`
   - `fix/s3-pagination-overflow`
   - `chore/remove-dead-code`
   - `docs/update-api-reference`

   ## Commit Messages

   Use [conventional commits](https://www.conventionalcommits.org/):

   ```
   type(scope): brief description

   Optional body explaining why.
   ```

   Types: `feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`
   Scopes: `frontend`, `backend`, or omit for repo-wide changes

   ## Pull Requests

   1. Create a feature branch from `main`
   2. Make small, focused commits
   3. Ensure `npm run check` passes
   4. Open a PR with a clear description
   5. All CI checks must pass before merge

   ## Docker (Backend)

   For containerized backend development:

   ```bash
   docker compose run --rm backend
   ```

   This runs backend tests in a container with Python 3.13 and FFmpeg pre-installed.
   ```

2. The CONTRIBUTING.md above already reflects the husky approach (Task 3 uses husky + lint-staged). No conditional adjustment needed.

**Verification Checklist:**
- [ ] `CONTRIBUTING.md` exists at repo root
- [ ] References `.env.example` files
- [ ] Documents pre-commit hook installation
- [ ] Includes branch naming and commit message conventions
- [ ] Quick start section is complete and accurate

**Testing Instructions:**
- No automated tests — review content for accuracy

**Commit Message Template:**
```
docs: add CONTRIBUTING.md with setup and contribution guidelines

Create CONTRIBUTING.md documenting prerequisites, quick start,
testing commands, branch naming, commit message format, and Docker
setup. Enables new contributors to self-serve on day one.
```

---

### Task 5: Add setup automation script

**Goal:** Provide a single command to set up the development environment. The eval flags this under Onboarding (Day 2: 7/10).

**Files to Modify:**
- `package.json` (root) — Add `setup` script

**Prerequisites:** Tasks 1, 3, 4 complete

**Implementation Steps:**

1. Open `package.json` at the repo root
2. Add a `setup` script to the `scripts` section:
   ```json
   "setup": "npm install --legacy-peer-deps && cd backend && pip install -r requirements.txt -r requirements-dev.txt && cd .. && echo 'Setup complete. Copy .env.example files to .env and fill in your API keys.'"
   ```

3. The setup script already includes `npm install --legacy-peer-deps` which installs husky (added as a devDependency in Task 3). Husky's `prepare` script runs automatically during `npm install`, so git hooks are set up automatically. No additional step needed for hooks.

4. Update `CONTRIBUTING.md` to reference `npm run setup` as the primary setup command.

**Verification Checklist:**
- [ ] `npm run setup` script exists in root `package.json`
- [ ] Script installs both frontend and backend dependencies
- [ ] Script installs pre-commit hooks
- [ ] Script prints reminder about `.env` files
- [ ] `npm run setup` runs successfully

**Testing Instructions:**
- Run `npm run setup` in a clean environment (or verify the command would work)

**Commit Message Template:**
```
chore: add npm run setup for one-command development setup

Add setup script that installs frontend dependencies, backend
dependencies, and pre-commit hooks. Prints a reminder to copy
.env.example files.
```

---

## Phase Verification

After completing all 5 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```

2. Verify new files exist:
   ```bash
   ls frontend/.env.example backend/.env.example CONTRIBUTING.md .husky/pre-commit docker-compose.yml backend/Dockerfile
   ```

3. Verify setup script:
   ```bash
   npm run setup --help 2>&1 | head -5
   # Or just: grep "setup" package.json
   ```

4. Verify husky hooks:
   ```bash
   ls .husky/pre-commit && npx lint-staged --verbose
   ```

All checks must pass before proceeding to Phase 8.
