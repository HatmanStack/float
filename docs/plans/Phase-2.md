# Phase 2: Backend Code Quality

**Status**: Type checking, linting, formatting, and code modernization
**Duration**: 4-5 days
**Effort**: ~20,000 tokens

**Prerequisites**: Phase 1 complete

---

## Overview

Phase 2 enforces code quality standards across the backend using mypy (type checking), ruff (linting), and black (formatting). We also refactor existing code to match new standards and improve code quality incrementally.

**Key Objectives**:

1. Run mypy type checking and fix type errors
2. Run ruff linting and fix style violations
3. Format code with black
4. Refactor existing code to modern Python standards
5. Document code quality practices
6. Integrate quality checks into development workflow

**Phase Dependencies**:
- Phase 1 must be complete (tests written, code has type hints)
- Backend environment set up (venv, tools installed)
- Phase 0 prerequisites checked

---

## Task 1: Run Type Checking with mypy

**Goal**: Check for type errors and establish type-safe codebase baseline

**Files to create/modify**:
- Modify: `backend/src/` (all Python files - add type hints as needed)
- Create: `backend/mypy_errors.log` (document baseline errors)

**Prerequisites**:
- Phase 1 complete
- mypy installed in venv
- Type hints added to public APIs (Phase 1, Task 5)

**Step-by-step Instructions**:

1. Run mypy to discover type errors
   - Run `mypy backend/src/ --show-error-codes` from project root
   - Or `cd backend && mypy src/` to run from backend directory
   - This generates list of all type errors found

2. Document baseline errors
   - Save output to `mypy_errors.log`
   - This shows what needs to be fixed
   - Will be referenced during refactoring

3. Prioritize and fix type errors by file
   - Start with handlers/ (most important)
   - Move to services/ (critical business logic)
   - Then models/ (should already be mostly typed)
   - Last: utils/ (less critical)

4. For each file with errors:
   - Open file and review mypy error messages
   - Add missing type imports: `from typing import Optional, List, Dict, Any`
   - Add type hints to untyped function signatures
   - Use `Any` for truly ambiguous types (mypy allows this)
   - Use `Optional[Type]` for values that can be None
   - Use `List[Type]`, `Dict[str, Type]`, etc. for collections

5. Address common type errors:

   **Missing Return Type**:
   ```python
   # Before
   def process_request(data):
       return data

   # After
   def process_request(data: Dict[str, Any]) -> Dict[str, Any]:
       return data
   ```

   **Optional Values**:
   ```python
   # Before
   def get_config(key):
       return config.get(key)

   # After
   def get_config(key: str) -> Optional[str]:
       return config.get(key)
   ```

   **Generic Types**:
   ```python
   # Before
   def handle_errors(errors):
       return errors

   # After
   def handle_errors(errors: List[str]) -> List[str]:
       return errors
   ```

6. Run mypy again after fixes
   - Verify error count decreases
   - Aim for 0 errors by end of task
   - If remaining errors are unavoidable, add `# type: ignore` comment with explanation

7. Enable mypy in CI (optional for Phase 2)
   - Already configured in pyproject.toml
   - Will be tested in Phase 4 (CI/CD)

**Verification Checklist**:

- [ ] `mypy backend/src/ --show-error-codes` runs without errors
- [ ] All public function signatures have type hints
- [ ] All model fields are properly typed
- [ ] No `Any` types used without justification
- [ ] No `# type: ignore` comments (or documented why needed)
- [ ] mypy_errors.log documents baseline (pre-fixes)
- [ ] Existing tests still pass after type hint changes

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Check for type errors
mypy src/ --show-error-codes

# Show more verbose output
mypy src/ --show-error-codes --show-error-context

# Check specific file
mypy src/handlers/lambda_handler.py

# Verify tests still pass after type hint changes
pytest tests/ -v
```

**Commit Message Template**:

```
refactor: add comprehensive type hints and fix mypy errors

- Add type hints to all function signatures in handlers/
- Add type hints to service method signatures
- Fix type errors found by mypy type checker
- Document baseline mypy errors before fixes
- Use Optional for nullable values, List/Dict for collections

