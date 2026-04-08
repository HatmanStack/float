# Phase 0: Foundation

This phase has no implementation tasks. It documents the architectural
decisions, project conventions, testing strategy, and commit format that all
subsequent phases must obey.

## Project Conventions

These conventions are extracted from the repo `CLAUDE.md` and the
2026-03-15 plan that this remediation builds upon. Implementers MUST NOT
deviate.

### Tooling and Runtimes

| Concern | Convention |
|---------|------------|
| Node | 24+ (CI uses `actions/setup-node@v6` with `node-version: '24'`) |
| Python | 3.13 runtime in Lambda; 3.12 lint target in `pyproject.toml` |
| Frontend package manager | `npm install --legacy-peer-deps` |
| Backend lint | `cd backend && uvx ruff check .` (the project uses `uvx`, not `python -m ruff`) |
| Backend tests | `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` |
| Backend full tests | `pytest backend/tests` (CI runs all backend tests, not just unit) |
| Frontend tests | `cd frontend && npx jest --forceExit` (no watch mode at root) |
| Full check | `npm run check` -- must pass after every phase |
| Deploy | `npm run deploy` -- DO NOT run unless explicitly asked |

### Code Style

| Layer | Conventions |
|-------|-------------|
| Frontend | ESLint flat config in `frontend/eslint.config.js`, Prettier 100 char width, TypeScript strict mode, `@typescript-eslint/no-explicit-any: warn`, `no-console: warn` (allows `warn`/`error`) |
| Backend | ruff + black, 100 char line length, target `py312`, ruff selects `E,F,W,I,UP,B,S` with the existing `ignore` list (do not narrow without justification) |

### Logging

- Backend uses `from ..utils.logging_utils import get_logger; logger = get_logger(__name__)`
- Do NOT use `logging.getLogger(__name__)` directly. `gemini_service.py:16` is
  the one current violator and is fixed in Phase 1.
- Use `logger.warning("text", extra={"data": {...}})` for structured logs.
  Do NOT use f-strings *and* `extra={"data": ...}` in the same call -- pick
  one. The single `ffmpeg_audio_service.py:83` f-string-only violator is
  fixed in Phase 1 Task 6 (line 76 of the same file is already correct).

### Exceptions

- All errors raised from backend code MUST be subclasses of
  `FloatException` from `backend/src/exceptions.py`. The taxonomy:
  - `ValidationError` -- 4xx, not retriable, client must fix request
  - `ExternalServiceError` -- 5xx, retriable (TTS, AI, S3 transient failure)
  - `TTSError`, `AIServiceError`, `CircuitBreakerOpenError` -- specialised
    `ExternalServiceError`
  - `AudioProcessingError` -- FFmpeg/encoding failure (5xx, not retriable)
  - `JobError`, `JobNotFoundError`, `JobNotCompletedError`, `JobAccessDeniedError`
- Raw `raise Exception(...)` is forbidden. Phase 3 Task 5 fixes all current
  violators across `backend/src/`. As of 2026-04-08 the violators (verified
  via `grep -rn "raise Exception(" backend/src/`) are:
  - `lambda_handler.py:237` ("Failed to encode combined audio")
  - `lambda_handler.py:290` ("Failed to download cached TTS audio")
  - `ffmpeg_audio_service.py:199` (wrapped multi-line raise)
  - `ffmpeg_audio_service.py:220` (`f"Failed to upload segment {i}"`)
  - `ffmpeg_audio_service.py:557` (`f"Failed to upload fade segment ..."`)
  - `ffmpeg_audio_service.py:751` (`f"FFmpeg exited unexpectedly: ..."`)
  - `ffmpeg_audio_service.py:761` (`f"FFmpeg failed: ..."`)
  - `ffmpeg_audio_service.py:773` (`f"FFmpeg pipe closed: ..."`)

  Phase 3 Task 5 verifies completion via `grep -rn "raise Exception("
  backend/src/` returning zero hits.

### Conventional Commits

All commits MUST follow `type(scope): description` per `commitlint.config.js`
(`@commitlint/config-conventional`). Husky enforces this via `.husky/commit-msg`.

Allowed types: `feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`, `perf`, `style`, `build`.
Allowed scopes used in this plan: `frontend`, `backend`, `ci`, `docs`, omit for
repo-wide changes.

