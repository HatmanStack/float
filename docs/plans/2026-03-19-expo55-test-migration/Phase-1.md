# Phase 1: Relocate Test Infrastructure and Fix All Tests

## Phase Goal

Move the Jest configuration and all frontend test files from the monorepo root into the `frontend/` workspace, fix the `jest.globals.js` and `jest.setup.js` files for Jest 30 / Expo 55 compatibility, migrate the one `react-test-renderer` usage to `@testing-library/react-native`, bump `@types/react`, and verify all 25 tests pass.

**Success criteria:**
- All test files live under `frontend/tests/` (not `tests/frontend/`)
- Jest config lives in `frontend/package.json`
- `npm test` from root delegates to frontend and passes
- `npm test -- --ci --forceExit` (as CI runs it) passes with all 25 tests green
- No `react-test-renderer` imports remain in test files
- No `requestAnimationFrame` polyfill in globals

**Estimated tokens:** ~30,000

## Prerequisites

- Expo 55 / React 19 / Jest 30 dependency bumps already in `package.json` files
- `npm install --legacy-peer-deps` succeeds
- Read Phase-0.md for architecture decisions

## Tasks

---

### Task 1: Move test files from `tests/frontend/` to `frontend/tests/`

**Goal:** Relocate all frontend test files into the frontend workspace so they resolve dependencies naturally from `frontend/node_modules`.

**Files to Modify/Create:**
- `frontend/tests/` - New location for all test files (entire directory tree)
- `tests/frontend/` - Will be deleted after move

**Prerequisites:**
- None (first task)

**Implementation Steps:**
1. Use `git mv` to move `tests/frontend/unit/` to `frontend/tests/unit/`
2. Use `git mv` to move `tests/frontend/integration/` to `frontend/tests/integration/`
3. Use `git mv` to move `tests/frontend/e2e/` to `frontend/tests/e2e/`
4. Verify the internal directory structure is preserved: `unit/utils/setup.ts`, `unit/utils/testUtils.tsx`, `unit/__snapshots__/`, `integration/setup.ts`, `integration/test-utils.tsx`, `e2e/jest.config.js`
5. If the `tests/` root directory is now empty (or only contains non-frontend dirs), leave it. If `tests/frontend/` is now empty, remove it.
6. Check if any `import` paths within the moved test files reference other test files using relative paths that need updating. Since the internal structure is preserved, relative imports between test files should not change. But verify.

**Verification Checklist:**
- [x] `frontend/tests/unit/` contains all unit test files (count should be ~20 files)
- [x] `frontend/tests/integration/` contains all integration test files and utils
- [x] `frontend/tests/e2e/` contains e2e test files and its own jest.config.js
- [x] `tests/frontend/` directory no longer exists
- [x] `git status` shows renames, not delete+add

**Testing Instructions:**
- No tests to run yet (Jest config still points to old paths)

**Commit Message Template:**
```text
refactor(tests): move tests/frontend/ to frontend/tests/

- Relocate all frontend test files into the frontend workspace
- Enables natural dependency resolution from workspace node_modules
- Internal directory structure preserved
```

---

### Task 2: Move and fix `jest.globals.js`

**Goal:** Move the Jest globals polyfill file into `frontend/` and fix it for Jest 30 compatibility by removing the `requestAnimationFrame` polyfill and adding timer cleanup.

**Files to Modify/Create:**
- `frontend/jest.globals.js` - Moved and modified from root `jest.globals.js`
- `jest.globals.js` (root) - Will be deleted

**Prerequisites:**
- Task 1 complete

**Implementation Steps:**
1. Create `frontend/jest.globals.js` with the following content:
   - Keep the `__ExpoImportMetaRegistry` polyfill (lines 4-8 of current file)
   - Keep the `structuredClone` polyfill (lines 10-12 of current file)
   - **Remove** the `requestAnimationFrame` and `cancelAnimationFrame` polyfills (lines 15-16 of current file) - these cause Jest 30 teardown crashes
   - Add a global `afterEach` that calls `jest.clearAllTimers()` to prevent timer leaks between tests
2. Delete the root `jest.globals.js`

