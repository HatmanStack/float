# Phase 5: Frontend Test Improvements - Integration & E2E (Detox)

## Phase Goal

Add integration tests for components with React Context and hooks, set up Detox end-to-end testing infrastructure (per ADR-10), and create critical user flow tests. Verify that frontend components work together correctly and that complete user journeys function as expected.

**Success Criteria:**
- Integration tests added for components with Context providers
- E2E testing framework set up (Detox, per ADR-10)
- Critical user flows tested end-to-end (auth, recording, meditation)
- All integration and E2E tests pass reliably
- Test isolation maintained across test types
- Overall frontend test suite comprehensive and maintainable

**Estimated Tokens:** ~25,000

## Prerequisites

- Phase 4 complete (component tests at 75%+ coverage)
- **Phase 0 ADR-10 reviewed (E2E framework decision: Detox)**
- Understanding of React Context API usage in the app
- Understanding of navigation structure
- Familiarity with E2E testing concepts
- Review existing Context providers in `context/` directory
- **Android Studio installed (for Android emulator) OR Xcode installed (for iOS simulator)**

## Tasks

### Task 1: Set Up Integration Test Infrastructure

**Goal:** Create infrastructure for integration tests that render components with Context providers and test realistic component interactions.

**Files to Create:**
- `__tests__/integration/` - Directory for integration tests
- `__tests__/integration/test-utils.tsx` - Integration test utilities
- `__tests__/integration/setup.ts` - Integration test setup

**Prerequisites:**
- Review Phase 4 test utilities
- Review Context providers in `context/` directory
- Understand difference between component and integration tests

**Implementation Steps:**

1. Create integration test directory:
   - Create `__tests__/integration/` at project root
   - Separate from component unit tests
   - Create `__init__.ts` for package structure
2. Create integration test utilities:
   - Custom render function that wraps components with all Context providers
   - Mock navigation for integration tests
   - Utilities for testing Context state changes
   - Utilities for testing async state updates across components
3. Set up Context provider mocks:
   - Create mock Context values with realistic data
   - Support customizing Context values per test
   - Handle nested Context providers correctly
4. Configure integration test environment:
   - Set appropriate timeouts for integration tests
   - Configure cleanup between tests
   - Set up test isolation for Context state
5. Document integration testing patterns:
   - How to test components with Context
   - How to test Context state changes
   - How to test component communication through Context
   - Examples of good integration tests

**Architecture Guidance:**
- Integration tests render components with real Context providers
- Mock external APIs (backend calls) but use real Context
- Test component interactions through shared state
- Longer timeouts than unit tests (components interact)
- Clean up Context state between tests

**Verification Checklist:**
- [ ] Integration test directory created
- [ ] Integration test utilities created with Context support
- [ ] Render function wraps components with all providers
- [ ] Test isolation verified between integration tests
- [ ] Documentation for integration testing patterns
- [ ] Example integration test working

**Testing Instructions:**
```bash
# Run integration tests
npm test -- __tests__/integration/ --watchAll=false

# Run with verbose output
npm test -- __tests__/integration/ --verbose

# Verify Context providers working
npm test -- __tests__/integration/ --watchAll=false --testNamePattern="context"
```

**Commit Message Template:**
```
test(frontend): set up integration test infrastructure

- Create __tests__/integration/ directory structure
- Add integration test utilities with Context provider support
- Create custom render function with all providers
- Add test isolation for Context state
- Document integration testing patterns
- Add example integration test
```

**Estimated Tokens:** ~3,500

---

### Task 2: Add Integration Tests for Auth Flow with Context

**Goal:** Add integration tests for authentication flow that involve AuthScreen component and authentication Context.

**Files to Create:**
- `__tests__/integration/auth-flow-test.tsx`

**Prerequisites:**
- Task 1 complete
- Review authentication Context provider
- Review AuthScreen component
- Understand auth token flow

**Implementation Steps:**

1. Add authentication Context integration tests:
   - Test AuthScreen with authentication Context provider
   - Test sign-in updates Context state
   - Test authenticated state propagates to other components
   - Test sign-out clears Context state
