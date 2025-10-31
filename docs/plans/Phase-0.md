# Phase 0: Setup & Prerequisites

**Status**: Foundation setup and architecture decisions
**Duration**: 1-2 days
**Effort**: ~8,000 tokens

---

## Overview

Phase 0 establishes the foundation for all subsequent phases. It includes:

1. **Architecture Decision Records (ADRs)** - Document why we're making specific choices
2. **Prerequisites checklist** - Ensure developer environment is ready
3. **Tool installation** - Set up linting, testing, and type-checking tools
4. **Configuration templates** - Create base configuration files
5. **Git setup** - Verify Git configuration and workflow

This phase applies to all following phases and should be completed before Phase 1 begins.

---

## Architecture Decision Records (ADRs)

### ADR 1: Language & Framework Decisions

**Decision**: Keep Expo/React Native for frontend, AWS Lambda for backend

**Rationale**:
- Frontend: Existing app deployed and working well with Expo 52
- No need to rewrite components or change architecture
- Expo Router provides modern file-based routing
- TypeScript already in use, no technical debt here
- Vite is overkill; Expo's bundler is sufficient

**Alternatives Considered**:
1. Migrate to web-first React + Vite (Rejected: too much refactoring, breaks existing mobile app)
2. Switch to different mobile framework (Rejected: unnecessary, Expo works well)

**Impact**: Minimizes refactoring scope, focuses on tooling and code quality

---

### ADR 2: Testing Framework Selection

**Decision**: Jest for frontend (Expo standard), pytest for backend

**Rationale**:
- Frontend: Jest already configured and working; jest-expo preset handles React Native
- Backend: pytest is Python standard, better than alternatives (unittest, nose)
- pytest has better fixture support, more readable test code
- Both integrate well with existing code

**Alternatives Considered**:
1. Vitest for both (Rejected: over-spec for our needs, frontend already on Jest)
2. unittest for backend (Rejected: verbose, less modern than pytest)

**Impact**: Leverages existing Jest setup, adds pytest for backend

---

### ADR 3: Linting & Formatting Philosophy

**Decision**: Balanced approach (not strict, not minimal)

**Rationale**:
- Strict rules frustrate developers and slow commits
- Minimal rules miss real issues and inconsistencies
- Balanced catches common bugs, enforces consistency, allows pragmatism
- Allow `// eslint-disable-next-line` and `# noqa` comments for edge cases

**Frontend Tooling**:
- ESLint: `eslint:recommended` + React/TypeScript plugins (not strict mode)
- Prettier: Opinionated formatter (no debates about style)
- TypeScript: Strict mode already enabled (preserve as-is)

**Backend Tooling**:
- ruff: Modern, fast linter (replaces pylint/flake8)
- black: Opinionated formatter (no configuration except line length)
- mypy: Standard mode (not strict; allows `Any`, untyped imports)

**Impact**: Better code quality without sacrificing developer velocity

---

### ADR 4: Type Safety Strategy

**Decision**: Pragmatic type coverage (not 100%, but critical paths covered)

**Rationale**:
- Full type coverage takes significant time and effort
- Critical business logic (handlers, services, models) should be typed
- Utilities and helpers can be incrementally improved
- mypy in standard mode balances safety and flexibility

**Frontend**:
- Keep TypeScript strict mode (already enabled)
- Add explicit return types to components and hooks
- Use `React.ReactNode` for component returns

**Backend**:
- Add type hints to all service and handler function signatures
- Add type hints to Pydantic models (already mostly typed)
- Skip type hints on internal utilities initially
- Run mypy in standard mode to find gaps

**Impact**: Type-safe critical paths without 100% coverage requirement

---

### ADR 5: CI/CD Automation Level

**Decision**: Minimal pipeline (tests only, no blocking gates)

**Rationale**:
- GitHub Actions provides feedback visibility
- Tests inform developers but don't block merges
- Developers retain responsibility for code quality
- Fast iteration and low process overhead
- No false positives blocking legitimate merges

**Scope**:
- Automated test runs on PR and push
- Coverage reports for visibility
- Manual deployment to Lambda (no auto-deploy)
- No linting gates in CI (developers run locally)

