# Phase 3: Frontend Tooling

**Status**: ESLint, Prettier, TypeScript configuration improvements
**Duration**: 2-3 days
**Effort**: ~15,000 tokens

**Prerequisites**: Phase 0 complete (frontend tools installed)

---

## Overview

Phase 3 configures and enforces code quality standards for the frontend using ESLint and Prettier. Unlike backend (Phases 1-2), we leverage existing Jest configuration and focus on linting and formatting.

**Key Objectives**:

1. Configure and run ESLint against all frontend code
2. Format code with Prettier
3. Fix TypeScript configuration issues
4. Refactor existing frontend code to match standards
5. Integrate checks into development workflow

**Phase Dependencies**:
- Phase 0 must be complete (.eslintrc.json, .prettierrc.json already created)
- Node.js v18+ verified
- npm dependencies installed

---

## Task 1: Run ESLint and Fix Violations

**Goal**: Configure ESLint and fix code style violations

**Files to create/modify**:
- Already created: `.eslintrc.json` (in Phase 0)
- Modify: `app/` and `components/` (all .ts and .tsx files - fix violations)
- Create: `eslint_errors.log` (baseline violations)

**Prerequisites**:
- Phase 0 complete (ESLint installed, .eslintrc.json created)
- Node modules installed

**Step-by-step Instructions**:

1. Verify ESLint installation
   - Run `npx eslint --version`
   - Should show version 8.x or higher
   - If error, run `npm install` in project root

2. Run ESLint to discover violations
   - Run `npx eslint app/ components/ --ext .ts,.tsx` to check frontend code
   - This shows all style violations found
   - Save output to `eslint_errors.log` as baseline

3. Understand common ESLint violations
   - `no-console`: console.log/warn/error in production code
   - `no-unused-vars`: Variables declared but not used
   - `react/prop-types`: Missing prop type validation (OK with TypeScript)
   - `@typescript-eslint/no-explicit-any`: Using `any` type
   - `@typescript-eslint/explicit-function-return-types`: Missing return types
   - `react-hooks/rules-of-hooks`: Improper hook usage

4. Use ESLint auto-fix for fixable violations
   - Run `npx eslint app/ components/ --ext .ts,.tsx --fix`
   - This automatically fixes:
     - Unused variables (comment with _ prefix if needed)
     - Simple formatting issues
     - Some style violations

5. Manually fix remaining violations
   - After auto-fix, check remaining errors: `npx eslint app/ components/ --ext .ts,.tsx`
   - Common manual fixes needed:

   **Remove unused variables**:
   ```typescript
   // Before
   const unusedVar = 42;

   // After (either use it or remove it)
   const usedVar = 42;
   console.log(usedVar);
   ```

   **Fix console statements in components**:
   ```typescript
   // Before - OK in development
   console.log('Debug:', data);

   // After - wrap in DEV check
   if (__DEV__) {
       console.log('Debug:', data);
   }
   ```

   **Fix prop types**:
   ```typescript
   // Before - no types
   function MyComponent(props) {
       return <Text>{props.title}</Text>;
   }

   // After - with types
   interface Props {
       title: string;
   }
   function MyComponent({ title }: Props): React.ReactNode {
       return <Text>{title}</Text>;
   }
   ```

6. Run ESLint again to verify
   - Should show 0 violations (or only warnings)
   - Warnings are OK (not errors)

**Verification Checklist**:

- [ ] `npx eslint app/ components/ --ext .ts,.tsx` shows 0 errors
- [ ] eslint_errors.log documents baseline
- [ ] Auto-fix was applied
- [ ] Manual fixes applied for remaining issues
- [ ] No unused variables remain
- [ ] Component props are properly typed
- [ ] Code quality improved

**Testing Instructions**:

```bash
# Check for linting violations
npx eslint app/ components/ --ext .ts,.tsx

# Auto-fix fixable violations
npx eslint app/ components/ --ext .ts,.tsx --fix

# Run tests to ensure no breaks
npm test

# Check again for remaining violations
npx eslint app/ components/ --ext .ts,.tsx
```

**Commit Message Template**:

```
refactor: fix ESLint violations in frontend code

- Run ESLint auto-fix on app/ and components/
- Manually fix remaining violations (unused vars, prop types)
- Document baseline ESLint errors
- Add type interfaces to components
- Remove dead code and console statements

All ESLint violations resolved. Tests pass.
```

**Token Estimate**: ~3,500 tokens

---

## Task 2: Format Code with Prettier

**Goal**: Apply consistent code formatting to all frontend files

**Files to create/modify**:
- Already created: `.prettierrc.json` (in Phase 0)
- Modify: All .ts, .tsx, .json, .md files in frontend

**Prerequisites**:
- Task 1 complete (ESLint violations fixed)
- Prettier installed (done in Phase 0)

**Step-by-step Instructions**:

1. Format all frontend code with Prettier
   - Run `npx prettier --write 'app/**/*.{ts,tsx}' 'components/**/*.{ts,tsx}'`
   - This formats TypeScript/React files
   - Also format JSON and Markdown: `npx prettier --write '**/*.{json,md}'`

2. Verify formatting applied
   - Run `npx prettier --check 'app/**/*.{ts,tsx}' 'components/**/*.{ts,tsx}'`
   - Should show no files need formatting
   - If violations remain, run write command again

3. Review formatted code
   - Check a few components to confirm formatting looks good
   - Prettier changes:
     - Line length to 100 chars
     - Single quotes for strings
     - Trailing commas in multiline structures
     - Consistent spacing

4. Ensure tests still pass
   - Run `npm test`
   - Prettier only changes formatting, not logic
   - Tests should all pass

**Verification Checklist**:

- [ ] `npx prettier --check 'app/**/*.{ts,tsx}' 'components/**/*.{ts,tsx}'` shows 0 violations
- [ ] `npx prettier --check '**/*.json'` shows 0 violations
- [ ] Code is consistently formatted
- [ ] Line length is ~100 characters
- [ ] All tests pass
- [ ] Formatting looks good visually

**Testing Instructions**:

```bash
# Format all frontend files
npx prettier --write 'app/**/*.{ts,tsx}' 'components/**/*.{ts,tsx}' '**/*.{json,md}'

# Verify formatting is correct
npx prettier --check 'app/**/*.{ts,tsx}' 'components/**/*.{ts,tsx}' '**/*.{json,md}'

# Run tests to ensure no breaks
npm test
```

**Commit Message Template**:

```
style: format frontend code with Prettier

- Format app/ and components/ with Prettier (line length 100)
- Format JSON and Markdown files
- Apply consistent code formatting throughout frontend
- No logic changes, formatting only

Frontend code is now consistently formatted per Prettier standards.
All tests pass.
```

**Token Estimate**: ~1,500 tokens

---

## Task 3: Fix TypeScript Configuration

**Goal**: Improve TypeScript configuration for better type safety and testing

**Files to create/modify**:
- Modify: `tsconfig.json` (exclude test files properly)
- Create: `tsconfig.test.json` (separate config for tests)

**Prerequisites**:
- Phase 0 complete
- Tasks 1-2 complete (code cleaned up)

**Step-by-step Instructions**:

1. Review current tsconfig.json
   - Should have `strict: true` already enabled
   - Should exclude test files
   - Review compiler options

2. Update main tsconfig.json
   - Add/verify `exclude` array with test files
   - Ensure main app code is compiled with strict settings
   - Example exclude patterns:
     - `**/__tests__/**`
     - `components/__tests__/**`
     - `**/*.test.ts`
     - `**/*.test.tsx`

3. Create tsconfig.test.json
   - Extends main tsconfig.json
   - Includes test files
   - May have looser settings for tests
   - Covers all test files only

4. Verify TypeScript compilation
   - Run `npx tsc --noEmit` (check types without emitting)
   - Should complete without errors
   - If errors, fix them in source code

5. Update package.json scripts (optional)
   - Keep existing scripts unchanged
   - Add script for type checking: `"type-check": "tsc --noEmit"`
   - Can be run manually or in CI

**Verification Checklist**:

- [ ] Main tsconfig.json has proper exclude array
- [ ] tsconfig.test.json exists and extends main config
- [ ] `npx tsc --noEmit` completes without errors
- [ ] Test files are not compiled as part of main build
- [ ] Expo still starts without errors: `npm start`