2. Add token persistence integration tests:
   - Test token saved to AsyncStorage after sign-in
   - Test token loaded from AsyncStorage on app start
   - Test Context initialized with stored token
   - Test token cleared on sign-out
3. Add navigation integration tests:
   - Test navigation after successful sign-in
   - Test navigation blocked when not authenticated
   - Test navigation to auth screen when token expired
4. Add multi-component integration tests:
   - Test AuthScreen + authenticated component interaction
   - Test Context state shared across multiple screens
   - Test auth state changes reflected in all components
5. Add error scenario integration tests:
   - Test sign-in error updates Context correctly
   - Test network error during auth flow
   - Test expired token handling

**Architecture Guidance:**
- Use real authentication Context provider
- Mock Google Sign-In API (external)
- Mock AsyncStorage with in-memory store
- Mock navigation
- Test state changes across multiple components
- Verify Context updates trigger re-renders

**Verification Checklist:**
- [ ] At least 10 integration tests for auth flow
- [ ] Context state changes tested across components
- [ ] Token persistence tested with AsyncStorage
- [ ] Navigation integration tested
- [ ] Error scenarios tested
- [ ] All tests pass reliably
- [ ] Tests isolated from each other

**Testing Instructions:**
```bash
# Run auth flow integration tests
npm test -- auth-flow-test.tsx

# Run with Context debugging
npm test -- auth-flow-test.tsx --verbose

# Verify AsyncStorage cleanup
npm test -- auth-flow-test.tsx --watchAll=false
npm test -- auth-flow-test.tsx --watchAll=false  # Run twice to verify isolation
```

**Commit Message Template:**
```
test(frontend): add auth flow integration tests with Context

- Add integration tests for AuthScreen with auth Context
- Test sign-in updates Context and persists token
- Test sign-out clears Context and token
- Test navigation integration with auth state
- Test multi-component auth state sharing
- Test error scenarios with Context updates
- All tests pass reliably with proper isolation
```

**Estimated Tokens:** ~4,000

---

### Task 3: Add Integration Tests for Recording Flow with Context

**Goal:** Add integration tests for audio recording flow that involve AudioRecording component and recording Context/state.

**Files to Create:**
- `__tests__/integration/recording-flow-test.tsx`

**Prerequisites:**
- Task 1 complete
- Review recording Context or state management
- Review AudioRecording and BackendSummaryCall components

**Implementation Steps:**

1. Add recording Context integration tests:
   - Test AudioRecording with recording Context
   - Test recording state updates Context
   - Test recording completion triggers summary request
   - Test recording error handling with Context
2. Add recording to summary integration tests:
   - Test AudioRecording → BackendSummaryCall flow
   - Test recording data passed to backend correctly
   - Test summary result updates Context/state
   - Test UI updates after summary received
3. Add recording permissions integration tests:
   - Test permission request with Context
   - Test permission denial blocks recording
   - Test permission status displayed across components
4. Add multi-component recording flow tests:
   - Test recording indicator visible in multiple components
   - Test recording stop updates all relevant components
   - Test recording playback with Context state
5. Add error scenario integration tests:
   - Test recording failure updates Context correctly
   - Test backend request failure after recording
   - Test network error during summary request

**Architecture Guidance:**
- Use real recording Context provider
- Mock expo-av Recording (external)
- Mock backend API calls
- Test data flow: recording → backend → Context → UI
- Verify state updates trigger appropriate re-renders
- Test cleanup of recording data

**Verification Checklist:**
- [ ] At least 8 integration tests for recording flow
- [ ] Recording Context integration tested
- [ ] Recording → summary flow tested
- [ ] Multi-component state sharing tested
- [ ] Error scenarios tested
- [ ] All tests pass reliably
- [ ] Recording cleanup verified

**Testing Instructions:**
```bash
# Run recording flow integration tests
npm test -- recording-flow-test.tsx

# Run with detailed output
npm test -- recording-flow-test.tsx --verbose

# Verify no memory leaks from recording
npm test -- recording-flow-test.tsx --watchAll=false --detectLeaks
```

