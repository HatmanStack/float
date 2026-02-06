# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
