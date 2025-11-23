# Phase 1: Implementation & Migration

## Phase Goal

Migrate the Float meditation app from complex multi-script infrastructure to a simplified, single-environment deployment system. Transform the current infrastructure/ directory setup into a colocated backend/ structure with interactive deployment scripts and clean configuration management.

**Success Criteria:**
- Backend directory contains all infrastructure code
- Single `npm run deploy` command works end-to-end
- Secrets never committed (gitignored properly)
- All tests pass without live AWS resources
- Clean migration with no orphaned files

**Estimated Tokens**: ~85,000

## Prerequisites

- Phase-0 foundation reviewed and understood
- Development environment setup (AWS CLI, SAM CLI, Python 3.13, Node.js)
- Access to AWS account for testing deployment
- API keys available for testing (can use test/dummy keys)

## Tasks

### Task 1: Prepare Backend Directory and Update .gitignore

**Goal**: Set up the backend directory to receive infrastructure files and ensure secrets will not be committed.

**Files to Modify/Create:**
- `backend/.gitignore` - Add deployment config and secrets
- `.gitignore` - Update root gitignore if needed

**Prerequisites:**
- None (first task)

**Implementation Steps:**

1. Navigate to backend/ directory and create .gitignore (file does not currently exist)
2. Add entries for deployment-related files that should never be committed:
   - `samconfig.toml` (will contain secrets)
   - `.deploy-config.json` (local deployment state)
   - `.env` (may contain sensitive outputs)
   - `.aws-sam/` (SAM build artifacts)
3. Ensure existing Python artifacts are already ignored (`__pycache__`, `*.pyc`, etc.)
4. Verify root .gitignore doesn't override backend-specific rules
5. Test gitignore rules using `git check-ignore -v` to confirm patterns match

**Verification Checklist:**
- [x] `backend/.gitignore` contains `samconfig.toml`
- [x] `backend/.gitignore` contains `.deploy-config.json`
- [x] `backend/.gitignore` contains `.aws-sam/`
- [x] Git status shows these files as ignored when created
- [x] Existing Python patterns still work

**Testing Instructions:**
- Create dummy `backend/samconfig.toml` file
- Run `git status` and verify it's not shown
- Run `git check-ignore -v backend/samconfig.toml` and verify it matches gitignore pattern
- Delete dummy file after verification

**Commit Message Template:**
```
chore(backend): add gitignore rules for deployment secrets

- Add samconfig.toml to prevent secret commits
- Add .deploy-config.json for local deployment state
- Add .aws-sam/ for SAM build artifacts
- Ensure deployment configuration stays local

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 2: Create Tool Configuration Files

**Goal**: Extract development tool configurations from pyproject.toml into separate standard files before removing pyproject.toml.

**Files to Create:**
- `backend/pytest.ini` - Pytest configuration
- `backend/ruff.toml` - Ruff linter configuration
- `backend/mypy.ini` - MyPy type checker configuration
- `backend/.coveragerc` - Coverage.py configuration

**Prerequisites:**
- Task 1 complete

**Implementation Steps:**

1. Read current `backend/pyproject.toml` to extract tool configurations
2. Create `pytest.ini` with test paths, markers, coverage settings:
   - testpaths pointing to tests/
   - markers for unit, integration, slow tests
   - coverage source and omit patterns
   - addopts for coverage reports
3. Create `ruff.toml` with linting rules:
   - line-length: 100
   - target-version: py313
   - select and ignore rules from current config
4. Create `mypy.ini` with type checking settings:
   - python_version = 3.13
   - strict settings from current config
   - module ignores if needed
5. Create `.coveragerc` with coverage settings:
   - source paths
   - omit patterns
   - exclude_lines for pragma, TYPE_CHECKING, etc.
6. Verify each tool still works with new config files:
   - Run `pytest --collect-only` to verify pytest.ini
   - Run `ruff check src/` to verify ruff.toml
   - Run `mypy src/` to verify mypy.ini
   - Run `pytest --cov` to verify coverage config

**Verification Checklist:**
- [x] `pytest.ini` exists with correct test paths
- [x] `ruff.toml` exists with Python 3.13 target
- [x] `mypy.ini` exists with Python 3.13 setting
- [x] `.coveragerc` exists with source and omit patterns
- [x] `pytest --collect-only` succeeds
- [x] `ruff check src/` succeeds
- [x] `mypy src/` runs (errors OK, but config loads)
- [x] Coverage runs with correct settings

**Testing Instructions:**
- Run pytest collection: `cd backend && pytest --collect-only`
- Run ruff: `ruff check src/`
- Run mypy: `mypy src/ --show-error-codes`
- Run coverage: `pytest --cov=src --cov-report=term-missing`
- Verify all tools use new config files (check output for config file paths)

**Commit Message Template:**
```
refactor(backend): extract tool configs from pyproject.toml

