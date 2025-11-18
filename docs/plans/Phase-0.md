# Phase 0: Foundation

## Phase Goal

Establish architectural decisions, testing strategies, and coding conventions that will guide all subsequent implementation phases. This phase contains no code implementation - it serves as the reference documentation for design decisions and patterns to follow throughout the project.

**Success Criteria:**
- Clear architecture decisions documented
- Testing strategy defined for both backend and frontend
- Coding conventions and patterns established
- Common pitfalls identified

**Estimated Tokens:** ~5,000

## Architecture Decision Records (ADRs)

### ADR-1: SAM Template Structure

**Decision:** Use a single environment-agnostic SAM template with parameter files for environment-specific values.

**Rationale:**
- Ensures true environment parity between staging and production
- Reduces duplication and maintenance burden
- CloudFormation parameter files provide clean separation of environment config
- Single source of truth for infrastructure definition

**Implementation Pattern:**
```
infrastructure/
├── template.yaml              # Environment-agnostic SAM template
├── parameters/
│   ├── staging.json          # Staging-specific parameters
│   └── production.json       # Production-specific parameters
└── scripts/
    ├── deploy-staging.sh     # Staging deployment wrapper
    └── deploy-production.sh  # Production deployment wrapper
```

**Alternatives Considered:**
- Separate templates per environment: Rejected due to duplication and drift risk
- Single template with hardcoded values: Rejected due to lack of flexibility

---

### ADR-2: API Gateway Choice - HTTP API (v2)

**Decision:** Use AWS API Gateway HTTP API (v2) instead of REST API (v1) or Lambda Function URLs.

**Rationale:**
- 70% cost reduction compared to REST API ($1.00 vs $3.50 per million requests)
- Built-in CORS support complements existing middleware
- Sufficient features for the application's needs (simple POST endpoint routing)
- Better performance and lower latency than REST API
- More robust than Lambda Function URLs (better monitoring, throttling, custom domains)

**Trade-offs:**
- Fewer features than REST API (no API keys, usage plans, request/response transformation)
- These advanced features are not required for the current use case

---

### ADR-3: Secrets Management - Environment Variables in SAM

**Decision:** Store API keys and configuration as environment variables in SAM parameter files, not AWS Secrets Manager or SSM Parameter Store.

**Rationale:**
- Simplicity: No additional AWS service dependencies
- Cost: Zero additional cost (Secrets Manager is $0.40/month per secret)
- Sufficient security: Environment variables are encrypted at rest by Lambda
- Developer experience: Easy to update and manage during development
- Git-ignored parameter files prevent accidental commits

**Security Measures:**
- Parameter files added to .gitignore
- Example parameter files (with placeholder values) committed for documentation
- Production parameters managed through secure deployment pipeline
- Least-privilege IAM roles for Lambda execution

**Future Consideration:** If compliance requirements change or secrets rotation is needed, migrate to AWS Secrets Manager without changing application code (only SAM template updates).

---

### ADR-4: FFmpeg Layer Management

**Decision:** Reference FFmpeg Lambda layer by ARN in SAM template; maintain layer separately from SAM deployments.

**Rationale:**
- FFmpeg binary changes infrequently (stable dependency)
- Large binary size (~50MB) would slow down every SAM deployment
- Decouples layer updates from application deployments
- Allows independent layer version management across environments

**Implementation:**
- SAM template accepts layer ARN as a parameter
- Different layer ARNs per environment (staging/production)
- Layer update process documented separately
- If layer doesn't exist, provide clear error message with creation instructions

---

### ADR-5: Testing Strategy - Layered Test Pyramid

**Decision:** Implement a test pyramid with unit tests at the base, integration tests in the middle, and E2E tests at the top.

**Test Distribution:**
- **Unit Tests (70%):** Fast, isolated tests for individual functions/components
- **Integration Tests (20%):** Tests for service interactions and API integrations
- **E2E Tests (10%):** Critical user flows through the entire system

**Backend Testing Targets:**
- Lambda handler: 60%+ coverage
- Services (AI, TTS, Storage, Audio): 80%+ coverage
- Models and utilities: 90%+ coverage
- Overall backend coverage: 65%+ (up from current 39%)

**Frontend Testing Targets:**
- Component unit tests: All components covered
- Integration tests: Components with Context/hooks
- E2E tests: Core user flows (auth, recording, meditation generation)
- Overall frontend coverage: 70%+