**The new `frontend/jest.globals.js` should contain:**
```javascript
// Polyfill expo 55 globals for jest
// Must run before test framework loads modules

if (!globalThis.__ExpoImportMetaRegistry) {
  globalThis.__ExpoImportMetaRegistry = {
    register: () => {},
    get: () => ({}),
  };
}

if (typeof globalThis.structuredClone === 'undefined') {
  globalThis.structuredClone = (val) => JSON.parse(JSON.stringify(val));
}

// Clean up timers after each test to prevent Jest 30 teardown crashes.
// React Native's internal requestAnimationFrame can fire after environment
// teardown if timers are not cleared.
afterEach(() => {
  jest.clearAllTimers();
});
```

**Verification Checklist:**
- [x]`frontend/jest.globals.js` exists with the polyfills and `afterEach` timer cleanup
- [x]No `requestAnimationFrame` or `cancelAnimationFrame` assignment in the file
- [x]Root `jest.globals.js` is deleted

**Testing Instructions:**
- No tests to run yet (Jest config not yet updated)

**Commit Message Template:**
```text
fix(tests): move jest.globals.js to frontend, remove rAF polyfill

- Remove requestAnimationFrame polyfill that causes Jest 30 teardown crash
- Add afterEach jest.clearAllTimers() to prevent timer leaks
- Keep __ExpoImportMetaRegistry and structuredClone polyfills
```

---

### Task 3: Move and fix `jest.setup.js`

**Goal:** Move the Jest setup file into `frontend/` and add the missing `EncodingType` to the `expo-file-system` mock.

**Files to Modify/Create:**
- `frontend/jest.setup.js` - Moved and modified from root `jest.setup.js`
- `jest.setup.js` (root) - Will be deleted

**Prerequisites:**
- Task 1 complete

**Implementation Steps:**
1. Create `frontend/jest.setup.js` with the contents of the current root `jest.setup.js`
2. Add an `expo-file-system` mock block after the AsyncStorage mock. The mock should include:
   - `readAsStringAsync`: `jest.fn().mockResolvedValue('base64-encoded-data')`
   - `writeAsStringAsync`: `jest.fn().mockResolvedValue(undefined)`
   - `deleteAsync`: `jest.fn().mockResolvedValue(undefined)`
   - `getInfoAsync`: `jest.fn().mockResolvedValue({ exists: true, size: 1024 })`
   - `documentDirectory`: `'file:///mock-document-directory/'`
   - `cacheDirectory`: `'file:///mock-cache-directory/'`
   - `EncodingType`: `{ Base64: 'base64', UTF8: 'utf8' }`
3. Delete the root `jest.setup.js`

**Note:** The integration tests already mock `expo-file-system` in their own `setup.ts` with `EncodingType`. The global mock ensures unit tests that reference `EncodingType` also work. If the integration setup re-mocks `expo-file-system`, the integration mock will take precedence (Jest mock behavior: later `jest.mock()` calls override earlier ones for the same module).

**Verification Checklist:**
- [x]`frontend/jest.setup.js` exists with AsyncStorage mock and expo-file-system mock (including EncodingType)
- [x]Root `jest.setup.js` is deleted
- [x]Environment variables (`EXPO_PUBLIC_LAMBDA_FUNCTION_URL`, `TZ`) are set

**Testing Instructions:**
- No tests to run yet (Jest config not yet updated)

**Commit Message Template:**
```text
fix(tests): move jest.setup.js to frontend, add expo-file-system mock

- Add EncodingType to expo-file-system mock for unit tests
- Keep AsyncStorage mock and env var setup
```

---

### Task 4: Update `frontend/package.json` — add test deps and bump `@types/react`

**Goal:** Add test-related devDependencies to the frontend workspace and bump `@types/react` to match React 19.

**Files to Modify/Create:**
- `frontend/package.json` - Add devDependencies, add test script

**Prerequisites:**
- None (can run in parallel with Tasks 1-3)