**Commit Message Template:**
```
test(frontend): add recording flow integration tests

- Add integration tests for AudioRecording with Context
- Test recording → BackendSummaryCall → Context flow
- Test recording state shared across components
- Test permission handling with Context
- Test error scenarios and cleanup
- Verify recording data cleanup
- All tests pass reliably
```

**Estimated Tokens:** ~4,000

---

### Task 4: Add Integration Tests for Meditation Flow with Context

**Goal:** Add integration tests for meditation generation and playback flow involving multiple components and Context.

**Files to Create:**
- `__tests__/integration/meditation-flow-test.tsx`

**Prerequisites:**
- Task 1 complete
- Review meditation Context or state management
- Review BackendMeditationCall and meditation playback components

**Implementation Steps:**

1. Add meditation generation Context integration tests:
   - Test BackendMeditationCall with meditation Context
   - Test meditation request updates Context state
   - Test meditation result stored in Context
   - Test meditation history updated in Context
2. Add meditation playback integration tests:
   - Test meditation audio playback with Context
   - Test playback controls update Context state
   - Test playback progress tracked in Context
   - Test playback completion updates Context
3. Add summary to meditation integration tests:
   - Test summary result → meditation generation flow
   - Test emotion data passed correctly
   - Test meditation appropriate for emotion
   - Test history updated with both summary and meditation
4. Add multi-component meditation flow tests:
   - Test meditation controls visible across components
   - Test playback state shared across screens
   - Test meditation history updated and displayed
5. Add error scenario integration tests:
   - Test meditation generation failure
   - Test audio playback failure
   - Test network error during meditation request

**Architecture Guidance:**
- Use real meditation Context provider
- Mock backend API calls
- Mock expo-av Audio playback
- Test complete flow: summary → meditation → playback → history
- Verify audio cleanup after playback
- Test meditation persistence in history

**Verification Checklist:**
- [ ] At least 10 integration tests for meditation flow
- [ ] Meditation Context integration tested
- [ ] Playback state shared across components
- [ ] Summary → meditation flow tested
- [ ] History integration tested
- [ ] Error scenarios tested
- [ ] All tests pass reliably

**Testing Instructions:**
```bash
# Run meditation flow integration tests
npm test -- meditation-flow-test.tsx

# Run with detailed output
npm test -- meditation-flow-test.tsx --verbose

# Verify audio cleanup
npm test -- meditation-flow-test.tsx --watchAll=false
```

**Commit Message Template:**
```
test(frontend): add meditation flow integration tests

- Add integration tests for meditation generation with Context
- Test meditation playback state shared across components
- Test summary → meditation → playback → history flow
- Test meditation controls with Context
- Test error scenarios and audio cleanup
- All tests pass reliably
```

**Estimated Tokens:** ~4,000

---

### Task 5: Set Up Detox E2E Testing Framework

**Goal:** Install and configure Detox for React Native E2E testing, following ADR-10.

**Files to Create:**
- `.detoxrc.js` - Detox configuration
- `e2e/` - Directory for E2E tests
- `e2e/init.ts` - E2E test initialization
- `e2e/config.json` - E2E test configuration

**Prerequisites:**
- Phase 0 ADR-10 reviewed (Detox decision and rationale)
- Detox documentation reviewed
- Understand Expo app testing with Detox
- Review app navigation structure
- Android Studio or Xcode installed

**Implementation Steps:**

1. Install Detox and dependencies:
   - Install Detox CLI: `npm install -g detox-cli`
   - Install Detox: `npm install --save-dev detox`
   - Install Jest integration: `npm install --save-dev jest`
   - Configure for React Native / Expo
2. Configure E2E testing:
   - Create configuration file
   - Configure iOS simulator / Android emulator
   - Set up test timeouts and retry logic
   - Configure test data and environment
3. Create E2E test utilities:
   - Helper functions for common actions (tap, swipe, type)
   - Helper functions for waiting for elements
   - Helper functions for assertions
   - Mock backend responses for E2E tests
4. Set up test data:
   - Create test user accounts
   - Create test audio files
   - Set up test backend environment (or mocks)
5. Create example E2E test:
   - Simple test that launches app
   - Test that navigates to main screen
   - Verify example test passes
