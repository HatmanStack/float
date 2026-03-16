# Phase 9: Documentation Content Fixes

**Tag:** `[DOC-HEALTH]`

## Phase Goal

Fix all documentation drift, fill critical gaps, remove stale references, and correct broken code examples across all doc files. Every change must be verified against the actual source code.

## Success Criteria

- All API.md response schemas, field names, and constraints match actual code
- All CLAUDE.md statements match CI config and pyproject.toml
- All README files use correct install commands and directory paths
- All code examples use correct field names and paths
- No references to non-existent files, markers, or endpoints remain undocumented
- `npm run check` passes (docs-only changes, but verify no accidental breakage)

## Estimated Tokens

~25k

## Prerequisites

- Phases 1-8 completed
- `npm run check` passes before starting

---

## Task 1: Fix API.md drift and gaps

**Goal:** Correct the summary response schema, CORS methods, request format statement, text limit, code examples, log retention, and add missing endpoint/field documentation.

**Files to Modify:**
- `docs/API.md`

**Implementation Steps:**

1. **Read** `backend/src/models/responses.py` to confirm `SummaryResponse` fields: `sentiment_label`, `intensity` (str), `speech_to_text`, `added_text`, `summary`, `user_summary`, `user_short_summary`.

2. **Line 19** — Replace `All requests must be POST with Content-Type: application/json.` with:
   ```
   Requests use POST for submissions and GET for job status polling. All POST requests require `Content-Type: application/json`.
   ```

3. **Line 71** — Replace `Text input maximum 5000 characters` with `Text input maximum 10000 characters` (matches `backend/src/config/constants.py` line 43: `MAX_TEXT_INPUT_LENGTH = 10000`).

4. **Lines 76-98** — Replace the summary response JSON example and response fields table. New JSON:
   ```json
   {
     "statusCode": 200,
     "body": {
       "request_id": 12345,
       "user_id": "user@example.com",
       "inference_type": "summary",
       "sentiment_label": "Fearful",
       "intensity": "high",
       "speech_to_text": "I'm worried about my presentation tomorrow",
       "added_text": "NotAvailable",
       "summary": "User is experiencing anxiety about an upcoming presentation.",
       "user_summary": "You're feeling fearful about your presentation. This is a common stress response.",
       "user_short_summary": "Presentation anxiety"
     }
   }
   ```
   New response fields table:
   | Field | Type | Description |
   |---|---|---|
   | `request_id` | number | Unique request identifier for tracking |
   | `user_id` | string | Echo of user ID |
   | `inference_type` | string | Always `"summary"` |
   | `sentiment_label` | string | Detected emotion (Angry, Disgusted, Fearful, Happy, Neutral, Sad, Surprised) |
   | `intensity` | string | Emotion intensity level (e.g., "high", "medium", "low") |
   | `speech_to_text` | string | Transcription of audio input, or `"NotAvailable"` |
   | `added_text` | string | Additional text context, or `"NotAvailable"` |
   | `summary` | string | AI-generated summary of the emotional state |
   | `user_summary` | string | User-facing explanation of detected emotion |
   | `user_short_summary` | string | Brief label for the float |

5. **Lines 397-401** — Replace CORS block. Change:
   ```
   Access-Control-Allow-Methods: POST, OPTIONS
   ```
   to:
   ```
   Access-Control-Allow-Methods: OPTIONS, POST, GET
   ```
   (matches `backend/src/config/constants.py` line 79)

6. **Line 384** — In Example 3, replace `result.body.base64_audio` with `result.body.base64` (matches `backend/src/models/responses.py` line 40: field is `base64`).

7. **Line 427** — Replace `CloudWatch logs retained for 7 days` with `CloudWatch logs retained for 14 days` (matches `backend/template.yaml` line 171: `RetentionInDays: 14`).

8. **Add `duration_minutes` to meditation request fields table** (after existing fields). Add row:
   | `duration_minutes` | number | No | Meditation length: 3, 5, 10, 15, or 20 (default: 5) |
   (matches `backend/src/models/requests.py` line 47)

