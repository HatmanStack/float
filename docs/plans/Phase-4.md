# Phase 4: CI/CD Pipeline

**Status**: GitHub Actions workflows for automated testing
**Duration**: 2-3 days
**Effort**: ~12,000 tokens

**Prerequisites**: Phases 0-3 complete

---

## Overview

Phase 4 creates GitHub Actions workflows for automated testing on pull requests and pushes. Per ADR 5 (CI/CD Strategy), we implement **minimal pipeline** (tests only, no blocking gates).

**Key Objectives**:

1. Create GitHub Actions workflow for frontend tests
2. Create GitHub Actions workflow for backend tests
3. Verify workflows run correctly on PRs
4. Configure test reporting and coverage
5. Document CI/CD process for team

**Phase Dependencies**:
- Phase 0-3 must be complete (tools configured, code quality improved)
- GitHub repository accessible
- GitHub Actions enabled on repository

---

## Task 1: Create Frontend Tests Workflow

**Goal**: Automate frontend test runs on pull requests and commits

**Files to create/modify**:
- Create: `.github/workflows/frontend-tests.yml`

**Prerequisites**:
- Phase 0-3 complete
- Frontend tests passing locally: `npm test -- --watchAll=false`
- npm dependencies defined in package.json

**Step-by-step Instructions**:

1. Create .github directory structure
   - Create `.github/` directory in project root
   - Create `.github/workflows/` directory inside
   - This is where GitHub Actions workflows are stored

2. Create frontend-tests.yml workflow
   - Name: "Frontend Tests"
   - Triggers: push to main/refactor-upgrade, PR to main
   - Path filters: only run on frontend changes (app/, components/, package.json)
   - Strategy: test on multiple Node versions (18.x, 20.x)
   - Steps:
     a. Checkout code
     b. Set up Node.js
     c. Cache npm dependencies
     d. Install dependencies
     e. Run Jest tests with coverage
     f. Upload coverage to Codecov (optional)

3. Configure workflow details
   - Set `runs-on: ubuntu-latest` (fastest, cheapest)
   - Use `actions/checkout@v4` (latest version)
   - Use `actions/setup-node@v4` with cache
   - Run command: `npm test -- --coverage --watchAll=false`
   - Coverage path: `./coverage/coverage-final.json`

4. Optional: Add Codecov integration
   - Add step to upload coverage to codecov.io
   - Use `codecov/codecov-action@v3`
   - Set flags: `frontend`
   - This provides visibility on coverage trends

5. Test the workflow
   - Push to a feature branch
   - Create PR to main branch
   - Check that workflow runs in GitHub Actions tab
   - Verify tests pass or fail correctly

**Verification Checklist**:

- [ ] `.github/workflows/frontend-tests.yml` exists and is valid YAML
- [ ] Workflow runs on PR to main branch
- [ ] Workflow runs on push to main/refactor-upgrade
- [ ] Tests pass in CI (same as local)
- [ ] Workflow only runs on frontend code changes
- [ ] Coverage report uploaded (if Codecov configured)
- [ ] Workflow can be viewed in GitHub Actions tab

**Testing Instructions**:

1. Create a test branch and make a change:
```bash
git checkout -b test/ci-workflow
echo "// test" >> components/ThemedText.tsx
git add components/ThemedText.tsx
git commit -m "test: trigger CI workflow"
git push -u origin test/ci-workflow
```

2. Go to GitHub → Actions tab → see workflow running

3. View results when complete

4. Revert test change:
```bash
git checkout main
git branch -D test/ci-workflow
```

**Commit Message Template**:

```
ci: add frontend tests GitHub Actions workflow

- Create .github/workflows/frontend-tests.yml
- Runs Jest tests on PR to main and push to main/refactor-upgrade
- Tests on Node 18.x and 20.x
- Generates coverage reports
- Provides CI feedback without blocking merges

Frontend tests now run automatically on GitHub.
```

**Token Estimate**: ~3,500 tokens

---

## Task 2: Create Backend Tests Workflow

**Goal**: Automate backend test runs and code quality checks