6. Document E2E testing:
   - How to run E2E tests
   - How to write E2E tests
   - How to debug E2E test failures
   - Known limitations and workarounds

**Architecture Guidance:**
- E2E tests run on real simulator/emulator
- Mock backend API or use test backend environment
- Longer timeouts needed (app startup, animations)
- Clean up test data after each test
- Consider test execution time (E2E tests slow)
- Run E2E tests separately from unit/integration tests

**Verification Checklist:**
- [ ] E2E framework installed and configured
- [ ] E2E test directory structure created
- [ ] Test utilities and helpers created
- [ ] Example E2E test passes
- [ ] Documentation complete
- [ ] E2E tests can run locally

**Testing Instructions:**
```bash
# Build app for E2E testing (if using Detox)
detox build --configuration ios.sim.debug

# Run E2E tests
detox test --configuration ios.sim.debug

# Run with verbose output
detox test --configuration ios.sim.debug --loglevel verbose

# Run single E2E test
detox test --configuration ios.sim.debug e2e/example.e2e.ts
```

**Commit Message Template:**
```
test(frontend): set up E2E testing framework

- Install and configure Detox for E2E testing
- Create e2e/ directory structure
- Add E2E test utilities and helpers
- Configure test environment and mock backend
- Create example E2E test
- Document E2E testing setup and usage
- Example test passes on iOS simulator
```

**Estimated Tokens:** ~4,000

---

### Task 6: Add E2E Test for Complete User Journey

**Goal:** Add end-to-end test for critical user journey: sign in → record audio → generate summary → generate meditation → play meditation.

**Files to Create:**
- `e2e/complete-user-journey.e2e.ts`

**Prerequisites:**
- Task 5 complete (E2E framework set up)
- App builds and runs in simulator/emulator
- Test backend configured or mocked

**Implementation Steps:**

1. Add app launch and sign-in E2E test:
   - Launch app
   - Wait for auth screen
   - Tap sign-in button
   - Handle Google Sign-In (mocked)
   - Verify navigation to main screen
2. Add audio recording E2E test:
   - Tap record button
   - Wait for permission prompt
   - Grant permission
   - Record for 3 seconds
   - Stop recording
   - Verify recording indicator
3. Add summary generation E2E test:
   - Wait for recording to upload
   - Wait for summary to generate
   - Verify summary displayed
   - Verify emotion label shown
   - Verify intensity shown
4. Add meditation generation E2E test:
   - Tap generate meditation button
   - Wait for meditation to generate
   - Verify meditation text displayed
   - Verify play button available
5. Add meditation playback E2E test:
   - Tap play button
   - Verify playback starts
   - Verify playback controls visible
   - Tap pause button
   - Verify playback pauses
   - Tap stop button
6. Add history verification:
   - Navigate to history screen
   - Verify incident appears in history
   - Verify incident details correct
   - Tap incident to view details

**Architecture Guidance:**
- Mock backend API responses for speed
- Use realistic test data
- Wait for animations to complete
- Take screenshots on failure for debugging
- Test on both iOS and Android if possible
- Long timeout for meditation generation (30-60s)

**Verification Checklist:**
- [ ] Complete user journey E2E test passes
- [ ] All steps verified: auth → record → summary → meditation → playback → history
- [ ] Test runs in <2 minutes
- [ ] Test passes reliably (run 3 times)
- [ ] Screenshots taken on failure
- [ ] Works on both iOS and Android (if applicable)

**Testing Instructions:**
```bash
# Run complete user journey test
detox test --configuration ios.sim.debug e2e/complete-user-journey.e2e.ts

# Run with screenshots
detox test --configuration ios.sim.debug e2e/complete-user-journey.e2e.ts --take-screenshots failing

# Run on Android
detox test --configuration android.emu.debug e2e/complete-user-journey.e2e.ts

# Run multiple times to check reliability
for i in {1..3}; do detox test --configuration ios.sim.debug e2e/complete-user-journey.e2e.ts; done
```

