# Remediation Plan: 2026-03-15-audit-float

## Overview

This plan remediates findings from three sources:

1. **Repo health audit** (Phases 1-3, completed): Critical/high operational bugs, dead code removal, and lint guardrails.
2. **12-pillar evaluation** (Phases 4-8): Code quality, type rigor, defensiveness, test value, reproducibility, onboarding, and git hygiene improvements to bring all 12 pillars to 9/10.
3. **Documentation health audit** (Phase 9): Fix documentation drift, fill gaps, remove stale references, and correct code examples.

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
| [Phase 9](Phase-9.md) | [DOC-HEALTH] | Documentation drift, gaps, stale refs | ~25k | 8 |

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
- [Phase 9: Documentation Content Fixes](Phase-9.md) -- API.md schema fixes, CLAUDE.md corrections, README fixes, test README paths
- [Doc Audit](doc-audit.md) -- Documentation health audit findings
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

## Documentation Health (Doc Audit)

Phase 9 fixes documentation drift, fills gaps, removes stale references, and corrects code examples across all documentation files. Based on [doc-audit.md](doc-audit.md).

### Doc Audit Findings Coverage

| Finding | Category | Status | Phase 9 Task |
|---------|----------|--------|-------------|
| D1. API.md summary response schema wrong | Drift | Open | 1 |
| D2. API.md CORS methods missing GET | Drift | Open | 1 |
| D3. API.md "all requests must be POST" | Drift | Open | 1 |
| D4. API.md text limit 5000 vs 10000 | Drift | Open | 1 |
| D5. API.md `base64_audio` vs `base64` | Drift | Open | 1 |
| D6. CLAUDE.md CI push trigger | Drift | Fixed (Phase 3) | -- |
| D7. CLAUDE.md Python version inconsistency | Drift | Open | 2 |
| D8. CLAUDE.md CI runs all tests vs unit | Drift | Open | 2 |
| D9. CLAUDE.md `e2e` pytest marker | Drift | Open | 2 |
| D10. docs/README.md `npm install` flag | Drift | Open | 3 |
| D11. docs/README.md samconfig.toml "Edit" | Drift | Open | 3 |
| D12. ARCHITECTURE.md deploy command | Drift | Open | 5 |
| D13. Integration README wrong paths | Drift | Open | 6 |
| D14. README.md `npm install` flag | Drift | Open | 4 |
| G1. `EXPO_PUBLIC_ANDROID_CLIENT_ID` undocumented | Gap | Fixed (Phase 7 .env.example) | -- |
| G2. Download endpoint undocumented | Gap | Open | 1, 5 |
| G3. HLS streaming undocumented | Gap | Open | 1 |
| G4. `duration_minutes` undocumented | Gap | Open | 1 |
| G5. Backend env vars undocumented | Gap | Partial | 8 |
| G6. `src/utils/` undocumented | Gap | Open | 3, 5 |
| G7. `src/config/` undocumented | Gap | Open | 3, 5 |
| G8. `src/exceptions.py` undocumented | Gap | Open | 5 |
| S1. E2E README planned files | Stale | Acceptable (marked planned) | -- |
| S2. samconfig.toml referenced but gitignored | Stale | Open | 3, 5 |
| B1. E2E README .detoxrc.js path | Broken Link | Open | 7 |
| CE1. API.md `base64_audio` example | Stale Code | Open | 1 (=D5) |
| CE2. API.md missing streaming field | Stale Code | Open | 1 (=G3) |
| CE3. Integration README paths | Stale Code | Open | 6 (=D13) |
| CF1. G_KEY env var naming | Config Drift | Fixed (Phase 5 alias) | -- |
| CF2. FfmpegLayerArn undocumented | Config Drift | Open | 3, 4 |
| CF3. SAM params missing from root README | Config Drift | Open | 4 |
| CF4. CloudWatch log retention 7 vs 14 | Config Drift | Open | 1 |
| ST1. CLAUDE.md components flat vs subdirs | Structure | Open | 2 |
| ST2. docs/README.md tree incomplete | Structure | Open | 3 |
| ST3. ARCHITECTURE.md missing modules | Structure | Open | 5 |
| ST4. Integration README wrong components | Structure | Open | 6 |

### Findings Already Fixed by Prior Phases

The following doc-audit findings were resolved by earlier phases and require no action:
- **D6** (CI push trigger): Fixed in Phase 3 — `.github/workflows/ci.yml` now has `push` trigger
- **G1** (`EXPO_PUBLIC_ANDROID_CLIENT_ID`): Documented in `frontend/.env.example` (Phase 7)
- **CF1** (G_KEY naming): Settings now accepts both `GEMINI_API_KEY` and `G_KEY` via AliasChoices (Phase 5)
- **S1** (E2E planned files): README already marks these as `(planned)` — acceptable as-is

---

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