9. **Add download endpoint section** after the meditation polling section. New section:
   ```markdown
   ### 3. Download Meditation

   Download a completed meditation as an audio file.

   **Endpoint**: `POST /job/{job_id}/download`

   **Request Body**:

   ```json
   {
     "user_id": "user@example.com"
   }
   ```

   **Response (200 OK)**:

   Returns the audio file as a downloadable response.
   ```
   (matches `backend/src/handlers/lambda_handler.py` lines 577-579 and `backend/template.yaml` lines 154-159)

10. **Add HLS streaming note** to the meditation job-created response section. After the existing JSON response at lines 177-185, add:
    ```markdown
    When HLS streaming is enabled (default), the response also includes:

    ```json
    {
      "streaming": {
        "enabled": true,
        "playlist_url": null
      }
    }
    ```

    The `playlist_url` becomes available once streaming processing begins. Poll `/job/{job_id}` to get the updated URL.
    ```
    (matches `backend/src/handlers/lambda_handler.py` lines 149-155)

11. **Remove from Future Enhancements** the line `- [x] Duration preference parameter` since `duration_minutes` already exists.

**Verification Checklist:**
- [x] Summary response JSON matches `SummaryResponse` dataclass fields exactly
- [x] `intensity` documented as `string`, not `number`
- [x] No `timestamp` field in summary response
- [x] `sentiment_label` not `sentiment`
- [x] CORS methods include GET
- [x] Text limit says 10000
- [x] Example 3 uses `base64` not `base64_audio`
- [x] Log retention says 14 days
- [x] `duration_minutes` field documented with allowed values
- [x] Download endpoint documented
- [x] HLS streaming info documented
- [x] Request format section mentions GET requests

**Commit Message Template:**
```
docs(api): fix response schemas, limits, CORS, and add missing endpoints

Update API.md to match actual code:
- Fix summary response schema (sentiment_label, intensity as string, etc.)
- Fix text input limit (10000, not 5000)
- Fix CORS methods (add GET)
- Fix base64 field name in Example 3
- Fix log retention (14 days, not 7)
- Add duration_minutes request field
- Add download endpoint documentation
- Add HLS streaming response field
- Fix "all requests must be POST" statement
- Remove duration_minutes from future enhancements (already exists)
```

---

## Task 2: Fix CLAUDE.md drift

**Goal:** Correct Python version description, CI trigger statement, pytest markers list, and component structure description.

**Files to Modify:**
- `CLAUDE.md`

**Implementation Steps:**

1. **Read** `backend/pyproject.toml` lines 70-74 and `.github/workflows/ci.yml` lines 1-8 to confirm current state.

2. **Line 64** — Replace:
   ```
   - **Tests**: `tests/unit/`, `tests/integration/`, `tests/e2e/` with pytest markers: `unit`, `integration`, `e2e`, `slow`
   ```
   with:
   ```
   - **Tests**: `tests/unit/`, `tests/integration/`, `tests/e2e/` with pytest markers: `unit`, `integration`, `slow`
   ```
   (Remove `e2e` — it is not defined in `backend/pyproject.toml` lines 70-74)

3. **Line 75** — Replace:
   ```
   - **Backend**: ruff + black, 100 char line length, Python 3.12+ target
   ```
   with:
   ```
   - **Backend**: ruff + black, 100 char line length, Python 3.13 runtime / 3.12 lint target
   ```
   (Clarifies that runtime is 3.13 per `backend/template.yaml` line 62, linting targets 3.12 per `backend/pyproject.toml` line 98)

4. **Line 49** — Replace:
   ```
   - **Components**: `components/` — HLS player, meditation controls, auth screen, download button
   ```
   with:
   ```
   - **Components**: `components/` — organized in subdirectories: `HLSPlayer/`, `DownloadButton/`, `ScreenComponents/` (meditation controls, record button, incident items), `navigation/`
   ```
   (Matches actual directory structure)

5. **Line 26** — The comment for `npm run test:backend` says it runs `pytest tests/unit` but CI runs `pytest backend/tests` (all tests). Change the comment to match what the npm script actually does. Read `package.json` to confirm the actual npm script command first. If the npm script runs `tests/unit`, keep the CLAUDE.md comment as-is (it documents the npm script, not CI). Add a note that CI runs all tests:
   After line 26, before the deploy comment, add:
   ```
   # Note: CI runs all backend tests (pytest backend/tests), not just unit tests
   ```