**Not Included**:
- Build blocking on lint errors
- Automatic deployment pipelines
- Code review automation

**Impact**: Lightweight process, quick feedback, developer accountability

---

### ADR 6: Python Packaging Evolution

**Decision**: Use `pyproject.toml` for configuration, keep `requirements.txt` for Lambda

**Rationale**:
- `pyproject.toml` is modern Python standard (PEP 517/518/621)
- Centralizes all tool configuration (pytest, ruff, black, mypy)
- Single source of truth for dependencies
- Keep `requirements.txt` for Lambda deployment (simpler, flat structure)
- Use `pip install -e ".[dev]"` for local development

**Structure**:
```
pyproject.toml         # Tool config + dependencies
requirements.txt       # Core deps (for Lambda)
requirements-dev.txt   # Dev tools (local development only)
```

**Impact**: Modern tooling, easier configuration management, clear separation

---

### ADR 7: Existing Code Refactoring Strategy

**Decision**: Refactor as we go (incremental modernization)

**Rationale**:
- Tests and linting will expose issues in existing code
- As we write tests, we naturally improve touched code
- Incremental refactoring prevents massive rewrites
- Code improves continuously rather than in one big phase
- Developers learn patterns from tests they write

**Approach**:
- Add type hints when touching code for tests
- Format with black when refactoring for tests
- Fix ruff warnings in files we're modifying
- Don't do wholesale refactoring of untouched code

**Impact**: Gradual improvement, learning opportunities, manageable change size

---

### ADR 8: Development Environment Setup

**Decision**: Python virtual environment + npm for local development

**Rationale**:
- Virtual env isolates Python dependencies (standard practice)
- npm workspaces already used for frontend
- Docker optional (not required for basic development)
- Simple to set up, works cross-platform

**Not Included**:
- Docker Compose (too heavy for this phase)
- Poetry (overkill, pip + pyproject.toml sufficient)
- conda (nvm + pip sufficient)

**Impact**: Simple, lightweight setup that works everywhere

---

## Prerequisites Checklist

### For All Developers

- [ ] Git installed and configured (`git config user.name` and `git config user.email`)
- [ ] Repository cloned and on `refactor-upgrade` branch
- [ ] `.gitignore` includes `.env` and `__pycache__/`
- [ ] GitHub Actions access (can view workflows in Actions tab)

### For Frontend Development

- [ ] Node.js v18+ installed (check with `node --version`)
- [ ] npm v9+ installed (check with `npm --version`)
- [ ] npm dependencies installed (`npm install` from project root)
- [ ] Expo CLI available (`npx expo --version`)

### For Backend Development

- [ ] Python 3.12 installed (check with `python3 --version`)
- [ ] pip available (check with `pip --version`)
- [ ] Virtual environment support (`python3 -m venv` works)
- [ ] AWS credentials configured or API keys available for local testing

### API Keys & Credentials (Optional for Phase 0, Required Later)

- [ ] Google Gemini API key (for backend testing)
- [ ] ElevenLabs API key (for TTS testing)
- [ ] OpenAI API key (optional, for TTS fallback)
- [ ] AWS credentials (for S3 testing)

---

## Task 1: Verify Local Environment

**Goal**: Ensure all required tools are installed and working

**Files to create/modify**: None (verification only)

**Prerequisites**:
- All items from checklist above completed

**Step-by-step Instructions**:

1. Verify Node.js version is 18+
   - Run `node --version`
   - If missing or too old, install via nvm or package manager

2. Verify npm version is 9+
   - Run `npm --version`
   - If too old, run `npm install -g npm`

3. Verify Python version is 3.12+
   - Run `python3 --version`
   - If missing, install via pyenv, conda, or package manager
   - On macOS: `brew install python@3.12`
   - On Linux: `sudo apt-get install python3.12`
   - On Windows: Download from python.org

4. Verify pip is available
   - Run `pip --version` or `python3 -m pip --version`
   - If missing, run `python3 -m ensurepip --upgrade`

5. Verify venv module available
   - Run `python3 -m venv --help`
   - Should show help output (not error)