- Create pytest.ini for test configuration
- Create ruff.toml for linter settings
- Create mypy.ini for type checking
- Create .coveragerc for coverage reporting
- Prepare for pyproject.toml removal

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 2.5: Create Development Dependencies File

**Goal**: Extract development dependencies into separate requirements-dev.txt before removing pyproject.toml, ensuring CI and local development can install dev tools.

**Files to Create:**
- `backend/requirements-dev.txt`

**Prerequisites:**
- Task 2 complete (tool configs migrated)

**Implementation Steps:**

1. Create `backend/requirements-dev.txt` with all development dependencies:
   ```
   pytest>=8.4.2
   pytest-mock>=3.11.0
   pytest-cov>=4.1.0
   moto[all]>=4.0.0
   ruff>=0.1.0
   black>=23.9.0
   mypy>=1.5.0
   types-requests
   types-python-dateutil
   ```
2. These dependencies were previously in `pyproject.toml` under `[project.optional-dependencies].dev`
3. Pin versions based on current pyproject.toml specifications
4. Test installation in clean environment:
   ```bash
   python3.13 -m venv test-env
   source test-env/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
5. Verify all dev tools work:
   - `pytest --version`
   - `ruff --version`
   - `mypy --version`
   - `black --version`
6. Run test suite to confirm dependencies sufficient:
   ```bash
   pytest tests/unit -v
   ruff check src/
   mypy src/
   ```

**Verification Checklist:**
- [x] `requirements-dev.txt` created with all dev dependencies
- [x] All dependencies have version pins (>=)
- [x] File includes pytest, pytest-mock, pytest-cov, moto
- [x] File includes ruff, black, mypy, types packages
- [x] Clean install succeeds: `pip install -r requirements-dev.txt`
- [x] All dev tools execute: pytest, ruff, mypy, black
- [x] Test suite runs successfully
- [x] No missing dependency errors

**Testing Instructions:**
- Create isolated environment:
  ```bash
  cd backend
  python3.13 -m venv .venv-test
  source .venv-test/bin/activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt
  ```
- Run full development workflow:
  ```bash
  pytest tests/unit -v           # Should pass
  ruff check src/ tests/         # Should pass
  mypy src/                      # Should run
  black --check src/ tests/      # Should run
  pytest --cov=src tests/        # Should generate coverage
  ```
- Deactivate and remove test env:
  ```bash
  deactivate
  rm -rf .venv-test
  ```

**Commit Message Template:**
```
feat(backend): create requirements-dev.txt for development dependencies

- Extract dev dependencies from pyproject.toml
- Create requirements-dev.txt with pinned versions
- Include pytest, ruff, mypy, black, moto
- Prepare for pyproject.toml removal
- Enable CI to install dev tools separately

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 3: Remove pyproject.toml Build Configuration

**Goal**: Remove pyproject.toml entirely to eliminate SAM build conflicts and simplify dependency management.

**Files to Modify/Delete:**
- `backend/pyproject.toml` - DELETE
- `backend/requirements.txt` - Verify and clean

**Prerequisites:**
- Task 2 complete (tool configs migrated)
- Task 2.5 complete (requirements-dev.txt created)

**Implementation Steps:**

1. Verify requirements.txt is clean:
   - Ensure no `-e .` editable install line exists
   - All dependencies are pinned versions
   - No references to pyproject.toml
2. Delete `backend/pyproject.toml` entirely
3. Test that SAM can build without pyproject.toml:
   - Run `sam build --use-container` in a test directory
   - Verify Python dependencies install correctly
   - Check for absence of "Invalid distribution name" errors
4. Verify development tools still work with separate config files:
   - pytest uses pytest.ini
   - ruff uses ruff.toml
   - mypy uses mypy.ini
5. Update any documentation that references pyproject.toml

**Verification Checklist:**
- [x] `pyproject.toml` does not exist
- [x] `requirements.txt` has no `-e .` line
- [x] All dependencies in requirements.txt have version pins
- [x] `requirements-dev.txt` exists with dev dependencies
- [x] CI can install deps: `pip install -r requirements.txt -r requirements-dev.txt`
- [x] `sam build` completes without errors (test in safe directory)
- [x] `pytest` runs using pytest.ini
- [x] `ruff check` runs using ruff.toml
- [x] `mypy` runs using mypy.ini

**Testing Instructions:**
- Create test SAM build:
  ```bash
  cd backend
  sam build --template ../infrastructure/template.yaml
  # Should complete without "Invalid distribution name" error
  ```
- Run development tools:
  ```bash
  pytest --version  # Should show pytest.ini in use
  ruff check src/
  mypy src/
  ```
- Verify no import errors related to missing package metadata