**Verification Checklist:**
- [x] No `e2e` in pytest markers list
- [x] Python version line clarifies runtime vs lint target
- [x] Components line mentions subdirectories
- [x] CI test scope note added

**Commit Message Template:**
```
docs(claude): fix pytest markers, Python version, component structure

- Remove non-existent 'e2e' pytest marker from markers list
- Clarify Python 3.13 runtime vs 3.12 lint target
- Update components description to show subdirectory structure
- Add note that CI runs all backend tests, not just unit tests
```

---

## Task 3: Fix docs/README.md drift

**Goal:** Fix install command, samconfig.toml reference, project structure tree, and add missing SAM parameters.

**Files to Modify:**
- `docs/README.md`

**Implementation Steps:**

1. **Line 31** — Replace `npm install` with `npm install --legacy-peer-deps` (matches CI and CLAUDE.md).

2. **Lines 106-116** — The section says `Edit backend/samconfig.toml:` but `samconfig.toml` doesn't exist in the repo (it's gitignored). Replace with:
   ```markdown
   Create `backend/samconfig.toml` (this file is gitignored — each developer creates their own):

   ```toml
   version = 0.1
   [default.deploy.parameters]
   stack_name = "float-backend"
   region = "us-east-1"
   capabilities = "CAPABILITY_IAM"
   parameter_overrides = "Environment=production GeminiApiKey=your-key OpenAIApiKey=your-key FfmpegLayerArn=arn:aws:lambda:..."
   resolve_s3 = true
   ```
   ```

3. **Lines 120-129** — Add missing SAM parameters to the environment variables table. Add row for `FfmpegLayerArn`:
   | `FfmpegLayerArn` | ARN of the FFmpeg Lambda layer (auto-created by deploy script) |
   (matches `backend/template.yaml` line 48)

4. **Lines 133-155** — Update the project structure tree. Add missing backend subdirectories under `src/`:
   ```
   │   │   ├── config/   # Settings and constants
   │   │   ├── models/   # Pydantic request/response models
   │   │   ├── utils/    # Circuit breaker, caching, logging, audio utilities
   │   │   └── exceptions.py  # Custom exception hierarchy
   ```
   Update frontend `components/` to show subdirectories:
   ```
   │   ├── components/    # React components
   │   │   ├── HLSPlayer/       # HLS audio player
   │   │   ├── DownloadButton/  # Download meditation button
   │   │   ├── ScreenComponents/ # UI controls (record, meditation, incidents)
   │   │   └── navigation/      # Navigation components
   ```

5. **Line 148** — Change `samconfig.toml # SAM deployment config` to `samconfig.toml # SAM deployment config (gitignored, create from template)`.

**Verification Checklist:**
- [x] Install command includes `--legacy-peer-deps`
- [x] samconfig.toml section says "Create" not "Edit"
- [x] `FfmpegLayerArn` appears in SAM parameters table
- [x] Project tree includes `config/`, `models/`, `utils/`, `exceptions.py`
- [x] Project tree shows component subdirectories
- [x] samconfig.toml noted as gitignored in tree

**Commit Message Template:**
```
docs(readme): fix install command, samconfig reference, project tree

- Add --legacy-peer-deps to npm install command
- Change samconfig.toml from "Edit" to "Create" (file is gitignored)
- Add FfmpegLayerArn to SAM parameters table
- Add missing backend modules to project structure tree
- Show component subdirectories in frontend tree
```

---

## Task 4: Fix root README.md drift

**Goal:** Fix install command and add missing SAM parameters.

**Files to Modify:**
- `README.md`

**Implementation Steps:**

1. **Line 38** — Replace `npm install     # Install dependencies` with `npm install --legacy-peer-deps  # Install dependencies` (matches CI and CLAUDE.md).

2. **Lines 63-68** — Add missing SAM parameters to the deployment table. Add rows:
   | `S3DataBucket` | S3 bucket for user data (default: `float-cust-data`) |
   | `S3AudioBucket` | S3 bucket for background music |
   | `IncludeDevOrigins` | Set to `true` for local dev CORS wildcard |
   | `FfmpegLayerArn` | ARN of the FFmpeg Lambda layer |
   (matches `backend/template.yaml` lines 27-50)

