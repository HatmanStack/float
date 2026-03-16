# Phase 0: Foundation

## Architecture Decisions

### ADR-1: Subtractive Before Additive

All cleanup, deletion, and consolidation work (Phases 1-2, tagged `[HYGIENIST]`) must be completed before any guardrail or enforcement work (Phase 3, tagged `[FORTIFIER]`). The hygienist phases must NOT introduce new code, abstractions, or patterns -- they only remove, simplify, and fix existing code. The fortifier phase must NOT fix existing code -- it only adds guardrails that enforce the clean state left by the hygienist.

### ADR-2: No Behavioral Changes

These phases fix tech debt without changing any user-facing behavior. No API contract changes, no new features, no new endpoints. All existing tests must continue to pass after each phase.

### ADR-3: Preserve Unused-but-Intentional Code

Some Vulture findings at 60% confidence may be intentional (e.g., `GeminiTTSProvider` may be a planned alternative provider, `service_factory` may be used in integration tests). The plan explicitly calls out which dead code to remove vs. which to leave with a justification comment. When in doubt, add a `# Used by: <context>` comment rather than deleting.

### ADR-4: Minimal Test Surface for Cleanup

Hygienist phases primarily verify through existing test suites (`npm run check`). New tests are only written when a code change alters control flow (e.g., adding `timeout` to `subprocess.run`). The fortifier phase adds no new tests -- it adds linting rules and CI checks.

---

## Testing Strategy

### Backend Tests
```bash
# Run all backend unit tests
cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short

# Run a specific test file
cd backend && PYTHONPATH=. pytest tests/unit/test_services.py -v --tb=short

# Run ruff lint
cd backend && uvx ruff check .
```

### Frontend Tests
```bash
# Run all frontend tests
npm test

# Run lint + TypeScript check
npm run lint
```

### Full Check (must pass after every phase)
```bash
npm run check
```

### Mocking Approach
- Backend tests mock at the service interface level (e.g., `mock_storage_service`, `mock.patch`)
- `subprocess.run` calls are mocked via `unittest.mock.patch` on the `subprocess` module
- No real AWS/S3/API calls in unit tests -- all external services are mocked in `backend/tests/mocks/external_apis.py` and `backend/tests/conftest.py`

---

## Commit Message Format

All commits use conventional commits format:

```
chore(scope): brief description of change

Body explaining what was removed/fixed and why.
```

Scopes used in this plan:
- `chore(backend)` -- backend code cleanup
- `chore(frontend)` -- frontend code cleanup
- `fix(backend)` -- operational bug fixes (e.g., missing timeouts)
- `ci` -- CI/workflow changes

---

## File Reference

Key files referenced across all phases:

| File | Role |
|------|------|
| `backend/src/services/ffmpeg_audio_service.py` | Audio processing (FFmpeg subprocess calls) |
| `backend/src/handlers/lambda_handler.py` | Main request handler (681 lines) |
| `backend/src/utils/color_utils.py` | Dead utility module (numpy/scipy) |
| `backend/src/models/domain.py` | Unused domain model layer |
| `backend/src/exceptions.py` | Exception hierarchy |
| `backend/src/providers/openai_tts.py` | OpenAI TTS provider |
| `backend/src/providers/gemini_tts.py` | Gemini TTS provider (potentially unused) |
| `backend/src/config/settings.py` | Settings class |
| `backend/src/models/requests.py` | Request parsing and validation |
| `frontend/components/Notifications.tsx` | Push notification component |
| `frontend/app/(tabs)/explore.tsx` | Main explore tab |
| `frontend/constants/Colors.ts` | Color gradients (3888 lines) |
