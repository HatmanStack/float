# Phase 0: Foundation & Architecture

## Phase Goal

Establish the architectural foundation, design decisions, and deployment patterns for the simplified Float deployment system. This phase defines the "law" that all subsequent implementation must follow, ensuring consistency and maintainability.

**Success Criteria:**
- Clear ADRs documenting all major decisions
- Deployment script logic fully specified
- Testing strategy defined with mocking approach
- Shared patterns and conventions established

**Estimated Tokens**: ~15,000

## Architecture Decision Records (ADRs)

### ADR-001: Single Environment Deployment

**Context**: Current system supports multiple environments (staging, production) with separate deployment scripts and configurations.

**Decision**: Simplify to single environment (default/development) deployment.

**Rationale**:
- Reduces cognitive overhead and maintenance burden
- Environment promotion can be handled through separate AWS accounts or stack names
- Most development workflows need only one active deployment
- Multi-environment support can be added later if genuinely needed (YAGNI principle)

**Consequences**:
- ✅ Simpler configuration management
- ✅ Fewer scripts to maintain
- ✅ Clearer deployment flow
- ⚠️ Environment-specific settings must be managed through stack names or AWS accounts

### ADR-002: Secrets in Gitignored samconfig.toml

**Context**: Need to manage sensitive API keys (Google Gemini, OpenAI, ElevenLabs) and configuration.

**Decision**: Store all secrets and configuration in `samconfig.toml`, add to `.gitignore`.

**Rationale**:
- Follows react-stocks pattern successfully used in production
- Simpler than AWS Secrets Manager for small projects
- Local development workflow is straightforward
- No additional AWS service dependencies or costs
- Clear separation between code (versioned) and secrets (local)

**Consequences**:
- ✅ Simple secret management
- ✅ No additional AWS services required
- ✅ Fast local iterations
- ⚠️ Developers must configure their own secrets locally
- ⚠️ Must ensure `.gitignore` is properly configured

### ADR-003: Colocated Infrastructure

**Context**: Current structure has separate `infrastructure/` directory with template.yaml and deployment scripts.

**Decision**: Move all infrastructure code into `backend/` directory, colocated with application code.

**Rationale**:
- Infrastructure-as-code is part of the backend application
- Follows react-stocks successful pattern
- Reduces directory hopping during development
- Clearer ownership and context
- Maintains monorepo structure for frontend separation

**Consequences**:
- ✅ Better code locality
- ✅ Simpler mental model
- ✅ Easier to find infrastructure code
- ⚠️ Requires migration of existing files

**New Structure**:
```
backend/
├── src/                    # Python application code
├── tests/                  # Backend-specific tests
├── scripts/                # Deployment scripts
│   ├── deploy.sh          # Main deployment script
│   ├── validate.sh        # Template validation
│   └── logs.sh            # CloudWatch logs viewer
├── template.yaml          # SAM template
├── samconfig.toml         # SAM configuration (gitignored)
├── .deploy-config.json    # Local deployment state (gitignored)
├── requirements.txt       # Python dependencies
├── pytest.ini             # Pytest configuration
├── ruff.toml              # Ruff linter configuration
├── lambda_function.py     # Lambda handler entry point
└── Makefile               # Development tasks only (not SAM build)
```

### ADR-004: Interactive Deployment Script

**Context**: Need balance between automation and developer control for deployment.

**Decision**: Implement interactive deployment script that prompts for missing configuration and persists locally.

**Rationale**:
- First-time setup is guided and user-friendly
- Subsequent deployments are automatic (no prompts)
- Secrets are saved locally, not committed
- Follows successful react-stocks pattern
- No reliance on SAM's `--guided` mode (we control the flow)

**Consequences**:
- ✅ Great developer experience
- ✅ No manual file editing required
- ✅ Secrets persist between deployments
- ⚠️ Requires shell script maintenance

### ADR-005: Standard SAM Build (No Makefile)

**Context**: Current system uses Makefile with `uv pip install` to work around pip issues.

**Decision**: Remove Makefile build integration, use standard SAM Python builder with requirements.txt only.

**Rationale**:
- Simpler is better (YAGNI)
- Remove pyproject.toml entirely (was causing build issues)
- Standard SAM conventions reduce surprises
- requirements.txt is sufficient for Lambda deployment
- Makefile can remain for development tasks (linting, testing) but not SAM builds

**Consequences**:
- ✅ Standard SAM workflow
- ✅ Fewer moving parts
- ✅ Better compatibility
- ⚠️ Development tools need separate config files

### ADR-006: Separate Tool Configuration Files

**Context**: pyproject.toml previously held both package metadata and tool configs (pytest, ruff, black, mypy).

**Decision**: Remove pyproject.toml, move tool configurations to separate standard files.

**Rationale**:
- Lambda deployment doesn't need package metadata
- Standard tool config files are more explicit
- Reduces confusion between development tools and deployment
- Each tool uses its canonical config file

**Tool Configuration Mapping**:
- pytest → `pytest.ini`
- ruff → `ruff.toml`
- mypy → `mypy.ini`
- black → `pyproject.toml` (minimal, black-only)
- coverage → `.coveragerc`

