# Remediation Plan: 2026-04-08-audit-float

## Overview

This plan unifies remediation work derived from three intake artifacts produced
on 2026-04-08:

1. `health-audit.md` -- 2 critical, 8 high, 12 medium, 6 low tech-debt findings
   centered on a 756-line `LambdaHandler` god object, the streaming HLS
   pipeline in `ffmpeg_audio_service.py`, and a `/token` endpoint that returns
   the raw Gemini API key.
2. `eval.md` -- 12-pillar evaluation across Hire, Stress, and Day-2 lenses.
   Lowest scores: Performance (5/10) and Defensiveness (6/10) on the Stress
   axis, plus Architecture (7/10) and Code Quality (8/10) on Hire.
3. `doc-audit.md` -- 9 drift items, 6 gaps, 4 stale references, and 2 broken
   code examples spanning README/CLAUDE/ARCHITECTURE/API documentation.

The plan follows the canonical sequencing required by the audit pipeline:
hygienist work first (subtractive cleanup), then implementer work (structural
fixes), then fortifier work (additive guardrails), then doc-engineer work
(documentation accuracy and prevention tooling). Where the same finding appears
in multiple intake docs (for example, `LambdaHandler` god object,
`Colors.ts` 3888-line outlier, `/token` API key leak, undocumented HLS flow),
the work is consolidated into a single task and cross-referenced.

The plan is intentionally compact: phase sizing reflects the work, not a token
budget. Each phase delivers a coherent slice that can be reviewed in one pass.

## Prerequisites

- Node.js 24+ and npm
- Python 3.13+
- `npm install --legacy-peer-deps` completed at the repo root
- Backend deps: `cd backend && pip install -r requirements.txt -r requirements-dev.txt`
- Local tooling: `uvx ruff` (already used by `npm run lint:backend`)
- All four CI jobs (`frontend`, `backend`, `dockerfile-lint`, `status-check`)
  must pass after every phase

## Phase Summary

| Phase | Tag | Goal | Est. Tokens | Tasks |
|-------|-----|------|-------------|-------|
| [Phase 0](Phase-0.md) | Foundation | ADRs, conventions, testing strategy | -- | -- |
| [Phase 1](Phase-1.md) | [HYGIENIST] | Quick wins and dead-data deletion | ~18k | 6 |
| [Phase 2](Phase-2.md) | [IMPLEMENTER] | Critical security and routing fixes | ~22k | 4 |
| [Phase 3](Phase-3.md) | [IMPLEMENTER] | FFmpeg streaming and job-state hardening | ~24k | 5 |
| [Phase 4](Phase-4.md) | [IMPLEMENTER] | Architecture decomposition and type rigor | ~22k | 4 |
| [Phase 5](Phase-5.md) | [FORTIFIER] | Lint expansion, CI, hooks, type guardrails | ~16k | 4 |
| [Phase 6](Phase-6.md) | [DOC-ENGINEER] | Documentation drift, gaps, prevention tooling | ~20k | 6 |

## Navigation

- [Phase 0: Foundation](Phase-0.md)
- [Phase 1: Hygienist -- Quick Wins and Dead Data](Phase-1.md)
- [Phase 2: Implementer -- Critical Security and Routing](Phase-2.md)
- [Phase 3: Implementer -- Streaming Pipeline and Job State](Phase-3.md)
- [Phase 4: Implementer -- Architecture and Type Rigor](Phase-4.md)
- [Phase 5: Fortifier -- Lint, CI, Hooks](Phase-5.md)
- [Phase 6: Doc-Engineer -- Documentation Accuracy and Prevention](Phase-6.md)
- [Feedback Log](feedback.md)
- [Health Audit (intake)](health-audit.md)
- [Repo Eval (intake)](eval.md)
- [Doc Audit (intake)](doc-audit.md)

## Findings Coverage

### Health Audit Findings

| Finding | Severity | Phase | Task |
|---------|----------|-------|------|
| `/token` returns raw `GEMINI_API_KEY` | CRITICAL | 2 | 1 |
| `requests==2.32.3` CVE-2024-47081, CVE-2026-25645 | CRITICAL | 1 | 2 |
| `LambdaHandler` god object (756 lines, 7 services) | HIGH | 4 | 1 |
| Routing via `rawPath` string matching | HIGH | 2 | 3 |
| `process_stream_to_hls` thread safety | HIGH | 3 | 1 |
| Watcher loop spin via `os.path.exists` | HIGH | 3 | 2 |
| `process.stdin.write` no backpressure | HIGH | 3 | 3 |
| Retry self-invoke double-fire risk | HIGH | 3 | 4 |
| Raw `Exception` raises bypass taxonomy | HIGH | 3 | 5 |
| `Colors.ts` 3888-line generated data | HIGH | 1 | 1 |
| `_prepare_mixed_audio` 5 sequential subprocesses | MEDIUM | 4 | 2 |
| `_get_audio_duration_from_file` duplicate of `get_audio_duration` | MEDIUM | 1 | 4 |
| Module-level `_token_rate_limit` unbounded | MEDIUM | 2 | 1 |
| Middleware `except Exception` swallows taxonomy | MEDIUM | 2 | 4 |
| Inline `from .middleware import cors_middleware` (3x) | MEDIUM | 2 | 3 |
| `combine_voice_and_music_hls` duplication | MEDIUM | 4 | 2 |
| `_invoke_async_meditation` boto3 client per call | MEDIUM | 1 | 5 |
| Three near-identical temp-file cleanup blocks | MEDIUM | 4 | 2 |
| Backend ~57 `except Exception` clauses | MEDIUM | -- | Out of Scope (see Phase 0) |
| Test files using `any` | MEDIUM | 5 | 4 |
| `lambda_handler.py` legacy `typing.Dict, List` | LOW | 5 | 3 |
| `gemini_service.py` uses `logging.getLogger` directly | LOW | 1 | 6 |
| Mixed logging conventions in `ffmpeg_audio_service.py:76` | LOW | 1 | 6 |
| `exceptions.py:143` bare `pass` | LOW | 1 | 6 |
| `console.log` in `hlsPlayerHtml.ts` and `inject-seo.js` | LOW | 1 | 3 |
| Module-level constants scattered in `lambda_handler.py` | LOW | 4 | 4 |

