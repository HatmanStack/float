# CI/CD Process Documentation

This document explains how the Float project uses GitHub Actions for continuous integration, testing, and deployment.

## Overview

The Float project uses GitHub Actions to automatically run tests, code quality checks, and deploy infrastructure on pull requests and commits. Our comprehensive CI/CD pipeline includes:

- **Automated testing** on PR creation and commit pushes (unit, integration, E2E)
- **Coverage enforcement** (Backend 68%+, Frontend 75%+)
- **Automated staging deployment** on merge to main branch
- **Manual production deployment** with approval workflow
- **Fast feedback loop** for developers

## Workflows

The project has **4 GitHub Actions workflows**:

1. **Backend Tests** (`.github/workflows/backend-tests.yml`) - Comprehensive backend testing
2. **Frontend Tests** (`.github/workflows/frontend-tests.yml`) - Comprehensive frontend testing
3. **Deploy Backend Staging** (`.github/workflows/deploy-backend-staging.yml`) - Automated staging deployment
4. **Deploy Backend Production** (`.github/workflows/deploy-backend-production.yml`) - Manual production deployment

## Workflow Details

### 1. Backend Tests (`backend-tests.yml`)

**Triggers:**
- **Push** to any branch with backend changes
- **Pull Request** with backend changes

**Jobs:**

| Job | Purpose | Duration | Required for Merge |
|-----|---------|----------|-------------------|
| Lint | Ruff, Black, MyPy checks | 2-3 min | ✅ Yes |
| Unit Tests | Fast isolated tests | 3-5 min | ✅ Yes |
| Integration Tests | External API tests | 5-10 min | ⚠️ Optional (needs API keys) |
| E2E Tests | Full Lambda flow tests | 5-10 min | ⚠️ Optional (needs API keys) |
| Coverage | Combined coverage report | 5-10 min | ✅ Yes (must be 68%+) |

**Environment**: Python 3.12, Ubuntu Latest

**Coverage Threshold**: 68% (enforced)

### 2. Frontend Tests (`frontend-tests.yml`)

**Triggers:**
- **Push** to any branch with frontend changes
- **Pull Request** with frontend changes

**Jobs:**

| Job | Purpose | Duration | Required for Merge |
|-----|---------|----------|-------------------|
| Lint | ESLint, TypeScript, Prettier | 2-3 min | ✅ Yes |
| Component Tests | React component tests | 3-5 min | ✅ Yes |
| Integration Tests | Context/hook integration | 3-5 min | ✅ Yes |
| E2E Tests | Detox E2E (main only) | 15-30 min | ⚠️ Optional (main branch) |
| Coverage | Combined coverage report | 5-10 min | ✅ Yes (informational) |

**Environment**: Node.js 24.x, Ubuntu Latest

**Coverage Threshold**: 75% (informational, not enforced)

### 3. Deploy Backend Staging (`deploy-backend-staging.yml`)

**Triggers:**
- **Push to main** branch (automatic deployment)
- **Manual** via workflow_dispatch

**Steps:**
1. Validate SAM template
2. Build SAM application (with Docker)
3. Deploy to AWS CloudFormation stack: `float-meditation-staging`
4. Run smoke tests against deployed API
5. Check Lambda health
6. Post deployment summary to workflow

**Duration**: 10-15 minutes

**Requirements**:
- AWS credentials (from GitHub secrets)
- API keys for staging environment
- FFmpeg layer ARN

**Deployment Target**: AWS CloudFormation stack `float-meditation-staging`

### 4. Deploy Backend Production (`deploy-backend-production.yml`)

**Triggers:**
- **Manual only** via workflow_dispatch
- Requires confirmation: type "DEPLOY TO PRODUCTION"
- Requires deployment notes

**Steps:**
1. Pre-deployment checks (staging health, branch verification)
2. **Manual approval required** (GitHub environment protection)
3. Validate SAM template
4. Build SAM application
5. Create CloudFormation change set
6. **Review change set** (pause for manual verification)
7. Execute change set
8. Run production smoke tests
9. Monitor initial traffic for errors
10. Post deployment summary

**Duration**: 20-30 minutes

**Requirements**:
- Manual approval from designated reviewers
- Production AWS credentials
- Production API keys
- Production FFmpeg layer ARN

**Deployment Target**: AWS CloudFormation stack `float-meditation-production`

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

| Status                    | Meaning                           | Action Required                     |
| ------------------------- | --------------------------------- | ----------------------------------- |
| ✅ **All checks passed**  | All tests ran successfully        | Ready to merge                      |
| ❌ **Some checks failed** | Tests found issues                | Review logs, fix issues, push again |
| ⏳ **Running**            | Tests currently executing         | Wait for completion                 |
| ⊘ **Skipped**             | Workflow didn't run (path filter) | Normal if unrelated files changed   |

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

## GitHub Secrets Configuration

The following secrets must be configured in GitHub repository settings for CI/CD workflows to function:

### AWS Credentials

