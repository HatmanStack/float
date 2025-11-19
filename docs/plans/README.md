# SAM Deployment Automation & Comprehensive Test Improvements

## Feature Overview

This implementation plan automates the deployment of the Float meditation app's serverless backend infrastructure using AWS SAM (Serverless Application Model) and establishes comprehensive test coverage for both backend and frontend codebases.

Currently, the Lambda backend requires manual deployment through the AWS Console: installing dependencies, creating zip files, uploading code, configuring environment variables, and managing Lambda layers. This manual process is error-prone, time-consuming, and makes it difficult to maintain environment parity between staging and production. The SAM automation will define all AWS resources (Lambda functions, S3 buckets, IAM roles/policies, API Gateway HTTP API, Lambda layers, and CloudWatch logs) as infrastructure-as-code, enabling single-command deployments with guaranteed environment consistency.

The testing improvements address current gaps in both backend and frontend test coverage. The backend currently has 39% overall coverage with critical areas like the Lambda handler at only 31% and AI services at 0%. The frontend has 7 test files covering approximately 12 components, with several tests failing or skipped. This plan establishes comprehensive test suites achieving 60%+ backend coverage and full frontend component coverage, along with integration and end-to-end tests to ensure reliability and confidence in deployments.

## Prerequisites

**Tools & Dependencies:**
- AWS SAM CLI (latest version)
- AWS CLI configured with appropriate credentials
- Python 3.12 (backend development)
- Node.js 24.x (frontend development)
- Docker (for SAM local testing)
- Git (version control)
- pytest and pytest-cov (backend testing)
- jest and @testing-library/react-native (frontend testing)

**AWS Prerequisites:**
- AWS account with permissions to create Lambda, S3, IAM, API Gateway, CloudWatch resources
- Pre-built FFmpeg Lambda layer ARN (maintained separately)
- API keys for external services (Google Gemini, OpenAI, ElevenLabs) for both environments

**Environment Setup:**
- Two AWS environments: Staging and Production
- Separate S3 buckets per environment
- Environment-specific API keys and configuration values

## Phase Summary

| Phase | Goal | Estimated Tokens |
|-------|------|------------------|
| [Phase 0](Phase-0.md) | Foundation - Architecture decisions, testing strategy, conventions | ~5,000 |
| [Phase 1](Phase-1.md) | SAM Infrastructure Setup - Template, parameters, deployment scripts | ~25,000 |
| [Phase 2](Phase-2.md) | Backend Test Improvements - Core Coverage (Handler & Services) | ~30,000 |
| [Phase 3](Phase-3.md) | Backend Test Improvements - Integration & E2E Tests | ~25,000 |
| [Phase 4](Phase-4.md) | Frontend Test Improvements - Fix Existing & Add Component Tests | ~30,000 |
| [Phase 5](Phase-5.md) | Frontend Test Improvements - Integration & E2E Tests | ~25,000 |
| [Phase 6](Phase-6.md) | CI/CD Integration & Documentation | ~15,000 |
| **Total** | | **~155,000** |

## Token Budget Notes

**Baseline Estimates:** ~155,000 tokens across all phases

**Contingency Planning:**
- Individual tasks may exceed estimates if debugging is required
- Estimates assume tests can be fixed/written without major code refactoring
- If component needs significant changes to be testable, task may grow 2-3x
- E2E framework setup (Phase 5) may require additional debugging (budget +5k tokens)
- Integration tests (Phase 3, 5) may hit API rate limits requiring retry logic (+2k tokens)

**Recommended Budget:** 175,000 - 200,000 tokens (includes 15-20% contingency)

**If Budget Exceeded:**
- Complete current phase before stopping
- Phases 1-3 are highest priority (infrastructure + backend)
- Phases 4-5 (frontend tests) can be deferred if needed
- Phase 6 (CI/CD) can be done incrementally

## Phase Breakdown

### Phase 0: Foundation
Establishes architectural decisions, testing strategies, and conventions that apply to all subsequent phases. No code implementation, purely planning and decision documentation.

### Phase 1: SAM Infrastructure Setup
Creates the complete SAM template with all AWS resources, parameter files for staging and production environments, deployment scripts, and validates deployment to staging environment. This establishes the foundation for automated infrastructure deployment.

### Phase 2: Backend Test Improvements - Core Coverage
Increases Lambda handler test coverage from 31% to 60%+, expands service layer tests to 80%+ coverage, and improves test fixtures and mocks. Focuses on unit tests for core business logic.

### Phase 3: Backend Test Improvements - Integration & E2E
Adds integration tests for AI services (Gemini, OpenAI TTS), end-to-end Lambda request-to-response tests, and audio processing tests. Ensures all components work together correctly.

### Phase 4: Frontend Test Improvements - Fix & Expand
Fixes failing/skipped tests in BackendSummaryCall and BackendMeditationCall components, adds tests for untested components (history, AuthScreen, AudioRecording, Notifications, etc.), and improves test reliability and patterns.

### Phase 5: Frontend Test Improvements - Integration & E2E
Adds integration tests for components with React Context and hooks, sets up end-to-end testing framework (Detox or similar), and creates critical user flow tests (authentication, recording, meditation generation).

### Phase 6: CI/CD Integration & Documentation
Updates GitHub Actions workflows to include SAM deployments, adds deployment status checks, updates all project documentation, and performs final verification of the complete system.

## Navigation

- [Phase 0: Foundation](Phase-0.md)
- [Phase 1: SAM Infrastructure Setup](Phase-1.md)
- [Phase 2: Backend Test Improvements - Core Coverage](Phase-2.md)
- [Phase 3: Backend Test Improvements - Integration & E2E](Phase-3.md)
- [Phase 4: Frontend Test Improvements - Fix & Expand](Phase-4.md)
- [Phase 5: Frontend Test Improvements - Integration & E2E](Phase-5.md)
- [Phase 6: CI/CD Integration & Documentation](Phase-6.md)

## Getting Started

1. Review Phase 0 thoroughly to understand architecture decisions and conventions
2. Proceed sequentially through phases - each phase builds on previous work
3. Complete all verification steps before moving to the next phase
4. Commit frequently with clear, conventional commit messages
5. Update this README if significant changes to the plan are needed