**Consequences**:
- ✅ Clear separation of concerns
- ✅ Standard tool usage
- ✅ No deployment confusion
- ⚠️ More config files to maintain

### ADR-007: Default FFmpeg Layer with Override

**Context**: Float backend requires FFmpeg Lambda layer for audio processing.

**Decision**: Provide public FFmpeg layer ARN as default, allow override via configuration.

**Rationale**:
- Out-of-box deployment experience
- Users can deploy without finding/building FFmpeg layer
- Advanced users can override with custom layer
- Public layer available: `arn:aws:lambda:us-east-1:145266761615:layer:ffmpeg:4`

**Consequences**:
- ✅ Immediate deployment capability
- ✅ Flexibility for custom layers
- ⚠️ Region-specific ARN (users in other regions must override)

### ADR-008: Programmatic samconfig.toml Generation

**Context**: SAM CLI offers `--guided` mode for interactive configuration.

**Decision**: Build samconfig.toml programmatically in deploy script, avoid `--guided` mode.

**Rationale**:
- Full control over configuration flow
- Can prompt in logical order
- Can validate inputs before saving
- Can read/merge existing configuration
- No surprises from SAM's guided mode behavior
- Consistent experience across SAM versions

**Consequences**:
- ✅ Predictable deployment flow
- ✅ Better error handling
- ✅ Custom validation logic
- ⚠️ Must maintain config generation code

## Deployment Script Specification

### Script: `backend/scripts/deploy.sh`

**Purpose**: Interactive deployment script that handles configuration, building, deployment, and environment setup.

**Behavior Flow**:

1. **Pre-flight Checks**
   - Verify in backend/ directory (template.yaml exists)
   - Check AWS CLI installed and configured (`aws sts get-caller-identity`)
   - Check SAM CLI installed (`sam --version`)
   - Display AWS account information

2. **Configuration Discovery**
   - Check for `.deploy-config.json` (local deployment state)
   - Check for `samconfig.toml` (SAM configuration)
   - Identify missing required parameters

3. **Interactive Prompts** (if configuration incomplete)
   - Stack name (default: `float-meditation-dev`)
   - AWS Region (default: `us-east-1`)
   - FFmpeg Layer ARN (default: `arn:aws:lambda:us-east-1:145266761615:layer:ffmpeg:4`)
   - Google Gemini API Key (masked input)
   - OpenAI API Key (masked input)
   - ElevenLabs API Key (optional, masked input)
   - Voice configuration (defaults provided)

4. **Configuration Persistence**
   - Save inputs to `.deploy-config.json` (JSON format)
   - Generate `samconfig.toml` from template with injected values
   - Both files are gitignored

5. **Build Phase**
   - Run `sam build` (no flags, uses template.yaml defaults)
   - Standard Python 3.13 builder (no Makefile)

6. **Deployment Phase**
   - Run `sam deploy` (uses samconfig.toml configuration)
   - Captures CloudFormation outputs

7. **Post-Deployment**
   - Extract stack outputs (API Gateway URL, Function ARN, S3 Bucket)
   - Generate/update `../frontend/.env` file with outputs
   - Display deployment summary

8. **Error Handling**
   - Clear error messages for common failures
   - Rollback guidance if deployment fails
   - Validation failures stop before deployment

**File: `.deploy-config.json`** (gitignored)
```json
{
  "stackName": "float-meditation-dev",
  "region": "us-east-1",
  "ffmpegLayerArn": "arn:aws:lambda:us-east-1:145266761615:layer:ffmpeg:4",
  "geminiApiKey": "***",
  "openaiApiKey": "***",
  "elevenLabsApiKey": "",
  "voiceId": "jKX50Q2OBT1CsDwwcTkZ",
  "similarityBoost": "0.7",
  "stability": "0.3",
  "voiceStyle": "0.3"
}
```

**File: `samconfig.toml`** (generated, gitignored)
```toml
version = 0.1

[default.global.parameters]
stack_name = "float-meditation-dev"
region = "us-east-1"

[default.build.parameters]
cached = true
parallel = true

[default.deploy.parameters]
capabilities = "CAPABILITY_IAM"
confirm_changeset = false
resolve_s3 = true
s3_prefix = "float-meditation-dev"
region = "us-east-1"
parameter_overrides = "FFmpegLayerArn=\"arn:aws:lambda:...\" GKey=\"***\" OpenAIKey=\"***\" XIKey=\"***\" SimilarityBoost=\"0.7\" Stability=\"0.3\" VoiceStyle=\"0.3\" VoiceId=\"jKX50Q2OBT1CsDwwcTkZ\""
```

### Script: `backend/scripts/validate.sh`

**Purpose**: Validate SAM template.yaml before deployment.

**Behavior**:
- Run `sam validate --template template.yaml --lint`
- Display validation results
- Exit with non-zero code on failure

### Script: `backend/scripts/logs.sh`

**Purpose**: Stream CloudWatch logs for deployed Lambda function.