**Rationale:**
- Unit tests provide fast feedback during development
- Integration tests catch service interaction bugs
- E2E tests validate critical user journeys
- Pyramid shape optimizes test suite speed and maintenance

---

### ADR-6: Test Isolation and Mocking Strategy

**Decision:** Use comprehensive mocking for external dependencies with clear mock fixture organization.

**Backend Mocking Pattern:**
- Mock external APIs (Gemini, OpenAI, Google TTS) at the service boundary
- Use pytest fixtures in conftest.py for reusable mocks
- Store sample API responses in `tests/fixtures/sample_data.py`
- Integration tests use actual API calls with test API keys (when possible)

**Frontend Mocking Pattern:**
- Mock backend API calls using jest mock functions
- Mock React Native platform-specific APIs (audio, file system)
- Use @testing-library/react-native for component testing
- Integration tests render components with actual Context providers

**Rationale:**
- Fast test execution without external API dependencies
- Deterministic test results (no flaky tests due to API changes)
- Cost reduction (no API charges during testing)
- Enables offline development and testing

**Exception:** Integration tests in Phase 3 and Phase 5 will include some tests with real API calls to validate actual service integration.

---

### ADR-7: Deployment Strategy - Manual Review Required

**Decision:** SAM deployments require manual approval before production deployment.

**Implementation:**
- Staging: Automatic deployment on merge to main branch (future enhancement)
- Production: Manual `deploy-production.sh` execution after staging validation
- Use CloudFormation change sets to review infrastructure changes
- Rollback capability through CloudFormation stack rollback

**Rationale:**
- Production safety: Prevent accidental production deployments
- Cost control: Review infrastructure changes before applying
- Compliance: Human verification step for production changes
- Aligns with ADR #5 from existing project documentation (no automatic deployment)

---

### ADR-8: Conventional Commits Standard

**Decision:** Use Conventional Commits specification for all commit messages.

**Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding or updating tests
- `refactor`: Code refactoring without behavior change
- `docs`: Documentation updates
- `chore`: Build process, tooling, dependencies
- `ci`: CI/CD pipeline changes
- `perf`: Performance improvements

**Scopes:**
- `infrastructure`: SAM templates, deployment scripts
- `backend`: Python Lambda code
- `frontend`: React Native code
- `tests`: Test files (can be combined with backend/frontend)

**Examples:**
```
feat(infrastructure): add SAM template with Lambda and S3 resources

test(backend): increase Lambda handler test coverage to 65%

fix(frontend): resolve BackendSummaryCall test timeout issues
```

**Rationale:**
- Clear, searchable commit history
- Automated changelog generation (future)
- Easy to understand change type at a glance
- Industry standard practice

---

## Testing Strategy

### Backend Testing Strategy

**Test Organization:**
```
backend/tests/
├── unit/                      # Unit tests (fast, isolated)
│   ├── test_lambda_handler.py
│   ├── test_services.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/               # Integration tests (with external deps)
│   ├── test_ai_integration.py
│   ├── test_tts_integration.py
│   └── test_s3_integration.py
├── e2e/                       # End-to-end tests (full Lambda invocation)
│   ├── test_summary_flow.py
│   └── test_meditation_flow.py
├── fixtures/                  # Test data and fixtures
│   └── sample_data.py
├── mocks/                     # Mock implementations
│   └── external_apis.py
└── conftest.py               # Shared pytest fixtures
```

**Test Naming Convention:**
- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName><TestType>`
- Test functions: `test_<functionality>_<expected_behavior>`

**Example:**
```python
class TestLambdaHandlerRouting:
    def test_summary_request_routes_to_summary_handler(self):
        # Test implementation
```

**Coverage Measurement:**
- Command: `pytest tests/ --cov=src --cov-report=term-missing`
- Minimum thresholds enforced in CI/CD
- Coverage reports tracked in `backend/coverage_baseline.txt`

**Test Markers:**
```python
@pytest.mark.unit        # Fast unit test
@pytest.mark.integration # Integration test (may be slower)
@pytest.mark.e2e         # End-to-end test (slowest)
@pytest.mark.slow        # Known slow test
```

**Running Tests:**
```bash
# All tests
pytest tests/

