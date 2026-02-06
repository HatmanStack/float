# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Float is a cross-platform meditation app that uses AI to turn user-submitted "floats" (stressful moments) into personalized guided meditations. Monorepo with npm workspaces.

## Commands

```bash
# Install
npm install --legacy-peer-deps

# Run all checks (lint + tests)
npm run check

# Frontend
npm start                  # Expo dev server
npm run web                # Web only
npm run lint               # ESLint + TypeScript check
npm test                   # Jest (all frontend tests)
npm test -- --testPathPattern="SomeTest"  # Single test file

# Backend
npm run test:backend       # pytest unit tests (cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short)
npm run lint:backend       # ruff check (cd backend && uvx ruff check .)

# Run specific backend test
cd backend && PYTHONPATH=. pytest tests/unit/test_middleware.py -v --tb=short

# Deploy (do NOT run unless explicitly asked)
npm run deploy
```

## Architecture

```
├── frontend/    # Expo 52 / React Native 0.74 / TypeScript
├── backend/     # Python 3.13 / AWS Lambda / Pydantic
├── tests/       # Frontend test suites (Jest)
└── docs/        # API.md, ARCHITECTURE.md
```

### Frontend (`frontend/`)

- **Routing**: Expo Router file-based routing in `app/` (tabs layout in `app/(tabs)/`)
- **State**: React Context API — `context/AuthContext.tsx` (auth), `context/IncidentContext.tsx` (floats)
- **Components**: `components/` — HLS player, meditation controls, auth screen, download button
- **Hooks**: `hooks/` — platform-specific hooks (e.g., `useHLSPlayer.ts` / `useHLSPlayer.web.ts`)
- **Path alias**: `@/` maps to `frontend/`
- **Config**: `app.config.js`, `.eslintrc.json`, `.prettierrc.json` (100 char width)
- **Env vars**: `frontend/.env` — `EXPO_PUBLIC_LAMBDA_FUNCTION_URL`, `EXPO_PUBLIC_WEB_CLIENT_ID`
- **Test patterns**: `*-test.tsx`, `*-test.ts` in `tests/frontend/`

### Backend (`backend/`)

- **Entry**: `lambda_function.py` → `src/handlers/lambda_handler.py`
- **Middleware**: `src/handlers/middleware.py` — CORS, validation, error handling
- **Services** (`src/services/`): AI (Gemini), TTS (OpenAI), audio (FFmpeg), HLS streaming, S3 storage, async job tracking
- **Providers** (`src/providers/`): OpenAI TTS, Gemini TTS implementations
- **Models** (`src/models/`): Pydantic request/response validation
- **Config**: `pyproject.toml` (ruff, black, pytest, mypy), `template.yaml` (SAM), `samconfig.toml` (deploy params)
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/e2e/` with pytest markers: `unit`, `integration`, `e2e`, `slow`

### API Flow

- `POST /` — Sync: emotion analysis of submitted floats; Async: meditation generation (returns `job_id`)
- `GET /job/{job_id}` — Poll async job status until `status: completed` (meditation takes 1-2 min)
- Backend self-invokes Lambda asynchronously for long-running meditation generation

## Code Style

- **Frontend**: ESLint + Prettier, 100 char width, TypeScript strict mode, `no-explicit-any: warn`
- **Backend**: ruff + black, 100 char line length, Python 3.12+ target

## CI

GitHub Actions (`.github/workflows/ci.yml`): frontend-lint, frontend-tests, backend-tests run on every push/PR. All three must pass.