**Commit Message Template:**
```
test(frontend): add complete user journey E2E test

- Add E2E test for full user flow: auth → record → summary → meditation → playback
- Test sign-in and navigation
- Test audio recording with permissions
- Test summary generation and display
- Test meditation generation and playback
- Test history updated correctly
- Test passes reliably in <2 minutes
```

**Estimated Tokens:** ~4,500

---

### Task 7: Add E2E Tests for Critical Error Scenarios

**Goal:** Add E2E tests for critical error scenarios to ensure app handles failures gracefully.

**Files to Create:**
- `e2e/error-scenarios.e2e.ts`

**Prerequisites:**
- Task 6 complete (basic E2E test working)
- Understanding of error handling in app

**Implementation Steps:**

1. Add network error E2E tests:
   - Test app behavior when offline
   - Test summary request failure
   - Test meditation request failure
   - Verify error messages displayed to user
   - Verify app doesn't crash
2. Add permission denial E2E tests:
   - Test recording when permission denied
   - Verify error message shown
   - Verify app guides user to settings
   - Test app continues to work after denial
3. Add invalid input E2E tests:
   - Test with very short recording
   - Test with very long recording (if limits)
   - Test with silent audio
   - Verify appropriate error messages
4. Add backend error E2E tests:
   - Test with 500 error from backend
   - Test with 400 error from backend
   - Test with timeout from backend
   - Verify error messages user-friendly
5. Add recovery E2E tests:
   - Test retry after network error
   - Test continuing after permission denial
   - Test recovering from backend error
   - Verify app state consistent after recovery

**Architecture Guidance:**
- Mock network failures with E2E framework
- Mock backend errors with test server
- Verify error messages user-friendly (not technical)
- Test app doesn't crash on errors
- Verify app state remains consistent
- Test error recovery flows

**Verification Checklist:**
- [ ] At least 8 E2E tests for error scenarios
- [ ] Network errors tested
- [ ] Permission errors tested
- [ ] Backend errors tested
- [ ] Recovery flows tested
- [ ] All tests pass reliably
- [ ] App never crashes in error scenarios

**Testing Instructions:**
```bash
# Run error scenario tests
detox test --configuration ios.sim.debug e2e/error-scenarios.e2e.ts

# Run with network mocking
detox test --configuration ios.sim.debug e2e/error-scenarios.e2e.ts --loglevel verbose

# Verify error messages user-friendly
detox test --configuration ios.sim.debug e2e/error-scenarios.e2e.ts --take-screenshots all
```

**Commit Message Template:**
```
test(frontend): add E2E tests for error scenarios

- Add E2E tests for network errors and offline behavior
- Add tests for permission denial handling
- Add tests for backend errors (500, 400, timeout)
- Add tests for invalid input handling
- Add tests for error recovery flows
- Verify error messages user-friendly
- Verify app never crashes on errors
- All tests pass reliably
```

**Estimated Tokens:** ~3,500

---

### Task 8: Verify Frontend Test Coverage and Quality

**Goal:** Run all frontend tests (component, integration, E2E), verify coverage and quality metrics, and ensure comprehensive test suite.

**Files to Modify:**
- `TESTING.md` - Update with integration and E2E test info
- `coverage/` - Final coverage reports

**Prerequisites:**
- All previous tasks in Phase 5 complete
- All test suites passing

**Implementation Steps:**

1. Run complete frontend test suite:
   - Run all component tests (Phase 4)
   - Run all integration tests (Phase 5)
   - Run all E2E tests (Phase 5)
   - Generate combined coverage report
2. Verify coverage:
   - Component coverage: 75%+ (from Phase 4)
   - Integration coverage: Incremental improvement
   - Overall frontend coverage: 75%+
3. Measure test performance:
   - Component tests: <2 minutes
   - Integration tests: <3 minutes
   - E2E tests: <5 minutes
   - Total: <10 minutes
4. Verify test quality:
   - Run all tests 3 times to check flakiness
   - Verify test isolation
   - Check for warnings or errors
   - Verify cleanup working correctly
5. Update documentation:
   - Document integration test patterns
   - Document E2E test patterns
   - Document how to run different test suites
   - Document test execution times
   - Add troubleshooting guide