# Unit tests only (fast feedback)
pytest tests/ -m unit

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_lambda_handler.py -v
```

---

### Frontend Testing Strategy

**Test Organization:**
```
components/__tests__/          # Component tests
  ├── BackendSummaryCall-test.tsx
  ├── BackendMeditationCall-test.tsx
  ├── History-test.tsx         # To be added
  └── ... (all components)

app/__tests__/                 # Screen/page tests (to be added)
  ├── index-test.tsx
  └── meditation-test.tsx

__tests__/                     # Integration & E2E tests
  ├── integration/
  │   ├── auth-flow-test.tsx
  │   └── recording-flow-test.tsx
  └── e2e/
      └── critical-user-flows.test.ts
```

**Test Naming Convention:**
- Test files: `<ComponentName>-test.tsx` (following existing convention)
- Test suites: `describe('<ComponentName>', () => {})`
- Test cases: `it('should <expected behavior>', () => {})`

**Example:**
```typescript
describe('AudioRecording', () => {
  it('should start recording when record button pressed', async () => {
    // Test implementation
  });
});
```

**Testing Library Patterns:**
- Use `@testing-library/react-native` queries (getByRole, getByText, getByTestId)
- Avoid implementation details (don't access state directly)
- Test user interactions and visual output
- Use `userEvent` for realistic user interactions

**Running Tests:**
```bash
# All tests
npm test -- --watchAll=false

# With coverage
npm test -- --coverage --watchAll=false

# Specific test file
npm test -- BackendSummaryCall-test.tsx

# Update snapshots
npm test -- -u
```

**Coverage Reporting:**
- HTML reports in `coverage/lcov-report/`
- JSON reports in `coverage/coverage-final.json`
- LCOV reports for CI/CD integration

---

## Coding Conventions

### Backend Conventions (Python)

**Type Hints:**
- All public functions must have complete type hints
- Use `Optional[T]` for nullable types
- Use `Union[T, U]` for multiple types
- Use `Dict[str, Any]` for flexible dictionaries

**Docstrings:**
- All public functions, classes, and modules must have docstrings
- Use Google-style docstrings

**Example:**
```python
def analyze_sentiment(prompt: str, audio: Optional[str] = None) -> dict[str, Any]:
    """
    Analyze sentiment from user input text or audio.

    Args:
        prompt: User's text input
        audio: Optional base64-encoded audio data

    Returns:
        Dictionary containing sentiment analysis results

    Raises:
        ValueError: If both prompt and audio are empty
    """
    # Implementation
```

**Error Handling:**
- Use custom exceptions for domain errors (defined in `src/utils/exceptions.py`)
- Catch specific exceptions, not bare `except`
- Log errors with context before raising
- Return error responses in consistent format

**Code Quality Tools:**
- `black` for formatting (100-char line length)
- `ruff` for linting (Flake8-compatible rules)
- `mypy` for type checking (strict mode)
- Run `backend/check_quality.sh` before committing

---

### Frontend Conventions (TypeScript)

**TypeScript:**
- Use strict mode (enabled in tsconfig.json)
- Avoid `any` type unless absolutely necessary
- Define interfaces for component props
- Use type inference where possible

**Component Structure:**
```typescript
interface MyComponentProps {
  title: string;
  onPress?: () => void;
}