All functions now have complete type annotations.
Existing tests pass after type changes. Mypy runs with 0 errors.
```

**Token Estimate**: ~4,000 tokens

---

## Task 2: Lint Code with ruff

**Goal**: Find and fix style violations and potential bugs using modern Python linter

**Files to create/modify**:
- Modify: `backend/src/` (all Python files - fix linting issues)
- Create: `backend/ruff_errors.log` (document baseline violations)

**Prerequisites**:
- Task 1 complete (type hints added)
- ruff installed in venv

**Step-by-step Instructions**:

1. Run ruff to find violations
   - Run `ruff check backend/src/` from project root
   - Or `cd backend && ruff check src/` from backend directory
   - This shows all style and bug violations found

2. Document baseline violations
   - Save output to `ruff_errors.log`
   - Shows types of issues to fix
   - Helps track improvement

3. Use ruff's auto-fix feature
   - Run `ruff check backend/src/ --fix`
   - This automatically fixes most common issues:
     - Unused imports (remove them)
     - Import sorting (alphabetize imports)
     - Whitespace issues (extra blank lines, etc.)
     - Simple style violations

4. Manually review remaining violations
   - After auto-fix, check remaining errors with `ruff check backend/src/`
   - Fix remaining issues manually (usually semantic issues)
   - Common remaining issues:
     - Line too long (100 char limit)
     - Complexity warnings
     - Unused variables
     - Import order issues

5. Common fixes for ruff violations:

   **Unused Imports**:
   ```python
   # Before
   import os
   import sys
   from typing import List, Optional, Dict

   # After (ruff auto-fixes this)
   from typing import Optional
   ```

   **Long Lines**:
   ```python
   # Before
   response = service.generate_meditation_audio_with_background_music_and_metadata(request.text, request.duration)

   # After (break line)
   response = service.generate_meditation_audio_with_background_music_and_metadata(
       request.text, request.duration
   )
   ```

   **Import Sorting**:
   ```python
   # Before
   from src.models import AudioRequest
   import os
   from typing import Optional

   # After (ruff auto-fixes this)
   import os
   from typing import Optional
   from src.models import AudioRequest
   ```

6. Address specific ruff rules
   - E501: Line too long (use black to format, or break manually)
   - F401: Unused imports (remove or use them)
   - F841: Unused variables (remove or prefix with `_`)
   - I: Import sorting (ruff can auto-fix most)
   - B: Flake8-bugbear (actual bugs, fix these)

7. Run ruff again to verify
   - `ruff check backend/src/` should show 0 violations
   - If not, fix remaining issues manually

**Verification Checklist**:

- [ ] `ruff check backend/src/` shows 0 violations
- [ ] Auto-fix was applied: `ruff check backend/src/ --fix`
- [ ] Remaining manual fixes applied
- [ ] Imports are sorted correctly
- [ ] No unused imports remain
- [ ] No unused variables remain
- [ ] Code quality improved
- [ ] Existing tests still pass

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Check for violations
ruff check src/ --show-fixes

# Auto-fix common issues
ruff check src/ --fix

# Check again for remaining violations
ruff check src/

# Verify tests still pass
pytest tests/ -v
```

**Commit Message Template**:

```
refactor: fix ruff linting violations

- Auto-fix with ruff: unused imports, import sorting, whitespace
- Manually fix remaining violations (long lines, complexity)
- Document baseline linting errors
- Remove unused imports and variables
- Improve code quality and consistency

All ruff violations resolved. Tests pass. Code is more consistent.
```

**Token Estimate**: ~3,500 tokens

---

## Task 3: Format Code with black

**Goal**: Apply consistent code formatting using black formatter

**Files to create/modify**:
- Modify: `backend/src/` and `backend/tests/` (all Python files - format)

**Prerequisites**:
- Task 1-2 complete (types checked, linting done)
- black installed in venv

**Step-by-step Instructions**:

1. Format all backend code with black
   - Run `black backend/src/` to format source code
   - Run `black backend/tests/` to format test code
   - Black automatically reformats files according to its opinionated style
   - No manual decisions needed - black decides all formatting

2. Verify formatting was applied
   - Run `black --check backend/src/` to verify format
   - Should show 0 violations
   - If it shows violations, run `black backend/src/` again

3. Review formatted code
   - Code should be consistently formatted now
   - Check a few files to confirm formatting looks good
   - Formatting includes:
     - Line length at 100 characters (set in pyproject.toml)
     - Consistent quote style
     - Consistent spacing around operators
     - Proper blank lines between functions/classes

4. Black commonly changes:
   - Long lines are broken intelligently
   - Extra whitespace is removed
   - Function signatures are reformatted
   - Dictionary/list formatting is normalized

5. Ensure tests still pass
   - Run `pytest tests/ -v` to verify black didn't break code
   - Black only changes formatting, not logic, so tests should pass

**Verification Checklist**:

- [ ] `black --check backend/src/` shows 0 files need reformatting
- [ ] `black --check backend/tests/` shows 0 files need reformatting
- [ ] Code is visually consistent throughout
- [ ] Line length is ~100 characters max
- [ ] Spacing is consistent
- [ ] All tests pass after formatting
- [ ] No syntax errors introduced

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Format all code
black src/ tests/

# Verify formatting is correct
black --check src/ tests/

# Run tests to ensure no breaks
pytest tests/ -v
```

**Commit Message Template**:

```
style: format code with black

- Format backend/src/ with black (line length 100)
- Format backend/tests/ with black
- Apply consistent code formatting throughout
- No logic changes, formatting only

Code is now consistently formatted per black standards.
All tests pass. No functional changes.
```

**Token Estimate**: ~2,000 tokens

---

## Task 4: Refactor Code Based on Quality Feedback

**Goal**: Improve code quality based on mypy, ruff, and test feedback

**Files to create/modify**:
- Modify: `backend/src/` (refactoring based on issues found)

**Prerequisites**:
- Tasks 1-3 complete (type checking, linting, formatting done)
- Phase 1 tests passing

**Step-by-step Instructions**:

1. Review mypy errors fixed in Task 1
   - If `# type: ignore` comments were added, try to resolve them
   - Improve type hints where possible
   - Use more specific types instead of `Any`

2. Review code quality patterns
   - Look for repeated code that could be extracted
   - Look for long functions that could be broken up
   - Look for classes that violate single responsibility
   - Don't do major refactoring - keep changes small

3. Common refactoring patterns:

   **Extract Repeated Code**:
   ```python
   # Before
   def generate_audio_elevenlabs(text):
       response = client.synthesize(text, voice_id=VOICE_ID)
       return response.audio_bytes

   def generate_audio_openai(text):
       response = client.synthesize(text, voice_id=VOICE_ID)
       return response.audio_bytes

   # After
   def _generate_audio_base(client, text):
       response = client.synthesize(text, voice_id=VOICE_ID)
       return response.audio_bytes

   def generate_audio_elevenlabs(text):
       return _generate_audio_base(ELEVENLABS_CLIENT, text)
   ```

   **Simplify Long Functions**:
   ```python
   # Before - one 50-line function
   def handle_request(event):
       # validation code (20 lines)
       # processing code (20 lines)
       # response formatting code (10 lines)

   # After - broken into smaller functions
   def handle_request(event):
       data = _validate_request(event)
       result = _process_audio(data)
       return _format_response(result)
   ```

   **Extract Constants**:
   ```python
   # Before
   if len(text) > 5000:  # What's this?
       raise ValueError("Text too long")

   # After
   MAX_TEXT_LENGTH = 5000
   if len(text) > MAX_TEXT_LENGTH:
       raise ValueError(f"Text exceeds {MAX_TEXT_LENGTH} characters")
   ```

4. Improve error handling
   - Ensure all exceptions are caught and handled
   - Provide meaningful error messages
   - Log errors appropriately

5. Add docstrings to complex functions
   - Public functions should have docstrings
   - Docstrings should explain what function does
   - Include parameter and return types if not obvious
   - Example:
   ```python
   def process_audio(request: AudioRequest) -> str:
       """Process audio request and upload to S3.

       Args:
           request: Audio generation request with text and settings

       Returns:
           S3 URL of generated audio file

       Raises:
           ValueError: If text exceeds maximum length
           ServiceException: If audio generation fails
       """
   ```

6. Run tests frequently
   - After each refactoring, run `pytest tests/`
   - Ensure all tests still pass
   - If test fails, revert refactoring and try different approach

**Verification Checklist**:

- [ ] Code quality improved (simpler, clearer, more testable)
- [ ] No repeated code blocks
- [ ] Functions are single responsibility
- [ ] Error handling is comprehensive
- [ ] Public functions have docstrings
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code still passes mypy: `mypy src/`
- [ ] Code still passes ruff: `ruff check src/`
- [ ] Code still passes black: `black --check src/`

**Testing Instructions**:

```bash
cd backend
source .venv/bin/activate

# Run all quality checks
pytest tests/ -v && mypy src/ && ruff check src/ && black --check src/

# Or individually
pytest tests/ -v
mypy src/
ruff check src/
black --check src/
```

**Commit Message Template** (for each refactoring):

```
refactor: simplify [component name] for better readability

- Extract repeated logic into helper functions
- Break [function name] into smaller, focused functions
- Add docstrings to public functions
- Improve error messages
- Improve code clarity without changing behavior

All tests pass. Code quality improved.
```

**Token Estimate**: ~4,000 tokens

---

## Task 5: Create Quality Assurance Checklist

