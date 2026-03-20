# Feature: Expo 55 Test Migration

## Overview
Dependabot bumped expo 52→55, react 18.2→19.2.4, react-native 0.74.5→0.84.1, and jest 29→30 in a single PR. Lint and typecheck pass after prior fixes (ESLint flat config migration, expo-file-system/legacy imports, removeNotificationSubscription → .remove(), ColorSchemeName narrowing). However, 24 of 25 frontend tests are failing due to a combination of monorepo resolution issues, React 19 deprecations, jest 30 runtime changes, and missing test mocks.

This work fixes all test failures by restructuring the test infrastructure: moving Jest config and test files into the frontend workspace for natural dependency resolution, migrating off deprecated `react-test-renderer`, fixing type mismatches, and addressing jest 30 teardown issues.

The goal is green CI with all 25 frontend tests passing under the new dependency versions.

## Decisions
1. Migrate snapshot tests from `react-test-renderer` to `@testing-library/react-native` — react-test-renderer is deprecated in React 19, and RTLN is already used everywhere else in the test suite
2. Move Jest config into `frontend/` — eliminates monorepo resolution issues by running Jest from the workspace that owns the dependencies, rather than fighting hoisting from root
3. Move `tests/frontend/` to `frontend/tests/` — tests live with their package, natural resolution, cleaner boundary
4. Clean root devDeps — remove all test-related packages from root (`jest`, `jest-expo`, `@testing-library/react-native`, `react-test-renderer`, `@types/jest`, `@types/react-test-renderer`, `react`, `react-dom`, `react-native`), root `npm test` delegates to frontend
5. Bump `@types/react` from `~18.2.45` to `~19.1` — fixes FlatList and other type mismatches from React 19 upgrade
6. Extend expo-file-system mock with `EncodingType: { Base64: 'base64' }` — tests reference Base64 encoding but mock doesn't export the constant
7. Remove `requestAnimationFrame` polyfill from `jest.globals.js`, add `jest.clearAllTimers()` in global `afterEach` — polyfilling rAF is flaky; clearing timers before teardown addresses the actual jest 30 crash
8. Keep `__ExpoImportMetaRegistry` and `structuredClone` polyfills — these fill genuine Expo 55 runtime APIs missing from the Jest VM
9. Keep `react-test-renderer` package installed (both root and frontend) — remove usage but don't remove the package yet
10. Delete old snapshots and regenerate after migration — RTLN produces different output, clean start needed
11. Preserve internal test directory structure — `unit/`, `integration/`, `e2e/` with existing utils stay as-is
12. Update both root `npm test` and CI — root script delegates to frontend; CI runs `npm test` from root so no workflow changes needed

## Scope: In
- Move `tests/frontend/` → `frontend/tests/` (same internal structure)
- Create `frontend/jest.config.js` (or jest section in `frontend/package.json`)
- Move `jest.globals.js` and `jest.setup.js` into frontend context
- Update root `package.json`: remove test devDeps, update `npm test` script to delegate
- Update `frontend/package.json`: add test devDeps (`jest`, `jest-expo`, `@testing-library/react-native`, `@types/jest`), bump `@types/react` to `~19.1`
- Migrate snapshot tests from `react-test-renderer` to `@testing-library/react-native`
- Delete and regenerate `__snapshots__/`
- Extend expo-file-system mock with `EncodingType`
- Replace `requestAnimationFrame` polyfill with `jest.clearAllTimers()` in `afterEach`
- Fix any new type errors from `@types/react` 19.1 bump
- Update `setupFilesAfterEnv` path references
- Update CI workflow if root `npm test` delegation isn't sufficient
- Verify all 25 tests pass

## Scope: Out
- Removing `react-test-renderer` package from `package.json` files
- Restructuring test directory internals (unit/integration/e2e layout stays)
- Backend test changes
- E2E (Detox) test changes
- New test coverage — this is about fixing existing tests, not writing new ones
- Any runtime/app code changes
- Deployment

## Open Questions
- The `modulePaths` config in root jest currently points to `frontend/node_modules` — once jest runs from `frontend/`, this should be unnecessary, but need to verify jest-expo preset resolves everything correctly without it
- The `--ci --forceExit` flags are passed both in root `npm test` script and again in CI (`npm test -- --ci --forceExit`) — may double up after delegation; need to decide where flags live
- Whether `jest.clearAllTimers()` alone is sufficient for the teardown crash, or if additional cleanup (e.g., `jest.restoreAllMocks()`) is needed alongside it

## Relevant Codebase Context
- `package.json` (root) — jest config at lines 24-53, devDeps at lines 55-73, workspaces config
- `frontend/package.json` — app deps, `@types/react: ~18.2.45` at line 48, `react-test-renderer` at line 54
- `jest.globals.js` — Expo 55 polyfills including the `requestAnimationFrame` polyfill to remove
- `jest.setup.js` — AsyncStorage mock, env vars
- `tests/frontend/unit/utils/setup.ts` — `setupFilesAfterEnv`, `beforeEach` mock clearing, console mocks
- `tests/frontend/unit/utils/testUtils.tsx` — `renderWithProviders()`, mock data, custom render helpers
- `tests/frontend/integration/setup.ts` — expo module mocks (expo-file-system missing Base64)
- `tests/frontend/integration/test-utils.tsx` — real provider wrappers, integration test utilities
- `.github/workflows/ci.yml` — line 46: `npm test -- --ci --forceExit`
- Snapshot tests using `react-test-renderer`: `ThemedText-test.tsx` and potentially others in `tests/frontend/unit/`
- `@testing-library/react-native` already used extensively in both unit and integration tests

## Technical Constraints
- npm workspaces hoisting means packages can resolve from either root or workspace `node_modules` — moving jest to frontend eliminates ambiguity
- `jest-expo` preset expects `react-native` resolvable from its context — running from frontend workspace ensures this
- React 19's strict mode and `act()` requirements are stricter than React 18 — some tests may need `act()` wrapping even after migrating off `react-test-renderer`
- jest 30 changed timer internals — `jest.now()` usage in react-native's `requestAnimationFrame` crashes after test environment teardown
- `--legacy-peer-deps` required for `npm install` — peer dep conflicts exist in the dependency tree