6. Create test execution guide:
   - Commands for different test types
   - CI/CD integration info
   - Local development workflow
   - Debugging failing tests

**Architecture Guidance:**
- Different test types serve different purposes
- Document when to use each test type
- Balance test coverage with execution time
- Provide clear commands for CI/CD
- Document test maintenance practices

**Verification Checklist:**
- [ ] All test suites pass (component, integration, E2E)
- [ ] Overall frontend coverage: 75%+
- [ ] Test performance acceptable: <10 minutes total
- [ ] No flaky tests (3 consecutive runs pass)
- [ ] Documentation complete and accurate
- [ ] Test execution guide created

**Testing Instructions:**
```bash
# Run all component tests
npm test -- components/ --watchAll=false --coverage

# Run all integration tests
npm test -- __tests__/integration/ --watchAll=false

# Run all E2E tests (separate command)
detox test --configuration ios.sim.debug

# Run complete frontend test suite (excluding E2E)
npm test -- --watchAll=false --coverage

# Verify no flakiness
for i in {1..3}; do npm test -- --watchAll=false; done

# Measure total execution time
time npm test -- --watchAll=false
```

**Coverage Verification:**
```bash
# Check coverage thresholds
npm test -- --coverage --watchAll=false --coverageThreshold='{"global":{"lines":75,"statements":75,"functions":70,"branches":70}}'

# Generate HTML report
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html

# View coverage summary
npm test -- --coverage --watchAll=false | grep "All files"
```

**Commit Message Template:**
```
test(frontend): verify complete frontend test suite

- Run all component, integration, and E2E tests
- Verify overall frontend coverage: 77%
- Verify test performance: <10 minutes total
- Check for flaky tests (none found)
- Update TESTING.md with integration and E2E patterns
- Create test execution guide
- Document troubleshooting for common issues

Frontend test suite summary:
- Component tests: ~100 tests, <2 min, 75% coverage
- Integration tests: ~30 tests, <3 min
- E2E tests: ~15 tests, <5 min
- Total: ~145 tests, <10 min, 77% overall coverage
- Zero flaky tests
- Comprehensive coverage of critical user flows
```

**Estimated Tokens:** ~3,000

---

## Review Feedback (Iteration 1)

### Overall Phase Assessment

> **Consider:** The plan specifies 8 tasks for Phase 5. Running `git log --oneline da15552 ^1fea4a9` shows 12 commits. How many tasks were actually completed versus partially completed or not started?
>
> **Reflect:** Run `npm test -- --watchAll=false` and observe the output. Do you see "2 failed, 19 passed, 21 total" test suites? What does "2 failed" mean for phase completion?

### Critical Test Failures

> **Consider:** The test run shows `FAIL __tests__/integration/setup.ts` and `FAIL __tests__/integration/test-utils.tsx`. Are these supposed to be test files, or are they utility files?
>
> **Think about:** Look at line 26-28 of package.json. The testPathIgnorePatterns only includes `/components/__tests__/utils/`. Does this pattern match `__tests__/integration/setup.ts`?
>
> **Reflect:** How should Jest be configured to prevent utility files from being executed as tests?

### Integration Test Setup Issues

> **Consider:** Look at line 8 of `__tests__/integration/setup.ts`. It imports `'@testing-library/react-native/extend-expect'`. Run `npm list @testing-library/react-native` - you have v13.3.3. Does this version include an `extend-expect` export?
>
> **Think about:** Search the @testing-library/react-native documentation for v13. Was the `extend-expect` import removed in newer versions? What's the correct way to set up test matchers in v13+?
>
> **Reflect:** This import failure causes 2 test suites to fail. Should test infrastructure files cause test suite failures?

### Task 6: Complete User Journey E2E Test (NOT COMPLETED)

> **Consider:** The plan at lines 458-553 specifies creating `e2e/complete-user-journey.e2e.ts`. Run `ls e2e/*.e2e.ts` - what files are found?
>
> **Think about:** Task 6 requires testing the complete flow: sign in → record audio → generate summary → generate meditation → play meditation. With zero .e2e.ts files, how can this user journey be tested end-to-end?
>
> **Reflect:** The e2e/README.md (line 106) mentions "complete-user-journey.e2e.ts (planned)". Does "planned" mean "completed"?