**Goal**: Document quality standards and create tools for developers to verify quality locally

**Files to create/modify**:
- Create: `backend/QUALITY.md` (quality standards documentation)
- Create: `backend/check_quality.sh` (shell script for quality checks)
- Create: `backend/Makefile` (optional, make targets for quality checks)

**Prerequisites**:
- Tasks 1-4 complete

**Step-by-step Instructions**:

1. Create QUALITY.md documentation
   - Document code quality standards
   - Explain mypy, ruff, black, and pytest
   - Show how to run each check locally
   - Document acceptable violations (if any)
   - Include examples of good/bad code

2. Create check_quality.sh script
   - Bash script that runs all quality checks
   - Helpful for developers before committing
   - Should run in order: tests → mypy → ruff → black
   - Stop on first failure with helpful message
   - Make it executable: `chmod +x backend/check_quality.sh`

3. Optional: Create Makefile
   - Add target: `make test` → `pytest tests/`
   - Add target: `make type-check` → `mypy src/`
   - Add target: `make lint` → `ruff check src/`
   - Add target: `make format` → `black src/`
   - Add target: `make format-check` → `black --check src/`
   - Add target: `make quality` → run all checks
   - Add target: `make quality-fix` → auto-fix issues (ruff --fix, black)

4. Document quality standards in QUALITY.md
   - Type hints: All public functions must be typed
   - Style: Must pass black formatting
   - Linting: Must pass ruff checks
   - Testing: Must have tests for critical paths
   - Coverage: Target 60%+ on core code
   - Examples: Show good and bad code patterns

5. Add quality checking instructions to README
   - Reference QUALITY.md from main README
   - Quick checklist before committing
   - Link to detailed documentation

**Verification Checklist**:

- [ ] QUALITY.md exists and is comprehensive
- [ ] check_quality.sh is executable and runs all checks
- [ ] Makefile exists (optional) with all targets
- [ ] Each target runs without errors
- [ ] Documentation is clear and helpful
- [ ] Examples show good/bad code patterns
- [ ] Quality standards are documented and enforced

**Testing Instructions**:

```bash
cd backend

# Run quality check script
./check_quality.sh

# Or with make
make quality       # Run all checks
make test         # Run tests only
make type-check   # Run mypy only
make lint         # Run ruff only
make format-check # Check formatting
```

**Commit Message Template**:

```
docs: add quality assurance guidelines and tooling

- Create QUALITY.md with standards and best practices
- Create check_quality.sh for automated quality verification
- Create Makefile with convenient quality check targets
- Document type hints, formatting, linting, and testing standards
- Add examples of good and bad code patterns

Developers can now easily verify code quality locally.
```

**Token Estimate**: ~2,000 tokens

---

## Summary & Verification

**Phase 2 Completion Checklist**:

- [ ] Task 1: mypy type checking complete (0 errors)
- [ ] Task 2: ruff linting complete (0 violations)
- [ ] Task 3: black formatting applied (100% formatted)
- [ ] Task 4: Code refactored for quality improvements
- [ ] Task 5: Quality documentation and tools created
- [ ] All tests still pass: `pytest tests/ -v`
- [ ] All quality checks pass:
  - `mypy backend/src/` → 0 errors
  - `ruff check backend/src/` → 0 violations
  - `black --check backend/src/` → no changes needed

**Code Quality Metrics**:

- ✅ 100% of code is type-hinted (public APIs minimum)
- ✅ 0 linting violations
- ✅ 100% code is black formatted
- ✅ 60%+ test coverage on critical paths
- ✅ All functions have clear names and docstrings

**When all tasks complete**:

1. Run full quality check: `cd backend && source .venv/bin/activate && ./check_quality.sh`
2. Verify 100% pass rate on all checks
3. Commit Phase 2 changes
4. **Proceed to Phase 3: Frontend Tooling**

---

## Notes

- Phase 2 assumes Phase 1 tests are passing (they guide refactoring)
- Type hints can use `Any` for truly ambiguous types, but should be minimized
- ruff auto-fix handles most issues; manual fixes are quick
- black formatting is non-negotiable (no configuration needed)
- Code should be refactored incrementally (not one massive refactor)
- Quality checks should run in order: tests → types → linting → formatting

**Total Phase 2 Effort**: ~20,000 tokens

**Blocked By**: Phase 1 (tests provide guidance)

**Blocks**: Phase 3 (can proceed in parallel if needed)

---

**Ready to continue? When Phase 2 is complete, proceed to [Phase 3: Frontend Tooling](./Phase-3.md)**