Examples used in this plan:

```text
chore(frontend): delete generated Colors.ts gradient data
fix(backend): bump requests to 2.33.0 to address CVE-2024-47081
refactor(backend): extract router from LambdaHandler
docs(api): document /token endpoint and download response shape
ci: add lychee link checker for markdown
```

### Branch Naming

Use `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `ci/` prefixes per
`CONTRIBUTING.md`. The plan is branch-agnostic -- the orchestrator selects the
working branch.

---

## Architecture Decisions

### ADR-1: Phase Order Is Inviolable

```text
HYGIENIST -> IMPLEMENTER -> FORTIFIER -> DOC-ENGINEER
```

- **Hygienist (Phase 1)** removes only. No new abstractions, no behavior change,
  no new lint rules. Quick wins, dead-data deletion, lint-of-existing-rules
  fixes, deprecation cleanup.
- **Implementer (Phases 2-4)** changes structure, error handling, performance
  characteristics, and architecture. Behavior preserving by default; explicit
  exceptions are called out per task (e.g. `/token` endpoint replacement).
- **Fortifier (Phase 5)** adds guardrails only -- new lint rules, new CI jobs,
  new pre-commit hooks, type-tightening config. Fortifier MUST NOT touch
  product code except to satisfy a guardrail it just enabled.
- **Doc-engineer (Phase 6)** updates only documentation files (`README.md`,
  `CLAUDE.md`, `CONTRIBUTING.md`, `docs/*.md`, comment-only header changes)
  plus prevention tooling (markdownlint, lychee). Doc-engineer MUST NOT change
  product code.

### ADR-2: Behavior Preservation Except for Documented Exceptions

These phases preserve all existing user-visible behavior except where
explicitly documented:

| Exception | Phase | Task | Justification |
|-----------|-------|------|---------------|
| `/token` endpoint behavior changes (returns ephemeral marker, not raw API key) | 2 | 1 | CRITICAL security finding -- the existing behavior is the bug |
| Routing pre-validates `user_id` format and rejects path-traversal patterns | 2 | 2 | Stress eval critical failure point -- raw `user_id` in S3 keys |
| Retry loop no longer self-fires on `_save_job` failure | 3 | 4 | Health audit HIGH finding -- prevents the ping-pong scenario |
| TTS streaming no longer leaks generator on `BrokenPipeError` | 3 | 3 | Health audit HIGH finding -- partial-write leak |

All other behavior MUST remain identical. Existing test suites
(`npm run check`) MUST pass after each phase.

### ADR-3: No DynamoDB Migration And No ETag Conditional Writes In This Plan

The Stress evaluation recommends migrating job state and rate limiting from S3
to DynamoDB. This plan EXPLICITLY DEFERS that migration. Reasons:

1. It is not a tech-debt fix; it is a new architectural choice with deployment,
   IAM, and cost implications outside the audit scope.
2. A DynamoDB migration is a one-day project that deserves its own plan and
   review pipeline.

This plan ALSO EXPLICITLY DEFERS the proposed in-place mitigation of adding
ETag-aware conditional writes to `S3StorageService.update_streaming_progress`.
An earlier draft of this ADR claimed Phase 3 would extend `S3StorageService`
with conditional-write helpers; that work is dropped because:

1. ETag-aware writes require either an optimistic-concurrency retry loop or a
   versioned-payload merge strategy. Both are non-trivial designs that touch
   `JobService`, `S3StorageService`, and the streaming watcher loop, and
   neither has a regression-safe surface against the existing test suite.
2. The race window is narrow in practice (concurrent retries against the same
   `job_id` are rare given `MAX_GENERATION_ATTEMPTS = 3` and idempotent
   downstream consumers).
3. A correct fix is part of the same migration as the DynamoDB switch; doing
   the S3 fix first risks two refactors landing back-to-back.

The Phase 3 thread-safety work mitigates the *in-process* race in
`process_stream_to_hls`. The cross-invocation race in
`update_streaming_progress` is documented as a Known Limitation in Phase 3
and remains. The README Performance pillar target reflects that the ETag fix
is out of scope (see the README "Out of Scope" section).

Phase 3 implementers MUST NOT introduce DynamoDB dependencies and MUST NOT add
ETag/conditional-write helpers to `S3StorageService` -- both are out of scope.

### ADR-4: Subtractive Phase 1 Constraints

Phase 1 (HYGIENIST) MUST satisfy these invariants:

1. No new files created (deletions and edits only)
2. No new dependencies added (only pinning/bumping versions)
3. No new lint rules introduced (Fortifier owns that)
4. No control-flow changes -- only deletions, renames, and direct equivalent
   substitutions

The single exception is the `Colors.ts` rewrite: the file is replaced with a
small, hand-written palette that preserves the same exported `Colors` object
shape so consumers compile unchanged. This is documented in Phase 1 Task 1.

### ADR-5: Single Source of Truth for Architecture Documentation

Documentation duplication between `README.md`, `docs/README.md`,
`docs/ARCHITECTURE.md`, and `CLAUDE.md` is a tracked structural finding (ST1,
ST3 in doc-audit). Phase 6 establishes the canonical hierarchy:

1. `docs/ARCHITECTURE.md` is the source of truth for architecture diagrams,
   layer definitions, and async flow.
2. `docs/API.md` is the source of truth for endpoints and request/response
   shapes.
3. `docs/README.md` indexes the docs/ tree only -- it does not duplicate
   architecture.
4. The repo-root `README.md` is a marketing-style landing page that links to
   `docs/`.
5. `CLAUDE.md` is the source of truth for build/test/lint commands and
   conventions only -- it links to `docs/ARCHITECTURE.md` for everything else.

Doc-engineer MUST NOT introduce new duplication.

---

## Out of Scope

The following findings are recognized but explicitly NOT addressed by any
phase in this plan. The README "Out of Scope" section mirrors this list as a
quick index; the canonical justifications live here.

1. **DynamoDB migration for job state and rate limiting.** See ADR-3.
1. **ETag-aware conditional writes on `S3StorageService`.** See ADR-3.
   Earlier drafts of ADR-3 promised Phase 3 would extend `S3StorageService`
   with conditional-write helpers; that work is dropped. The cross-invocation
   read-modify-write race in `update_streaming_progress` remains as a Known
   Limitation in Phase 3.
1. **Server-issued opaque `user_id` identifier.** Phase 2 Task 2 adds a
   validating regex on `user_id` to block path-traversal patterns. The
   broader identity overhaul (server-minted UUIDs, JWTs, etc.) belongs to a
   separate auth plan.
1. **Broad narrowing of the ~57 `except Exception` clauses across
   `backend/src/`.** Phase 2 Task 4 narrows the THREE middleware-level
   catch-all clauses in `json_middleware`, `request_validation_middleware`,
   and the request-size validator so domain exception taxonomy reaches HTTP
   responses (this is the user-visible symptom called out by the eval). The
   remaining ~54 service-level catches are mostly defensive logging
   boundaries (`hls_service.py` 11, `job_service.py` 8,
   `ffmpeg_audio_service.py` 7, etc.) that do not surface in HTTP responses.
   A coherent narrowing pass requires per-service review and a per-service
   exception taxonomy decision; that is a multi-day refactor that exceeds
   the audit-remediation scope. A future plan should target this work
   service-by-service.
1. **`BackendMeditationCall.tsx` full redesign.** Phase 4 Task 4 splits the
   component into a hook plus a view; a complete state-management redesign
   is out of scope.
1. **Modernization of legacy `typing.List`/`typing.Dict`/`typing.Union`
   imports across `backend/src/handlers/lambda_handler.py` and friends.**
   Phase 5 Task 3 verifies that any UP* rule with zero violators is moved
   from the ignore list, but Phases 1-4 do NOT add a modernization sweep
   (Phase 1 is subtractive only, and Phase 4's TypedDict additions use
   modern syntax in new files only). UP006/UP007/UP035 will therefore
   remain ignored after Phase 5; that is expected behaviour. A future plan
   can do the import sweep across legacy files in one pass.

---

## Testing Strategy

### Backend

- Unit tests: `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Full backend tests (matches CI): `pytest backend/tests`
- Mocking: services are mocked at the interface level. `subprocess.run`,
  `boto3` clients, and HTTP libraries are mocked via `unittest.mock.patch`
  or `moto` (already in `requirements-dev.txt`).
- No real AWS calls in unit tests. CI sets `AWS_DEFAULT_REGION=us-east-1` and
  `S3_BUCKET=test-bucket` as harmless placeholders only.
- New tests for code path changes:
  - Phase 2: `/token` endpoint test (returns 410 Gone OR enforces shared
    rate-limit fence -- chosen by implementer per Task 1 spec)
  - Phase 2: routing test that `/download/job/x` does not double-match
  - Phase 2: `user_id` validator rejects `..`, `/`, and other path-traversal
    inputs
  - Phase 3: `process_stream_to_hls` thread-safety test using a synthetic
    `voice_generator` and a mocked `hls_service`
  - Phase 3: retry-loop test that asserts no second `_invoke_async_meditation`
    if `increment_generation_attempt` raises
  - Phase 4: router smoke test that the new dispatch table covers all four
    historical route shapes
  - Phase 4: `_prepare_mixed_audio` test that asserts subprocess sequence and
    cleanup contract

### Frontend

- Unit and integration tests: `cd frontend && npx jest --forceExit`
- The Jest projects (`unit`, `integration`) are configured in
  `frontend/package.json` -- do not move tests
- The `Colors.ts` rewrite in Phase 1 MUST be accompanied by a snapshot or
  shape-equivalence test asserting that consumers (`IncidentColoring.tsx`,
  any `useColorScheme` consumers) still type-check
- Test files may use `any` (eslint relaxes the rule under `**/tests/**`); the
  Phase 5 `any` reduction work targets test files only as an opt-in cleanup,
  not as a hard cutover

### CI Gate

- All four CI jobs (`frontend`, `backend`, `dockerfile-lint`, `status-check`)
  must pass before PHASE_APPROVED is emitted
- The Phase 5 fortifier work adds new CI checks; those are listed in Phase 5
  itself, not enforced retroactively in earlier phases

---

## File Reference

Files referenced across multiple phases:

| File | Role | Phases |
|------|------|--------|
| `backend/src/handlers/lambda_handler.py` | 756-line god handler | 2, 3, 4 |
| `backend/src/handlers/middleware.py` | Middleware chain, exception handling | 2, 4 |
| `backend/src/services/ffmpeg_audio_service.py` | 805-line FFmpeg orchestration | 3, 4 |
| `backend/src/services/job_service.py` | S3-backed job state | 3 |
| `backend/src/services/gemini_service.py` | Logging convention violator | 1 |
| `backend/src/exceptions.py` | Domain exception taxonomy | 1, 3 |
| `backend/src/config/settings.py` | Pydantic BaseSettings | 6 (docs) |
| `backend/src/config/constants.py` | Shared constants | 4 |
| `backend/src/models/requests.py` | Pydantic request models | 4, 6 |
| `backend/requirements.txt` | Backend deps (CVE bump) | 1 |
| `frontend/constants/Colors.ts` | 3888-line generated color data | 1 |
| `frontend/components/HLSPlayer/hlsPlayerHtml.ts` | `console.log` in shipped code | 1 |
| `frontend/scripts/inject-seo.js` | `console.log` in shipped script | 1 |
| `frontend/components/BackendMeditationCall.tsx` | 427-line component | 4 |
| `README.md` | Repo-root landing | 6 |
| `CLAUDE.md` | Build/test/lint conventions | 6 |
| `docs/README.md` | Docs index | 6 |
| `docs/API.md` | API reference (stale) | 6 |
| `docs/ARCHITECTURE.md` | Architecture (stale) | 6 |
| `.github/workflows/ci.yml` | CI pipeline | 5 |
| `.husky/pre-commit`, `.husky/commit-msg` | Git hooks | 5 |

---

## Pipeline References

This plan is the planner-stage artifact for the pipeline described in
`.claude/skills/pipeline/pipeline-protocol.md`. Plan reviewer is invoked
after `PLAN_COMPLETE`. Implementers receive the phase tag in their phase title
(`[HYGIENIST]`, `[IMPLEMENTER]`, `[FORTIFIER]`, `[DOC-ENGINEER]`) and route
to the matching role file in `.claude/skills/pipeline/`.