6. Verify Git is configured
   - Run `git config user.name` (should return your name)
   - Run `git config user.email` (should return your email)
   - If missing, run `git config --global user.name "Your Name"` and `git config --global user.email "your@email.com"`

7. Verify npm dependencies are installed
   - From project root, run `npm list`
   - Should show dependency tree (not errors)
   - If missing, run `npm install`

**Verification Checklist**:

- [ ] `node --version` returns v18.0.0 or higher
- [ ] `npm --version` returns 9.0.0 or higher
- [ ] `python3 --version` returns 3.12.0 or higher
- [ ] `python3 -m venv --help` shows help output
- [ ] `git config user.name` and `git config user.email` return values
- [ ] `npm list` shows dependency tree without errors
- [ ] All prerequisites from checklist are satisfied

**Testing Instructions**:

No automated tests for this task. Verification is manual:

```bash
# Frontend environment
node --version          # v18+
npm --version          # v9+
npm list               # no errors

# Backend environment
python3 --version      # 3.12+
python3 -m venv --help # shows help

# Git environment
git config user.name   # your name
git config user.email  # your email
```

**Commit**: No commit for this task (verification only)

**Token Estimate**: ~500 tokens

---

## Task 2: Create Configuration Files (Phase 0 Foundation)

**Goal**: Create base configuration files and placeholders needed by later phases

**Files to create/modify**:
- Create: `.env.example`
- Create: `.editorconfig`
- Create: `pyproject.toml` (backend configuration)
- Create: `backend/requirements-dev.txt`
- Modify: `.gitignore`

**Prerequisites**:
- Task 1 complete (environment verified)
- Git repository ready

**Step-by-step Instructions**:

1. Create `.env.example` in project root
   - Document all environment variables needed
   - Use placeholder values (no real API keys)
   - Include frontend variables (EXPO_PUBLIC_*) and backend variables (G_KEY, etc.)
   - Add comments explaining each variable's purpose

2. Create `.editorconfig` in project root
   - Configure editor settings for consistency
   - Set line endings, indentation, charset, trim whitespace
   - Apply to all files and special rules for Markdown
   - Reference: https://editorconfig.org/

3. Create `pyproject.toml` in `backend/` directory
   - Define Python project metadata (name, version, description)
   - List core dependencies (from existing requirements.txt)
   - List dev dependencies (pytest, ruff, black, mypy, etc.)
   - Configure pytest, ruff, black, and mypy tool sections
   - Set Python version requirement to 3.12

4. Create `backend/requirements-dev.txt` in backend directory
   - List development-only dependencies
   - Include: pytest, pytest-cov, pytest-mock, ruff, black, mypy, type stubs
   - Add comment explaining this is for local development only
   - Keep main requirements.txt unchanged (for Lambda)

5. Update `.gitignore` in project root
   - Ensure `.env` is ignored (never commit real secrets)
   - Add `*.pyc`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`
   - Add `*.egg-info/`, `dist/`, `build/` (Python build artifacts)
   - Add `node_modules/` and `.next/` (already likely there)
   - Add `backend/.venv/` and `venv/` (Python virtual environments)

**Verification Checklist**:

- [ ] `.env.example` exists with all environment variables documented
- [ ] `.editorconfig` exists and is valid
- [ ] `pyproject.toml` exists in `backend/` with proper structure
- [ ] `backend/requirements-dev.txt` exists with dev dependencies listed
- [ ] `.gitignore` includes `.env`, `__pycache__/`, `.venv/`, etc.
- [ ] No real secrets are visible in any configuration files
- [ ] Project structure is unchanged, only new files added

**Testing Instructions**:

Verify configuration files are syntactically correct:

```bash
# Check .env.example is readable
cat .env.example | head -20

# Check .editorconfig syntax
# (EditorConfig validators available online)

# Check pyproject.toml is valid TOML
python3 -c "import tomllib; tomllib.parse(open('backend/pyproject.toml').read())"

# Check requirements-dev.txt is readable
cat backend/requirements-dev.txt

# Check .gitignore syntax
# (Just verify it's valid text)
```

**Commit Message Template**:

```
feat: add foundation configuration files