**Files to create/modify**:
- Create: `.github/workflows/backend-tests.yml`

**Prerequisites**:
- Phase 1-2 complete (backend tests and code quality done)
- Backend tests passing: `pytest tests/`
- All code quality checks passing: mypy, ruff, black

**Step-by-step Instructions**:

1. Create backend-tests.yml workflow
   - Name: "Backend Tests"
   - Triggers: push to main/refactor-upgrade, PR to main
   - Path filters: only run on backend changes (backend/, .github/workflows/backend-tests.yml)
   - Strategy: test on multiple Python versions (3.11, 3.12)
   - Steps:
     a. Checkout code
     b. Set up Python
     c. Cache pip dependencies
     d. Install dependencies (including dev)
     e. Run ruff linting
     f. Run black format check
     g. Run mypy type checking
     h. Run pytest tests with coverage
     i. Upload coverage to Codecov (optional)

2. Configure workflow details
   - Set `runs-on: ubuntu-latest`
   - Use `actions/checkout@v4`
   - Use `actions/setup-python@v4` with cache
   - Python versions: 3.11, 3.12
   - Install: `pip install -e ".[dev]"` (uses pyproject.toml)
   - Commands:
     - ruff: `ruff check backend/src/`
     - black: `black --check backend/src/`
     - mypy: `mypy backend/src/`
     - pytest: `pytest backend/tests/ --cov=backend/src --cov-report=xml`

3. Configure test discovery
   - pytest should find tests in `backend/tests/`
   - Coverage should report on `backend/src/`
   - XML coverage for Codecov integration

4. Optional: Add Codecov integration
   - Upload coverage.xml from pytest
   - Set flags: `backend`
   - Provides coverage trend visibility

5. Test the workflow
   - Push to feature branch
   - Create PR to main
   - Verify workflow runs and passes

**Verification Checklist**:

- [ ] `.github/workflows/backend-tests.yml` exists and is valid YAML
- [ ] Workflow runs on PR and push to main
- [ ] Workflow tests Python 3.11 and 3.12
- [ ] All quality checks run in order: ruff → black → mypy → pytest
- [ ] Tests pass in CI (same as local)
- [ ] Workflow only runs on backend changes
- [ ] Coverage report uploaded (if configured)

**Testing Instructions**:

1. Create test branch:
```bash
git checkout -b test/backend-ci
echo "# test" >> backend/README.md
git add backend/README.md
git commit -m "test: trigger backend CI"
git push -u origin test/backend-ci
```

2. Check GitHub Actions → workflow running

3. Verify all steps pass (ruff, black, mypy, pytest)

4. Revert:
```bash
git checkout main
git branch -D test/backend-ci
```

**Commit Message Template**:

```
ci: add backend tests GitHub Actions workflow

- Create .github/workflows/backend-tests.yml
- Runs ruff linting, black formatting, mypy type checking
- Runs pytest tests on Python 3.11 and 3.12
- Generates coverage reports
- Provides CI feedback without blocking merges

Backend code quality checks now automated.
```

**Token Estimate**: ~3,500 tokens

---

## Task 3: Verify Workflows and Configure Options

**Goal**: Test workflows in realistic scenarios and optimize configuration

**Files to create/modify**:
- Modify: `.github/workflows/frontend-tests.yml` (refinements)
- Modify: `.github/workflows/backend-tests.yml` (refinements)

**Prerequisites**:
- Tasks 1-2 complete
- Both workflows created

**Step-by-step Instructions**:

1. Test workflows with real changes
   - Make small code change in frontend
   - Create PR and verify frontend workflow runs only
   - Check that backend workflow doesn't run (path filter works)
   - Repeat for backend changes

2. Verify workflow notifications
   - Check if GitHub sends PR status checks
   - Verify status shows test pass/fail
   - Status should NOT block PR merge (per ADR)
   - Status is informational only

3. Configure workflow caching
   - npm cache: workflows should cache `node_modules/`
   - pip cache: workflows should cache Python packages
   - This speeds up workflow runs significantly
   - Uses `actions/setup-node` and `actions/setup-python` built-in cache

