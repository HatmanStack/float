---
type: doc-health
date: 2026-03-15
scope: all-documentation
constraints: none
---

## DOCUMENTATION AUDIT

### SUMMARY
- Docs scanned: 8 files (README.md, CLAUDE.md, CHANGELOG.md, docs/API.md, docs/README.md, docs/ARCHITECTURE.md, tests/frontend/e2e/README.md, tests/frontend/integration/README.md)
- Code modules scanned: ~60+ files across frontend and backend
- Total findings: 14 drift, 8 gaps, 2 stale, 1 broken link

---

### DRIFT (doc exists, doesn't match code)

**D1. API.md: Summary response schema does not match code**
- `docs/API.md` lines 76-98 document the summary response as having `sentiment`, `intensity` (number 0-1), `reasoning`, and `timestamp`.
- `backend/src/models/responses.py` lines 24-29 show the actual `SummaryResponse` has: `sentiment_label`, `intensity` (str, not number), `speech_to_text`, `added_text`, `summary`, `user_summary`, `user_short_summary`. None of the documented fields match. The response also includes `request_id`, `user_id`, and `inference_type` but NOT a `timestamp` field.

**D2. API.md: CORS headers do not match code**
- `docs/API.md` lines 397-401 document `Access-Control-Allow-Methods: POST, OPTIONS`.
- `backend/src/config/constants.py` line 79 shows the actual CORS methods are `OPTIONS,POST,GET`. GET is missing from the docs.

**D3. API.md: "All requests must be POST" is incorrect**
- `docs/API.md` line 19 states "All requests must be POST with Content-Type: application/json."
- The code at `backend/src/handlers/lambda_handler.py` lines 565-570 handles GET requests for `/job/{job_id}` and POST for `/job/{job_id}/download`.

**D4. API.md: Text input maximum documented as 5000, code uses 10000**
- `docs/API.md` line 71: "Text input maximum 5000 characters"
- `backend/src/config/constants.py` line 43: `MAX_TEXT_INPUT_LENGTH = 10000`

**D5. API.md: meditation response field name inconsistency**
- `docs/API.md` line 384 references `result.body.base64_audio` in the code example.
- `backend/src/models/responses.py` line 40 shows the actual field is `base64` (not `base64_audio`). The earlier JSON example at line 218 correctly shows `"base64"` but the JavaScript example uses the wrong field name.

**D6. CLAUDE.md: CI runs "on every push/PR" — actually only on PRs**
- `CLAUDE.md` line 79: "frontend-lint, frontend-tests, backend-tests run on every push/PR"
- `.github/workflows/ci.yml` line 4: `on: pull_request:` — there is no `push` trigger.

**D7. CLAUDE.md: Python target version inconsistency**
- `CLAUDE.md` line 75: "Python 3.12+ target"
- `CLAUDE.md` line 40: "Python 3.13" in architecture section.
- `backend/pyproject.toml` lines 98, 106: `target-version = "py312"`. The runtime is 3.13 but the linting target is 3.12, which could be confusing since the doc doesn't distinguish.

**D8. CI backend tests run all tests, not just unit tests**
- `CLAUDE.md` line 26: `npm run test:backend` documents running `pytest tests/unit`
- `.github/workflows/ci.yml` line 72: CI runs `pytest backend/tests` (all tests, not just unit tests).

**D9. CLAUDE.md: pytest markers list is incomplete**
- `CLAUDE.md` line 64: Lists markers `unit`, `integration`, `e2e`, `slow`
- `backend/pyproject.toml` lines 71-74: Only `unit`, `integration`, and `slow` are defined. There is no `e2e` marker.

**D10. docs/README.md: `npm install` without `--legacy-peer-deps`**
- `docs/README.md` line 31: `npm install`
- `CLAUDE.md` line 12 and CI workflow both use `npm install --legacy-peer-deps`. The docs/README.md omits the required flag.

**D11. docs/README.md: samconfig.toml example references non-existent file**
- `docs/README.md` lines 106-116 show example `samconfig.toml` content and reference editing it.
- `backend/samconfig.toml` does not exist (gitignored). Docs should mention creating it.

**D12. ARCHITECTURE.md: Deployment command incomplete**
- `docs/ARCHITECTURE.md` line 98: `cd backend && sam build && sam deploy`
- `package.json` line 16: `npm run deploy` runs `node ./backend/scripts/deploy.mjs`, a custom deploy script.

**D13. Integration test README: Wrong directory paths**
- `tests/frontend/integration/README.md` lines 17, 148, 153 reference `__tests__/integration/` as the test directory.
- Actual directory is `tests/frontend/integration/`. All run commands using `__tests__/integration/` would fail.

**D14. README.md: `npm install` without `--legacy-peer-deps`**
- `README.md` line 38: `npm install` in Quick Start
- CI and CLAUDE.md both require `--legacy-peer-deps`.

---

### GAPS (code exists, no doc)

**G1. `EXPO_PUBLIC_ANDROID_CLIENT_ID` env var undocumented**
- `frontend/components/AuthScreen.tsx` line 195 reads `process.env.EXPO_PUBLIC_ANDROID_CLIENT_ID`.
- Not mentioned in any documentation file.

