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

# Note: CI runs all backend tests (pytest backend/tests), not just unit tests

# Deploy (do NOT run unless explicitly asked)
npm run deploy
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the canonical
description of layers, data flow, and the async meditation pipeline.

Quick reference:

- `frontend/` — Expo 55 / React Native 0.84 / React 19 / TypeScript
- `backend/` — Python 3.13 / AWS Lambda / Pydantic
- `frontend/tests/{unit,integration,e2e}/` — Jest test suites (patterns: `*-test.tsx`, `*-test.ts`)
- `backend/tests/{unit,integration,e2e}/` — pytest suites
- `docs/` — `API.md`, `ARCHITECTURE.md`, `plans/`

## Code Style

- **Frontend**: ESLint + Prettier, 100 char width, TypeScript strict mode, `no-explicit-any: warn`
- **Backend**: ruff + black, 100 char line length, Python 3.13 runtime / 3.12 lint target

## CI

GitHub Actions (`.github/workflows/ci.yml`): frontend-lint, frontend-tests, backend-tests, dockerfile-lint run on every push/PR. All four must pass.
