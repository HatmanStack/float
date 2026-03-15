# Repo Health Remediation Plan: 2026-03-15-audit-float

## Overview

This plan remediates tech debt identified in the [health audit](health-audit.md) of the Float monorepo. The audit found 2 critical, 7 high, 9 medium, and 6 low findings across architectural, structural, operational, and hygiene vectors.

The plan follows a **subtractive-first** approach: Phases 1-2 (tagged `[HYGIENIST]`) remove dead code, fix operational bugs, and consolidate duplication without adding new abstractions. Phase 3 (tagged `[FORTIFIER]`) adds linting rules and CI guardrails that prevent the cleaned issues from recurring.

Several HIGH findings are explicitly deferred as they require dedicated architectural refactoring beyond the scope of a health remediation: `lambda_handler.py` god module (681 lines), `Colors.ts` static gradients (3888 lines), `job_service.py` S3 polling overhead, and `hls_service.py` leaky storage abstraction.

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

## Navigation

- [Phase 0: Foundation](Phase-0.md) -- ADRs, testing strategy, conventions
- [Phase 1: Quick Wins & Dead Code](Phase-1.md) -- FFmpeg timeouts, dead module removal, deprecated API fixes
- [Phase 2: Critical & High Fixes](Phase-2.md) -- S3 pagination, streaming timeout, polling consolidation
- [Phase 3: Guardrails & CI](Phase-3.md) -- Ruff rules, CI push trigger, lint verification
- [Feedback](feedback.md) -- Review feedback tracking
- [Health Audit](health-audit.md) -- Original audit findings

## Findings Coverage

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
| Settings class-level attrs | MEDIUM | Deferred | -- |
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
| G_KEY env var naming | LOW | Deferred | -- |
