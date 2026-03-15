# Remediation Plan: 2026-03-15-audit-float

## Overview

This plan remediates findings from two sources:

1. **Repo health audit** (Phases 1-3, completed): Critical/high operational bugs, dead code removal, and lint guardrails.
2. **12-pillar evaluation** (Phases 4-8, this plan): Code quality, type rigor, defensiveness, test value, reproducibility, onboarding, and git hygiene improvements to bring all 12 pillars to 9/10.

The plan follows a **subtractive-first** approach: Phases 1-2 and 4 (tagged `[HYGIENIST]`) remove dead code and fix quick wins. Phases 5-6 (tagged `[STRUCTURAL]`) improve error handling, types, and tests. Phases 3, 7-8 (tagged `[FORTIFIER]`) add guardrails and contributor tooling.

## Prerequisites

- Node.js 24+ and npm
- Python 3.13+ with pip
- `npm install --legacy-peer-deps` completed
- Backend dependencies: `cd backend && pip install -r requirements.txt -r requirements-dev.txt`

## Phase Summary

| Phase | Tag | Goal | Est. Tokens | Tasks |
|-------|-----|------|-------------|-------|
| [Phase 0](Phase-0.md) | Foundation | ADRs, testing strategy, commit format | -- | -- |
| [Phase 1](Phase-1.md) | [HYGIENIST] | Quick wins, dead code removal, hygiene fixes | ~20k | 7 |
| [Phase 2](Phase-2.md) | [HYGIENIST] | Critical & high operational/structural fixes | ~25k | 5 |
| [Phase 3](Phase-3.md) | [FORTIFIER] | Lint rule expansion, CI hardening | ~15k | 3 |
| [Phase 4](Phase-4.md) | [HYGIENIST] | Code quality & pragmatism quick wins | ~20k | 4 |
| [Phase 5](Phase-5.md) | [STRUCTURAL] | Defensiveness & type rigor | ~30k | 4 |
| [Phase 6](Phase-6.md) | [STRUCTURAL] | Test value & creativity | ~25k | 4 |
| [Phase 7](Phase-7.md) | [FORTIFIER] | Reproducibility & onboarding | ~25k | 5 |
| [Phase 8](Phase-8.md) | [FORTIFIER] | Git hygiene & final guardrails | ~15k | 3 |

## Navigation

- [Phase 0: Foundation](Phase-0.md) -- ADRs, testing strategy, conventions
- [Phase 1: Quick Wins & Dead Code](Phase-1.md) -- FFmpeg timeouts, dead module removal, deprecated API fixes
- [Phase 2: Critical & High Fixes](Phase-2.md) -- S3 pagination, streaming timeout, polling consolidation
- [Phase 3: Guardrails & CI](Phase-3.md) -- Ruff rules, CI push trigger, lint verification
- [Phase 4: Code Quality & Pragmatism](Phase-4.md) -- print() cleanup, ServiceFactory removal, boolean-flag refactor
- [Phase 5: Defensiveness & Type Rigor](Phase-5.md) -- S3 error propagation, Pydantic migration, Settings conversion
- [Phase 6: Test Value & Creativity](Phase-6.md) -- Placeholder test fix, conftest audit, magic number extraction
- [Phase 7: Reproducibility & Onboarding](Phase-7.md) -- .env.example, Docker, pre-commit, CONTRIBUTING.md
- [Phase 8: Git Hygiene & Final Guardrails](Phase-8.md) -- commitlint, PR template, final verification
- [Feedback](feedback.md) -- Review feedback tracking
- [Eval Document](eval.md) -- 12-pillar evaluation scores
- [Health Audit](health-audit.md) -- Original health audit findings

## Pillar Coverage

| Pillar | Current | Target | Phases |
|--------|---------|--------|--------|
| Reproducibility | 6/10 | 9/10 | 7 (env, Docker, pre-commit) |
| Git Hygiene | 6/10 | 9/10 | 8 (commitlint, PR template) |
| Code Quality | 7/10 | 9/10 | 1, 4 (print cleanup, boolean-flag, dead code) |
| Defensiveness | 7/10 | 9/10 | 2, 5 (S3 pagination, error propagation) |
| Performance | 7/10 | 9/10 | 1, 2 (FFmpeg timeouts, S3 pagination) |
| Type Rigor | 7/10 | 9/10 | 5 (Pydantic migration, Settings, type cast fix) |
| Test Value | 7/10 | 9/10 | 6 (placeholder test, conftest audit, e2e test) |
| Onboarding | 7/10 | 9/10 | 7 (CONTRIBUTING.md, setup script) |
| Problem-Solution Fit | 8/10 | 9/10 | 2, 4 (polling consolidation, TODO cleanup) |
| Architecture | 8/10 | 9/10 | 6 (magic number extraction) |
| Pragmatism | 8/10 | 9/10 | 1, 4 (dead code, ServiceFactory removal) |
| Creativity | 8/10 | 9/10 | 6 (TTS duration constant) |

## Findings Coverage (Health Audit)

| Audit Finding | Severity | Phase | Task |
|--------------|----------|-------|------|
| FFmpeg subprocess.run() no timeout | CRITICAL | 1 | 1 |
| S3 list_objects no pagination | CRITICAL | 2 | 1 |
| lambda_handler.py god module (681 lines) | HIGH | Deferred | -- |
| FFmpeg Popen no timeout (streaming) | HIGH | 2 | 2 |
| Colors.ts (3888 lines) | HIGH | Deferred | -- |
| Authorization/CORS duplication | HIGH | 2 | 4 (partial: `_` fix) |
| Polling function triplication | HIGH | 2 | 3 |
| job_service S3 GET+PUT per segment | HIGH | Deferred | -- |
| domain.py unused model layer | HIGH | 1 | 4 |
| Unused `c` lambda variables | MEDIUM | 2 | 4 |
| color_utils.py dead module | MEDIUM | 1 | 3 |
| Deprecated expo-permissions | MEDIUM | 1 | 7 |
| Settings class-level attrs | MEDIUM | 5 | 4 |
| Duplicate FFmpeg pipeline | MEDIUM | 2 | 5 |
| HLS leaky StorageService | MEDIUM | Deferred | -- |
| Unused exceptions/error codes | MEDIUM | 1 | 5 |
| traceback.print_exc() | MEDIUM | 1 | 2 |
| GeminiTTSProvider unused | MEDIUM | Deferred | -- |
| console.error in production | LOW | 3 | 3 (verified) |
| Empty useEffect | LOW | 1 | 6 |
| eslint-disable suppression | LOW | 1 | 6 |
| Test `as any` casts | LOW | Deferred | -- |
| Prompt strings in code | LOW | Deferred | -- |
| G_KEY env var naming | LOW | 5 | 4 (alias) |