**Commit Message Template:**
```
refactor(backend): remove pyproject.toml build configuration

- Delete pyproject.toml entirely
- Rely on requirements.txt for dependencies
- Remove editable install reference
- Simplify SAM build process
- Tool configs now in separate files

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 4: Migrate Infrastructure Files to Backend

**Goal**: Move template.yaml, samconfig.toml, scripts/, and related files from infrastructure/ to backend/.

**Files to Move:**
- `infrastructure/template.yaml` → `backend/template.yaml`
- `infrastructure/samconfig.toml` → `backend/samconfig.toml` (will be regenerated)
- `infrastructure/scripts/` → `backend/scripts/` (will be rewritten)
- `infrastructure/test-requests/` → `backend/test-requests/`
- `infrastructure/parameters/` → DELETE (using samconfig.toml instead)

**Prerequisites:**
- Task 1 complete (gitignore updated)
- Task 3 complete (pyproject.toml removed)

**Implementation Steps:**

1. Create `backend/scripts/` directory if it doesn't exist
2. Move template.yaml:
   - Copy `infrastructure/template.yaml` to `backend/template.yaml`
   - Update CodeUri to point to current directory (`.` instead of `../backend/`)
3. Move test-requests for later use:
   - Copy `infrastructure/test-requests/` to `backend/test-requests/`
4. DO NOT move existing scripts yet (will be rewritten in later tasks)
5. DO NOT move samconfig.toml (will be regenerated by deploy script)
6. Verify template.yaml is valid after move:
   - Run `sam validate --template backend/template.yaml --lint`
7. Keep infrastructure/ directory for now (will clean up in final task)

**Verification Checklist:**
- [x] `backend/template.yaml` exists
- [x] `backend/test-requests/` directory exists with JSON files
- [x] `backend/scripts/` directory exists (may be empty)
- [x] Template CodeUri updated to `.` (current directory)
- [x] `sam validate` succeeds on new template location
- [x] Infrastructure directory still exists (not deleted yet)

**Testing Instructions:**
- Validate template: `sam validate --template backend/template.yaml --lint`
- Check template syntax: `cat backend/template.yaml | grep CodeUri` (should show `.`)
- Verify test requests: `ls -la backend/test-requests/`

**Commit Message Template:**
```
refactor(infrastructure): migrate template to backend directory

- Move template.yaml to backend/
- Update CodeUri to current directory
- Move test-requests to backend/
- Prepare for infrastructure consolidation

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 5: Update template.yaml for Simplified Deployment

**Goal**: Modify template.yaml to support single-environment deployment with sensible defaults and remove unnecessary complexity.

**Files to Modify:**
- `backend/template.yaml`

**Prerequisites:**
- Task 4 complete (template migrated)

**Implementation Steps:**

1. Update Parameters section:
   - Remove `Environment` parameter (single environment only)
   - Add default value to FFmpegLayerArn: `arn:aws:lambda:us-east-1:145266761615:layer:ffmpeg:4`
   - Make FFmpegLayerArn pattern validation less strict (allow overrides)
   - Keep all API key parameters (GKey, OpenAIKey, XIKey)
   - Add description notes about defaults
2. Update Globals section:
   - Keep timeout, memory, runtime settings
   - Remove any environment-specific conditional logic
3. Update FloatMeditationFunction:
   - Remove `Metadata.BuildMethod: makefile` (use standard Python builder)
   - Update FunctionName to remove Environment reference: `float-meditation`
   - Keep all other properties (Layers, Role, Events, Environment variables)
   - Update Environment variables to remove Environment reference
4. Update S3 bucket names and resources:
   - Remove Environment suffix from resource names
   - Use simple naming: `float-meditation-audio`
5. Update outputs:
   - Remove Environment references from output names
   - Ensure outputs are consumable by frontend .env generation
6. Add comments explaining simplified deployment model
7. Validate template after changes

**Verification Checklist:**
- [x] No `Environment` parameter exists
- [x] FFmpegLayerArn has default value
- [x] Function name is `float-meditation` (no variable)
- [x] No BuildMethod metadata on function
- [x] All parameters have descriptions
- [x] Template validates successfully
- [x] Outputs section has all needed values (API URL, bucket, function ARN)

**Testing Instructions:**
- Validate template: `sam validate --template backend/template.yaml --lint`
- Check for Environment references: `grep -i "environment" backend/template.yaml` (should only be ENV vars, not parameter)
- Verify FFmpeg default: `grep "FFmpegLayerArn" backend/template.yaml -A 3`
- Review outputs: `grep -A 20 "^Outputs:" backend/template.yaml`

**Commit Message Template:**
```
refactor(template): simplify for single-environment deployment

- Remove Environment parameter (single env only)
- Add default FFmpeg layer ARN for us-east-1
- Remove Makefile build method (use standard Python)
- Simplify function and resource naming
- Update outputs for frontend consumption

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 6: Create Deployment Script

**Goal**: Implement the interactive deployment script that handles configuration, building, deploying, and environment file generation.

**Files to Create:**
- `backend/scripts/deploy.sh`
- `backend/.deploy-config.json.template` (example structure)

**Prerequisites:**
- Task 4 complete (scripts directory exists)
- Task 5 complete (template updated)
- Phase-0 deployment script specification reviewed

**Implementation Steps:**

1. Create `deploy.sh` with proper shell header:
   - `#!/bin/bash`
   - `set -e` for error handling
   - Script should be executable
