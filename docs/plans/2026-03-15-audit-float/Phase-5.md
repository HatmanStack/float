# Phase 5: [STRUCTURAL] Defensiveness & Type Rigor

## Phase Goal

Harden error handling and type safety. Address the Defensiveness (7 -> 9) and Type Rigor (7 -> 9) pillar findings: S3 silent failures, the dual Pydantic/legacy request model layer, the `SummaryResponse`-to-`Incident` type cast, and the `Settings` class pattern.

**Success criteria:**
- `_save_job` raises on S3 failure instead of silently proceeding
- Legacy request wrapper classes removed; `parse_request_body` uses Pydantic directly
- `SummaryResponse`-to-`Incident` type cast replaced with a proper mapping function
- `Settings` class uses proper typing or Pydantic `BaseSettings`
- `npm run check` passes
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~30k

## Prerequisites

- Phases 0-4 completed and verified
- All checks passing

---

## Tasks

### Task 1: Make `_save_job` raise on S3 failure

**Goal:** Currently `S3StorageService.upload_json()` returns `False` on error, and `_save_job()` in `job_service.py` ignores the return value. This means a failed job update leaves the frontend polling forever. The eval flags this under Defensiveness (Stress: 7/10).

**Files to Modify:**
- `backend/src/services/job_service.py` — Check `upload_json` return value in `_save_job`

**Prerequisites:** None

**Implementation Steps:**

1. Open `backend/src/services/job_service.py`
2. Locate `_save_job` (line ~365):
   ```python
   def _save_job(self, user_id: str, job_id: str, job_data: Dict[str, Any]):
       """Save job data to S3."""
       key = f"jobs/{user_id}/{job_id}.json"
       self.storage_service.upload_json(self.bucket, key, job_data)
   ```
3. Replace with:
   ```python
   def _save_job(self, user_id: str, job_id: str, job_data: Dict[str, Any]):
       """Save job data to S3.

       Raises:
           ExternalServiceError: If the S3 upload fails.
       """
       key = f"jobs/{user_id}/{job_id}.json"
       success = self.storage_service.upload_json(self.bucket, key, job_data)
       if not success:
           from ..exceptions import ErrorCode, ExternalServiceError
           raise ExternalServiceError(
               f"Failed to save job {job_id} to S3",
               ErrorCode.STORAGE_FAILURE,
               details=f"key={key}",
           )
   ```
4. Verify all callers of `_save_job` are inside try/except blocks that can handle this. Search for `self._save_job(` in `job_service.py`:
   - `create_job` (line ~103) — called by `handle_meditation_request` which has error handling
   - `update_job_status` (line ~123) — called during processing, has error handling
   - `update_streaming_progress` (line ~157) — called during streaming, has error handling
   - Any other callers — verify they handle exceptions

5. Verify the `STORAGE_FAILURE` error code exists in `exceptions.py` — it does (line 27)

**Verification Checklist:**
- [ ] `_save_job` checks return value of `upload_json`
- [ ] Raises `ExternalServiceError` with `STORAGE_FAILURE` on failure
- [ ] All callers handle exceptions appropriately
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Search tests for `_save_job` — if tests mock `upload_json` to return `True`, add a test case where it returns `False` and verify the error is raised

**Commit Message Template:**
```
fix(backend): raise on S3 failure in _save_job

Check the return value of upload_json in _save_job and raise
ExternalServiceError with STORAGE_FAILURE code on failure. Previously,
a failed S3 write was silently ignored, leaving the frontend polling
a stale job status indefinitely.
```

---

### Task 2: Remove legacy request wrapper layer, route through Pydantic

**Goal:** The `requests.py` file has two layers: Pydantic models (`SummaryRequestModel`, `MeditationRequestModel`, `RequestBody` discriminated union) and legacy classes (`BaseRequest`, `SummaryRequest`, `MeditationRequest`, `parse_request_body`). The legacy layer duplicates all validation and is actually used by the handler. Remove it and use the Pydantic models directly. The eval flags this under Type Rigor (Stress: 7/10) and Pragmatism (Stress: 8/10).

**Files to Modify:**
- `backend/src/models/requests.py` — Remove legacy classes, update `parse_request_body` to return Pydantic models
- `backend/src/handlers/lambda_handler.py` — Update type annotations and attribute access if needed

**Prerequisites:** None

**Implementation Steps:**

