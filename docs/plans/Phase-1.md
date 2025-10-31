# Phase 1: Backend Infrastructure

**Status**: Pytest setup, test structure, critical path test writing
**Duration**: 3-4 days
**Effort**: ~18,000 tokens

**Prerequisites**: Phase 0 complete

---

## Overview

Phase 1 establishes the testing foundation for the backend. We implement pytest configuration, write tests for critical paths (Lambda handler entry point and main inference services), and create mock infrastructure for external APIs.

**Key Objectives**:

1. Write unit tests for Lambda handler (happy path + error cases)
2. Write tests for critical services (AI, TTS, storage)
3. Set up mock infrastructure for external APIs
4. Achieve 60%+ coverage on critical paths
5. Integrate tests into development workflow

**Phase Dependencies**:
- Phase 0 must be complete
- Backend Python environment set up (venv, dependencies)
- pyproject.toml and pytest configuration in place

---

## Task 1: Write Lambda Handler Tests

**Goal**: Test the main Lambda entry point with happy paths and error cases

**Files to create/modify**:
- Create: `backend/tests/unit/test_lambda_handler.py`
- Modify: `backend/tests/mocks/external_apis.py` (add Google Gemini mocks)
- Modify: `backend/tests/conftest.py` (add fixtures for requests/responses)

**Prerequisites**:
- Phase 0 complete
- Python environment activated
- pytest discovered and configured

**Step-by-step Instructions**:

1. Review existing Lambda handler code
   - Open `backend/src/handlers/lambda_handler.py`
   - Understand the entry point and how requests are processed
   - Identify the main inference types: `summary` and `meditation`
   - Note how errors are handled and responses are formatted

2. Create mock for external APIs in `test_mocks/external_apis.py`
   - Create mock Google Gemini API responses for sentiment analysis
   - Create mock TTS provider responses (ElevenLabs, OpenAI)
   - Create mock S3 storage responses
   - Use pytest.fixture decorators for reusable mocks
   - Make mocks return realistic data structures

3. Create request/response fixtures in `conftest.py`
   - Add fixture for valid summary inference request
   - Add fixture for valid meditation inference request
   - Add fixture for invalid requests (missing fields, wrong types)
   - Use Pydantic models from `backend/src/models/` for validation

4. Write test_lambda_handler.py with test cases

   **Test Case 1: Summary Inference - Happy Path**
   - Create valid summary request (text, user_id)
   - Mock AI service to return sentiment analysis
   - Mock TTS service to return audio bytes
   - Assert response contains audio_url and metadata
   - Assert HTTP status is 200

   **Test Case 2: Summary Inference - API Error**
   - Create valid request
   - Mock AI service to raise exception
   - Assert Lambda returns 500 error response
   - Assert error message is descriptive

   **Test Case 3: Meditation Inference - Happy Path**
   - Create valid meditation request
   - Mock AI service to generate meditation text
   - Mock TTS with background music
   - Assert response contains audio_url, duration, metadata

   **Test Case 4: Meditation Inference - Invalid Input**
   - Create request with missing required fields
   - Assert Lambda returns 400 validation error
   - Assert error message lists missing fields

   **Test Case 5: Request Validation**
   - Test middleware validates request structure
   - Test invalid JSON is rejected
   - Test missing Authorization header is handled

   **Test Case 6: CORS Headers**
   - Verify CORS headers in response
   - Verify correct origin handling

5. Run tests and check coverage
   - Run `pytest tests/unit/test_lambda_handler.py -v`
   - Run with coverage: `pytest tests/unit/test_lambda_handler.py --cov=src.handlers`
   - Verify 80%+ coverage of lambda_handler.py

**Verification Checklist**:

- [ ] `test_lambda_handler.py` exists and is syntactically correct
- [ ] All 6 test cases pass
- [ ] `pytest --collect-only` shows 6 tests in this file
- [ ] Coverage report shows 80%+ for lambda_handler.py
- [ ] Mock responses use realistic data structures
- [ ] Tests use pytest fixtures for setup
- [ ] Tests marked with `@pytest.mark.unit`

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Run just these tests
pytest tests/unit/test_lambda_handler.py -v

# Run with coverage
pytest tests/unit/test_lambda_handler.py --cov=src.handlers --cov-report=term-missing

# Check test count
pytest tests/unit/test_lambda_handler.py --collect-only -q
```

**Commit Message Template**:

```
test: add Lambda handler unit tests