- Add .env.example with environment variable documentation
- Add .editorconfig for cross-editor consistency
- Add pyproject.toml with project metadata and tool configuration
- Add backend/requirements-dev.txt for development dependencies
- Update .gitignore for Python and Node artifacts

This establishes the configuration foundation for all subsequent phases.
```

**Token Estimate**: ~2,000 tokens

---

## Task 3: Install Frontend Development Tools

**Goal**: Install ESLint, Prettier, and TypeScript dependencies for frontend

**Files to create/modify**:
- Modify: `package.json` (add dev dependencies)
- Create: `.eslintrc.json`
- Create: `.prettierrc.json`
- Modify: `tsconfig.json` (fix test file inclusion)

**Prerequisites**:
- Task 1 complete (Node.js v18+ verified)
- Task 2 complete (base configs created)

**Step-by-step Instructions**:

1. Add ESLint and Prettier to package.json dev dependencies
   - Install: eslint, @typescript-eslint/eslint-plugin, @typescript-eslint/parser
   - Install: eslint-plugin-react, eslint-plugin-react-hooks
   - Install: prettier
   - Run `npm install --save-dev` with all packages

2. Create `.eslintrc.json` in project root
   - Extend eslint:recommended
   - Add TypeScript and React plugins
   - Set rules to balanced (not strict)
   - Allow console.warn and eslint-disable comments
   - Disable rule: react/react-in-jsx-scope (not needed with modern React)

3. Create `.prettierrc.json` in project root
   - Set printWidth to 100 (match backend)
   - Set tabWidth to 2 (Expo standard)
   - Use single quotes (JavaScript convention)
   - Use trailing commas (cleaner diffs)
   - Use arrow parens always

4. Add linting and formatting scripts to package.json
   - Add script: `lint` → `eslint . --ext .ts,.tsx`
   - Add script: `lint:fix` → `eslint . --ext .ts,.tsx --fix`
   - Add script: `format` → `prettier --write '**/*.{ts,tsx,json,md}'`
   - Add script: `format:check` → `prettier --check '**/*.{ts,tsx,json,md}'`

5. Fix tsconfig.json to exclude test files from main compilation
   - Add `exclude` array with `**/__tests__/**` and `components/__tests__/**`
   - This prevents test files from being compiled as main application code
   - Tests will have their own tsconfig.test.json (created in Phase 3)

**Verification Checklist**:

- [ ] `.eslintrc.json` exists and is valid JSON
- [ ] `.prettierrc.json` exists and is valid JSON
- [ ] package.json has new scripts: lint, lint:fix, format, format:check
- [ ] npm install completed without errors
- [ ] `npx eslint --version` returns version (e.g., v8.50.0)
- [ ] `npx prettier --version` returns version (e.g., 3.0.0)
- [ ] tsconfig.json has exclude array for test files
- [ ] No existing code is broken (Expo start still works)

**Testing Instructions**:

Verify configuration files work:

```bash
# Check ESLint loads configuration
npx eslint --print-config . > /dev/null

# Check Prettier loads configuration
npx prettier --check . 2>/dev/null || true

# Check TypeScript still works
npx tsc --noEmit

# Check Expo still starts
npx expo start --help > /dev/null
```

**Commit Message Template**:

```
feat: install and configure frontend linting and formatting

- Add ESLint with TypeScript and React plugins
- Add Prettier for consistent code formatting
- Create .eslintrc.json with balanced rule set
- Create .prettierrc.json with consistent formatting rules
- Add npm scripts: lint, lint:fix, format, format:check
- Fix tsconfig.json to exclude test files from compilation

This establishes linting and formatting standards for the frontend.
```

**Token Estimate**: ~2,500 tokens

---

## Task 4: Set Up Backend Python Environment

**Goal**: Create Python virtual environment and install development tools

**Files to create/modify**:
- Create: `backend/.venv/` (local virtual environment)
- No source code changes in this task

**Prerequisites**:
- Task 1 complete (Python 3.12 verified)
- Task 2 complete (pyproject.toml and requirements-dev.txt created)

**Step-by-step Instructions**:

1. Create Python virtual environment
   - Navigate to `backend/` directory
   - Run `python3 -m venv .venv`
   - This creates isolated Python environment in `backend/.venv/`
   - Virtual environment should already be in .gitignore

2. Activate virtual environment
   - On macOS/Linux: `source backend/.venv/bin/activate`
   - On Windows: `backend\.venv\Scripts\activate`
   - Verify activation: prompt should show `(.venv)` prefix

3. Upgrade pip in virtual environment
   - Run `pip install --upgrade pip`
   - Ensures latest pip for reliable dependency installation

4. Install development dependencies
   - Run `pip install -e ".[dev]"` (uses pyproject.toml)
   - Or if pyproject.toml not yet working: `pip install -r requirements-dev.txt`
   - This installs both core and dev dependencies in virtual environment

5. Verify installations
   - Run `pytest --version` (should show version, e.g., pytest 7.4.0)
   - Run `ruff --version` (should show version, e.g., ruff 0.1.0)
   - Run `black --version` (should show version, e.g., black 23.9.0)
   - Run `mypy --version` (should show version, e.g., mypy 1.5.0)

**Verification Checklist**:

- [ ] `backend/.venv/` directory exists
- [ ] Virtual environment activates without errors
- [ ] `which python` (or `where python` on Windows) points to `.venv/bin/python`
- [ ] `pytest --version` shows version 7.4.0+
- [ ] `ruff --version` shows version 0.1.0+
- [ ] `black --version` shows version 23.9.0+
- [ ] `mypy --version` shows version 1.5.0+
- [ ] All tools run without import errors

**Testing Instructions**:

Verify all tools work:

```bash
# Activate virtual environment first
source backend/.venv/bin/activate

# Test each tool
pytest --version
ruff --version
black --version
mypy --version

# Test that tools can be run on existing code
ruff check backend/src/ | head -5
black --check backend/src/ | head -5
mypy backend/src/ | head -5

# If no errors, setup is successful
```

**Commit**: No commit for this task (virtual environment in .gitignore)

**Note**: Add to development setup documentation (Phase 5) that developers must activate venv before running backend commands

**Token Estimate**: ~1,500 tokens

---

## Task 5: Create Placeholder Test Infrastructure

**Goal**: Create pytest configuration and test directory structure

**Files to create/modify**:
- Create: `backend/tests/` directory structure
- Create: `backend/tests/conftest.py` (pytest configuration and fixtures)
- Create: `backend/tests/mocks/external_apis.py` (placeholder for mocks)
- Create: `backend/tests/fixtures/sample_data.py` (placeholder for fixtures)

**Prerequisites**:
- Task 2 complete (pyproject.toml created)
- Task 4 complete (Python environment set up)

**Step-by-step Instructions**:

1. Create test directory structure
   - Create `backend/tests/` directory
   - Create `backend/tests/__init__.py` (empty file)
   - Create `backend/tests/unit/` directory
   - Create `backend/tests/unit/__init__.py`
   - Create `backend/tests/mocks/` directory
   - Create `backend/tests/mocks/__init__.py`
   - Create `backend/tests/fixtures/` directory
   - Create `backend/tests/fixtures/__init__.py`

2. Create `backend/tests/conftest.py`
   - Add pytest configuration
   - Import and register any global fixtures
   - Document how to use fixtures in tests
   - Add setup/teardown for test environment if needed

3. Create `backend/tests/mocks/external_apis.py`
   - Add placeholder docstring explaining mock purpose
   - Create mock responses for Google Gemini API
   - Create mock responses for TTS providers (ElevenLabs, OpenAI)
   - Create mock responses for S3 storage
   - Each mock should be a class or function returning realistic sample data

4. Create `backend/tests/fixtures/sample_data.py`
   - Add sample request data (AudioRequest, SummaryRequest)
   - Add sample response data (AudioResponse, SummaryResponse)
   - Use realistic but non-sensitive data
   - Include edge cases (empty strings, long text, special characters)

5. Verify pytest discovers configuration
   - Run `pytest --collect-only` from backend directory
   - Should show pytest.ini configuration loaded
   - Should show 0 tests collected (no test files written yet)

**Verification Checklist**:

- [ ] `backend/tests/` directory exists with all subdirectories
- [ ] `conftest.py` is syntactically correct Python
- [ ] `mocks/external_apis.py` is syntactically correct Python
- [ ] `fixtures/sample_data.py` is syntactically correct Python
- [ ] All `__init__.py` files present in test directories
- [ ] `pytest --collect-only` runs without errors
- [ ] 0 tests collected (expected, no tests written yet)
- [ ] pytest.ini options from pyproject.toml are recognized

**Testing Instructions**:

Verify pytest configuration:

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate

# Collect tests (should find 0, no tests yet)
pytest --collect-only

# Run with verbose output to see configuration
pytest --version
pytest backend/tests/ -v

# Check coverage configuration
pytest --co -q
```

**Commit Message Template**:

```
feat: create test infrastructure and configuration

- Create backend/tests/ directory structure (unit, mocks, fixtures)
- Add conftest.py with pytest configuration and fixtures
- Add mocks/external_apis.py with mock factory functions
- Add fixtures/sample_data.py with realistic sample data
- Configure pytest in pyproject.toml with proper paths and markers

This establishes the foundation for backend unit and integration tests.
```

**Token Estimate**: ~2,000 tokens

---

## Summary & Next Steps

**Phase 0 Completion Checklist**:

- [ ] Task 1: Local environment verified (Node 18+, Python 3.12+)
- [ ] Task 2: Configuration files created (.env.example, .editorconfig, pyproject.toml)
- [ ] Task 3: Frontend tools installed (ESLint, Prettier, dependencies)
- [ ] Task 4: Backend Python environment set up (venv, pip, tools)
- [ ] Task 5: Test infrastructure created (pytest config, test directories)

**When all tasks complete**:
1. Commit Phase 0 changes with clear message
2. Verify all configuration files are correct
3. Push changes to feature branch
4. Create PR for Phase 0 (optional at this stage)
5. **Proceed to Phase 1: Backend Infrastructure**

**Total Phase 0 Effort**: ~8,500 tokens (slightly over estimate due to comprehensive ADRs)

**Blocked By**: Nothing (foundation phase)

**Blocks**: All subsequent phases depend on Phase 0 completion

---

## Troubleshooting

### Node.js Version Issues

**Problem**: `node --version` shows v16 or lower

**Solution**:
- Install nvm: https://github.com/nvm-sh/nvm
- Run `nvm install 18` then `nvm use 18`
- Or use Homebrew: `brew install node@18`

### Python Version Issues

**Problem**: `python3 --version` shows 3.11 or lower, or `python3 not found`

**Solution**:
- On macOS: `brew install python@3.12`
- On Linux: `sudo apt-get install python3.12`
- On Windows: Download from https://www.python.org/downloads/
- Or use pyenv: https://github.com/pyenv/pyenv

### Virtual Environment Activation Issues

**Problem**: Virtual environment doesn't activate (no `.venv` prompt)

**Solution**:
- Ensure you're in `backend/` directory
- On macOS/Linux: `source .venv/bin/activate`
- On Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- On Windows (CMD): `.venv\Scripts\activate.bat`

### pyproject.toml Parsing Errors

**Problem**: `pip install -e ".[dev]"` fails with TOML parsing error

**Solution**:
- Verify pyproject.toml syntax (copy from Phase-0.md example)
- Check for tabs vs spaces (must be spaces)
- Check for quotes (must be consistent)
- Try: `python3 -m tomllib < backend/pyproject.toml` to validate

### Git Configuration Issues

**Problem**: `git config user.name` returns nothing

**Solution**:
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### Dependencies Installation Hangs

**Problem**: `npm install` or `pip install` seems stuck

**Solution**:
- Try canceling with Ctrl+C
- Clear cache: `npm cache clean --force` or `pip cache purge`
- Check internet connection
- Retry with verbose: `npm install -v` or `pip install -v`

---

**Ready to continue? When Phase 0 is complete, proceed to [Phase 1: Backend Infrastructure](./Phase-1.md)**