1. Open `backend/src/handlers/lambda_handler.py`
2. Search for all uses of `SummaryRequest` and `MeditationRequest`:
   ```bash
   grep -n "SummaryRequest\|MeditationRequest\|BaseRequest\|parse_request_body" backend/src/handlers/lambda_handler.py
   ```
   Note every line number and how the request object is used (attribute access patterns).

3. Also check other files:
   ```bash
   grep -rn "SummaryRequest\|MeditationRequest\|BaseRequest\|parse_request_body" backend/src/ --include="*.py" | grep -v requests.py
   ```

4. Compare attribute access patterns between legacy and Pydantic models:
   - Both have: `user_id`, `inference_type`, `audio`, `prompt`, `input_data`, `music_list`, `duration_minutes`
   - Legacy `MeditationRequest.to_dict()` uses `inference_type.value` (Enum); Pydantic `MeditationRequestModel.to_dict()` uses `self.inference_type` (string literal `"meditation"`)
   - Legacy `SummaryRequest` has no `to_inference_type()`; Pydantic `SummaryRequestModel` does
   - Legacy classes use `inference_type: InferenceType` (enum); Pydantic uses `Literal["summary"]` / `Literal["meditation"]`

5. Open `backend/src/models/requests.py`
6. Refactor `parse_request_body` to use Pydantic's discriminated union directly:
   ```python
   from pydantic import ValidationError as PydanticValidationError

   def parse_request_body(body: Dict[str, Any]) -> Union[SummaryRequestModel, MeditationRequestModel]:
       """Parse and validate request body using Pydantic discriminated union.

       Args:
           body: Raw request body dictionary.

       Returns:
           SummaryRequestModel or MeditationRequestModel based on inference_type.

       Raises:
           ValidationError: If required fields are missing or invalid.
       """
       from ..exceptions import ErrorCode, ValidationError

       try:
           # Pydantic discriminated union handles type routing automatically
           from pydantic import TypeAdapter
           adapter = TypeAdapter(RequestBody)
           return adapter.validate_python(body)
       except PydanticValidationError as e:
           # Convert Pydantic validation errors to domain errors
           first_error = e.errors()[0] if e.errors() else {"msg": "Validation failed"}
           raise ValidationError(
               first_error.get("msg", "Invalid request data"),
               ErrorCode.INVALID_REQUEST,
               details=str(e),
           ) from e
   ```

7. Delete the entire legacy section (everything from `class BaseRequest:` to end of `parse_request_body`): classes `BaseRequest`, `SummaryRequest`, `MeditationRequest`, functions `_parse_json_field`, `_validate_request_fields`, and the old `parse_request_body`.

8. Update the imports in `lambda_handler.py`:
   ```python
   # Before:
   from ..models.requests import MeditationRequest, SummaryRequest, parse_request_body
   # After:
   from ..models.requests import MeditationRequestModel, SummaryRequestModel, parse_request_body
   ```

9. Update type annotations in `lambda_handler.py`:
   - `handle_summary_request(self, request: SummaryRequest)` -> `handle_summary_request(self, request: SummaryRequestModel)`
   - Any `MeditationRequest` type hints -> `MeditationRequestModel`
   - Any `isinstance` checks against the old classes -> update to new classes

10. Check if `request.to_dict()` is called anywhere. The Pydantic `MeditationRequestModel` has `to_dict()` but it uses `self.inference_type` (string) rather than `self.inference_type.value` (the legacy version converts InferenceType enum). Verify that downstream consumers expect a string or enum value. If they expect a string like `"meditation"`, the Pydantic version is correct.

11. Check if `request.validate()` is called anywhere. Pydantic models validate on construction, so explicit `.validate()` calls can be removed.

12. Update any test files that import the old classes:
    ```bash
    grep -rn "SummaryRequest\|MeditationRequest\|BaseRequest" backend/tests/ --include="*.py"
    ```

**Verification Checklist:**
- [ ] `BaseRequest`, `SummaryRequest`, `MeditationRequest` classes deleted from `requests.py`
- [ ] `_parse_json_field` and `_validate_request_fields` helper functions deleted
- [ ] `parse_request_body` uses Pydantic `TypeAdapter` with `RequestBody` discriminated union
- [ ] `lambda_handler.py` imports and uses `SummaryRequestModel` / `MeditationRequestModel`
- [ ] No `request.validate()` calls remain (Pydantic validates on construction)
- [ ] All test files updated to use new model names
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Run `cd backend && uvx ruff check .`
- Manually verify `parse_request_body` handles the same edge cases (missing fields, invalid inference_type)