3. **Line 162** — In Troubleshooting "Module not found" section, replace `npm install` with `npm install --legacy-peer-deps`.

**Verification Checklist:**
- [x] Quick Start install command includes `--legacy-peer-deps`
- [x] All SAM parameters from template.yaml are listed
- [x] Troubleshooting npm install includes `--legacy-peer-deps`

**Commit Message Template:**
```
docs(readme): fix install command, add missing SAM parameters

- Add --legacy-peer-deps to npm install commands
- Add S3DataBucket, S3AudioBucket, IncludeDevOrigins, FfmpegLayerArn
  to deployment parameters table
```

---

## Task 5: Fix ARCHITECTURE.md drift and gaps

**Goal:** Fix deployment command and add missing backend layer documentation.

**Files to Modify:**
- `docs/ARCHITECTURE.md`

**Implementation Steps:**

1. **Lines 97-99** — Replace the deployment section:
   ```markdown
   ## Deployment

   ```bash
   npm run deploy
   ```

   This runs a custom deploy script (`backend/scripts/deploy.mjs`) that builds and deploys via AWS SAM. See `backend/samconfig.toml` for configuration (gitignored — create your own with `sam deploy --guided`).
   ```
   (matches `package.json` line 16)

2. **After the "Layers" section (around line 63)**, add missing backend modules:
   ```markdown
   - **Config** (`src/config/`): Application settings (`settings.py` via Pydantic BaseSettings) and constants (`constants.py`)
   - **Models** (`src/models/`): Pydantic request/response validation models
   - **Utils** (`src/utils/`): Circuit breaker, caching, structured logging, audio utilities
   - **Exceptions** (`src/exceptions.py`): Custom exception hierarchy (FloatException, ValidationError, ExternalServiceError, TTSError)
   ```

3. **Add download endpoint** to the Endpoints list:
   ```
   - `POST /job/{job_id}/download` - Download completed meditation audio
   ```

**Verification Checklist:**
- [x] Deployment command is `npm run deploy`, not `sam build && sam deploy`
- [x] Config, Models, Utils, Exceptions modules documented
- [x] Download endpoint listed
- [x] samconfig.toml noted as gitignored

**Commit Message Template:**
```
docs(architecture): fix deploy command, add missing backend modules

- Replace sam build/deploy with npm run deploy (custom script)
- Add Config, Models, Utils, Exceptions to backend layers
- Add download endpoint to endpoints list
- Note samconfig.toml is gitignored
```

---

## Task 6: Fix integration test README

**Goal:** Fix all `__tests__/integration/` path references and non-existent component references.

**Files to Modify:**
- `tests/frontend/integration/README.md`

**Implementation Steps:**

1. **Lines 17-23** — Replace `__tests__/integration/` with `tests/frontend/integration/` in the directory tree header.

2. **Lines 147-157** — Replace all `__tests__/integration/` in run commands with `tests/frontend/integration/`:
   - `npm test -- __tests__/integration/ --watchAll=false` → `npm test -- tests/frontend/integration/ --watchAll=false`
   - `npm test -- __tests__/integration/auth-flow-test.tsx` → `npm test -- tests/frontend/integration/auth-flow-test.tsx`
   - `npm test -- __tests__/integration/ --verbose` → `npm test -- tests/frontend/integration/ --verbose`
   - `npm test -- __tests__/integration/ --coverage --watchAll=false` → `npm test -- tests/frontend/integration/ --coverage --watchAll=false`