**Implementation Steps:**
1. Add the following to `frontend/package.json` `devDependencies`:
   - `"jest": "^30.3.0"` (match root version)
   - `"jest-expo": "~55.0.10"` (match root version)
   - `"@testing-library/react-native": "^13.2.0"` (match root version)
   - `"@types/jest": "^29.5.12"` (match root version — note: @types/jest 29 works with Jest 30)
2. Bump existing `@types/react` from `"~18.2.45"` to `"~19.1"`
3. Add a `"test"` script to `frontend/package.json` scripts:
   ```json
   "test": "jest"
   ```
4. Do NOT remove `react-test-renderer` from frontend devDependencies (per ADR-5)

**Verification Checklist:**
- [x]`frontend/package.json` has `jest`, `jest-expo`, `@testing-library/react-native`, `@types/jest` in devDependencies
- [x]`@types/react` is `"~19.1"` (not `"~18.2.45"`)
- [x]`"test": "jest"` script exists
- [x]`react-test-renderer` is still in devDependencies

**Testing Instructions:**
- Run `npm install --legacy-peer-deps` from monorepo root and verify it succeeds

**Commit Message Template:**
```text
chore(deps): add test deps to frontend, bump @types/react to ~19.1

- Add jest, jest-expo, @testing-library/react-native, @types/jest to frontend
- Bump @types/react from ~18.2.45 to ~19.1 for React 19 compat
```

---

### Task 5: Create Jest config in `frontend/package.json`

**Goal:** Add a Jest configuration section to `frontend/package.json` that mirrors the current root config but adapted for the workspace context.

**Files to Modify/Create:**
- `frontend/package.json` - Add `"jest"` config section

**Prerequisites:**
- Task 1 (test files are in `frontend/tests/`)
- Task 2 (jest.globals.js is in `frontend/`)
- Task 3 (jest.setup.js is in `frontend/`)

**Implementation Steps:**
1. Add a `"jest"` section to `frontend/package.json` with:

```json
{
  "jest": {
    "preset": "jest-expo",
    "roots": [
      "<rootDir>/tests",
      "<rootDir>"
    ],
    "testMatch": [
      "**/*-test.tsx",
      "**/*-test.ts"
    ],
    "setupFiles": [
      "./jest.globals.js",
      "./jest.setup.js"
    ],
    "setupFilesAfterEnv": [
      "./tests/unit/utils/setup.ts"
    ],
    "testPathIgnorePatterns": [
      "/node_modules/",
      "/tests/unit/utils/",
      "/tests/integration/setup.ts",
      "/tests/integration/test-utils.tsx",
      "/tests/e2e/"
    ],
    "moduleNameMapper": {
      "^@/(.*)$": "<rootDir>/$1"
    }
  }
}
```

Key differences from the old root config:
- `rootDir` is implicitly `.` (relative to `frontend/`)
- `roots` changed from `["<rootDir>/tests/frontend", "<rootDir>/frontend"]` to `["<rootDir>/tests", "<rootDir>"]`
- `setupFiles` paths are now `./jest.globals.js` and `./jest.setup.js` (local to frontend)
- `setupFilesAfterEnv` path updated to `./tests/unit/utils/setup.ts`
- `testPathIgnorePatterns` updated to reflect new paths
- `moduleNameMapper` simplified: `"^@/(.*)$": "<rootDir>/$1"` (since rootDir IS frontend)
- **No `modulePaths`** — dependencies resolve naturally from the workspace
- Added `/tests/e2e/` to `testPathIgnorePatterns` so Detox tests don't run under the normal Jest config

**Verification Checklist:**
- [x]`frontend/package.json` has a `"jest"` section
- [x]No `modulePaths` in the config
- [x]`moduleNameMapper` maps `@/` to `<rootDir>/` (not `<rootDir>/frontend/`)
- [x]`setupFiles` point to local `./jest.globals.js` and `./jest.setup.js`
- [x]`testPathIgnorePatterns` includes `/tests/e2e/`

**Testing Instructions:**
- From `frontend/`, run `npx jest --listTests` and verify it finds the expected test files (unit + integration, not e2e, not utils)

