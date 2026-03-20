# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-03-20

### Changed
- Upgraded Expo 52→55, React 18.2→19.2, React Native 0.74→0.84, Jest 29→30
- Migrated test infrastructure from monorepo root into frontend/ workspace
- Replaced deprecated react-test-renderer with @testing-library/react-native
- Jest config uses projects to separate unit and integration test environments
- Bumped @types/react from ~18.2 to ~19.1 for React 19 compatibility
- ESLint migrated to flat config; test files now linted with relaxed rules
- lint-staged extended to cover JS/JSX files under frontend/
- Root npm test delegates to frontend workspace

### Fixed
- Jest 30 teardown crashes from requestAnimationFrame (timer cleanup in afterEach)
- Expo 55 globals (TextEncoder, structuredClone, __ExpoImportMetaRegistry) polyfilled for Jest
- AsyncStorage mock store leak between test files via __resetStore
- Integration test setup.ts wired to run via Jest projects setupFilesAfterEnv
- expo-file-system mock extended with EncodingType.Base64

## [1.1.0] - 2026-03-15

### Added
- Changelog-driven release automation: pushing CHANGELOG.md to main creates tags and GitHub releases
- Docker setup for backend development with Dockerfile and compose
- Contributing guide, PR template, and `.env.example` files
- Commitlint with conventional commits enforcement and husky pre-commit hooks
- One-command `npm run setup` for development environment
- End-to-end handler test for summary flow
- Dockerfile linting (hadolint) in CI pipeline

### Fixed
- Backend test reliability: mock Lambda async invocation properly in unit tests
- Unsafe SummaryResponse-to-Incident cast replaced with explicit mapping
- S3 failure handling: raise on `_save_job` errors
- FFmpeg subprocess timeouts for streaming and audio mixing
- S3 `list_objects` pagination for large result sets
- Deprecated `expo-permissions` replaced with `expo-notifications` API

### Changed
- Backend settings converted to Pydantic BaseSettings
- Legacy request wrapper layer removed in favor of direct Pydantic validation
- Removed unused domain model layer, exception classes, and dead code
- Consolidated three frontend polling functions into one
- Deduplicated FFmpeg pipeline in `combine_voice_and_music`
- Expanded ruff rules to catch dead code and security patterns
- Structured logging replaces all `print()` calls in backend
- Documentation overhauled: API schemas, architecture, test READMEs, CLAUDE.md

## [1.0.0] - 2026-02-05

### Added
- Adjustable meditation duration (3, 5, 10, 15, 20 min) with dynamic HLS fade (#9)
- HLS streaming for real-time meditation playback (#7)
- Async meditation generation with job polling
- SEO optimization for web
- Append-only fade segments for glitch-free HLS streaming
- Circuit breaker pattern for external service calls
- TTL cache for music list and job data
- Download service for offline meditation access

### Fixed
- Code hygiene: debug prints removed, logging standardized (#10)
- HLS streaming playback and audio mixing improvements
- Security dependency updates (protobuf CVE)
- ESLint warnings and test failures resolved

### Changed
- Refactored "incidents" to "floats/stressful moments" (#11)
- Code quality improvements: type rigor, defensiveness, performance
- Deployment and infrastructure updates (#6)
- Normalized amix filters for consistent volume levels