2. Implement pre-flight checks:
   - Verify running in backend/ directory (check for template.yaml)
   - Check AWS CLI installed and configured
   - Check SAM CLI installed
   - Display AWS account information
3. Implement configuration discovery:
   - Check for `.deploy-config.json` existence
   - Check for `samconfig.toml` existence
   - Parse existing values if files exist
4. Implement interactive prompts for missing configuration:
   - Stack name with default `float-meditation-dev`
   - AWS region with default `us-east-1`
   - FFmpeg layer ARN with default (from Phase-0)
   - Google Gemini API key (masked input, show last 4 if exists)
   - OpenAI API key (masked input, show last 4 if exists)
   - ElevenLabs API key (optional, masked input)
   - Voice configuration with defaults (similarity, stability, style, voiceId)
   - Skip prompts for values that already exist
5. Implement configuration persistence:
   - Save all values to `.deploy-config.json` (JSON format)
   - Generate `samconfig.toml` with proper structure (see Phase-0 spec)
   - Use proper escaping for parameter_overrides
6. Implement build phase:
   - Echo build status
   - Run `sam build` (no flags)
   - Check for build errors
7. Implement deployment phase:
   - Echo deployment status
   - Run `sam deploy` (uses samconfig.toml)
   - Capture deployment outputs
8. Implement post-deployment:
   - Extract stack outputs using AWS CLI
   - Generate `../frontend/.env` file with:
     - EXPO_PUBLIC_LAMBDA_FUNCTION_URL=<ApiEndpoint>
     - EXPO_PUBLIC_S3_BUCKET=<AudioBucket>
   - Display success summary with next steps
9. Implement error handling:
   - Trap errors and display helpful messages
   - Provide rollback guidance
   - Clean up partial state on failure

**Verification Checklist:**
- [x] Script is executable (`chmod +x`)
- [x] Pre-flight checks verify AWS and SAM CLI
- [x] Interactive prompts work with defaults
- [x] `.deploy-config.json` is created with correct structure
- [x] `samconfig.toml` is generated with proper format
- [x] `sam build` executes successfully
- [x] `sam deploy` executes successfully
- [x] Frontend `.env` file is generated
- [x] Script handles errors gracefully

**Testing Instructions:**

**Unit-level testing** (manual):
- Run script with no config: `./scripts/deploy.sh`
  - Verify all prompts appear
  - Test with dummy values
  - Check generated files
- Run script with existing config: `./scripts/deploy.sh`
  - Verify no prompts appear
  - Check it uses saved values
- Test error conditions:
  - Remove AWS credentials, verify error message
  - Provide invalid API key format, verify validation

**Integration testing** (requires AWS):
- Full deployment with test API keys
- Verify stack creation in CloudFormation
- Verify frontend .env has correct values
- Test subsequent deployment (should skip prompts)

**Mock testing** (for CI):
- Create unit tests in `tests/unit/test_deploy_script.sh`:
  - Test configuration parsing logic
  - Test samconfig.toml generation
  - Test .env generation from mock outputs
  - Mock AWS CLI and SAM CLI calls

**Commit Message Template:**
```
feat(deploy): create interactive deployment script

- Implement pre-flight checks for AWS/SAM CLI
- Add interactive prompts for missing configuration
- Generate samconfig.toml programmatically
- Persist configuration in .deploy-config.json
- Auto-generate frontend .env from stack outputs
- Handle errors with clear messaging

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 7: Create Validation Script

**Goal**: Create a simple script to validate the SAM template before deployment.

**Files to Create:**
- `backend/scripts/validate.sh`

**Prerequisites:**
- Task 4 complete (scripts directory exists)

**Implementation Steps:**

1. Create `validate.sh` with shell header and error handling
2. Implement template validation:
   - Check template.yaml exists in current directory
   - Run `sam validate --template template.yaml --lint`
   - Display validation results clearly
3. Handle validation errors:
   - Exit with non-zero code on failure
   - Display error details
   - Provide guidance for common issues
4. Add success message
5. Make script executable

**Verification Checklist:**
- [x] Script is executable
- [x] Validates template.yaml successfully
- [x] Shows clear error messages on validation failure
- [x] Exits with appropriate exit codes (0=success, 1=failure)
- [x] Can be run from backend/ directory

**Testing Instructions:**
- Run on valid template: `cd backend && ./scripts/validate.sh`
  - Should show success message
  - Should exit with code 0
- Test with invalid template:
  - Temporarily break template YAML syntax
  - Run script, verify error shown
  - Restore template
- Verify lint flag works (catches template issues)

**Commit Message Template:**
```
feat(deploy): add template validation script

