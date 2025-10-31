# CI/CD Process Documentation

This document explains how the Float project uses GitHub Actions for continuous integration and testing.

## Overview

The Float project uses GitHub Actions to automatically run tests and code quality checks on pull requests and commits. Our CI/CD pipeline follows a minimal strategy per ADR 5:

- **Tests run automatically** on PR creation and commit pushes
- **Status checks are informational only** (do not block merges)
- **No automatic deployment** (manual Lambda deployment still required)
- **Fast feedback loop** for developers

## Workflow Triggers

### Frontend Tests (`frontend-tests.yml`)

Runs automatically when:
- **Push** to `main` or `refactor-upgrade` branch
- **Pull Request** to `main` branch
- **File changes** in: `app/`, `components/`, `package.json`, `tsconfig.json`, `.eslintrc.json`, `.prettierrc.json`

**Runs on**: Node.js 22.x

**Tests performed**:
1. Jest tests with coverage
2. TypeScript type checking
3. ESLint linting
4. Prettier formatting check

**Typical duration**: 5-10 minutes

### Backend Tests (`backend-tests.yml`)

Runs automatically when:
- **Push** to `main` or `refactor-upgrade` branch
- **Pull Request** to `main` branch
- **File changes** in: `backend/`, `.github/workflows/backend-tests.yml`

**Runs on**: Python 3.11 and 3.12 (parallel matrix)

**Tests performed**:
1. Ruff linting
2. Black formatting check
3. MyPy type checking
4. Pytest tests with coverage

**Typical duration**: 5-10 minutes per Python version

## Viewing Workflow Results

### On GitHub Web UI

1. Go to repository → **Actions** tab
2. Select a workflow from the left sidebar
3. Click on a specific run to see details
4. Click on a job to see step-by-step execution logs

### On Pull Requests

1. Open a PR to `main` branch
2. Scroll to **Checks** section (below PR description)
3. See status of all workflows:
   - ✅ **Passing**: All tests passed
   - ❌ **Failed**: One or more tests failed (click to see details)
   - ⏳ **Running**: Tests are currently executing

Status checks do **not block merge** - developers can merge even if tests fail.

## Understanding Workflow Status

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| ✅ **All checks passed** | All tests ran successfully | Ready to merge |
| ❌ **Some checks failed** | Tests found issues | Review logs, fix issues, push again |
| ⏳ **Running** | Tests currently executing | Wait for completion |
| ⊘ **Skipped** | Workflow didn't run (path filter) | Normal if unrelated files changed |

## Common Failure Scenarios

### Frontend Tests Fail

**Possible causes**:
- Jest tests failed (syntax error, logic error, breaking change)
- TypeScript compilation error (type mismatch)
- ESLint rule violation (linting error)
- Prettier formatting issue (inconsistent formatting)

**How to fix**:
1. Click the failed job in GitHub Actions
2. Scroll to the failed step (red X)
3. Review the error message and file location
4. Fix the issue locally: `npm run lint:fix && npm run format`
5. Run tests locally: `npm test -- --watchAll=false`
6. Commit and push the fix

### Backend Tests Fail

**Possible causes**:
- Ruff linting error (style or bug)
- Black formatting issue (inconsistent code style)
- MyPy type error (type annotation mismatch)
- Pytest test failure (logic error or missing import)

**How to fix**:
1. Click the failed job in GitHub Actions
2. Scroll to the failed step (red X)
3. Review the error message and file location
4. Fix the issue locally:
   ```bash
   cd backend
   source .venv/bin/activate
   ruff check src/ --fix
   black src/
   mypy src/
   pytest tests/
   ```
5. Commit and push the fix

### Tests Pass Locally but Fail in CI

**Possible causes**:
- Different Python/Node version in CI vs local
- Missing environment variables
- File path differences (case sensitivity on Linux vs macOS)
- Caching issue in GitHub Actions

