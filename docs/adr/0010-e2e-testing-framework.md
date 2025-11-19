# ADR-0010: E2E Testing Framework (Detox)

**Status**: Accepted

**Date**: 2025-11-19

**Context**: The Float React Native app needed end-to-end testing to validate complete user journeys (authentication, recording audio, generating meditations, playing audio). Traditional web E2E tools (Selenium, Playwright) don't work well with React Native. Mobile-specific E2E frameworks include Detox, Maestro, and Appium. We needed a framework that could test iOS and Android builds, integrate with our Jest testing infrastructure, and provide reliable tests without excessive flakiness.

**Decision**: Use Detox for React Native end-to-end testing, focusing on critical user flows only (authentication, recording, meditation generation).

**Alternatives Considered**:

1. **Maestro**
   - Pros: Simpler setup, no native builds needed, easier debugging, YAML-based tests, faster iteration
   - Cons: Newer tool (less mature ecosystem), less control over React Native internals, uncertain long-term support
   - Rejected: Too new with uncertain longevity, less community support

2. **Appium**
   - Pros: Cross-platform (mobile + web), industry standard, WebDriver protocol, extensive features
   - Cons: Slower (WebDriver overhead), more complex setup, not React Native-specific, verbose tests
   - Rejected: Overkill for RN-only app, slower test execution, complex configuration

3. **Playwright (experimental RN support)**
   - Pros: Popular web testing tool, good developer experience
   - Cons: RN support still experimental/incomplete, better suited for web applications
   - Rejected: Not mature enough for React Native testing

4. **Manual E2E Testing Only**
   - Pros: No framework complexity, flexible, can test edge cases
   - Cons: Not repeatable, slow, error-prone, doesn't scale, no CI integration
   - Rejected: Insufficient for production-quality testing

**Decision Rationale**:

**Detox Strengths**:
- **Built for React Native**: Native RN support, no WebViews or bridges required
- **Gray-box testing**: Can access React Native internals for faster, more reliable tests
- **Automatic synchronization**: Waits for RN to be idle (no manual `waitFor` everywhere)
- **Cross-platform**: Works with both iOS and Android
- **Jest integration**: Familiar testing patterns, reuses existing Jest config
- **Active development**: Maintained by Wix, good community support (used by major RN apps)

**Use Case Alignment**:
- Float only needs mobile app E2E (not web), so Detox's RN focus is ideal
- Critical user flows are well-defined (auth, record, meditation)
- E2E tests represent 10% of total test suite (per test pyramid)
- Tests run in CI on Android (Linux runners available, iOS requires macOS)

**Trade-offs Accepted**:
- **Requires native builds**: Slower CI builds (need to compile iOS/Android apps)
- **More complex setup**: Requires Xcode or Android Studio for local development
- **Learning curve**: More complex than pure JavaScript solutions (Maestro)
- **CI cost**: Expensive macOS runners for iOS tests (Android only in CI)

**Consequences**:

**Positive**:
- Realistic mobile testing (actual iOS/Android builds, not simulators)
- Automatic synchronization eliminates flaky waits
- Fast test execution (gray-box access to RN internals)
- Jest integration (familiar syntax, shared config)
- Catches platform-specific bugs (audio recording, file system)
- CI integration on Android (Linux runners are free/cheap)

**Negative**:
- Native build requirement slows CI (5-10 minutes to build app)
- More complex setup than web testing frameworks
- Requires Xcode (macOS) for iOS tests (expensive CI runners)
- Learning curve for Detox matchers and configuration
- Test debugging more difficult (emulator logs, native errors)

**Implementation**:

**Test Coverage** (E2E tests represent 10% of total tests):
- Authentication flow (sign in, sign out)
- Recording flow (record audio, submit)
- Meditation generation flow (generate, play, save)
- Error scenarios (network failures, validation errors)

**CI Strategy**:
- E2E tests run on **Android only** in CI (Linux runners)
- iOS E2E tests run locally only (manual testing before releases)
- E2E tests only run on **main branch** (not every PR, to save CI time)
- E2E tests marked as `continue-on-error` (informational, don't block merges)

**Configuration**:
- Test on Android API 31+ (Linux CI runners)
- Test on iOS 15+ (local development only)
- Use release builds for E2E tests (matches production)
- Mock backend API for deterministic E2E tests (no external dependencies)

**Test Organization**:
```
e2e/
├── complete-user-journey.e2e.ts    # Happy path end-to-end
├── error-scenarios.e2e.ts          # Error handling
└── README.md                       # Setup instructions
```

**Detox Matchers Used**:
- `by.id()` - Find elements by testID prop (preferred)
- `by.text()` - Find elements by visible text
- `by.type()` - Find elements by component type
- `element().tap()` - User interactions
- `expect(element()).toBeVisible()` - Assertions

**Future Considerations**:
- If web support added → consider Playwright for web E2E
- If CI budget allows → add iOS E2E tests on macOS runners
- If flakiness increases → review synchronization and waits
- If test suite grows → implement test sharding for parallel execution

**Alternative Solutions if Detox Fails**:
1. Migrate to Maestro if Detox becomes unmaintained
2. Use Appium if cross-platform testing (mobile + web) becomes required
3. Increase integration test coverage if E2E tests too unreliable

**Related ADRs**:
- ADR-0009: Comprehensive Testing Strategy
- ADR-0005: Testing Strategy (Phase 0)

**References**:
- [Detox Documentation](https://wix.github.io/Detox/)
- [e2e/README.md](../../e2e/README.md) - Setup and usage guide
- [.detoxrc.js](../../.detoxrc.js) - Configuration file
- [Why Detox for RN](https://wix.github.io/Detox/docs/introduction/how-detox-works)