### Task 7: Error Scenarios E2E Test (NOT COMPLETED)

> **Consider:** Lines 557-640 specify creating `e2e/error-scenarios.e2e.ts` with at least 8 E2E tests for error scenarios. Does this file exist?
>
> **Think about:** The plan requires testing network errors, permission denials, backend errors, and recovery flows. Can these be verified without actual E2E test code?
>
> **Reflect:** The verification checklist (line 605-612) asks "At least 8 E2E tests for error scenarios". How many exist?

### Detox Configuration Issues

> **Consider:** Open `.detoxrc.js` and look at lines 15-16 and 20-21. The binaryPath references `YourApp.app` and `YourApp.xcworkspace`. What is the actual name of this application?
>
> **Think about:** Try running `detox build --configuration ios.sim.debug`. Will this work with placeholder values like "YourApp"?
>
> **Reflect:** Can Detox E2E tests run if the configuration points to non-existent paths?

### Task 5: E2E Framework Setup (PARTIALLY COMPLETE)

> **Consider:** Task 5 (lines 288-454) requires: "E2E framework installed", "Test utilities created", "Example E2E test passes". Which of these three requirements are actually met?
>
> **Think about:** The verification checklist (line 418-425) includes "Example E2E test passes" and "E2E tests can run locally". Can you run an example E2E test with the current setup?
>
> **Reflect:** Is having configuration files and documentation the same as having a "working" E2E framework?

### Integration Test Quality Assessment

> **Consider:** Despite the configuration issues, 47 integration tests are passing (auth-flow: 16, recording-flow: 13, meditation-flow: 10, example: 8). What does this say about the quality of Tasks 1-4?
>
> **Think about:** The integration tests test real Context providers and multi-component interactions. This is exactly what Task 1-4 specified. Are these tasks well-executed despite the setup file issues?

### Test Suite Metrics vs Plan

> **Consider:** The plan's verification checklist (line 776-783) expects ~30 integration tests. You have 47 integration tests. Does this exceed expectations?
>
> **Think about:** The plan expects ~15 E2E tests (line 782). How many .e2e.ts files exist? What is 0 compared to 15?
>
> **Reflect:** If you complete 157% of integration tests (47/30) but 0% of E2E tests (0/15), what's the overall task completion?

### Success Criteria Review

> **Consider:** The Phase 5 success criteria (lines 7-13) state:
> - "Integration tests added for components with Context providers" ✓
> - "E2E testing framework set up (Detox, per ADR-10)" ⚠️ (configured but not functional)
> - "Critical user flows tested end-to-end" ✗ (no .e2e.ts files)
> - "All integration and E2E tests pass reliably" ✗ (2 failed suites, 0 E2E tests)
>
> **Reflect:** With 1/4 success criteria fully met and 1/4 partially met, can the phase be considered complete?

### Configuration vs Implementation

> **Consider:** You have excellent documentation (TESTING.md, e2e/README.md, __tests__/integration/README.md). You have configuration files (.detoxrc.js, e2e/jest.config.js). But how many actual E2E test files (.e2e.ts) exist?
>
> **Think about:** What's the difference between "infrastructure ready" and "tests implemented and passing"?
>
> **Reflect:** Can you ship an E2E test suite with zero test files?

### PHASE_5_SUMMARY.md Claims vs Reality

> **Consider:** PHASE_5_SUMMARY.md line 151 states "E2E Tests | 0* | N/A | N/A" with a note "*E2E tests configured but not executed (requires emulator/simulator)". Does "configured but not executed" mean the test files exist?
>
> **Think about:** The summary says "Status: ✅ COMPLETE". But Tasks 6 and 7 have no test files. Is this accurate?
>
> **Reflect:** Should completion summaries distinguish between "infrastructure ready" and "tests implemented"?

### Quantitative Task Completion