**Commit Message Template:**
```text
refactor(tests): add Jest config to frontend/package.json

- Configure jest-expo preset for workspace context
- Remove modulePaths (unnecessary when running from workspace)
- Simplify moduleNameMapper for @/ alias
- Ignore e2e tests in standard jest config
```

---

### Task 6: Update root `package.json` — delegate test script, clean devDeps

**Goal:** Change the root `npm test` script to delegate to the frontend workspace and remove test-related devDependencies from the root that are now in frontend.

**Files to Modify/Create:**
- `package.json` (root) - Update test script, remove devDeps

**Prerequisites:**
- Task 4 (frontend has its own test deps)
- Task 5 (frontend has Jest config)

**Implementation Steps:**
1. Change the root `"test"` script from:
   ```json
   "jest --passWithNoTests --ci --runInBand --forceExit"
   ```
   to:
   ```json
   "cd frontend && npx jest --passWithNoTests"
   ```
   **Rationale:** Remove `--ci --runInBand --forceExit` from the root script. CI already passes `--ci --forceExit` via `npm test -- --ci --forceExit`. Having them in both places could cause issues. The `--passWithNoTests` flag stays because it's a safe default for local dev. CI flags get appended by the CI workflow.

2. Remove these devDependencies from root `package.json` (they are now in frontend or unused):
   - `@testing-library/react-native`
   - `@types/jest`
   - `@types/react-test-renderer`
   - `jest`
   - `jest-expo`
   - `react` (only needed at root for jest resolution, now resolved from frontend)
   - `react-dom` (same reason)
   - `react-native` (same reason)
   - `react-test-renderer`

3. **Keep** these root devDependencies (not test-related):
   - `@commitlint/cli`
   - `@commitlint/config-conventional`
   - `aws-sdk`
   - `detox`
   - `expo` (may be needed for workspace tooling)
   - `husky`
   - `lint-staged`
   - `prettier`

4. Remove the root `"jest"` config section entirely (lines 24-53 in current `package.json`)

**Important:** After removing root devDeps, run `npm install --legacy-peer-deps` to update `package-lock.json`.

**Verification Checklist:**
- [x]Root `package.json` `"test"` script delegates to frontend
- [x]No `"jest"` config section in root `package.json`
- [x]Test-related packages removed from root devDependencies
- [x]`@commitlint`, `husky`, `lint-staged`, `prettier` still in root devDependencies
- [x]`npm install --legacy-peer-deps` succeeds

