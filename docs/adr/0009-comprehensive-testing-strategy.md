# ADR-0009: Comprehensive Testing Strategy

**Status**: Accepted

**Date**: 2025-11-19

**Context**: The Float project had low test coverage (backend 39%, frontend ~30%) with unreliable tests, several skipped tests, and no systematic testing approach. The backend lacked integration and E2E tests for AI services, while the frontend had incomplete component coverage and no integration tests for React Context or hooks. This made refactoring risky and deployment confidence low.

**Decision**: Implement a comprehensive layered testing strategy following the test pyramid pattern, with distinct test types for both backend and frontend, achieving 68%+ backend coverage and 75%+ frontend coverage.

**Test Pyramid Distribution**:
- **Unit Tests (70%)**: Fast, isolated tests for individual functions/components
- **Integration Tests (20%)**: Service interaction and API integration tests
- **E2E Tests (10%)**: Critical user flows through the entire system

**Backend Testing Strategy**:

**Unit Tests** (`backend/tests/unit/`):
- Lambda handler routing and error handling
- Service layer business logic (AI, TTS, storage, audio)
- Utilities and helper functions
- Models and data validation
- Target: 200+ tests, 80%+ coverage for core modules

**Integration Tests** (`backend/tests/integration/`):
- Real API calls to Google Gemini, OpenAI TTS
- S3 storage operations (with test buckets)
- Lambda initialization and configuration
- External service error handling
- Target: 30+ tests, covers external integrations

**E2E Tests** (`backend/tests/e2e/`):
- Full Lambda invocation flow (summary and meditation)
- Request validation → AI processing → TTS → S3 storage → response
- Error scenarios and edge cases
- Target: 10+ tests, covers critical paths

**Frontend Testing Strategy**:

**Component Tests** (`components/__tests__/`):
- All React Native components (UI rendering, props, state)
- User interactions (button presses, form inputs)
- Conditional rendering and error states
- Target: 100+ tests, all components covered

**Integration Tests** (`__tests__/integration/`):
- Components with React Context (FloatContext)
- Custom hooks with state management
- Multi-component workflows (auth flow, recording flow, meditation flow)
- Target: 20+ tests, covers Context and hook interactions

**E2E Tests** (`e2e/`):
- Complete user journeys (auth → record → generate meditation → play)
- Cross-screen navigation and state persistence
- Error scenarios and recovery
- Uses Detox for realistic mobile testing
- Target: 5+ tests, critical user paths only

**Alternatives Considered**:

1. **Focus on E2E Tests Only**
   - Pros: Test real user flows, catch integration bugs
   - Cons: Slow, flaky, expensive to maintain, poor debugging
   - Rejected: Not enough coverage, too slow for daily development

2. **Focus on Unit Tests Only**
   - Pros: Fast, easy to write, good code coverage numbers
   - Cons: Miss integration bugs, false confidence from mocked dependencies
   - Rejected: Not enough confidence in real-world behavior

3. **Snapshot Testing for All Components**
   - Pros: Easy to write, catches unintended changes
   - Cons: Brittle, poor debugging, test implementation details
   - Rejected: Not descriptive enough, snapshots alone insufficient

4. **Manual Testing Only**
   - Pros: No test code to maintain
   - Cons: Not repeatable, slow, error-prone, doesn't scale
   - Rejected: Unacceptable for production application

**Decision Rationale**:

**Test Pyramid Benefits**:
- Unit tests provide fast feedback during development (<1 minute)
- Integration tests catch service interaction bugs (real API behavior)
- E2E tests validate critical user journeys (realistic end-to-end flows)
- Balanced speed vs. confidence trade-off

**Coverage Targets**:
- Backend 68%+: Significant improvement from 39%, achievable without over-testing
- Frontend 75%+: Significant improvement from 30%, covers all critical components
- Not 100%: Avoid testing trivial code (getters, setters, simple renders)

**Test Isolation**:
- Unit tests use mocks for external dependencies (fast, deterministic)
- Integration tests use real APIs with test keys (catch real issues)
- E2E tests use mock backend or staging environment (full flow testing)

**Consequences**:

**Positive**:
- High confidence in code correctness and refactoring safety
- Fast feedback loop during development (unit tests <1 min)
- Catches real integration bugs before production (integration tests)
- Documents expected behavior through tests
- CI/CD enforces coverage thresholds (68% backend, 75% frontend)
- Reduces manual QA time
- Easier onboarding for new developers (tests as documentation)

**Negative**:
- Longer test execution time (~8 minutes backend, ~10 minutes frontend)
- More test code to maintain (200+ backend tests, 145+ frontend tests)
- Learning curve for writing good tests
- Some tests require external API keys (not available for forks)
- E2E tests can be flaky (mitigated with retry logic)

**Trade-offs Accepted**:
- Test suite execution time vs. confidence in deployments
- Test maintenance burden vs. refactoring safety
- Mocked dependencies (fast) vs. real integrations (slow but realistic)

**Implementation**:
- Backend: pytest with pytest-cov, fixtures in conftest.py, markers for test types
- Frontend: Jest with @testing-library/react-native, Detox for E2E
- CI/CD: Separate jobs for unit/integration/E2E tests (parallel execution)
- Coverage reports: HTML reports locally, XML for CI/CD, threshold enforcement

**Success Metrics** (Achieved):
- Backend: 200+ tests, 68% coverage (up from 39%)
- Frontend: 145+ tests, 75% coverage (up from 30%)
- Zero flaky tests (reliable CI/CD)
- All tests pass on every PR (required for merge)

**Related ADRs**:
- ADR-0005: Testing Strategy (Phase 0)
- ADR-0010: E2E Testing Framework (Detox)

**References**:
- [TESTING.md](../../TESTING.md) - Comprehensive testing guide
- [backend/tests/](../../backend/tests/) - Backend test implementation
- [__tests__/](../../__tests__/) - Frontend test implementation
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