3. **Lines 225-226** — Replace the example that references `IncidentCreator` and `IncidentList` (which don't exist). Replace with components that do exist. Change:
   ```typescript
   const { getByTestId } = renderWithIncidentContext(
     <>
       <IncidentCreator />
       <IncidentList />
     </>
   );

   // Create incident in one component
   fireEvent.press(getByTestId('create-incident'));

   // Verify it appears in another component
   await waitForIntegration(() => {
     expect(getByTestId('incident-list')).toContainElement(
       getByTestId('incident-item-0')
     );
   });
   ```
   to:
   ```typescript
   const { getByTestId } = renderWithIncidentContext(
     <>
       <AudioRecording />
       <history />
     </>
   );

   // Record audio in one component
   fireEvent.press(getByTestId('record-button'));

   // Verify incident appears in history component
   await waitForIntegration(() => {
     expect(getByTestId('incident-list')).toContainElement(
       getByTestId('incident-item-0')
     );
   });
   ```
   (Uses actual components: `AudioRecording` from `components/AudioRecording.tsx` and `history` from `components/history.tsx`)

**Verification Checklist:**
- [x] No occurrences of `__tests__/integration/` remain
- [x] All paths use `tests/frontend/integration/`
- [x] No references to `IncidentCreator` or `IncidentList` remain
- [x] Replacement components (`AudioRecording`, `history`) exist in `frontend/components/`

**Commit Message Template:**
```
docs(tests): fix integration README paths and component references

- Replace all __tests__/integration/ with tests/frontend/integration/
- Replace non-existent IncidentCreator/IncidentList with actual components
```

---

## Task 7: Fix E2E test README stale references

**Goal:** Mark planned-but-nonexistent files clearly as planned, fix .detoxrc.js path, and fix stale cross-reference.

**Files to Modify:**
- `tests/frontend/e2e/README.md`

**Implementation Steps:**

1. **Lines 99-107** — The test structure tree already marks items as `(planned)`. This is acceptable. No change needed for S1 — the README already says these are planned.

2. **Line 314** — Change `Detox configuration created (.detoxrc.js)` to `Detox configuration created (frontend/.detoxrc.js)` to clarify the actual file location.

3. **Line 325** — Replace `Integration tests in __tests__/integration/` with `Integration tests in tests/frontend/integration/`.

**Verification Checklist:**
- [x] `.detoxrc.js` reference includes `frontend/` prefix
- [x] Cross-reference to integration tests uses correct path

**Commit Message Template:**
```
docs(tests): fix e2e README .detoxrc.js path and integration test reference

- Clarify .detoxrc.js lives at frontend/.detoxrc.js
- Fix integration test path from __tests__/integration/ to tests/frontend/integration/
```

---

## Task 8: Add backend env vars to documentation

**Goal:** Document `ENABLE_HLS_STREAMING`, `LOG_LEVEL`, and `ENVIRONMENT` backend environment variables.

**Files to Modify:**
- `backend/.env.example`
- `docs/README.md`

**Implementation Steps:**

1. **Append to `backend/.env.example`** the following lines:
   ```

   # Enable HLS streaming for meditation audio (default: true)
   # ENABLE_HLS_STREAMING=true

   # Log level (default: INFO)
   # LOG_LEVEL=INFO

   # Deployment environment (set via SAM parameter, default: production)
   # ENVIRONMENT=production
   ```
   (matches `backend/src/handlers/lambda_handler.py` line 46, `backend/src/utils/logging_utils.py` line 99, `backend/template.yaml` line 111)

2. **In `docs/README.md`** environment variables table (lines 120-129), add these env var entries with a note that they are set automatically in Lambda via SAM but useful for local development.

**Verification Checklist:**
- [x] `ENABLE_HLS_STREAMING` documented in `.env.example`
- [x] `LOG_LEVEL` documented in `.env.example`
- [x] `ENVIRONMENT` documented in `.env.example`
- [x] All three mentioned in docs/README.md

**Commit Message Template:**
```
docs(backend): document ENABLE_HLS_STREAMING, LOG_LEVEL, ENVIRONMENT env vars

Add missing environment variables to backend/.env.example and docs/README.md.
These are set automatically in Lambda via SAM template but useful for local dev.
```

---

## Phase Verification

After completing all tasks:

1. Run `npm run check` — must pass
2. Verify no remaining `__tests__/integration/` references:
   ```bash
   grep -r "__tests__/integration/" docs/ tests/ --include="*.md"
   ```
3. Verify API.md summary response fields match code:
   ```bash
   grep -A 8 "class SummaryResponse" backend/src/models/responses.py
   ```
4. Verify CORS methods in API.md match code:
   ```bash
   grep "Allow-Methods" backend/src/config/constants.py
   ```
5. Verify no `base64_audio` references remain in docs:
   ```bash
   grep -r "base64_audio" docs/
   ```
6. Verify all SAM parameters from template.yaml appear in at least one doc:
   ```bash
   grep "Type: String" backend/template.yaml | head -20
   grep -l "FfmpegLayerArn" docs/ README.md
   ```