**G2. Download endpoint (`POST /job/{job_id}/download`) undocumented**
- `backend/src/handlers/lambda_handler.py` lines 568-570 and `template.yaml` lines 154-159 define this endpoint.
- Not mentioned in API.md, ARCHITECTURE.md, or CLAUDE.md.

**G3. HLS streaming feature undocumented in API.md**
- Meditation response includes streaming info when HLS is enabled (`lambda_handler.py` lines 141-146).
- API.md has no mention of HLS streaming, playlist URLs, or the `streaming` field.

**G4. `duration_minutes` request field undocumented in API.md**
- `backend/src/models/requests.py` line 47: `duration_minutes: Literal[3, 5, 10, 15, 20] = 5`
- Not mentioned in API.md meditation request fields.

**G5. Backend env vars `ENABLE_HLS_STREAMING`, `LOG_LEVEL`, `FFMPEG_PATH`, `ENVIRONMENT` undocumented**
- Read by backend code but not documented in any docs.

**G6. `src/utils/` module undocumented**
- Contains `circuit_breaker.py`, `cache.py`, `logging_utils.py`, `color_utils.py`, `file_utils.py`, `audio_utils.py`.
- None mentioned in architecture docs.

**G7. `src/config/` module undocumented**
- `settings.py` and `constants.py` not mentioned in ARCHITECTURE.md.

**G8. `src/exceptions.py` undocumented**
- Custom exception hierarchy (FloatException, ValidationError, ExternalServiceError, TTSError) exists but not documented.

---

### STALE (doc exists, code doesn't)

**S1. E2E README references non-existent files**
- `tests/frontend/e2e/README.md` lines 101-107 list planned files: `init.ts`, `helpers/navigation.ts`, `helpers/authentication.ts`, `helpers/backend-mocks.ts`.
- None of these exist.

**S2. samconfig.toml referenced but does not exist**
- Multiple docs reference `backend/samconfig.toml` but it does not exist in the repo (gitignored).

---

### BROKEN LINKS

**B1. E2E README: .detoxrc.js location ambiguity**
- `tests/frontend/e2e/README.md` line 314: "Detox configuration created (.detoxrc.js)"
- The file exists at `frontend/.detoxrc.js` but the README implies it's in the E2E directory.

---

### STALE CODE EXAMPLES

**CE1. API.md Example 3: Wrong field name `base64_audio`**
- `docs/API.md` line 384: `const audioData = result.body.base64_audio;`
- Code uses `base64` as the field name, not `base64_audio`.

**CE2. API.md: Meditation response JSON doesn't mention `streaming` field**
- Actual response includes `streaming` object when HLS enabled, but documented JSON shows only `job_id`, `status`, `message`.

**CE3. Integration test README: All code examples use `__tests__/integration/` path**
- Commands like `npm test -- __tests__/integration/` would fail. Correct path is `tests/frontend/integration/`.

---

### CONFIG DRIFT

**CF1. `G_KEY` env var name mismatch**
- `backend/src/config/settings.py` line 11: `GEMINI_API_KEY: str = os.getenv("G_KEY", "")`
- `docs/README.md` line 124: documents `GeminiApiKey` as a SAM parameter.
- The SAM template maps `GeminiApiKey` → `G_KEY` env var. The env var name `G_KEY` is never documented — only the SAM parameter name.

**CF2. `FfmpegLayerArn` SAM parameter undocumented**
- `backend/template.yaml` line 48: `FfmpegLayerArn` is a required parameter.
- Not documented in README.md or docs/README.md deployment sections.

**CF3. `S3DataBucket`, `S3AudioBucket`, `IncludeDevOrigins` SAM parameters partially documented**
- Appear in docs/README.md but not in root README.md deployment table.

**CF4. CloudWatch log retention mismatch**
- `docs/API.md` line 427: "CloudWatch logs retained for 7 days"
- `backend/template.yaml` line 171: `RetentionInDays: 14`

---

### STRUCTURE ISSUES

**ST1. CLAUDE.md lists components as flat but they use subdirectories**
- `CLAUDE.md` line 49: "Components: `components/` — HLS player, meditation controls, auth screen, download button"
- Actual structure has subdirectories: `components/HLSPlayer/`, `components/DownloadButton/`, `components/ScreenComponents/`, `components/navigation/`.

**ST2. docs/README.md project structure tree is incomplete**
- Tree omits `src/config/`, `src/models/`, `src/utils/`, `src/exceptions.py` from the backend section.
- Frontend tree omits `components/` subdirectories.

**ST3. Backend `models/` module missing from ARCHITECTURE.md**
- Lists Services, Handler, Middleware layers but does not mention Models, Config, or Utils.

**ST4. Integration test README references non-existent components**
- `tests/frontend/integration/README.md` lines 225-226 reference `IncidentCreator` and `IncidentList` components.
- These do not exist. Actual components are `AudioRecording`, `history`, `IncidentItem`, etc.