### Eval Pillar Coverage

| Pillar | Current | Target | Phases |
|--------|---------|--------|--------|
| Defensiveness | 6/10 | 9/10 | 2, 3 (rate limit, retry loop, raw user_id) |
| Performance | 5/10 | 7/10 | 1, 3 (boto3 reuse, retry loop, generator drain) |
| Architecture | 7/10 | 9/10 | 4 (router decomposition, ffmpeg split) |
| Pragmatism | 7/10 | 9/10 | 4 (dual validation collapse, prelude extract) |
| Type Rigor | 7/10 | 9/10 | 4, 5 (TypedDict for events/jobs, lint) |
| Code Quality | 8/10 | 9/10 | 4 (BackendMeditationCall trim, prelude) |
| Problem-Solution Fit | 8/10 | 9/10 | 2 (token endpoint replaced or hardened) |
| Creativity | 8/10 | 9/10 | 4 (MeditationPlanner constants extracted) |

### Doc Audit Coverage

| Finding | Category | Phase 6 Task |
|---------|----------|--------------|
| D1 Expo/RN/React versions stale | Drift | 1 |
| D2 Node 24 LTS claim | Drift | 1 |
| D3 Download endpoint response shape wrong | Drift | 2 |
| D4 `/token` endpoint missing | Drift | 2 |
| D5 `qa_transcript` field missing | Drift | 2 |
| D6 `intensity` type drift | Drift | 2 |
| D7 `Invalid inference_type` text drift | Drift | 2 |
| D8 Job-status example missing fields | Drift | 2 |
| D9 ARCHITECTURE.md tech stack drift | Drift | 1 |
| G1 HLS streaming flow undocumented | Gap | 3 |
| G2 Token/Gemini Live auth flow undocumented | Gap | 3 |
| G3 `EXPO_PUBLIC_ANDROID_CLIENT_ID` undocumented | Gap | 1 |
| G4 `G_KEY` alias undocumented | Gap | 1 |
| G5 Retry semantics undocumented | Gap | 3 |
| G6 Job-endpoint authorization undocumented | Gap | 2 |
| S1 docs/README.md tests path stale | Stale | 1 |
| S2 README.md tests path stale | Stale | 1 |
| S3 CLAUDE.md tests path stale | Stale | 1 |
| S4 docs/README.md `npm test` watch claim | Stale | 1 |
| CE1 API.md polling loop missing playlist_url | Stale Code | 2 |
| CE2 API.md JS example treats meditation as sync | Stale Code | 2 |
| CF1 `ENABLE_HLS_STREAMING` default | Config Drift | (no action -- already correct) |
| CF2 Deploy parameter tables drift | Config Drift | 4 |
| ST1 README duplication of env/deploy | Structure | 4 |
| ST2 docs/ hierarchy missing plans index | Structure | 4 |
| ST3 CLAUDE.md duplicates ARCHITECTURE.md | Structure | 4 |

## Out of Scope

The following items are recognized but deferred to a future plan. Phase 0
holds the canonical justifications; this section is a quick index.

- Migrating job state from S3 to DynamoDB (called out by Stress eval as a
  performance fix). This plan does NOT add ETag-aware conditional writes
  either -- the read-modify-write race in `update_streaming_progress` is
  documented as a Known Limitation in Phase 3 and remains for a future plan.
- Replacing the in-memory rate limiter with a DynamoDB atomic counter. Phase 2
  removes the unsafe `/token` plaintext path; the rate limiter is replaced or
  removed in the same task. A DynamoDB-backed limiter is a separate plan.
- Migration of `user_id` to a server-issued opaque identifier. Phase 2 adds a
  validating regex on `user_id` (path-traversal protection) and the broader
  identity overhaul is deferred.
- Decomposing `BackendMeditationCall.tsx` (427 lines) is in scope for Phase 4
  Task 4 only as a "split into hooks + view" refactor; a full redesign is not.
- Narrowing the ~57 backend `except Exception` clauses in product code. Phase
  2 Task 4 narrows the THREE middleware-level catch-alls so domain exception
  taxonomy reaches HTTP responses (the user-visible symptom). The remaining
  ~54 service-level clauses are mostly defensive logging boundaries that do
  not affect HTTP responses; broad narrowing across `hls_service.py` (11),
  `job_service.py` (8), `ffmpeg_audio_service.py` (7), and friends is a
  multi-service review that exceeds the audit-remediation scope. See Phase 0
  "Out of Scope" for the full justification.
