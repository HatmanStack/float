# Contributing to Float

## Prerequisites

- Node.js 24+
- Python 3.13+
- FFmpeg (for audio processing)
- AWS CLI (for deployment only)

## Quick Start

```bash
# Clone and install everything (frontend + backend + git hooks)
git clone <repo-url>
cd float
npm run setup

# Set up environment
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
# Edit .env files with your API keys

# Verify everything works
npm run check
```

If you prefer manual setup:

```bash
npm install --legacy-peer-deps

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt -r requirements-dev.txt
cd ..

# Install git hooks (husky)
npm run prepare
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