**Behavior**:
- Read stack name from `.deploy-config.json` or samconfig.toml
- Determine function name from stack
- Run `aws logs tail /aws/lambda/{function-name} --follow`
- Handle cases where stack not deployed

## Testing Strategy

### Overview

CI pipeline runs linting, unit tests, and mocked integration tests. **No live AWS resources in CI**.

### Test Categories

**1. Unit Tests** (`backend/tests/unit/`)
- Test individual functions and classes in isolation
- Mock all external dependencies (AWS services, API calls)
- Fast execution (< 1 second per test)
- 100% mockable, no network calls
- Pattern: pytest with pytest-mock

**2. Integration Tests** (`backend/tests/integration/`)
- Test interactions between components
- Mock external services (AWS SDK, HTTP APIs)
- Use moto for AWS service mocking
- Verify service integration logic
- Pattern: pytest with moto + pytest-mock

**3. E2E Tests** (`tests/e2e/`)
- Test full user workflows
- Frontend + Backend integration
- Mock backend API calls (no live Lambda)
- Pattern: Detox for mobile, mock API responses

### Mocking Strategy

**AWS Services** (using moto):
```python
import boto3
from moto import mock_s3, mock_lambda

@mock_s3
def test_s3_storage():
    # S3 client uses moto-mocked S3
    s3 = boto3.client('s3', region_name='us-east-1')
    # Test S3 storage service logic
```

**External APIs** (using pytest-mock):
```python
def test_gemini_service(mocker):
    # Mock Google Generative AI SDK
    mock_model = mocker.patch('google.generativeai.GenerativeModel')
    mock_model.return_value.generate_content.return_value = Mock(text="meditation")
    # Test service logic without real API calls
```

**Environment Variables**:
```python
@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
```

### CI Pipeline Configuration

**GitHub Actions** (`.github/workflows/test.yml`):
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      # Linting
      - name: Lint with ruff
        run: |
          pip install ruff
          ruff check backend/src backend/tests

      # Unit Tests
      - name: Run unit tests
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-mock pytest-cov moto
          pytest tests/unit -v --cov=src

      # Integration Tests (Mocked)
      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration -v
```

**Key Principles**:
- ✅ No AWS credentials in CI
- ✅ No live resource creation
- ✅ Fast test execution (< 5 minutes total)
- ✅ Reproducible results
- ✅ No external API calls

## Shared Patterns and Conventions

### Commit Message Format

**Template**:
```
type(scope): brief description

Detail 1
Detail 2

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

**Types**: feat, fix, refactor, test, docs, chore, ci

**Examples**:
```
refactor(deploy): simplify deployment to single script

- Consolidate deploy-staging.sh and deploy-production.sh
- Interactive prompts for missing configuration
- Generate samconfig.toml programmatically

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

### File Naming Conventions

- Scripts: `kebab-case.sh` (e.g., `deploy.sh`, `validate.sh`)
- Python: `snake_case.py` (e.g., `lambda_function.py`)
- Config: `lowercase.ext` (e.g., `pytest.ini`, `ruff.toml`)
- Documentation: `UPPERCASE.md` or `PascalCase.md`

### Code Organization

**Backend Structure**:
```
backend/
├── src/              # Application code (DRY, testable)
│   ├── config/       # Configuration and constants
│   ├── handlers/     # Lambda handlers and middleware
│   ├── models/       # Data models (Pydantic)
│   ├── services/     # Business logic (testable, mockable)
│   ├── providers/    # External service integrations
│   └── utils/        # Shared utilities
├── tests/            # Test suite (mirrors src/ structure)
│   ├── unit/         # Unit tests (fast, isolated)
│   ├── integration/  # Integration tests (mocked externals)
│   └── fixtures/     # Test data and mocks
└── scripts/          # Deployment and utility scripts
```

### Python Code Standards

- **Type Hints**: Use for all function signatures
- **Docstrings**: Only where logic is non-obvious (avoid restating code)
- **Error Handling**: Raise specific exceptions, catch narrowly
- **Mocking**: Inject dependencies for testability
- **Pydantic Models**: Use for all API request/response validation

### Shell Script Standards

- **Set flags**: `set -e` (exit on error)
- **Functions**: Use for reusable logic
- **Error messages**: Clear, actionable, with context
- **User prompts**: Show defaults, allow empty for defaults
- **Comments**: Only for complex logic, not obvious steps

## Phase Verification

### Completion Criteria

- [ ] All ADRs documented and reviewed
- [ ] Deployment script specification complete
- [ ] Testing strategy defined with mock examples
- [ ] Shared patterns established
- [ ] Phase-1 tasks can reference this foundation

### Integration Points

Phase-1 implementation will reference:
- ADR decisions for architectural choices
- Deployment script spec for implementation details
- Testing strategy for test creation
- Shared patterns for code style and commits

### Known Limitations

- Single environment only (multi-environment requires separate effort)
- Region-specific FFmpeg layer default (us-east-1)
- No automated stack teardown script (manual via CloudFormation console)
- Secrets in local files (not centralized secret management)