- Create validate.sh for pre-deployment checks
- Run sam validate with lint flag
- Provide clear error messaging
- Exit with appropriate codes

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 8: Create Logs Script

**Goal**: Create a script to easily view CloudWatch logs for the deployed Lambda function.

**Files to Create:**
- `backend/scripts/logs.sh`

**Prerequisites:**
- Task 6 complete (deploy script creates config)

**Implementation Steps:**

1. Create `logs.sh` with shell header
2. Implement configuration reading:
   - Try to read stack name from `.deploy-config.json`
   - Fallback to reading from `samconfig.toml`
   - Fallback to prompting user for stack name
3. Implement function name determination:
   - Function name is based on stack: `float-meditation`
   - Build log group name: `/aws/lambda/float-meditation`
4. Implement log streaming:
   - Use AWS CLI to tail logs: `aws logs tail /aws/lambda/{function-name} --follow`
   - Add optional parameters (--since, --filter-pattern)
   - Handle case where function doesn't exist yet
5. Add usage instructions in comments
6. Make script executable

**Verification Checklist:**
- [x] Script is executable
- [x] Reads configuration correctly
- [x] Determines function name correctly
- [x] Streams logs from CloudWatch
- [x] Handles missing deployment gracefully
- [x] Can accept optional time filter (--since 1h)

**Testing Instructions:**
- Test with deployed stack:
  - Deploy stack first (Task 6)
  - Run `./scripts/logs.sh`
  - Invoke function to generate logs
  - Verify logs appear in stream
- Test with no deployment:
  - Remove .deploy-config.json
  - Run script, verify error handling
- Test with time filter:
  - `./scripts/logs.sh --since 1h`
  - Verify only recent logs shown

**Commit Message Template:**
```
feat(deploy): add CloudWatch logs viewer script

- Create logs.sh to stream Lambda logs
- Auto-detect function name from config
- Support time filtering (--since flag)
- Handle missing deployment gracefully

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 9: Update Backend Package.json

**Goal**: Add npm scripts for deployment commands to provide consistent developer interface.

**Files to Modify/Create:**
- `backend/package.json` - Create if doesn't exist

**Prerequisites:**
- Task 6, 7, 8 complete (scripts created)

**Implementation Steps:**

1. Check if `backend/package.json` exists:
   - If not, create minimal package.json
   - If exists, update scripts section
2. Add deployment scripts:
   - `"deploy": "./scripts/deploy.sh"`
   - `"validate": "./scripts/validate.sh"`
   - `"logs": "./scripts/logs.sh"`
   - `"build": "sam build"`
3. Add project metadata (if creating new):
   - name: "float-backend"
   - version: "1.0.0"
   - private: true
   - description: "Float meditation backend deployment scripts"
4. Ensure scripts are executable before adding to package.json
5. Test npm scripts work from backend/ directory

**Verification Checklist:**
- [x] `package.json` exists in backend/
- [x] "deploy" script points to deploy.sh
- [x] "validate" script points to validate.sh
- [x] "logs" script points to logs.sh
- [x] "build" script runs sam build
- [x] All script files are executable
- [x] `npm run deploy` works from backend/
- [x] `npm run validate` works from backend/
- [x] `npm run logs` works from backend/

**Testing Instructions:**
- From backend/ directory:
  ```bash
  npm run validate  # Should validate template
  npm run deploy    # Should start deployment (can cancel)
  npm run logs      # Should stream logs (requires deployed stack)
  npm run build     # Should run sam build
  ```
- Verify each command executes the corresponding script
- Check that errors from scripts are properly shown

**Commit Message Template:**
```
feat(deploy): add npm scripts for deployment commands

- Add npm run deploy for deployment
- Add npm run validate for template validation
- Add npm run logs for CloudWatch logs
- Add npm run build for SAM building
- Provide consistent developer interface

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 10: Update Backend Makefile

**Goal**: Update Makefile to remove SAM build target and keep only development quality checks.

**Files to Modify:**
- `backend/Makefile`

**Prerequisites:**
- Task 3 complete (pyproject.toml removed)
- Task 9 complete (npm scripts added)

**Implementation Steps:**

1. Read current Makefile
2. Remove the `build-FloatMeditationFunction` target:
   - This was used for SAM builds with uv pip
   - No longer needed with standard SAM builder
3. Keep development targets:
   - test (pytest)
   - lint (ruff)
   - format (black)
   - type-check (mypy)
   - quality (all checks)
4. Update .PHONY declaration to remove build target
5. Update help text to remove build references
6. Verify remaining targets still work

**Verification Checklist:**
- [x] `build-FloatMeditationFunction` target removed
- [x] Development targets remain (test, lint, format, type-check)
- [x] .PHONY updated correctly
- [x] `make test` runs pytest
- [x] `make lint` runs ruff
- [x] `make type-check` runs mypy
- [x] `make quality` runs all checks
- [x] Help text updated