**Testing Instructions:**
- Run `npm test` from root — it should delegate to frontend (may still fail if test files aren't fixed yet, but should start Jest from the right location)

**Commit Message Template:**
```text
refactor(tests): delegate root npm test to frontend workspace

- Remove test-related devDeps from root (now in frontend)
- Remove root jest config section
- Root npm test now runs: cd frontend && npx jest
```

---

### Task 7: Migrate ThemedText snapshot test from `react-test-renderer` to RTLN

**Goal:** Rewrite the only test that uses `react-test-renderer` to use `@testing-library/react-native` instead. Delete the old snapshot.

**Files to Modify/Create:**
- `frontend/tests/unit/ThemedText-test.tsx` - Rewrite test
- `frontend/tests/unit/__snapshots__/ThemedText-test.tsx.snap` - Delete

**Prerequisites:**
- Task 1 (files are in `frontend/tests/`)

**Implementation Steps:**
1. Delete `frontend/tests/unit/__snapshots__/ThemedText-test.tsx.snap`
2. Rewrite `frontend/tests/unit/ThemedText-test.tsx`:
   - Remove the `import renderer from 'react-test-renderer'` line
   - Import `render` from `@testing-library/react-native`
   - Change the test body to use `render(<ThemedText>Snapshot test!</ThemedText>).toJSON()` and `expect(tree).toMatchSnapshot()`

**The new test file should be:**
```typescript
import * as React from 'react';
import { render } from '@testing-library/react-native';

import { ThemedText } from '@/components/ThemedText';

it('renders correctly', () => {
  const tree = render(<ThemedText>Snapshot test!</ThemedText>).toJSON();

  expect(tree).toMatchSnapshot();
});
```

**Verification Checklist:**
- [x]No `react-test-renderer` import in `ThemedText-test.tsx`
- [x]Old snapshot file is deleted
- [x]Test uses `render` from `@testing-library/react-native`

**Testing Instructions:**
- This test will generate a new snapshot on first run. The new snapshot will differ from the old one (expected). Run with `--updateSnapshot` or `-u` flag on first run to create it.

**Commit Message Template:**
```text
fix(tests): migrate ThemedText test from react-test-renderer to RTLN

- Replace deprecated react-test-renderer with @testing-library/react-native
- Delete old snapshot (will be regenerated)
```

---

### Task 8: Run tests, diagnose remaining failures, and fix

**Goal:** Run the full test suite from the new location and fix any remaining failures. This is the catch-all task for issues that emerge from the migration.

**Files to Modify/Create:**
- Various test files and setup files as needed based on failures

**Prerequisites:**
- Tasks 1-7 complete

**Implementation Steps:**
1. Run `cd frontend && npx jest --verbose 2>&1` and capture output
2. Categorize failures:

   **Expected failure categories (from brainstorm):**
   - **Module resolution errors** — If any test can't resolve `@/` imports or node_modules, check `moduleNameMapper` and verify the dependency is in `frontend/package.json`
   - **`act()` warnings becoming errors** — React 19 is stricter about wrapping state updates in `act()`. If tests fail with `act()` errors, wrap the offending `fireEvent` or state update calls in `await act(async () => { ... })`
   - **Timer-related crashes** — If tests crash during teardown despite the `afterEach(jest.clearAllTimers)`, also add `jest.useRealTimers()` in the `afterEach`, or check if specific tests use `jest.useFakeTimers()` without cleaning up
   - **Type errors** — The `@types/react` bump to `~19.1` may surface type issues in test files. Fix type annotations as needed. Common issues: `ReactElement` vs `ReactNode`, `FlatList` render item type changes
   - **Missing mocks** — If a module is not mocked and tries to access native APIs, add the mock to the appropriate setup file (`jest.setup.js` for global, `tests/unit/utils/setup.ts` for unit, `tests/integration/setup.ts` for integration)

3. Fix each failure. For each fix:
   - Identify the root cause
   - Apply the minimal fix
   - Re-run the failing test to confirm it passes
   - Then run the full suite to check for regressions

4. If the `setupFilesAfterEnv` path (`./tests/unit/utils/setup.ts`) only applies to unit tests but integration tests also need it, consider whether integration tests need their own `setupFilesAfterEnv` or if the current setup is compatible. The current root config only lists the unit setup file, and integration tests have their own `setup.ts` that is imported by individual test files. Verify this pattern still works.

5. Check whether the integration `setup.ts` needs to be added to `setupFilesAfterEnv` or if it's imported directly by test files. Look at the integration test files to see if they `import './setup'` or rely on Jest config. Based on the current root config, `tests/frontend/integration/setup.ts` is in `testPathIgnorePatterns` (not run as a test) but NOT in `setupFilesAfterEnv` (not auto-loaded). This means integration tests must import it themselves. Verify this is the case and that it still works after the move.

**Verification Checklist:**
- [x]`cd frontend && npx jest --verbose` shows all 25 tests passing
- [x]No `act()` warnings in test output (or they are suppressed intentionally)
- [x]No timer-related crashes or open handle warnings
- [x]Snapshot file regenerated for ThemedText test

**Testing Instructions:**
- Run full suite: `cd frontend && npx jest --verbose`
- Run with CI flags: `cd frontend && npx jest --ci --forceExit`
- Run from root (as CI does): `npm test -- --ci --forceExit`

**Commit Message Template:**
```text
fix(tests): resolve remaining test failures after migration

- [describe specific fixes applied]
```

---

### Task 9: Verify CI compatibility

**Goal:** Ensure the root `npm test` delegation works correctly with the CI workflow's flag passing.

**Files to Modify/Create:**
- `.github/workflows/ci.yml` - Only if needed
- `package.json` (root) - Only if flag delegation needs adjustment

**Prerequisites:**
- Task 8 (all tests pass locally)

**Implementation Steps:**
1. Simulate what CI runs: `npm test -- --ci --forceExit`
2. Verify this correctly delegates to `cd frontend && npx jest --passWithNoTests --ci --forceExit`
3. Check whether `--` forwarding works correctly with the `cd frontend && npx jest` pattern:
   - When root script is `"cd frontend && npx jest --passWithNoTests"`, running `npm test -- --ci --forceExit` should result in `cd frontend && npx jest --passWithNoTests --ci --forceExit`
   - **Potential issue:** npm may not forward `--` args to compound shell commands correctly. Test this.
   - If forwarding doesn't work, change the root test script to use `npm -w frontend test --` instead: `"test": "npm -w frontend test"`. Then CI's `npm test -- --ci --forceExit` becomes `npm -w frontend test -- --ci --forceExit` which runs `jest --ci --forceExit` in the frontend workspace.
   - Alternative: use `npx --workspace=frontend jest` pattern
4. If the CI workflow file needs changes (unlikely but possible), update `.github/workflows/ci.yml`

**Verification Checklist:**
- [x]`npm test -- --ci --forceExit` from root passes all 25 tests
- [x]Flags are correctly forwarded to Jest (visible in verbose output)
- [x]`npm run check` from root passes (runs lint + tests)

**Testing Instructions:**
- `npm test -- --ci --forceExit` from root
- `npm run check` from root

**Commit Message Template:**
```text
fix(tests): ensure CI flag forwarding works with workspace delegation

- [describe any changes needed]
```

---

### Task 10: Final cleanup

**Goal:** Remove any leftover files and verify the clean state.

**Files to Modify/Create:**
- Delete root `jest.globals.js` if not already deleted
- Delete root `jest.setup.js` if not already deleted
- Delete `tests/frontend/` directory if not already deleted
- Delete `tests/` directory if it is now empty

**Prerequisites:**
- Task 9 (CI compatibility verified)

**Implementation Steps:**
1. Verify these root files are deleted (should have been done in Tasks 2-3):
   - `jest.globals.js`
   - `jest.setup.js`
2. Verify `tests/frontend/` is gone (should have been done in Task 1)
3. Check if `tests/` directory is now empty. If so, delete it. If it contains other directories (backend tests reference it), leave it.
4. Run `npm install --legacy-peer-deps` to ensure `package-lock.json` is up to date
5. Run `npm run check` for final validation (lint + all tests)

**Verification Checklist:**
- [x]No `jest.globals.js` or `jest.setup.js` at monorepo root
- [x]No `tests/frontend/` directory
- [x]`npm install --legacy-peer-deps` succeeds
- [x]`npm run check` passes (lint + frontend tests + backend tests)
- [x]`git status` shows a clean diff (only intended changes)

**Testing Instructions:**
- `npm run check` (full validation)

**Commit Message Template:**
```text
chore(tests): clean up leftover files from test migration

- Remove root jest config files
- Remove empty tests/frontend/ directory
```

---

## Phase Verification

After all tasks are complete:

1. **All 25 tests pass:** `npm test -- --ci --forceExit` from root
2. **Lint passes:** `npm run lint` from root
3. **Backend tests unaffected:** `npm run test:backend`
4. **Full check:** `npm run check`
5. **File locations are correct:**
   - `frontend/tests/unit/` has all unit tests
   - `frontend/tests/integration/` has all integration tests
   - `frontend/tests/e2e/` has e2e tests (unchanged, own config)
   - `frontend/jest.globals.js` and `frontend/jest.setup.js` exist
   - No test infrastructure at monorepo root
6. **No `react-test-renderer` imports** in any test file (package still installed per ADR-5)
7. **Git diff review:** Changes should be renames + config changes + one test rewrite. No runtime/app code changes.

### Known Limitations
- `react-test-renderer` package remains installed but unused (intentional, cleanup in separate PR)
- `@types/jest` is at `^29.5.12` even though Jest 30 is installed — this is a known compatibility gap; Jest 30 types are not yet published separately. The `29.x` types work for all APIs used in this codebase.
- E2e tests have their own `jest.config.js` and are not affected by this migration
