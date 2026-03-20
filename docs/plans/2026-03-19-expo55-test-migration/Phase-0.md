# Phase 0: Foundation

## Architecture Decisions

### ADR-1: Move Jest config and test files into `frontend/` workspace

**Context:** Jest currently runs from the monorepo root with `modulePaths` pointing to `frontend/node_modules`. With npm workspaces hoisting, dependency resolution is ambiguous: packages may resolve from root or workspace `node_modules`. The `jest-expo` preset expects `react-native` resolvable from its own context.

**Decision:** Move the Jest configuration into `frontend/package.json` and relocate `tests/frontend/` to `frontend/tests/`. Root `npm test` will delegate to `cd frontend && npx jest`.

**Consequence:** Tests run in the workspace that owns the dependencies. `modulePaths` becomes unnecessary. The `@/` module alias simplifies to a relative path from within the frontend workspace.

### ADR-2: Migrate snapshot tests from `react-test-renderer` to `@testing-library/react-native`

**Context:** `react-test-renderer` is deprecated in React 19. Only one test file (`ThemedText-test.tsx`) uses it. `@testing-library/react-native` is already used by all other tests.

**Decision:** Rewrite `ThemedText-test.tsx` to use `@testing-library/react-native`'s `render()` and `toJSON()`. Delete the old snapshot and regenerate.

**Consequence:** Eliminates the React 19 deprecation warning. The new snapshot will have a different structure than the old one (RTLN output differs from `react-test-renderer`), which is expected.

### ADR-3: Fix Jest 30 teardown crash with `jest.clearAllTimers()`

**Context:** Jest 30 changed timer internals. React Native's `requestAnimationFrame` polyfill calls `jest.now()` after the test environment tears down, causing a crash. The current `jest.globals.js` polyfills `requestAnimationFrame` using `setTimeout`, which interacts poorly with Jest 30.

**Decision:** Remove the `requestAnimationFrame`/`cancelAnimationFrame` polyfill from `jest.globals.js`. Add a global `afterEach(() => { jest.clearAllTimers(); })` to the setup file to ensure no timers leak between tests. Keep the `__ExpoImportMetaRegistry` and `structuredClone` polyfills.

**Consequence:** The teardown crash is resolved by clearing timers before Jest tears down the environment, rather than trying to polyfill the animation frame API.

### ADR-4: Bump `@types/react` to `~19.1`

**Context:** `@types/react` is at `~18.2.45` in `frontend/package.json`. With React 19.2.4 installed, type mismatches occur (e.g., `FlatList` render item types, component prop types).

**Decision:** Bump `@types/react` from `~18.2.45` to `~19.1` in `frontend/package.json`.

**Consequence:** Type definitions match the installed React version. Any new type errors surfaced by this bump must be fixed (though the brainstorm indicates lint/typecheck already passes, so this should be minimal).

### ADR-5: Keep `react-test-renderer` installed but unused

**Context:** The brainstorm explicitly states: keep `react-test-renderer` package installed in both root and frontend `package.json`, but remove all usage.

**Decision:** Do not remove `react-test-renderer` from any `package.json`. Only remove `import` statements that reference it.

**Consequence:** No dependency tree changes from removing the package. Cleanup can happen in a separate PR.

### ADR-6: Add `EncodingType` to `expo-file-system` mock

**Context:** Some tests reference `EncodingType.Base64` from `expo-file-system`, but the unit test mock in `jest.setup.js` (which will become `frontend/jest.setup.js`) does not export `EncodingType`. The integration test setup already has it.

**Decision:** Add `EncodingType: { Base64: 'base64', UTF8: 'utf8' }` to the `expo-file-system` mock in the global setup file. This matches the integration setup's mock.

**Consequence:** Tests that reference `EncodingType` will resolve correctly.

## Testing Strategy

### Test Runner
- **Jest 30** via `jest-expo` preset (version `~55.0.10`)
- Run from `frontend/` workspace: `cd frontend && npx jest`
- Root `npm test` delegates: `cd frontend && npx jest --ci --runInBand --forceExit`

### Test Structure (after migration)
```
frontend/
  tests/
    unit/              # Component and hook unit tests
      utils/
        setup.ts       # setupFilesAfterEnv: mock clearing, console mocks
        testUtils.tsx   # renderWithProviders, mock data, re-exports RTLN
      __snapshots__/   # Regenerated snapshots
      *-test.tsx       # Unit test files
    integration/       # Cross-component integration tests
      setup.ts         # Integration-specific mocks
      test-utils.tsx   # Integration render helpers
      *-test.tsx       # Integration test files
    e2e/               # Detox E2E tests (NOT migrated, has own jest.config.js)
  jest.setup.js        # Moved from root: env vars, AsyncStorage mock, expo-file-system EncodingType
  jest.globals.js      # Moved from root: Expo 55 polyfills (minus rAF)
```

### Jest Configuration Location
- `frontend/package.json` `"jest"` section (mirrors current root config, adapted for workspace context)
- `rootDir`: `.` (relative to `frontend/`)
- `roots`: `["<rootDir>/tests"]` (plus `<rootDir>` for any co-located tests)
- `moduleNameMapper`: `{ "^@/(.*)$": "<rootDir>/$1" }` (simpler since rootDir is `frontend/`)
- No `modulePaths` needed (dependencies resolve naturally from workspace)

### Mock Strategy
- Global mocks in `jest.setup.js`: AsyncStorage, expo-file-system (with EncodingType)
- Unit setup in `tests/unit/utils/setup.ts`: console suppression, `beforeEach` mock clearing
- Integration setup in `tests/integration/setup.ts`: expo-notifications, expo-av, expo-permissions, Google Sign-In, navigation mocks
- Timer cleanup: global `afterEach` with `jest.clearAllTimers()` in `jest.globals.js`

## Commit Convention

All commits use conventional commit format:

```
type(scope): description

- Detail 1
- Detail 2
```

Types for this plan:
- `refactor(tests)` - moving files, restructuring config
- `fix(tests)` - fixing test failures, mocks, types
- `chore(deps)` - dependency version bumps

## CI Integration

- CI workflow (`.github/workflows/ci.yml`) runs `npm test -- --ci --forceExit` from root
- Root `npm test` will delegate to `cd frontend && npx jest`
- The `--ci --forceExit` flags passed via `--` will forward correctly through the delegation
- No CI workflow file changes needed if the root script delegation works correctly
- If double-flag issue occurs (root script has `--ci --runInBand --forceExit` and CI appends `--ci --forceExit`), remove flags from root script and let CI pass them