**Commit Message Template:**
```
refactor(backend): remove legacy request wrapper layer, use Pydantic directly

Delete BaseRequest, SummaryRequest, MeditationRequest legacy classes
and their helper functions. Rewrite parse_request_body to use Pydantic
TypeAdapter with the existing RequestBody discriminated union. All
validation now happens through Pydantic models, eliminating the
duplicated validation layer.
```

---

### Task 3: Fix `SummaryResponse`-to-`Incident` type cast

**Goal:** In `frontend/app/(tabs)/index.tsx:109`, `response as Incident` is an unsafe type cast. `SummaryResponse` and `Incident` have different shapes (e.g., `SummaryResponse.notification_id` vs `Incident.notificationId`, `SummaryResponse.color_key` has no `Incident` equivalent). Add a proper mapping function.

**Files to Modify:**
- `frontend/components/BackendSummaryCall.tsx` — Add a `toIncident` mapping function
- `frontend/app/(tabs)/index.tsx` — Use the mapping function

**Prerequisites:** None

**Implementation Steps:**

1. Open `frontend/components/BackendSummaryCall.tsx`
2. Add the `Incident` import:
   ```typescript
   import { Incident } from '@/context/IncidentContext';
   ```
3. Add a mapping function after the `SummaryResponse` interface:
   ```typescript
   /**
    * Convert a SummaryResponse from the API into an Incident for local state.
    */
   export function toIncident(response: SummaryResponse): Incident {
     return {
       timestamp: response.timestamp,
       sentiment_label: response.sentiment_label,
       intensity: response.intensity,
       summary: response.summary,
       speech_to_text: response.speech_to_text,
       added_text: response.added_text,
       notificationId: response.notification_id,
     };
   }
   ```

4. Open `frontend/app/(tabs)/index.tsx`
5. Update the import:
   ```typescript
   // Before:
   import { BackendSummaryCall, SummaryResponse } from '@/components/BackendSummaryCall';
   // After:
   import { BackendSummaryCall, SummaryResponse, toIncident } from '@/components/BackendSummaryCall';
   ```
6. Replace line 109:
   ```typescript
   // Before:
   setIncidentList((prevList) => [response as Incident, ...prevList]);
   // After:
   setIncidentList((prevList) => [toIncident(response), ...prevList]);
   ```

**Verification Checklist:**
- [ ] `toIncident` function exists in `BackendSummaryCall.tsx`
- [ ] Maps all `SummaryResponse` fields to corresponding `Incident` fields
- [ ] `as Incident` cast removed from `index.tsx`
- [ ] `npm run lint` passes
- [ ] `npm test` passes

**Testing Instructions:**
- Run `npm run lint`
- Run `npm test`
- Search for any other `as Incident` casts: `grep -rn "as Incident" frontend/ --include="*.tsx"`

**Commit Message Template:**
```
fix(frontend): replace unsafe SummaryResponse-to-Incident cast with mapping

Add toIncident() function that properly maps SummaryResponse fields
to Incident fields (e.g., notification_id -> notificationId). Removes
the unsafe `as Incident` type cast that silently allowed mismatched
field names.
```

---

### Task 4: Convert `Settings` to Pydantic `BaseSettings`

**Goal:** The `Settings` class uses class-level attributes that are evaluated at import time via `os.getenv()`. This means settings are frozen at module load. The eval flags this under Type Rigor (Stress: 7/10). Convert to Pydantic `BaseSettings` for proper typing, validation, and `.env` file support.

**Files to Modify:**
- `backend/src/config/settings.py` — Convert to Pydantic BaseSettings

**Prerequisites:** None

**Implementation Steps:**

1. Check if `pydantic-settings` is in requirements:
   ```bash
   grep -n "pydantic" backend/requirements.txt
   ```
   If `pydantic-settings` is not listed, add it. If only `pydantic` is listed, add `pydantic-settings` on the next line.