- Add test_lambda_handler.py with 6 test cases covering:
  * Summary inference happy path and error handling
  * Meditation inference happy path and validation
  * Request validation and error responses
  * CORS header verification
- Add mock responses for Google Gemini, TTS, S3
- Add request/response fixtures in conftest.py
- Achieve 80%+ coverage of lambda_handler.py

Tests use pytest fixtures and mock external APIs.
```

**Token Estimate**: ~3,500 tokens

---

## Task 2: Write Service Layer Tests

**Goal**: Test core business logic (AI, TTS, audio, storage services)

**Files to create/modify**:
- Create: `backend/tests/unit/test_services.py`
- Modify: `backend/tests/mocks/external_apis.py` (add service-level mocks)
- Modify: `backend/tests/conftest.py` (add service fixtures)

**Prerequisites**:
- Task 1 complete (mock infrastructure in place)
- Phase 0 complete

**Step-by-step Instructions**:

1. Review service implementations
   - Open `backend/src/services/ai_service.py` (Google Gemini)
   - Open `backend/src/services/tts_service.py` (Text-to-speech)
   - Open `backend/src/services/audio_service.py` (Audio processing)
   - Open `backend/src/services/storage_service.py` (S3 storage)
   - Understand service interfaces and dependencies

2. Create service test fixtures in conftest.py
   - Add fixture for AI service (with mocked Gemini API)
   - Add fixture for TTS service (with mocked providers)
   - Add fixture for audio service (with mocked FFmpeg calls)
   - Add fixture for storage service (with mocked S3)

3. Create mock responses for services in `external_apis.py`
   - Create Google Generative AI mock with generate_content method
   - Create ElevenLabs TTS mock with rate limits and errors
   - Create OpenAI TTS mock
   - Create S3 mock with bucket operations
   - Each mock should return realistic response structures

4. Write test_services.py with test cases

   **AI Service Tests**:
   - Test sentiment analysis on positive text
   - Test sentiment analysis on negative text
   - Test sentiment analysis on neutral text
   - Test meditation text generation
   - Test error handling when API fails
   - Test timeout handling

   **TTS Service Tests**:
   - Test provider selection (ElevenLabs primary, fallback to OpenAI)
   - Test audio generation from text
   - Test provider fallback on error
   - Test voice ID configuration
   - Test parameter handling (stability, similarity_boost)

   **Audio Service Tests**:
   - Test audio format conversion (if applicable)
   - Test background music mixing (if implemented)
   - Test audio file operations
   - Test error handling for invalid input

   **Storage Service Tests**:
   - Test file upload to S3
   - Test file download from S3
   - Test error handling (bucket missing, permission denied)
   - Test URL generation for uploaded files

5. Run tests and verify coverage
   - Run all service tests
   - Aim for 70%+ coverage of services
   - Ensure critical paths (happy paths + common errors) are covered

**Verification Checklist**:

- [ ] `test_services.py` exists with all test cases
- [ ] All tests pass with mocked external APIs
- [ ] Coverage for ai_service.py is 70%+
- [ ] Coverage for tts_service.py is 70%+
- [ ] Coverage for audio_service.py is 60%+ (less critical)
- [ ] Coverage for storage_service.py is 70%+
- [ ] Tests use pytest fixtures (not hardcoded mocks)
- [ ] Tests marked with `@pytest.mark.unit`
- [ ] Mock responses are realistic and comprehensive

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Run service tests
pytest tests/unit/test_services.py -v

# Run with coverage by service
pytest tests/unit/test_services.py --cov=src.services --cov-report=term-missing

# Check specific service coverage
pytest tests/unit/test_services.py --cov=src.services.ai_service -v
```

**Commit Message Template**:

```
test: add service layer unit tests

- Add test_services.py with 15+ test cases covering:
  * AI service sentiment analysis and generation
  * TTS service provider selection and fallback
  * Audio service format conversion and mixing
  * Storage service S3 operations
- Add comprehensive mock responses for external APIs
- Add service fixtures in conftest.py
- Achieve 70%+ coverage for all core services

Tests use pytest fixtures and external API mocks.
```

**Token Estimate**: ~4,000 tokens

---

## Task 3: Write Model Validation Tests

**Goal**: Test Pydantic models for request/response validation

**Files to create/modify**:
- Create: `backend/tests/unit/test_models.py`
- Modify: `backend/tests/conftest.py` (add model fixtures)

**Prerequisites**:
- Task 1 & 2 complete
- Familiar with Pydantic validation

**Step-by-step Instructions**:

1. Review model definitions
   - Open `backend/src/models/requests.py`
   - Open `backend/src/models/responses.py`
   - Open `backend/src/models/domain.py`
   - Understand required fields, types, and validation rules

2. Create model test fixtures
   - Add fixture for valid SummaryRequest
   - Add fixture for valid MeditationRequest
   - Add fixture for valid responses
   - Add fixtures for edge cases (empty strings, max length, special chars)

3. Write test_models.py with validation tests

   **Request Validation Tests**:
   - Test SummaryRequest with valid data
   - Test SummaryRequest with missing required field (should raise ValidationError)
   - Test SummaryRequest with wrong type (should raise ValidationError)
   - Test MeditationRequest with valid data
   - Test MeditationRequest with invalid duration (if constrained)
   - Test request with extra fields (should be allowed or rejected per model config)

   **Response Validation Tests**:
   - Test SummaryResponse with valid data
   - Test MeditationResponse serialization to JSON
   - Test response with missing required field (should raise ValidationError)
   - Test response field types are correct

   **Domain Model Tests**:
   - Test domain objects serialize/deserialize correctly
   - Test computed properties if any
   - Test enum values are handled correctly

4. Run tests and verify coverage
   - Run all model tests
   - Aim for 80%+ coverage of model code
   - Ensure validation errors are raised correctly

**Verification Checklist**:

- [ ] `test_models.py` exists with 10+ test cases
- [ ] All validation tests pass
- [ ] Coverage for models/ is 80%+
- [ ] Both happy path and error cases tested
- [ ] Tests marked with `@pytest.mark.unit`

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Run model tests
pytest tests/unit/test_models.py -v

# Run with coverage
pytest tests/unit/test_models.py --cov=src.models --cov-report=term-missing
```

**Commit Message Template**:

```
test: add Pydantic model validation tests

- Add test_models.py with 10+ test cases
- Test request/response model validation
- Test edge cases (missing fields, wrong types, constraints)
- Test domain model serialization
- Achieve 80%+ coverage for models/

Tests verify Pydantic validation works correctly.
```

**Token Estimate**: ~2,000 tokens

---

## Task 4: Set Up Coverage Reporting

**Goal**: Configure coverage reporting and create baseline metrics

**Files to create/modify**:
- Modify: `pyproject.toml` (coverage configuration already there, verify)
- Create: `backend/.coveragerc` (optional, for advanced config)
- Create: `backend/coverage_baseline.txt` (document baseline for comparison)

**Prerequisites**:
- Tasks 1-3 complete
- pytest and coverage tools installed

**Step-by-step Instructions**:

1. Verify coverage configuration in pyproject.toml
   - Ensure pytest section includes: `addopts = "--cov=src --cov-report=term-missing --cov-report=html"`
   - If missing, add coverage configuration to pyproject.toml

2. Run full test suite with coverage
   - Run `pytest tests/ --cov=src --cov-report=html`
   - This generates HTML coverage report in `htmlcov/index.html`
   - Also displays summary in terminal

3. Create baseline metrics document
   - Document current coverage percentage
   - List files with lowest coverage (these are targets for Phase 2)
   - Note any files that are intentionally low coverage (utilities, etc.)
   - Save as `backend/coverage_baseline.txt`

4. Set coverage targets
   - Aim for 60% overall coverage (critical paths only, per ADR)
   - Core services should be 70%+
   - Models and handlers should be 80%+
   - Utilities can be lower (intentional)

5. Create script to check coverage locally
   - Add to backend Makefile or as shell script
   - Allow developers to run coverage checks before committing
   - Make it easy to view HTML report

**Verification Checklist**:

- [ ] pyproject.toml has coverage configuration
- [ ] `pytest tests/ --cov=src` runs without errors
- [ ] Coverage report generated as HTML
- [ ] `coverage_baseline.txt` documents initial coverage %
- [ ] Coverage targets documented (60% overall, 70%+ services)
- [ ] Script or Makefile created for easy coverage checking

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# View HTML report (opens in browser)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Check coverage for specific module
pytest tests/ --cov=src.services --cov-report=term-missing
```

**Commit Message Template**:

```
ci: configure coverage reporting and baseline

- Verify pytest coverage configuration in pyproject.toml
- Document coverage baseline metrics
- Create script for local coverage checking
- Set coverage targets: 60% overall, 70%+ for services

Establishes coverage reporting for tracking improvement.
```

**Token Estimate**: ~1,500 tokens

---

## Task 5: Refactor Existing Backend Code for Tests

**Goal**: Improve existing backend code to be more testable and follow new standards