> **Consider:** Calculate completion:
> - Task 1 (Integration infrastructure): ✅ Complete (with minor config issues)
> - Task 2 (Auth flow integration): ✅ Complete (16 tests)
> - Task 3 (Recording flow integration): ✅ Complete (13 tests)
> - Task 4 (Meditation flow integration): ✅ Complete (10 tests)
> - Task 5 (E2E framework setup): ⚠️ 40% (config ✓, docs ✓, example test ✗)
> - Task 6 (User journey E2E): ❌ 0% (no test file)
> - Task 7 (Error scenarios E2E): ❌ 0% (no test file)
> - Task 8 (Verification): ⚠️ 50% (integration ✓, E2E ✗, docs ✓)
>
> **Reflect:** That's approximately 5.4 out of 8 tasks = 67.5% completion. Does this warrant approval?

### What Needs to be Fixed

> **Consider:** To achieve phase completion, what specific files need to be created or fixed?
> 1. Fix package.json to ignore `__tests__/integration/*.ts` utility files
> 2. Remove invalid import from `__tests__/integration/setup.ts` (line 8)
> 3. Create `e2e/complete-user-journey.e2e.ts` with ~10 tests
> 4. Create `e2e/error-scenarios.e2e.ts` with ~8 tests
> 5. Fix `.detoxrc.js` with actual app name (replace "YourApp")
>
> **Reflect:** Are these fixes achievable? Should they be completed before phase approval?

---

## Phase Verification

### Complete Phase Verification Checklist

- [ ] All 8 tasks completed successfully
- [ ] Integration tests added for Context flows
- [ ] E2E testing framework set up
- [ ] Critical user journey tested E2E
- [ ] Error scenarios tested E2E
- [ ] Overall frontend coverage: 75%+
- [ ] All tests pass reliably (3 consecutive runs)
- [ ] Test performance acceptable: <10 minutes

### Test Type Summary

| Test Type | Count | Execution Time | Purpose |
|-----------|-------|----------------|---------|
| Component Tests | ~100 | <2 min | Component behavior |
| Integration Tests | ~30 | <3 min | Context & multi-component |
| E2E Tests | ~15 | <5 min | User journeys |
| **Total** | **~145** | **<10 min** | **Comprehensive** |

### Integration Points Verified

1. **Components ↔ Context:**
   - Auth state shared across components
   - Recording state shared across components
   - Meditation state shared across components
   - History state synchronized

2. **Components ↔ Backend:**
   - Summary requests from recording
   - Meditation requests from summary
   - Error handling across flow
   - Retry logic working

3. **End-to-End Flows:**
   - Complete user journey working
   - Error scenarios handled gracefully
   - App state remains consistent
   - No crashes in critical flows

### Known Limitations or Technical Debt

1. **E2E Test Coverage:**
   - Not all screens tested E2E
   - Focus on critical user flows only
   - Consider adding more E2E tests if issues arise

2. **E2E Test Performance:**
   - E2E tests slower than unit/integration tests
   - Run E2E tests less frequently (CI/CD only or pre-release)
   - Consider parallel execution if needed

3. **Platform Coverage:**
   - E2E tests may run only on iOS or Android
   - Consider testing both platforms before releases
   - Document platform-specific issues

4. **Test Maintenance:**
   - E2E tests more brittle than unit tests
   - Keep E2E tests focused on critical flows
   - Update E2E tests when UI changes significantly

---

## Phase Complete

Once all tasks are complete and verification checks pass, this phase is finished.

**Final Commit:**
```
test(frontend): complete Phase 5 integration and E2E tests

- Add integration tests for auth, recording, and meditation flows with Context
- Set up E2E testing framework (Detox)
- Add E2E test for complete user journey
- Add E2E tests for critical error scenarios
- Overall frontend test coverage: 77%
- All 145 tests pass reliably
- Complete test suite runs in <10 minutes
- Comprehensive coverage of critical user flows

Frontend testing complete:
- Phase 4: Component tests (100 tests, 75% coverage)
- Phase 5: Integration + E2E tests (45 tests)
- Total: 145 tests, 77% coverage, <10 min execution
- Zero flaky tests, all flows tested

This completes Phase 5 of frontend test improvements.
```

**Next Phase:** [Phase 6: CI/CD Integration & Documentation](Phase-6.md)
