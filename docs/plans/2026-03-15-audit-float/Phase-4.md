# Phase 4: [HYGIENIST] Code Quality & Pragmatism Quick Wins

## Phase Goal

Address the lowest-hanging remaining eval findings: stray `print()` calls, the unused `ServiceFactory`, the `Notifications.tsx` TODO stub, and the boolean-flag `useEffect` anti-pattern. These are all small, isolated changes that improve Code Quality (7 -> 9), Pragmatism (8 -> 9), and Problem-Solution Fit (8 -> 9).

**Success criteria:**
- Zero `print()` calls in backend production code
- `ServiceFactory` is either wired into `LambdaHandler` or removed
- `Notifications.tsx` TODO stub is implemented or the component is cleaned up
- Boolean-flag `useEffect` in `index.tsx` is replaced with direct async call
- `npm run check` passes
- `cd backend && uvx ruff check .` passes

**Estimated tokens:** ~20k

## Prerequisites

- Phases 0-3 completed and verified
- All checks passing

---

## Tasks

### Task 1: Replace `print()` calls with `logger` in backend

**Goal:** Remove 5 stray `print()` calls that bypass structured logging. The eval flags these under Code Quality (Hire: 7/10).

**Files to Modify:**
- `backend/src/utils/audio_utils.py` — lines 44, 79
- `backend/src/services/service_factory.py` — lines 50, 53
- `backend/src/utils/file_utils.py` — line 20

**Prerequisites:** None

**Implementation Steps:**

1. Open `backend/src/utils/audio_utils.py`
2. Add a logger import at the top of the file, after existing imports:
   ```python
   from ..utils.logging_utils import get_logger

   logger = get_logger(__name__)
   ```
   **Important:** Check if `logging_utils` is in the same package. Since this file is at `src/utils/audio_utils.py` and `logging_utils` is at `src/utils/logging_utils.py`, use a relative import:
   ```python
   from .logging_utils import get_logger

   logger = get_logger(__name__)
   ```
3. Replace line 44:
   ```python
   # Before:
   print(f"Error removing temporary file {file_path}: {e}")
   # After:
   logger.warning("Error removing temporary file", extra={"data": {"path": file_path, "error": str(e)}})
   ```
4. Replace line 79:
   ```python
   # Before:
   print(f"Error encoding audio file {file_path}: {e}")
   # After:
   logger.error("Error encoding audio file", extra={"data": {"path": file_path, "error": str(e)}})
   ```

5. Open `backend/src/services/service_factory.py`
6. Add a logger import at the top:
   ```python
   from ..utils.logging_utils import get_logger

   logger = get_logger(__name__)
   ```
7. Replace line 50:
   ```python
   # Before:
   print("All services validated successfully")
   # After:
   logger.info("All services validated successfully")
   ```
8. Replace line 53:
   ```python
   # Before:
   print(f"Service validation failed: {e}")
   # After:
   logger.error("Service validation failed", extra={"data": {"error": str(e)}})
   ```

9. Open `backend/src/utils/file_utils.py`
10. Add a logger import at the top:
    ```python
    from .logging_utils import get_logger

    logger = get_logger(__name__)
    ```
11. Replace line 20:
    ```python
    # Before:
    print(f"Error creating directory {directory_path}: {e}")
    # After:
    logger.error("Error creating directory", extra={"data": {"path": directory_path, "error": str(e)}})
    ```

**Verification Checklist:**
- [x] Zero `print()` calls remain in `backend/src/` (verify with `grep -rn "print(" backend/src/ --include="*.py"`)
- [x] All replacements use the structured `extra={"data": {...}}` format matching `logging_utils`
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [x] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Run `cd backend && uvx ruff check .`

**Commit Message Template:**
```
chore(backend): replace print() calls with structured logger

Replace 5 stray print() calls in audio_utils, service_factory, and
file_utils with structured logger calls using the existing
logging_utils pattern. Ensures all output goes through the
sensitive-data-redacting structured logger.
```

---

### Task 2: Remove unused `ServiceFactory` or wire it into `LambdaHandler`

**Goal:** The `ServiceFactory` class in `service_factory.py` is never imported outside its own file. `LambdaHandler.__init__` directly instantiates all services. The eval flags this under Pragmatism (Stress: 8/10). Remove the dead code.

**Files to Modify:**
- `backend/src/services/service_factory.py` — DELETE this file

**Prerequisites:** Task 1 complete (print calls replaced in this file)

**Implementation Steps:**

1. Verify `ServiceFactory` and `service_factory` are not imported anywhere:
   ```bash
   grep -rn "service_factory\|ServiceFactory" backend/src/ --include="*.py" | grep -v "service_factory.py"
   ```
   This should return nothing. If it does, wire the import instead of deleting.

2. Also check tests:
   ```bash
   grep -rn "service_factory\|ServiceFactory" backend/tests/ --include="*.py"
   ```
   If tests import it, those imports must be updated too.

3. If no references exist, delete `backend/src/services/service_factory.py`

4. Check `backend/src/services/__init__.py` — if it re-exports `ServiceFactory` or `service_factory`, remove that line

**Verification Checklist:**
- [x] No references to `ServiceFactory` or `service_factory` in `backend/src/` or `backend/tests/`
- [x] `backend/src/services/service_factory.py` is deleted
- [x] `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short` passes
- [x] `cd backend && uvx ruff check .` passes

**Testing Instructions:**
- Run `cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short`
- Verify no import errors: `cd backend && python -c "from src.handlers.lambda_handler import LambdaHandler; print('OK')"`