4. Configure timeout settings
   - Set timeout for jobs (e.g., 15 minutes)
   - Prevents hanging workflows
   - Most tests complete in 5-10 minutes

5. Configure job parallelization (optional)
   - Frontend and backend workflows are already separate
   - Within each workflow, matrix strategy parallelizes (Node versions, Python versions)
   - No need for further optimization at this stage

6. Test workflow with failing tests
   - Temporarily break a test
   - Push to branch
   - Verify workflow shows failure
   - Verify PR status shows failure (doesn't block merge)
   - Fix test and verify workflow passes again

**Verification Checklist**:

- [ ] Workflows only run on their respective code changes (path filters work)
- [ ] Workflows cache dependencies (npm, pip)
- [ ] Matrix strategy parallelizes tests
- [ ] Workflows complete in reasonable time (10-15 min)
- [ ] PR status correctly shows pass/fail
- [ ] Status doesn't block PR merge
- [ ] Both workflows run on same PR (if both frontend and backend changed)

**Testing Instructions**:

```bash
# Test 1: Frontend-only change
git checkout -b test/frontend-only
echo "// test" >> components/ThemedText.tsx
git add components/ThemedText.tsx
git commit -m "test: frontend change"
git push -u origin test/frontend-only
# Verify: only frontend workflow runs, backend skipped

# Test 2: Backend-only change
git checkout -b test/backend-only
echo "# test" >> backend/README.md
git add backend/README.md
git commit -m "test: backend change"
git push -u origin test/backend-only
# Verify: only backend workflow runs, frontend skipped

# Test 3: Both changes
git checkout -b test/both-changes
echo "// test" >> components/ThemedText.tsx
echo "# test" >> backend/README.md
git add .
git commit -m "test: both frontend and backend"
git push -u origin test/both-changes
# Verify: both workflows run in parallel
```

**Commit Message Template**:

```
ci: optimize and verify GitHub Actions workflows

- Configure npm and pip caching for faster runs
- Set job timeouts (15 minutes)
- Verify path filters work correctly
- Test workflow behavior with failing tests
- Ensure workflows complete in reasonable time

Workflows are now optimized and verified working correctly.
```

**Token Estimate**: ~2,500 tokens

---

## Task 4: Configure Coverage Reporting (Optional)

**Goal**: Set up Codecov integration for coverage tracking (optional)

**Files to create/modify**:
- Modify: `.github/workflows/frontend-tests.yml` (add Codecov step)
- Modify: `.github/workflows/backend-tests.yml` (add Codecov step)
- Create: `codecov.yml` (optional, Codecov configuration)

**Prerequisites**:
- Tasks 1-3 complete
- Codecov account created (optional, free for public repos)

**Step-by-step Instructions**:

1. Decide on coverage tracking
   - Codecov.io is free for public GitHub repos
   - Provides coverage trend tracking
   - Shows per-PR coverage changes
   - Optional - not required for Phase 4 success
   - Skip this task if not interested

2. Sign up for Codecov (if proceeding)
   - Go to https://codecov.io
   - Sign in with GitHub
   - Grant permission to repository
   - Codecov should auto-detect your repo

3. Add Codecov upload steps to workflows
   - Already configured in task 1-2 steps (optional)
   - Uncomment if Codecov desired
   - Use action: `codecov/codecov-action@v3`

4. Create codecov.yml (optional)
   - Configure coverage requirements per file
   - Set minimum coverage percentages
   - Configure comment behavior on PRs
   - Example:
   ```yaml
   coverage:
     precision: 2
     round: down
     range: "70...100"
   comment:
     layout: "reach,diff,files,footer"
   ```

5. Verify Codecov integration
   - Push test branch
   - Codecov should comment on PR (if enabled)
   - Shows coverage summary
   - May take a few minutes to process

**Verification Checklist**:

- [ ] Codecov integration working (if configured)
- [ ] Coverage reports uploaded from CI
- [ ] Codecov comments on PRs (optional feature)
- [ ] Coverage trends tracked over time

**Note**: This task is optional. Coverage visibility is helpful but not critical.

**Commit Message Template**:

```
ci: configure Codecov for coverage tracking (optional)

- Add Codecov upload steps to workflows
- Create codecov.yml configuration
- Enable coverage reporting on PRs

Coverage trends now tracked in Codecov dashboard.
```

**Token Estimate**: ~1,500 tokens

---

## Task 5: Document CI/CD Process

**Goal**: Create documentation for team about CI/CD workflows

**Files to create/modify**:
- Create: `docs/CI_CD.md` (CI/CD process documentation)

**Prerequisites**:
- Tasks 1-4 complete

**Step-by-step Instructions**:

1. Create CI_CD.md documentation
   - Explain how workflows are triggered
   - Document what each workflow does
   - Show how to view workflow results
   - Explain status check behavior
   - Document how to debug failing workflows

2. Document workflow triggers
   - When workflows run (push to main, PR to main)
   - What triggers each workflow (path filters)
   - How long workflows typically take

3. Document status checks
   - Green checkmark = all tests passed
   - Red X = tests failed
   - Status is informational (doesn't block merge)
   - How to view details

4. Document workflow results
   - Where to find workflow logs
   - How to view test failures
   - How to view coverage reports
   - How to re-run workflows manually

5. Troubleshooting section
   - Workflow won't start (check paths, branches)
   - Tests fail in CI but pass locally (env differences)
   - Coverage report missing (check upload step)

6. Update main README
   - Reference CI_CD.md
   - Add badge showing CI status (optional)
   - Explain that tests run automatically

**Verification Checklist**:

- [ ] CI_CD.md is comprehensive and clear
- [ ] Explains how to view results
- [ ] Includes troubleshooting guide
- [ ] README updated with CI info
- [ ] Team can understand CI process from docs

**Testing Instructions**:

Review documentation:
```bash
cat docs/CI_CD.md

# Verify links work
grep -r "github.com/.*/actions" docs/CI_CD.md
```

**Commit Message Template**:

```
docs: add CI/CD process documentation

- Create docs/CI_CD.md with process explanation
- Document workflow triggers and behavior
- Add troubleshooting guide
- Update README with CI info
- Document how to view results and debug failures

Team can now understand CI/CD process from documentation.
```

**Token Estimate**: ~2,000 tokens

---

## Summary & Verification

**Phase 4 Completion Checklist**:

- [ ] Task 1: Frontend tests workflow created and running
- [ ] Task 2: Backend tests workflow created and running
- [ ] Task 3: Workflows verified and optimized
- [ ] Task 4: Coverage reporting configured (optional)
- [ ] Task 5: CI/CD documentation created
- [ ] Both workflows run on example branches
- [ ] Status checks appear on PRs (informational only)
- [ ] Workflows complete in reasonable time (10-15 min)

**CI/CD Capabilities**:

- ✅ Automated frontend tests on PR and push
- ✅ Automated backend tests, type checking, linting on PR and push
- ✅ Parallel test execution on multiple Node/Python versions
- ✅ Coverage reporting (if Codecov configured)
- ✅ Status checks appear on PRs (non-blocking)
- ✅ Developers can see full logs in Actions tab

**When all tasks complete**:

1. Verify both workflows appear in Actions tab
2. Test with example branch (push and create PR)
3. Confirm status checks appear on PR
4. Commit Phase 4 changes
5. **Proceed to Phase 5: Documentation**

---

## Notes

- Phase 4 is independent of Phases 1-3 (could be done after Phase 0 too)
- Status checks are informational only (don't block merges)
- Workflows are minimal per ADR 5 (tests only, no deployment)
- Coverage reporting is optional (helpful but not required)
- Workflows can be re-run manually from GitHub Actions tab

**Total Phase 4 Effort**: ~12,000 tokens

**Blocked By**: Phases 1-3 (need tests and code quality first)

**Blocks**: Phase 5 (can proceed in parallel)

---

**Ready to continue? When Phase 4 is complete, proceed to [Phase 5: Documentation](./Phase-5.md)**