**Testing Instructions**:

```bash
# Check TypeScript compilation
npx tsc --noEmit

# Check specific file
npx tsc app/index.tsx --noEmit

# Start Expo to verify nothing is broken
npm start
```

**Commit Message Template**:

```
refactor: improve TypeScript configuration

- Fix tsconfig.json to properly exclude test files
- Create tsconfig.test.json for test-specific settings
- Verify all TypeScript compiles without errors
- Update strict type checking configuration

TypeScript compilation now works correctly for main code and tests.
```

**Token Estimate**: ~1,500 tokens

---

## Task 4: Refactor Frontend Components for Quality

**Goal**: Improve component quality and consistency

**Files to create/modify**:
- Modify: `app/` and `components/` (refactoring for quality)

**Prerequisites**:
- Tasks 1-3 complete (linting, formatting, TypeScript config fixed)

**Step-by-step Instructions**:

1. Review component structure
   - Open several component files
   - Check for consistent patterns
   - Look for opportunities to improve

2. Common refactoring patterns for React components:

   **Extract Prop Interfaces**:
   ```typescript
   // Before - inline props
   function Button(props: { label: string; onPress?: () => void }) {
       return <Pressable onPress={props.onPress}><Text>{props.label}</Text></Pressable>;
   }

   // After - named interface
   interface ButtonProps {
       label: string;
       onPress?: () => void;
   }
   function Button({ label, onPress }: ButtonProps): React.ReactNode {
       return <Pressable onPress={onPress}><Text>{label}</Text></Pressable>;
   }
   ```

   **Extract Custom Hooks**:
   ```typescript
   // Before - logic in component
   function AudioPlayer() {
       const [isPlaying, setIsPlaying] = useState(false);
       const [currentTime, setCurrentTime] = useState(0);
       const togglePlay = () => setIsPlaying(!isPlaying);
       // ... more logic
   }

   // After - extract hook
   function useAudioPlayer() {
       const [isPlaying, setIsPlaying] = useState(false);
       const [currentTime, setCurrentTime] = useState(0);
       const togglePlay = () => setIsPlaying(!isPlaying);
       return { isPlaying, currentTime, togglePlay };
   }
   ```

   **Add Return Type Annotations**:
   ```typescript
   // Before
   function MyComponent(props) {
       return <View><Text>Hello</Text></View>;
   }

   // After
   function MyComponent(props): React.ReactNode {
       return <View><Text>Hello</Text></View>;
   }
   ```

   **Simplify Complex Components**:
   - Break large components into smaller pieces
   - Extract sub-components if JSX is >30 lines
   - Extract constants from component body

3. Improve component consistency
   - All components should export function declaration or named export
   - All components should have Props interface if they take props
   - All components should have return type: `React.ReactNode`
   - Props should be destructured with type annotation

4. Add missing JSDoc comments
   - Complex components should have docstring
   - Hooks should have docstring
   - Example:
   ```typescript
   /**
    * Plays audio with playback controls
    * @param url - URL of audio to play
    * @param onComplete - Callback when audio finishes
    */
   function AudioPlayer({ url, onComplete }: AudioPlayerProps): React.ReactNode {
       // ...
   }
   ```

5. Run tests frequently
   - After each refactoring: `npm test`
   - Ensure tests still pass
   - If test fails, revert and try different approach

**Verification Checklist**:

- [ ] All components have Props interfaces
- [ ] All functions have return type annotations
- [ ] No `any` types used in components
- [ ] Prop destructuring is consistent
- [ ] Complex logic is extracted to hooks
- [ ] Components are single responsibility
- [ ] All tests pass: `npm test`
- [ ] ESLint still passes: `npx eslint app/ components/`
- [ ] Prettier still formats correctly

**Testing Instructions**:

```bash
# Run tests after each refactoring
npm test

# Verify linting still passes
npx eslint app/ components/ --ext .ts,.tsx

# Verify formatting is still correct
npx prettier --check 'app/**/*.{ts,tsx}' 'components/**/*.{ts,tsx}'

# Type check
npx tsc --noEmit
```

**Commit Message Template**:

```
refactor: improve frontend component quality

- Extract prop interfaces for all components
- Add return type annotations
- Extract custom hooks for reusable logic
- Improve component consistency and clarity
- Add JSDoc comments to complex components

All tests pass. Code is more consistent and maintainable.
```

**Token Estimate**: ~4,000 tokens

---

## Task 5: Create Frontend Quality Guidelines

**Goal**: Document frontend standards and provide tools for developers

**Files to create/modify**:
- Create: `FRONTEND_QUALITY.md` (frontend standards)
- Create: `check_frontend_quality.sh` (script for quality checks)

**Prerequisites**:
- Tasks 1-4 complete

**Step-by-step Instructions**:

1. Create FRONTEND_QUALITY.md
   - Document ESLint standards and rules
   - Document Prettier formatting standards
   - Document TypeScript practices
   - Document component patterns
   - Include good/bad code examples
   - Reference existing patterns in codebase

2. Create check_frontend_quality.sh script
   - Bash script that runs all frontend checks
   - Runs: tests → type-check → lint → format-check
   - Make it executable: `chmod +x check_frontend_quality.sh`
   - Helpful for developers before committing

3. Add quality check scripts to package.json
   - Add script: `"type-check"`: `tsc --noEmit`
   - Add script: `"quality"`: runs all checks
   - Already has: lint, lint:fix, format, format:check (from Phase 0)

4. Document component patterns in FRONTEND_QUALITY.md
   - Component structure template
   - Props interface pattern
   - Hook pattern
   - Testing pattern
   - Import organization

5. Update main README with frontend quality info
   - Reference FRONTEND_QUALITY.md
   - Quick checklist before committing
   - Link to detailed documentation

**Verification Checklist**:

- [ ] FRONTEND_QUALITY.md exists and is comprehensive
- [ ] check_frontend_quality.sh is executable and runs all checks
- [ ] Each check runs without errors
- [ ] Documentation is clear with examples
- [ ] README updated with quality information

**Testing Instructions**:

```bash
# Run all frontend quality checks
./check_frontend_quality.sh

# Or individually
npm test
npm run type-check
npm run lint
npm run format:check

# Or with separate script
npm run quality
```

**Commit Message Template**:

```
docs: add frontend quality guidelines and tooling

- Create FRONTEND_QUALITY.md with standards and patterns
- Create check_frontend_quality.sh for verification
- Add npm scripts for quality checking
- Document component patterns and best practices
- Update README with quality information

Developers can now easily verify frontend quality locally.
```

**Token Estimate**: ~2,500 tokens

---

## Summary & Verification

**Phase 3 Completion Checklist**:

- [ ] Task 1: ESLint violations fixed (0 errors)
- [ ] Task 2: Code formatted with Prettier (100% formatted)
- [ ] Task 3: TypeScript configuration fixed
- [ ] Task 4: Components refactored for quality
- [ ] Task 5: Quality guidelines and tools documented
- [ ] All tests pass: `npm test`
- [ ] All quality checks pass:
  - `npx eslint app/ components/` → 0 errors
  - `npx prettier --check 'app/**/*.{ts,tsx}'` → no changes needed
  - `npx tsc --noEmit` → 0 errors

**Code Quality Metrics**:

- ✅ 100% ESLint compliant
- ✅ 100% Prettier formatted
- ✅ 100% TypeScript type-safe
- ✅ All components have Props interfaces
- ✅ All functions have return type annotations

**When all tasks complete**:

1. Run full quality check: `./check_frontend_quality.sh`
2. Verify all checks pass
3. Commit Phase 3 changes
4. **Proceed to Phase 4: CI/CD Pipeline**

---

## Notes

- Phase 3 is independent of Phases 1-2 (can be done in parallel)
- Frontend already uses Jest (Phase 0 task notes this)
- Expo's existing configuration is preserved
- Focus is on tooling, not major refactoring
- Changes are incremental and low-risk

**Total Phase 3 Effort**: ~15,000 tokens

**Blocked By**: Phase 0 (tools must be installed)

**Blocks**: Phase 4 (CI/CD uses configured tools)

---

**Ready to continue? When Phase 3 is complete, proceed to [Phase 4: CI/CD Pipeline](./Phase-4.md)**