**Commit Message Template:**
```
chore(backend): remove unused ServiceFactory

Delete service_factory.py which defines ServiceFactory — a dependency
injection container never imported or used by LambdaHandler or any
other module. LambdaHandler directly instantiates all services.
```

---

### Task 3: Clean up `Notifications.tsx` TODO stub

**Goal:** The `Notifications.tsx` component has a `TODO: Implement push notification display UI` comment but the component actually has working registration and listener setup. The TODO is misleading — the component works but renders an empty `<View />`. Remove the TODO comment since notification display is a feature, not a code quality issue.

**Files to Modify:**
- `frontend/components/Notifications.tsx` — Remove TODO comment

**Prerequisites:** None

**Implementation Steps:**

1. Open `frontend/components/Notifications.tsx`
2. Remove line 6: `// TODO: Implement push notification display UI`
3. The component already:
   - Registers for push notifications using the modern `expo-notifications` API
   - Sets up notification listeners
   - Cleans up listeners on unmount
   - Returns `<View />` (invisible — notification display is handled by the OS)
4. The empty `<View />` is intentional — this component exists to register the notification handlers, not to render UI. No further changes needed.

**Verification Checklist:**
- [x] TODO comment removed
- [x] No other changes to the file
- [x] `npm run lint` passes
- [x] `npm test` passes

**Testing Instructions:**
- Run `npm run lint`
- Run `npm test`

**Commit Message Template:**
```
chore(frontend): remove misleading TODO from Notifications component

Remove "TODO: Implement push notification display UI" comment. The
component correctly handles push notification registration and
listeners. The empty View return is intentional — notification
display is handled by the OS, not this component.
```

---

### Task 4: Replace boolean-flag `useEffect` with direct async call in `index.tsx`

**Goal:** The `useSummarySubmission` pattern in `frontend/app/(tabs)/index.tsx` (lines 85-130) uses a boolean state flag (`summaryCall`) to trigger a `useEffect` that immediately resets the flag and runs async work. This is a React anti-pattern. Replace it with a direct async function call.

**Files to Modify:**
- `frontend/app/(tabs)/index.tsx` — Refactor `handleSummaryCall` / `summaryCall` pattern

**Prerequisites:** None

**Implementation Steps:**

1. Open `frontend/app/(tabs)/index.tsx`
2. Find the current pattern (approximately lines 82-130):
   ```tsx
   const [summaryCall, setSummaryCall] = useState(false);

   const handleSummaryCall = useCallback(async () => {
     setSummaryCall(true);
     setSubmitActivity(true);
   }, []);

   useEffect(() => {
     if (summaryCall) {
       setSummaryCall(false);
       const fetchData = async () => {
         // ... async work
       };
       fetchData();
     }
   }, [summaryCall, ...deps]);
   ```

3. Replace with a direct async call:
   ```tsx
   const handleSummaryCall = useCallback(async () => {
     setSubmitActivity(true);
     if (!URI && !separateTextPrompt) {
       setSubmitActivity(false);
       return;
     }
     try {
       let response: SummaryResponse;
       if (recording) {
         const base64_file = await StopRecording(recording);
         response = await BackendSummaryCall(
           base64_file ?? '',
           separateTextPrompt,
           user?.id ?? ''
         );
       } else {
         response = await BackendSummaryCall(URI, separateTextPrompt, user?.id ?? '');
       }
       setIncidentList((prevList) => [response as Incident, ...prevList]);
       onSubmitSuccess();
     } catch (error) {
       console.error('Failed to call summary lambda:', error);
     } finally {
       setSubmitActivity(false);
       router.push('/explore');
     }
   }, [URI, separateTextPrompt, recording, setIncidentList, user?.id, router, onSubmitSuccess]);
   ```

4. Remove the `summaryCall` state variable (`useState(false)` declaration)
5. Remove the entire `useEffect` block that depends on `summaryCall`
6. Remove the `useState` import for `summaryCall` only if no other `useState` calls remain (they will — `submitActivity` still uses it)

**Verification Checklist:**
- [x] No `summaryCall` state variable exists
- [x] No `useEffect` triggered by `summaryCall` flag
- [x] `handleSummaryCall` directly calls the async logic
- [x] All dependencies are in the `useCallback` dependency array
- [x] `npm run lint` passes (especially exhaustive-deps)
- [x] `npm test` passes

**Testing Instructions:**
- Run `npm run lint` — verify no exhaustive-deps warnings
- Run `npm test` — verify all tests pass
- Search tests for `summaryCall` to check if any test sets this state directly

**Commit Message Template:**
```
chore(frontend): replace boolean-flag useEffect with direct async call

Replace the summaryCall boolean-flag pattern (setState(true) ->
useEffect -> setState(false) -> async work) with a direct async
function call in handleSummaryCall. Eliminates an unnecessary render
cycle and simplifies the control flow.
```

---

## Phase Verification

After completing all 4 tasks:

1. Run the full check suite:
   ```bash
   npm run check
   ```

2. Run backend checks:
   ```bash
   cd backend && PYTHONPATH=. pytest tests/unit -v --tb=short
   cd backend && uvx ruff check .
   ```

3. Verify no print() calls remain:
   ```bash
   grep -rn "print(" backend/src/ --include="*.py"
   # Should return nothing
   ```

4. Verify ServiceFactory is removed:
   ```bash
   ls backend/src/services/service_factory.py
   # Should return "No such file or directory"
   ```

5. Verify no boolean-flag pattern:
   ```bash
   grep -n "summaryCall" frontend/app/\(tabs\)/index.tsx
   # Should return nothing
   ```

All checks must pass before proceeding to Phase 5.