2. Open `backend/src/config/settings.py`
3. Replace the entire file with:
   ```python
   from pydantic_settings import BaseSettings


   class Settings(BaseSettings):
       """Application settings loaded from environment variables.

       Pydantic BaseSettings automatically reads from environment variables
       and .env files, with proper type coercion and validation.
       """

       AWS_S3_BUCKET: str = "float-cust-data"
       AWS_AUDIO_BUCKET: str = "audio-er-lambda"
       GEMINI_API_KEY: str = ""
       OPENAI_API_KEY: str = ""
       FFMPEG_PATH: str = "/opt/bin/ffmpeg"
       TEMP_DIR: str = "/tmp"
       AUDIO_SAMPLE_RATE: int = 44100
       GEMINI_SAFETY_LEVEL: int = 4

       model_config = {
           "env_file": ".env",
           "env_file_encoding": "utf-8",
           "extra": "ignore",
           "case_sensitive": True,
           # Map G_KEY env var to GEMINI_API_KEY field
           "env_prefix": "",
       }

       @classmethod
       def validate(cls, require_keys: bool = True) -> bool:
           """Validate that required API keys are present.

           Kept for backward compatibility with existing callers.
           """
           if not require_keys:
               return True
           instance = settings
           required_vars = [
               ("GEMINI_API_KEY", instance.GEMINI_API_KEY),
               ("OPENAI_API_KEY", instance.OPENAI_API_KEY),
           ]
           missing = [name for name, value in required_vars if not value]
           if missing:
               raise ValueError(
                   f"Missing required environment variables: {', '.join(missing)}"
               )
           return True


   settings = Settings()
   ```

4. **Important:** The current code maps `G_KEY` env var to `GEMINI_API_KEY`. Pydantic BaseSettings looks for env vars matching the field name by default. To support the `G_KEY` alias, use a `Field` with `validation_alias`:
   ```python
   from pydantic import Field

   class Settings(BaseSettings):
       GEMINI_API_KEY: str = Field(default="", validation_alias="G_KEY")
   ```
   However, `validation_alias` only applies to input data, not env vars. For env var aliases in pydantic-settings v2, use `alias`:
   ```python
   from pydantic import AliasChoices, Field

   class Settings(BaseSettings):
       GEMINI_API_KEY: str = Field(
           default="",
           validation_alias=AliasChoices("GEMINI_API_KEY", "G_KEY"),
       )
   ```
   Test this locally to ensure `G_KEY` env var is properly read.

5. Remove the `import os` and `from dotenv import load_dotenv` and `load_dotenv()` call — Pydantic BaseSettings handles `.env` files natively.

6. Check if `dotenv` is still used elsewhere in the backend:
   ```bash
   grep -rn "dotenv\|load_dotenv" backend/src/ --include="*.py" | grep -v settings.py
   ```
   If not used, it can stay in requirements (removing it is a separate concern).

7. Update `requirements.txt` to add `pydantic-settings` if missing.

**Verification Checklist:**
- [ ] `Settings` extends `pydantic_settings.BaseSettings`
- [ ] `os.getenv()` calls removed
- [ ] `load_dotenv()` call removed
- [ ] `G_KEY` env var alias configured
- [ ] `validate()` classmethod preserved for backward compatibility
- [ ] `pydantic-settings` added to `requirements.txt` if missing
- [ ] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [ ] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Verify settings load: `cd backend && python -c "from src.config.settings import settings; print(settings.TEMP_DIR)"`
- Verify validate works: `cd backend && python -c "from src.config.settings import Settings; Settings.validate(require_keys=False)"`

**Commit Message Template:**
```
refactor(backend): convert Settings to Pydantic BaseSettings

Replace class-level os.getenv() attributes with Pydantic BaseSettings
for proper type validation, .env file support, and environment variable
binding. Adds G_KEY alias for GEMINI_API_KEY backward compatibility.
Removes manual dotenv loading (handled by BaseSettings natively).
```

---

## Phase Verification

After completing all 4 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```

2. Run backend checks:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   cd backend && uvx ruff check .
   ```

3. Verify legacy request classes are gone:
   ```bash
   grep -n "class BaseRequest\|class SummaryRequest\|class MeditationRequest" backend/src/models/requests.py
   # Should return nothing
   ```

4. Verify no `as Incident` casts:
   ```bash
   grep -rn "as Incident" frontend/ --include="*.tsx"
   # Should return nothing
   ```

5. Verify Settings is Pydantic-based:
   ```bash
   grep "BaseSettings" backend/src/config/settings.py
   # Should return the class definition
   ```

All checks must pass before proceeding to Phase 6.