**How to fix**:
1. Check Python version locally: `python --version` (must be 3.11 or 3.12)
2. Check Node version locally: `node --version` (must be 22.x)
3. Verify `.env` is in `.gitignore` (secrets shouldn't be in repo)
4. Re-run workflow manually from GitHub Actions → click "Re-run jobs"
5. If still fails, ask for help in PR comments

### Workflow Never Runs

**Possible causes**:
- GitHub Actions disabled on repository (admin setting)
- Branch protection rules preventing runs
- File path filters don't match changes

**How to verify**:
1. Go to repository → **Actions** tab
2. Should see both `Frontend Tests` and `Backend Tests` workflows
3. If empty, check Settings → Actions → check "Allow all actions and reusable workflows"

### Timeout or Hanging Workflow

**Possible causes**:
- Dependency installation taking too long (network issue)
- Test hanging on external API call
- Large test suite taking too long

**How to fix**:
1. Click "Cancel workflow" button in GitHub Actions UI
2. Check for `pytest.set_timeout()` or similar in test code
3. Check for external API calls not mocked in tests
4. Optimize slow tests or move to separate test suite
5. Re-run workflow after fixes

## Manually Re-running Workflows

Sometimes you want to re-run tests without making a new commit:

1. Go to GitHub Actions tab
2. Click on the workflow run you want to re-run
3. Click "Re-run jobs" → "Re-run all jobs"
4. Workflow will start again with the same code

## Path Filters Explanation

Workflows use "path filters" to only run when relevant files change:

**Frontend workflow skips if only backend changed**:
```yaml
paths:
  - 'app/**'
  - 'components/**'
  - 'package.json'
```

**Backend workflow skips if only frontend changed**:
```yaml
paths:
  - 'backend/**'
  - '.github/workflows/backend-tests.yml'
```

This saves time and resources - no need to run full test suite for unrelated changes.

## Integration with Development Workflow

### For Feature Development

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes to frontend or backend code
3. Push to GitHub: `git push -u origin feature/my-feature`
4. Create pull request to `main`
5. GitHub Actions automatically runs tests
6. If tests pass ✅: ready to merge (after code review)
7. If tests fail ❌: fix issues and push again (tests re-run automatically)

### Best Practices

- **Run tests locally before pushing**: `npm test` (frontend) or `make quality` (backend)
- **Fix linting issues locally**: `npm run lint:fix` (frontend) or `ruff check --fix` (backend)
- **Format code before committing**: `npm run format` (frontend) or `black src/` (backend)
- **Review CI logs on PR**: Check what failed and fix before code review
- **Don't push test-breaking changes**: CI will catch them, but faster to fix locally

## Configuration Details

### Frontend Workflow Configuration

**File**: `.github/workflows/frontend-tests.yml`

```yaml
- Node.js version: 22.x only (per requirement)
- Cache: npm packages (actions/setup-node)
- Install: npm ci (clean install)
- Tests: npm test -- --coverage --watchAll=false
- Coverage: ./coverage/coverage-final.json
```

### Backend Workflow Configuration

**File**: `.github/workflows/backend-tests.yml`

```yaml
- Python versions: 3.11 and 3.12 (parallel matrix)
- Cache: pip packages (actions/setup-python)
- Install: pip install -e ".[dev]"
- Linting: ruff check src/
- Formatting: black --check src/
- Type checking: mypy src/
- Tests: pytest tests/ --cov=src --cov-report=xml
```

## Environment Setup

Workflows automatically set up:
- **GitHub Actions Linux environment** (ubuntu-latest)
- **Code checkout** via `actions/checkout@v4`
- **Language runtime** (Node.js or Python)
- **Dependency caching** for faster runs
- **Working directory** (project root)

Developers running tests locally need:
- **Frontend**: Node.js 22+, npm 9+
- **Backend**: Python 3.11+, virtual environment activated

See [README.md](../README.md) for local setup instructions.

## Troubleshooting Tips

### "Module not found" errors in tests

1. **Frontend**: Run `npm install` again
2. **Backend**: Run `pip install -e ".[dev]"` again
3. Both: Clear cache in GitHub Actions by re-running

### "Port already in use" in local tests

- You're likely running tests in watch mode (don't commit to CI)
- Run with `--watchAll=false` (frontend) or single run (backend)

### Workflow file syntax error

- Check for proper YAML indentation (must be spaces, not tabs)
- Use online YAML validator: https://www.yamllint.com/
- Common issue: `run:` commands need `|` for multi-line

### Coverage reports not working

- We don't currently upload to Codecov (optional Task 4)
- Coverage reports are printed to logs
- Configure later if needed per `.github/workflows/*.yml` comments

## Questions or Issues?

- **CI workflow behavior**: Check this documentation first
- **Test failures**: Review the failing step in GitHub Actions logs
- **Feature requests**: Create an issue in GitHub
- **Configuration changes**: Update both documentation and workflow files

## Next Steps

When Phase 4 is complete:
- Workflows are set up and running on PRs
- Status checks appear on all PRs (informational only)
- Tests provide fast feedback to developers
- Ready to proceed to Phase 5: Documentation