**Testing Instructions:**
- Run each make target:
  ```bash
  cd backend
  make test
  make lint
  make type-check
  make format-check
  make quality
  ```
- Verify no references to SAM build
- Verify all development tools still work

**Commit Message Template:**
```
refactor(backend): remove SAM build from Makefile

- Remove build-FloatMeditationFunction target
- Keep development quality check targets
- Update help text and PHONY declarations
- SAM builds now via npm run build

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 11: Create Deployment Script Tests

**Goal**: Create unit tests for deployment script logic to ensure CI can verify deployment code without AWS resources.

**Files to Create:**
- `backend/tests/unit/test_deploy_helpers.py` - Test helper functions
- `backend/scripts/deploy-helpers.sh` - Extract testable functions from deploy.sh

**Prerequisites:**
- Task 6 complete (deploy script created)

**Implementation Steps:**

1. Refactor deploy.sh to extract testable functions into `deploy-helpers.sh`:
   - `generate_samconfig_toml()` - Generate samconfig content from config
   - `generate_env_file()` - Generate .env content from stack outputs
   - `parse_deploy_config()` - Parse .deploy-config.json
   - `validate_api_key_format()` - Basic API key validation
2. Create test fixtures in `tests/fixtures/`:
   - `sample-deploy-config.json` - Example configuration
   - `sample-stack-outputs.json` - Mock CloudFormation outputs
3. Create Python tests that:
   - Mock subprocess calls to bash functions
   - Test samconfig.toml generation with various inputs
   - Test .env generation from mock outputs
   - Test config validation logic
   - Test error handling for missing required values
4. Add test to verify gitignore prevents committing secrets:
   - Create temporary samconfig.toml
   - Run `git check-ignore`
   - Verify file is ignored
5. Create bash test harness if needed for shell-specific testing

**Verification Checklist:**
- [x] Helper functions extracted from deploy.sh
- [x] Test fixtures created for configuration
- [x] Python tests cover configuration parsing
- [x] Tests verify samconfig.toml generation
- [x] Tests verify .env file generation
- [x] Tests verify gitignore rules work
- [x] All tests pass without AWS credentials
- [x] Tests can run in CI environment

**Testing Instructions:**
- Run tests: `pytest backend/tests/unit/test_deploy_helpers.py -v`
- Verify no AWS calls made: `AWS_ACCESS_KEY_ID= pytest ...` (should still pass)
- Check coverage: `pytest --cov=backend/scripts --cov-report=term-missing`
- Run in CI-like environment:
  ```bash
  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
  pytest backend/tests/unit/test_deploy_helpers.py
  ```

**Commit Message Template:**
```
test(deploy): add unit tests for deployment script logic

- Extract testable helper functions
- Create test fixtures for configuration
- Test samconfig.toml generation
- Test .env file generation
- Test gitignore rules for secrets
- Enable CI verification without AWS

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 12: Update CI Configuration

**Goal**: Update GitHub Actions workflow to work with new backend structure and run tests without AWS credentials.

**Files to Modify:**
- `.github/workflows/backend-tests.yml`

**Prerequisites:**
- Task 11 complete (deployment tests created)
- All tool configs migrated (Tasks 2-3)

**Implementation Steps:**

1. Review existing CI workflow at `.github/workflows/backend-tests.yml`
2. Update Python version in all setup-python actions:
   - Change from `python-version: '3.12'` to `python-version: '3.13'`
   - Update in all job steps (currently lines 24, 60, 94, 136)
3. Update dependency installation:
   - Replace all `pip install -e ".[dev]"` with `pip install -r requirements.txt -r requirements-dev.txt`
   - Remove all `-e` flags (editable install no longer needed)
   - Update in all job steps (currently lines 33, 69, 102, 145)
4. Update Python setup paths:
   - Change to backend/ directory for Python work
   - Update requirements.txt path
   - Update pytest paths
3. Add linting steps:
   - Install ruff
   - Run `ruff check backend/src backend/tests`
4. Update test steps:
   - Install test dependencies (pytest, pytest-mock, pytest-cov, moto)
   - Run unit tests: `pytest backend/tests/unit -v --cov=backend/src`
   - Run integration tests: `pytest backend/tests/integration -v` (mocked AWS)
   - Ensure no AWS credentials needed
5. Add deployment script validation:
   - Run shellcheck on scripts: `shellcheck backend/scripts/*.sh`
   - Run deployment helper tests
6. Remove any steps that require live AWS resources
7. Ensure frontend tests still run (separate job if needed)
8. Add status badge to README

**Verification Checklist:**
- [x] File path correct: `.github/workflows/backend-tests.yml`
- [x] Python version updated to 3.13 in ALL setup-python actions
- [x] All `pip install -e ".[dev]"` replaced with `pip install -r requirements.txt -r requirements-dev.txt`
- [x] No `-e` flags remain in workflow
- [x] CI runs without AWS credentials
- [x] Linting runs on backend code
- [x] Unit tests run and pass
- [x] Integration tests run with mocked AWS
- [x] Deployment script tests run
- [x] Frontend tests still run (if applicable)
- [x] No live resource creation
- [x] CI completes in < 5 minutes
- [x] Failed tests show clear error messages