**Files to create/modify**:
- Modify: `backend/src/handlers/lambda_handler.py` (dependency injection, type hints)
- Modify: `backend/src/services/*.py` (add type hints to function signatures)
- Modify: `backend/src/models/*.py` (ensure Pydantic models are complete)

**Prerequisites**:
- Tasks 1-4 complete (tests are written and passing)
- Phase 0 complete (tools installed)

**Step-by-step Instructions**:

1. Add type hints to lambda_handler.py
   - Review function signatures in lambda_handler
   - Add input and return type hints to all public functions
   - Use proper types: `Dict[str, Any]`, `Optional[str]`, `List[str]`, etc.
   - Use Pydantic models as types where applicable
   - Example: `def process_request(event: Dict[str, Any]) -> Dict[str, Any]:`

2. Add type hints to service functions
   - Review each service in `backend/src/services/`
   - Add type hints to public method signatures
   - Don't require 100% - focus on entry points
   - Example: `def generate_audio(self, request: AudioRequest) -> bytes:`

3. Add type hints to model fields (if not already present)
   - Review `backend/src/models/`
   - Ensure Pydantic models have all fields typed
   - Add docstrings if helpful
   - Example: `class AudioRequest(BaseModel): text: str`

4. Improve dependency injection in lambda_handler
   - If services are hardcoded, refactor to allow injection
   - Make it easier to pass mocked services in tests
   - Don't require major refactoring - just make tests easier

5. Add missing error handling
   - Review service implementations
   - Ensure exceptions are caught and logged
   - Return appropriate error responses
   - Add type hints to error handlers

6. Run tests after each change
   - Ensure changes don't break existing tests
   - Tests should guide refactoring
   - If tests fail, fix the code (not the tests)

**Verification Checklist**:

- [ ] All public functions in handlers have type hints
- [ ] All public methods in services have type hints
- [ ] All Pydantic models have properly typed fields
- [ ] Type hints use proper typing module imports
- [ ] Tests still pass after refactoring (100% pass rate)
- [ ] No new type errors when running mypy (will be done in Phase 2)
- [ ] Code is cleaner and more testable

**Testing Instructions**:

After each refactoring change:

```bash
cd backend
source .venv/bin/activate

# Run full test suite
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_lambda_handler.py -v

# Check no import errors
python -c "from src.handlers.lambda_handler import *"
python -c "from src.services.ai_service import *"
```

**Commit Message Template**:

```
refactor: improve backend code for testability and type safety

- Add type hints to lambda_handler.py public functions
- Add type hints to service method signatures
- Ensure Pydantic models have complete type information
- Improve dependency injection for easier mocking
- Add missing error handling in critical paths

This prepares code for Phase 2 (mypy type checking) and improves testability.
All tests pass after refactoring.
```

**Token Estimate**: ~4,000 tokens

---

## Summary & Verification

**Phase 1 Completion Checklist**:

- [ ] Task 1: Lambda handler tests written (6+ tests, 80%+ coverage)
- [ ] Task 2: Service layer tests written (15+ tests, 70%+ coverage)
- [ ] Task 3: Model validation tests written (10+ tests, 80%+ coverage)
- [ ] Task 4: Coverage reporting configured and baselined
- [ ] Task 5: Existing code refactored with type hints and improved testability
- [ ] All tests pass: `pytest tests/ -v` returns 100% pass rate
- [ ] Coverage target met: `pytest tests/ --cov=src` shows 60%+

**Total Test Count**: 30+ unit tests across Lambda handler, services, and models

**Total Coverage**: 60%+ on core backend code (critical paths)

**When all tasks complete**:

1. Run full test suite: `cd backend && source .venv/bin/activate && pytest tests/ -v --cov=src`
2. Verify 100% pass rate
3. Verify 60%+ coverage
4. Commit Phase 1 changes
5. **Proceed to Phase 2: Backend Code Quality**

---

## Notes

- Phase 1 focuses on testing critical paths (handler, services, models)
- Utilities and helper functions can be tested in Phase 2 or skipped
- Tests use mocked external APIs (no real API calls)
- Phase 2 will add type checking, formatting, and linting
- Phase 2 will refactor remaining code based on linting output

**Total Phase 1 Effort**: ~18,000 tokens

**Blocked By**: Phase 0 (setup & prerequisites)

**Blocks**: Phase 2 (code quality & type checking)

---

**Ready to continue? When Phase 1 is complete, proceed to [Phase 2: Backend Code Quality](./Phase-2.md)**