export function MyComponent({ title, onPress }: MyComponentProps) {
  // Component implementation
}
```

**Hooks:**
- Keep hooks at the top of component (before any conditions)
- Extract complex logic into custom hooks
- Name custom hooks with `use` prefix

**Styling:**
- Use StyleSheet.create for styles
- Prefer inline styles only for dynamic values
- Keep styles at bottom of file

**Code Quality Tools:**
- `eslint` for linting
- `prettier` for formatting
- `tsc` for type checking
- Run `npm run lint && npm run type-check` before committing

---

## Common Pitfalls to Avoid

### Backend Pitfalls

1. **Missing Environment Variables:**
   - Always check settings.validate() before using config values
   - Use validate_config=False in tests to skip environment checks
   - Document all required environment variables

2. **Mock Leakage Between Tests:**
   - Reset mocks in teardown or use fresh fixtures per test
   - Avoid global state in tests
   - Use pytest's built-in fixture scopes appropriately

3. **Hardcoded AWS Resource Names:**
   - Always use environment variables for bucket names, regions, etc.
   - Make Lambda handler accept injected dependencies for testing
   - Avoid direct boto3 client creation in business logic

4. **Incomplete Error Handling in Lambda:**
   - Wrap handler logic in try/except at the top level
   - Return proper HTTP status codes (200, 400, 500)
   - Include correlation IDs for debugging

5. **FFmpeg Binary Path Issues:**
   - Use FFMPEG_BINARY and FFMPEG_PATH environment variables
   - Test audio processing in Lambda environment (not just locally)
   - Handle missing FFmpeg gracefully with clear error messages

### Frontend Pitfalls

1. **Mocking React Native APIs Incorrectly:**
   - Use jest.mock() at the top of test files
   - Mock all platform-specific APIs (Audio, FileSystem, Notifications)
   - Reset mocks between tests with jest.clearAllMocks()

2. **Async Timing Issues:**
   - Use waitFor() for async operations
   - Avoid arbitrary setTimeout() in tests
   - Use act() for state updates that happen outside user events

3. **Snapshot Test Brittleness:**
   - Keep snapshots small and focused
   - Review snapshot changes carefully
   - Prefer explicit assertions over snapshots when possible

4. **Testing Implementation Details:**
   - Don't test component state directly
   - Test user-visible behavior, not internal methods
   - Use accessibility queries (getByRole) over getByTestId when possible

5. **Ignoring Test Failures:**
   - Fix failing tests immediately - don't skip them
   - Investigate intermittent failures - they indicate real issues
   - Don't commit code with failing tests

### SAM/Infrastructure Pitfalls

1. **Missing IAM Permissions:**
   - Grant least-privilege permissions to Lambda execution role
   - Include permissions for all AWS services Lambda uses (S3, CloudWatch Logs)
   - Test IAM permissions in staging before production

2. **Stack Update Failures:**
   - Review CloudFormation change sets before applying
   - Understand which resource changes require replacement
   - Have rollback plan for failed deployments

3. **Parameter File Security:**
   - Never commit parameter files with real API keys
   - Add `infrastructure/parameters/*.json` to .gitignore (except examples)
   - Use placeholder values in example parameter files

4. **Environment Name Confusion:**
   - Use clear parameter names (staging vs production, not env1 vs env2)
   - Include environment name in stack names for clarity
   - Document which AWS account hosts which environment

5. **Deployment Script Errors:**
   - Validate SAM template before deployment (sam validate)
   - Check AWS credentials before running deploy script
   - Include clear error messages in deployment scripts

---

## Development Workflow

### Daily Development Flow

1. **Start of Day:**
   - Pull latest changes: `git pull origin claude/sam-deployment-testing-01KSjcbwLqaXQJQ8c9JQrV9h`
   - Check CI/CD status for any failures
   - Review current phase checklist

2. **During Development:**
   - Write test first (TDD approach)
   - Implement feature to make test pass
   - Run relevant tests frequently
   - Commit often with conventional commit messages

3. **Before Committing:**
   - Run quality checks:
     - Backend: `cd backend && ./check_quality.sh`
     - Frontend: `npm run lint && npm run type-check && npm test -- --watchAll=false`
   - Review your changes: `git diff`
   - Stage changes: `git add <files>`
   - Commit with conventional message: `git commit -m "type(scope): description"`

4. **End of Day/Task:**
   - Push changes: `git push -u origin claude/sam-deployment-testing-01KSjcbwLqaXQJQ8c9JQrV9h`
   - Update phase checklist
   - Document any blockers or questions

### Test-Driven Development (TDD) Flow

1. **Write a failing test** that describes the desired behavior
2. **Run the test** to verify it fails (red)
3. **Write minimal code** to make the test pass
4. **Run the test** to verify it passes (green)
5. **Refactor** the code while keeping tests passing
6. **Repeat** for next feature

**Benefits:**
- Clear specification of desired behavior
- Higher confidence in correctness
- Better code design (testable code is often better structured)
- Living documentation of system behavior

---

## Phase Completion

This phase is complete when:
- All ADRs are reviewed and understood
- Testing strategy is clear
- Coding conventions are documented
- Common pitfalls are identified
- Team (or engineer) is ready to begin Phase 1

No code changes or tests are created in this phase.

---

**Next Phase:** [Phase 1: SAM Infrastructure Setup](Phase-1.md)