**Testing Instructions:**
- Create test PR to trigger CI
- Verify workflow runs without errors
- Check that all test steps pass
- Verify no AWS credential errors
- Test with intentional failures:
  - Break a unit test, verify CI catches it
  - Break linting, verify CI catches it
  - Fix and verify CI passes

**Commit Message Template:**
```
ci: update workflow for new backend structure

- Update Python version from 3.12 to 3.13
- Replace pip install -e with requirements files
- Use requirements.txt and requirements-dev.txt
- Update paths for backend/ directory
- Add ruff linting step
- Run unit and integration tests without AWS
- Add deployment script validation
- Verify secrets gitignored correctly
- Remove live resource dependencies

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 13: Clean Up Infrastructure Directory

**Goal**: Remove the old infrastructure/ directory now that all files are migrated to backend/.

**Files to Delete:**
- `infrastructure/` (entire directory)

**Prerequisites:**
- Tasks 1-12 complete (all migration done)
- Deployment tested and working from backend/

**Implementation Steps:**

1. Verify all necessary files have been migrated:
   - template.yaml in backend/ ✓
   - Scripts rewritten in backend/scripts/ ✓
   - samconfig.toml will be generated (don't need old one) ✓
   - test-requests in backend/ ✓
2. Create backup of infrastructure/ directory (just in case):
   - `cp -r infrastructure/ infrastructure-backup/`
   - Add to .gitignore temporarily
3. Remove infrastructure/ directory:
   - `git rm -r infrastructure/`
4. Update any documentation that references infrastructure/:
   - Update README.md
   - Update docs/ files that reference old paths
5. Test deployment still works after deletion:
   - Run `npm run deploy` from backend/
   - Verify success
6. Remove backup after successful deployment

**Verification Checklist:**
- [x] Backup created (infrastructure-backup/)
- [x] infrastructure/ directory deleted
- [x] Git shows directory removal
- [x] No broken references in documentation
- [x] Deployment works from backend/
- [x] All tests still pass
- [x] No orphaned files remain

**Testing Instructions:**
- Before deletion:
  - Create backup: `cp -r infrastructure/ infrastructure-backup/`
  - Document current state: `ls -R infrastructure/ > infrastructure-manifest.txt`
- After deletion:
  - Full deployment test: `cd backend && npm run deploy`
  - Run test suite: `pytest backend/tests/`
  - Check documentation links
- If successful, remove backup:
  - `rm -rf infrastructure-backup/`

**Commit Message Template:**
```
refactor: remove infrastructure directory

- Delete infrastructure/ directory
- All files migrated to backend/
- Update documentation references
- Simplify repository structure
- Complete deployment consolidation

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

### Task 14: Update Documentation

**Goal**: Update project documentation to reflect new deployment structure and commands.

**Files to Modify/Delete:**
- `README.md` - Update
- `docs/DEVELOPMENT.md` - Update
- `docs/infrastructure-deploy.md` - DELETE
- `docs/infrastructure-deployment.md` - DELETE
- `docs/infrastructure-deployment-status.md` - DELETE
- `docs/infrastructure-readme.md` - DELETE
- `docs/QUICK_REFERENCE.md` - Update
- `backend/README.md` - Create
- `docs/DEPLOYMENT.md` - Create

**Prerequisites:**
- Task 13 complete (infrastructure cleaned up)

**Implementation Steps:**

1. Update root README.md:
   - Update deployment instructions to use `cd backend && npm run deploy`
   - Remove references to infrastructure/ directory
   - Add quick start section with new commands
   - Update architecture diagram if present
2. Update docs/DEVELOPMENT.md:
   - Document new backend structure
   - Update setup instructions
   - Document npm scripts (deploy, validate, logs)
   - Add troubleshooting for common issues
3. Delete ALL infrastructure-related docs (all outdated):
   - Delete `docs/infrastructure-deploy.md`
   - Delete `docs/infrastructure-deployment.md`
   - Delete `docs/infrastructure-deployment-status.md`
   - Delete `docs/infrastructure-readme.md`
   - Create new `docs/DEPLOYMENT.md` with simplified deployment guide
4. Update docs/QUICK_REFERENCE.md:
   - Add deployment commands
   - Document environment variables
   - Document secrets management
5. Create backend/README.md:
   - Overview of backend structure
   - Development setup
   - Available npm scripts
   - Testing instructions
   - Deployment process
6. Verify all internal links still work

**Verification Checklist:**
- [x] README.md updated with new deployment commands
- [x] ALL infrastructure docs deleted (4 files):
  - [x] infrastructure-deploy.md
  - [x] infrastructure-deployment.md
  - [x] infrastructure-deployment-status.md
  - [x] infrastructure-readme.md