**Staging Environment:**
- `AWS_ACCESS_KEY_ID_STAGING` - AWS access key for staging deployments
- `AWS_SECRET_ACCESS_KEY_STAGING` - AWS secret key for staging deployments
- `AWS_REGION_STAGING` - AWS region (e.g., `us-east-1`)

**Production Environment:**
- `AWS_ACCESS_KEY_ID_PRODUCTION` - AWS access key for production deployments
- `AWS_SECRET_ACCESS_KEY_PRODUCTION` - AWS secret key for production deployments
- `AWS_REGION_PRODUCTION` - AWS region (e.g., `us-east-1`)

### API Keys

**Test Environment** (for integration/E2E tests):
- `G_KEY_TEST` - Google Gemini API key for testing
- `OPENAI_API_KEY_TEST` - OpenAI API key for testing
- `XI_KEY_TEST` - ElevenLabs API key for testing (optional)

**Staging Environment:**
- `G_KEY_STAGING` - Google Gemini API key for staging
- `OPENAI_API_KEY_STAGING` - OpenAI API key for staging
- `XI_KEY_STAGING` - ElevenLabs API key for staging

**Production Environment:**
- `G_KEY_PRODUCTION` - Google Gemini API key for production
- `OPENAI_API_KEY_PRODUCTION` - OpenAI API key for production
- `XI_KEY_PRODUCTION` - ElevenLabs API key for production

### Infrastructure

**FFmpeg Layer ARNs:**
- `FFMPEG_LAYER_ARN_STAGING` - Lambda layer ARN for staging (e.g., `arn:aws:lambda:us-east-1:123456789:layer:ffmpeg:1`)
- `FFMPEG_LAYER_ARN_PRODUCTION` - Lambda layer ARN for production

### GitHub Environments

Two GitHub Environments should be configured:

**`staging` Environment:**
- No special protection rules
- Automatically deployed on merge to main
- Uses staging secrets

**`production` Environment:**
- **Required reviewers**: 2+ people
- **Deployment branches**: main only
- **Wait timer**: Optional (e.g., 5 minutes)
- Uses production secrets

### How to Configure Secrets

1. Go to GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Enter secret name and value
4. Click **Add secret**
5. Repeat for all required secrets

### How to Configure Environments

1. Go to GitHub repository → **Settings** → **Environments**
2. Click **New environment**
3. Enter environment name (`staging` or `production`)
4. For production:
   - Enable **Required reviewers**
   - Add reviewer usernames
   - Enable **Deployment branches** → select main only
5. Click **Save protection rules**

### Secret Rotation

API keys and AWS credentials should be rotated regularly:

1. Generate new credentials in AWS Console / API provider
2. Update GitHub secrets with new values
3. Test in staging environment first
4. Update production secrets after verification
5. Revoke old credentials after successful deployment

## Deployment Process

### Staging Deployment (Automatic)

1. Create PR with backend or infrastructure changes
2. All tests must pass
3. Get code review approval
4. **Merge to main** branch
5. **Automatic deployment** workflow triggers
6. SAM builds and deploys to staging
7. Smoke tests verify deployment
8. Staging is updated with latest code

**Rollback**: If deployment fails, workflow provides rollback instructions.

### Production Deployment (Manual)

1. Verify staging is healthy and stable
2. Go to GitHub Actions → **Deploy Backend Production**
3. Click **Run workflow**
4. Fill in required inputs:
   - Confirmation: Type "DEPLOY TO PRODUCTION"
   - Deployment notes: Describe what changed
5. Click **Run workflow**
6. **Wait for approval** (GitHub environment protection)
7. Designated reviewers approve deployment
8. Workflow creates CloudFormation change set
9. **Review change set** in AWS Console
10. Workflow executes change set
11. Smoke tests verify production deployment
12. Monitor CloudWatch Logs for errors

**Rollback**: See workflow summary for rollback commands if deployment fails.

## Deployment Architecture

```
┌─────────────┐
│   GitHub    │
│  Repository │
└──────┬──────┘
       │
       │ Push to main
       │
       ▼
┌─────────────────────────────────┐
│  GitHub Actions                 │
│  (Deploy Backend Staging)       │
├─────────────────────────────────┤
│  1. Validate SAM template       │
│  2. Build with Docker           │
│  3. Deploy to AWS               │
│  4. Run smoke tests             │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  AWS CloudFormation             │
│  Stack: float-meditation-staging│
├─────────────────────────────────┤
│  - Lambda Function              │
│  - S3 Buckets                   │
│  - API Gateway HTTP API         │
│  - IAM Roles                    │
│  - CloudWatch Logs              │
└─────────────────────────────────┘

Production follows same flow but requires manual approval.
```

## Next Steps

With Phase 6 complete:

- **All 4 workflows** are configured and functional
- **Staging deploys automatically** on merge to main
- **Production deploys manually** with approval
- **All tests run** on every PR with coverage enforcement
- **Documentation** is complete and up-to-date
- **Project is production-ready**
