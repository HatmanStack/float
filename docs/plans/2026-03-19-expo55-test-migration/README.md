# Expo 55 Test Migration Plan

## Overview

The Float monorepo was upgraded from Expo 52 to Expo 55, bringing React 18.2 to 19.2.4, React Native 0.74.5 to 0.84.1, and Jest 29 to 30. Lint and typecheck pass, but 24 of 25 frontend tests are failing due to monorepo resolution issues, React 19 deprecations (`react-test-renderer`), Jest 30 runtime changes, and missing test mocks.

This plan fixes all test failures by restructuring the test infrastructure: moving Jest config and test files into the `frontend/` workspace for natural dependency resolution, migrating off deprecated `react-test-renderer`, fixing type mismatches from the `@types/react` 19 bump, and addressing Jest 30 teardown crashes. The e2e test directory structure is out of scope (Detox has its own jest config).

The goal is green CI with all 25 frontend tests passing under the new dependency versions.

## Prerequisites

- Node v24 LTS (nvm)
- `npm install --legacy-peer-deps` must succeed
- Current branch has the Expo 55 / React 19 / Jest 30 dependency bumps already applied
- Familiarity with npm workspaces, Jest configuration, and `@testing-library/react-native`

## Phase Summary

| Phase | Goal | Token Estimate |
|-------|------|----------------|
| 0 | Foundation: architecture decisions, testing strategy, conventions | ~3,000 |
| 1 | Relocate test infrastructure into frontend workspace, fix all 25 tests | ~30,000 |

## Navigation

- [Phase-0.md](./Phase-0.md) - Foundation (ADRs, conventions, testing strategy)
- [Phase-1.md](./Phase-1.md) - Implementation (move files, fix config, fix tests)
- [feedback.md](./feedback.md) - Review feedback tracking
- [brainstorm.md](./brainstorm.md) - Original brainstorm document