- [x] New DEPLOYMENT.md created
- [x] QUICK_REFERENCE.md updated
- [x] backend/README.md created
- [x] All documentation links verified
- [x] No references to old infrastructure/ directory
- [x] Examples use current structure

**Testing Instructions:**
- Read through each updated doc
- Follow quick start instructions from scratch
- Verify commands work as documented
- Check all links (relative and absolute)
- Have another developer review for clarity

**Commit Message Template:**
```
docs: update for simplified deployment structure

- Update README with new deployment commands
- Delete all 4 infrastructure-related docs
- Create comprehensive DEPLOYMENT.md
- Add backend/README.md with structure overview
- Update QUICK_REFERENCE with current commands
- Fix all documentation links

Author & Commiter: HatmanStack
Email: 82614182+HatmanStack@users.noreply.github.com
```

---

## Phase Verification

### Complete Phase Test

After all tasks are complete, perform this end-to-end verification:

1. **Clean Slate Test**:
   ```bash
   # Start from fresh clone
   git clone <repo> float-test
   cd float-test/backend

   # Should prompt for all config
   npm run deploy

   # Verify deployment
   aws cloudformation describe-stacks --stack-name <stack>

   # Verify frontend .env created
   cat ../frontend/.env

   # Test subsequent deployment (no prompts)
   npm run deploy

   # Clean up
   aws cloudformation delete-stack --stack-name <stack>
   ```

2. **Test Suite Verification**:
   ```bash
   # All tests pass without AWS credentials
   unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
   pytest backend/tests/ -v

   # Linting passes
   ruff check backend/src backend/tests

   # Type checking runs
   mypy backend/src
   ```

3. **CI Verification**:
   - Create PR with all changes
   - Verify CI runs without AWS credentials
   - All checks pass
   - No secret leakage warnings

4. **Documentation Verification**:
   - New developer can follow README to deploy
   - All commands work as documented
   - No broken links in docs

### Success Criteria

- [ ] `npm run deploy` works end-to-end from backend/
- [ ] Secrets never committed (verified with `git log --all --full-history --source`)
- [ ] All tests pass without AWS credentials
- [ ] CI pipeline green without AWS credentials
- [ ] Frontend .env auto-generated correctly
- [ ] infrastructure/ directory removed
- [ ] Documentation updated and accurate
- [ ] Clean git history with conventional commits
- [ ] No Makefile used for SAM builds
- [ ] pyproject.toml removed entirely

### Integration Points

This phase integrates with:
- **Frontend**: Receives .env file from deployment
- **CI/CD**: Runs tests without live AWS
- **AWS**: Deploys via SAM to CloudFormation
- **Developer Workflow**: Single command deployment

### Known Limitations

- **Single Region**: Default FFmpeg layer is us-east-1 only
- **Single Environment**: No staging/production separation (use stack names or accounts)
- **Local Secrets**: Secrets stored locally, not in AWS Secrets Manager
- **Manual Teardown**: Stack deletion via AWS Console or CLI (no automated script)
- **API Key Rotation**: Requires manual update in `.deploy-config.json`

### Post-Phase Cleanup

After successful verification:

1. Remove infrastructure-backup/ if created
2. Tag release: `git tag v2.0.0-deployment-simplified`
3. Update project board/issues
4. Announce changes to team
5. Archive old deployment documentation
6. Consider blog post on migration process

## Troubleshooting Guide

### Common Issues

**Issue**: "sam: command not found"
- **Solution**: Install SAM CLI globally: `brew install aws-sam-cli`

**Issue**: "Invalid distribution name: __init__-0.0.0"
- **Solution**: Verify pyproject.toml deleted and requirements.txt has no `-e .`

**Issue**: Deployment succeeds but frontend .env not created
- **Solution**: Check stack outputs exist, verify deploy.sh post-deployment logic

**Issue**: "No module named pip" during sam build
- **Solution**: Verify BuildMethod metadata removed from template.yaml

**Issue**: samconfig.toml committed to git
- **Solution**: Add to .gitignore, remove from git: `git rm --cached backend/samconfig.toml`

**Issue**: Tests fail in CI with "AWS credentials required"
- **Solution**: Ensure tests use moto/mocks, no live AWS SDK calls

**Issue**: Old infrastructure/ scripts being used
- **Solution**: Clear shell hash: `hash -r`, verify PATH, remove infrastructure-backup/

### Rollback Plan

If deployment fails catastrophically:

1. Restore infrastructure/ from backup
2. Revert to main branch
3. Use old deployment method
4. Debug issue in separate branch
5. Re-attempt migration with fixes

### Getting Help

- Check Phase-0 ADRs for design rationale
- Review deployment script specification
- Examine react-stocks reference implementation
- Check SAM CLI documentation for errors
- Review AWS CloudFormation console for stack issues
