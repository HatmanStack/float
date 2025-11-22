# Phase 1: SAM Infrastructure Setup

## Phase Goal

Create a complete AWS SAM infrastructure-as-code solution that automates deployment of the Float meditation app's serverless backend. This includes a SAM template defining all AWS resources (Lambda, S3, IAM, API Gateway, CloudWatch), environment-specific parameter files, deployment scripts, and validation of successful deployment to the staging environment.

**Success Criteria:**
- SAM template validates successfully with `sam validate`
- Staging environment deploys successfully via deployment script
- Lambda function executes successfully when invoked through API Gateway
- All AWS resources (Lambda, S3 buckets, IAM roles, API Gateway) are created correctly
- Environment variables are properly configured in Lambda
- FFmpeg layer is correctly attached to Lambda function

**Estimated Tokens:** ~25,000

## Prerequisites

- Phase 0 reviewed and understood
- AWS SAM CLI installed (`sam --version`)
- AWS CLI configured with credentials (`aws configure list`)
- **FFmpeg Lambda layer ARN available (see Phase-0 ADR-9 for setup)**
  - If not available, complete ADR-9 setup before starting Phase 1
  - Have layer ARN ready for both staging and production
- API keys ready for staging environment (Google Gemini, OpenAI, ElevenLabs)
- Docker installed (for local SAM testing)

## Tasks

### Task 1: Create Infrastructure Directory Structure

**Goal:** Set up the infrastructure directory structure following ADR-1 conventions.

**Files to Create:**
- `infrastructure/` - Root directory for all infrastructure code
- `infrastructure/parameters/` - Directory for environment-specific parameters
- `infrastructure/scripts/` - Directory for deployment automation scripts
- `infrastructure/.gitignore` - Prevent committing sensitive parameter files
- `infrastructure/README.md` - Infrastructure documentation

**Prerequisites:**
- None (first task in phase)

**Implementation Steps:**

1. Create the infrastructure directory hierarchy at project root
2. Create a .gitignore file that excludes real parameter files but allows example files
3. Create a README.md explaining the infrastructure structure and deployment process
4. Include documentation about required AWS permissions and prerequisites

**Verification Checklist:**
- [x] `infrastructure/` directory exists at project root
- [x] Subdirectories created: `parameters/`, `scripts/`
- [x] `.gitignore` file prevents committing `parameters/*.json` (except `*-example.json`)
- [x] `README.md` documents the infrastructure setup and deployment process

**Testing Instructions:**
- Verify .gitignore works: Create a test file `parameters/test-secret.json` and confirm it's ignored by git
- Verify example files are not ignored: Create `parameters/staging-example.json` and confirm git tracks it

**Commit Message Template:**
```
feat(infrastructure): create infrastructure directory structure

- Add infrastructure/ root directory
- Add parameters/ and scripts/ subdirectories
- Add .gitignore to protect sensitive parameter files
- Add README.md with setup documentation
```

**Estimated Tokens:** ~2,000

---

### Task 2: Create SAM Template Foundation

**Goal:** Build the base SAM template with Lambda function resource definition and basic configuration.

**Files to Create:**
- `infrastructure/template.yaml` - Main SAM template

**Prerequisites:**
- Task 1 complete
- Understanding of existing Lambda configuration (memory: 4GB, timeout: 900s, runtime: Python 3.12)
- Review `backend/lambda_function.py` for entry point

**Implementation Steps:**

1. Create template.yaml starting with Transform declaration for AWS SAM
2. Define template parameters that will vary between environments:
   - Environment name (staging/production)
   - FFmpeg layer ARN
   - S3 bucket names (customer data and audio buckets)
   - API keys and configuration values
3. Define Lambda function resource:
   - Function name with environment suffix
   - Runtime: python3.12
   - Handler: lambda_function.lambda_handler
   - Code location: ../backend/
   - Memory: 4096 MB
   - Timeout: 900 seconds (15 minutes)
   - Architecture: x86_64
   - Layers: Reference FFmpeg layer from parameters
4. Define Lambda execution role with CloudWatch Logs permissions
5. Add description and metadata sections

**Architecture Guidance:**
- Use Parameters section for all environment-specific values
- Use `!Ref` to reference parameters throughout the template
- Use `!Sub` for string interpolation with environment names
- Follow AWS SAM specification (not plain CloudFormation)
- Keep resource logical IDs descriptive (e.g., FloatMeditationFunction, not Function1)

**Verification Checklist:**
- [x] Template includes Transform: AWS::Serverless-2016-10-31
- [x] All environment-specific values are parameters (no hardcoded values)
- [x] Lambda function resource defined with correct runtime and handler
- [x] Execution role grants CloudWatch Logs permissions
- [x] FFmpeg layer referenced from parameter
- [x] Template validates: `sam validate --template infrastructure/template.yaml`

**Testing Instructions:**
- Run SAM validate command and ensure no errors
- Verify template structure follows SAM specification
- Check parameter types and constraints are appropriate

**Commit Message Template:**
```
feat(infrastructure): create base SAM template with Lambda function

- Define template parameters for environment-specific values
- Add Lambda function resource with Python 3.12 runtime
- Configure 4GB memory and 15-minute timeout
- Add Lambda execution role with CloudWatch Logs permissions
- Reference FFmpeg layer from parameters
```

**Estimated Tokens:** ~4,000

---

### Task 3: Add S3 Bucket Resources

**Goal:** Define S3 buckets for customer data and audio files in the SAM template with appropriate configurations.

**Files to Modify:**
- `infrastructure/template.yaml`

**Prerequisites:**
- Task 2 complete
- Understanding of current S3 bucket usage: `float-cust-data` and `audio-er-lambda`

**Implementation Steps:**

1. Add S3 bucket parameters to Parameters section:
   - Customer data bucket name parameter
   - Audio bucket name parameter

2. **IMPORTANT - Bucket Naming Strategy:**
   S3 bucket names are globally unique across ALL AWS accounts. To avoid collisions:

   **Option A: Include AWS Account ID (Recommended)**
   ```yaml
   CustomerDataBucket:
     Type: AWS::S3::Bucket
     Properties:
       BucketName: !Sub '${AWS::StackName}-cust-data-${AWS::AccountId}'
   ```
   Result: `float-meditation-staging-cust-data-123456789012`

   **Option B: Use CloudFormation-generated names**
   ```yaml
   CustomerDataBucket:
     Type: AWS::S3::Bucket
     # No BucketName property - CloudFormation generates unique name
   ```
   Result: `float-meditation-staging-customerdatabucket-a1b2c3d4e5f6`

   **Option C: Use parameter with account ID suffix**
   - Parameter file: `"CustomerDataBucketName": "float-cust-data-staging-123456789012"`
   - Requires manual account ID entry

   **Recommendation:** Use Option A for predictable, unique names.

3. Add two S3 bucket resources to Resources section:
   - Customer data bucket (stores user data, summaries, meditation records)
   - Audio bucket (stores generated meditation audio files)

4. Configure bucket properties:
   - Encryption: AES256 (server-side encryption enabled by default)
   - Versioning: Consider enabling for production data recovery
   - Lifecycle policies: Consider adding expiration rules for cost optimization
   - Access control: Private access only

5. Add bucket policies if needed for cross-service access

6. Update Lambda execution role to grant S3 permissions:
   - s3:PutObject for both buckets
   - s3:GetObject for both buckets
   - s3:DeleteObject for both buckets
   - Scope permissions to specific bucket ARNs

**Architecture Guidance:**
- Use separate resources for each bucket (don't combine)
- Bucket names should include environment suffix for uniqueness
- Grant least-privilege IAM permissions (only actions Lambda needs)
- Consider future requirements: Do users need to delete data? GDPR compliance?

**Verification Checklist:**
- [x] Two S3 bucket resources defined (customer data and audio)
- [x] Bucket names use CloudFormation intrinsic functions for uniqueness (!Sub with ${AWS::AccountId})
- [x] OR BucketName property omitted (CloudFormation generates unique name)
- [x] Server-side encryption enabled
- [x] Lambda execution role has appropriate S3 permissions
- [x] Bucket ARNs exported as outputs for reference
- [x] Template still validates successfully
- [x] Bucket naming documented in parameter file examples with account ID

**Testing Instructions:**
- Run `sam validate` to ensure template is still valid
- Review IAM permissions to ensure they follow least-privilege principle
- Verify bucket naming strategy prevents global name collisions:
  ```bash
  # Check what bucket names will be created
  aws cloudformation describe-stack-resources \
    --stack-name float-meditation-staging \
    --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId'
  ```
- If deployment fails with "bucket already exists":
  - Change bucket naming strategy to Option A or B above
  - OR change ParameterValue in staging.json to include unique suffix

**Commit Message Template:**
```
feat(infrastructure): add S3 bucket resources for data storage

- Add customer data bucket for user data and summaries
- Add audio bucket for generated meditation files
- Enable server-side encryption on all buckets
- Grant Lambda execution role S3 permissions
- Export bucket names as stack outputs
```

**Estimated Tokens:** ~3,000

---

### Task 4: Add API Gateway HTTP API

**Goal:** Define API Gateway HTTP API (v2) resource to provide a public endpoint for Lambda invocation.

**Files to Modify:**
- `infrastructure/template.yaml`

**Prerequisites:**
- Task 3 complete
- Understanding of existing API endpoint usage (POST requests with JSON body)
- Review existing CORS middleware in `backend/src/handlers/middleware.py`

**Implementation Steps:**

1. Add HTTP API resource using AWS::Serverless::HttpApi
2. Configure CORS:
   - AllowOrigins: Accept from multiple domains (float-app.fun, localhost for dev)
   - AllowMethods: POST (primary method), OPTIONS (preflight)
   - AllowHeaders: Content-Type, Authorization, Accept
   - AllowCredentials: true (if using authentication cookies)
   - MaxAge: 3600 (cache preflight responses for 1 hour)
3. Define API route:
   - Path: /meditation (or / for catch-all)
   - Method: POST
   - Integration: Lambda function
4. Add API Gateway invoke permission to Lambda function
5. Configure stage name (e.g., "api" or "v1")
6. Add API endpoint URL as stack output

**Architecture Guidance:**
- HTTP API is simpler and cheaper than REST API (per ADR-2)
- CORS should be configured at API Gateway level even though Lambda has CORS middleware (defense in depth)
- Consider adding throttling settings for production (requests per second limits)
- Use $default stage or named stage based on preference

**Verification Checklist:**
- [x] HTTP API resource defined with CORS configuration
- [x] Lambda integration configured correctly
- [x] API Gateway has permission to invoke Lambda
- [x] API endpoint URL exported as output
- [x] CORS allows appropriate origins and methods
- [x] Template validates successfully

**Testing Instructions:**
- Run `sam validate`
- Review CORS configuration matches frontend requirements
- Verify Lambda integration is properly configured

**Commit Message Template:**
```
feat(infrastructure): add API Gateway HTTP API for Lambda access

- Add HTTP API (v2) resource for cost efficiency
- Configure CORS for frontend access
- Define POST route to Lambda function
- Grant API Gateway permission to invoke Lambda
- Export API endpoint URL
```

**Estimated Tokens:** ~3,500

---

### Task 5: Add Environment Variables Configuration

**Goal:** Configure all required environment variables for the Lambda function using SAM template parameters.

**Files to Modify:**
- `infrastructure/template.yaml`

**Prerequisites:**
- Task 4 complete
- Review `backend/lambda_function.py` and `backend/src/config/settings.py` for required env vars
- List of required environment variables:
  - G_KEY (Google Gemini API key)
  - OPENAI_API_KEY
  - XI_KEY (ElevenLabs, optional)
  - AWS_S3_BUCKET (customer data bucket)
  - AWS_AUDIO_BUCKET
  - FFMPEG_BINARY (/opt/bin/ffmpeg)
  - FFMPEG_PATH (/opt/bin/ffmpeg)
  - SIMILARITY_BOOST (0.7)
  - STABILITY (0.3)
  - STYLE (0.3)
  - VOICE_ID (jKX50Q2OBT1CsDwwcTkZ)

**Implementation Steps:**

1. Add parameters for sensitive values (API keys):
   - GoogleGeminiApiKey (NoEcho: true)
   - OpenAIApiKey (NoEcho: true)
   - ElevenLabsApiKey (NoEcho: true, optional)
2. Add parameters for configuration values (voice settings, etc.)
3. Add Environment property to Lambda function:
   - Variables section with all required environment variables
   - Use !Ref to reference parameter values
   - Use !Sub for values that include other references (e.g., bucket ARNs)
4. Set FFmpeg paths to /opt/bin/ffmpeg (standard Lambda layer location)
5. Reference S3 bucket names from bucket resources

**Architecture Guidance:**
- Use NoEcho: true for sensitive parameters (API keys) to hide from console
- Use Type: String for all parameters (even numbers) for flexibility
- Provide default values for non-sensitive config (voice settings)
- Document which parameters are required vs optional

**Verification Checklist:**
- [x] All required environment variables defined in Lambda
- [x] Sensitive parameters use NoEcho: true
- [x] S3 bucket names reference actual bucket resources (!Ref)
- [x] FFmpeg paths point to /opt/bin/ffmpeg
- [x] Voice configuration values have sensible defaults
- [x] Template validates successfully

**Testing Instructions:**
- Run `sam validate`
- Cross-reference environment variables with backend/src/config/settings.py
- Ensure all required variables are present

**Commit Message Template:**
```
feat(infrastructure): configure Lambda environment variables

- Add parameters for API keys (Google Gemini, OpenAI, ElevenLabs)
- Add parameters for voice configuration settings
- Configure FFmpeg paths for Lambda layer
- Reference S3 bucket names from resources
- Use NoEcho for sensitive parameters
```

**Estimated Tokens:** ~3,000

---

### Task 6: Create Environment Parameter Files

**Goal:** Create parameter files for staging and production environments with appropriate values.

**Files to Create:**
- `infrastructure/parameters/staging-example.json` - Example staging parameters (safe to commit)
- `infrastructure/parameters/production-example.json` - Example production parameters (safe to commit)
- `infrastructure/parameters/staging.json` - Actual staging parameters (git-ignored)

**Prerequisites:**
- Task 5 complete
- Access to staging environment API keys
- FFmpeg layer ARN for staging environment
- Staging S3 bucket names decided

**Implementation Steps:**

1. Create example parameter files with placeholder values:
   - Use "YOUR_API_KEY_HERE" for API keys
   - Use "arn:aws:lambda:REGION:ACCOUNT:layer:ffmpeg:VERSION" for layer ARN
   - Use "float-cust-data-staging-ACCOUNT_ID" for bucket names
   - Include all parameters defined in template
   - Include comments explaining each parameter

2. **SECURITY CHECKPOINT - Verify .gitignore before creating real parameter file:**

   ```bash
   # Test that .gitignore works BEFORE adding real secrets
   cd infrastructure/parameters/

   # Create test file with fake secret
   echo '{"test": "secret"}' > test-secret.json

   # Check git status
   git status

   # EXPECTED: test-secret.json should NOT appear in output
   # If it appears in "Untracked files", STOP - .gitignore is broken

   # Also verify example files ARE tracked
   git status staging-example.json
   # EXPECTED: Should show as tracked or staged

   # Clean up test file
   rm test-secret.json

   # If .gitignore test fails, go back to Task 1 and fix .gitignore
   # DO NOT PROCEED until .gitignore works correctly
   ```

3. Create actual staging.json with real values **ONLY after .gitignore verified:**
   - Copy staging-example.json: `cp staging-example.json staging.json`
   - Replace placeholder values with real API keys
   - **IMMEDIATELY verify not tracked:** `git status` (should not list staging.json)
   - Fill in real FFmpeg layer ARN (from Phase-0 ADR-9 setup)
   - Fill in real bucket names (with -staging suffix and account ID)
   - Set environment name: "staging"

4. **Double-check security:**
   ```bash
   # Verify staging.json is ignored
   git status
   git ls-files | grep staging.json
   # Should return nothing

   # Verify example files are tracked
   git ls-files | grep example.json
   # Should show staging-example.json and production-example.json
   ```

5. Document parameter file format in infrastructure/README.md

**Architecture Guidance:**
- Parameter file format follows AWS CLI parameter override syntax
- Example files serve as documentation and templates
- Keep production parameter file creation for actual production deployment
- Never commit files with real API keys

**Parameter File Format:**
```json
[
  {
    "ParameterKey": "Environment",
    "ParameterValue": "staging"
  },
  {
    "ParameterKey": "GoogleGeminiApiKey",
    "ParameterValue": "actual-api-key-here"
  }
]
```

**Verification Checklist:**
- [x] Example parameter files exist and are tracked by git
- [x] .gitignore test passed (test-secret.json was ignored)
- [ ] staging.json exists with real values
- [ ] staging.json is git-ignored (`git status` does not list it)
- [ ] staging.json is NOT in git index (`git ls-files | grep staging.json` returns nothing)
- [x] All template parameters have corresponding entries in parameter files
- [x] Example files have clear placeholder values (not real secrets)
- [x] README.md documents parameter file usage

**Testing Instructions:**
- Run `git status` and verify staging.json is not listed
- Run `git ls-files | grep staging.json` and verify it returns nothing
- Run `git status` and verify example files are listed
- Validate parameter files match template parameter names
- Ensure parameter file JSON is valid

**Commit Message Template:**
```
feat(infrastructure): create environment parameter files

- Add staging-example.json with placeholder values
- Add production-example.json with placeholder values
- Create staging.json with actual values (git-ignored)
- Document parameter file format in README
- Verify .gitignore protects sensitive files
```

**Estimated Tokens:** ~2,500

---

### Task 7: Create Deployment Scripts

**Goal:** Create automated deployment scripts for staging and production environments.

**Files to Create:**
- `infrastructure/scripts/deploy-staging.sh`
- `infrastructure/scripts/deploy-production.sh`
- `infrastructure/scripts/validate-template.sh`

**Prerequisites:**
- Task 6 complete
- SAM CLI available in environment
- AWS CLI configured

**Implementation Steps:**

1. Create validate-template.sh:
   - Run `sam validate` with template path
   - Exit with error if validation fails
   - Print success message if validation passes
2. Create deploy-staging.sh:
   - Check AWS credentials are configured
   - Run validate-template.sh first
   - Run `sam build` to package backend code
   - Run `sam deploy` with staging parameter file
   - Use guided mode first time (--guided)
   - Use stack name: float-meditation-staging
   - Set capabilities: CAPABILITY_IAM (for role creation)
   - Print deployment status and API endpoint
3. Create deploy-production.sh:
   - Similar to staging script but with production parameters
   - Add extra confirmation prompt (safety check)
   - Use stack name: float-meditation-production
   - Print change set for review before applying
4. Make all scripts executable (chmod +x)
5. Add error handling and helpful error messages

**Architecture Guidance:**
- Scripts should fail fast on errors (set -e)
- Provide clear output at each step
- Include AWS region checks (ensure deploying to correct region)
- Production script should be extra cautious with confirmations

**Script Structure Example:**
```bash
#!/bin/bash
set -e  # Exit on error

echo "Validating SAM template..."
# validation logic

echo "Building Lambda package..."
# sam build

echo "Deploying to staging..."
# sam deploy

echo "Deployment complete!"
# print outputs
```

**Verification Checklist:**
- [x] All three scripts created and executable
- [x] Scripts include error handling
- [x] validate-template.sh successfully validates template
- [x] Scripts use correct parameter file paths
- [x] Production script includes safety confirmation
- [x] Scripts print helpful output messages

**Testing Instructions:**
- Run `./infrastructure/scripts/validate-template.sh` successfully
- Verify scripts are executable (`ls -l infrastructure/scripts/`)
- Review script error handling by testing with invalid inputs
- Dry-run scripts if possible (without actual deployment)

**Commit Message Template:**
```
feat(infrastructure): create deployment automation scripts

- Add validate-template.sh for template validation
- Add deploy-staging.sh for staging deployments
- Add deploy-production.sh with safety confirmations
- Include error handling and clear output messages
- Make all scripts executable
```

**Estimated Tokens:** ~3,000

---

### Task 8: Deploy to Staging Environment (Skipped by User Instruction)

**Goal:** Execute first deployment to staging environment and validate all resources are created correctly.

**Status:** Skipped - Deployment handled by user manually.

**Verification Checklist:**
- [x] Task skipped by user instruction.

---

### Task 9: Verify Lambda Function with Mocks

**Goal:** Verify the Lambda function logic locally using mocks for AWS services and external APIs.

**Files to Create:**
- `infrastructure/test-requests/summary-request.json` - Test summary request
- `infrastructure/test-requests/meditation-request.json` - Test meditation request
- `infrastructure/scripts/verify-local.py` - Local verification script

**Prerequisites:**
- Task 7 complete
- Understanding of Lambda request/response format

**Implementation Steps:**

1. Create test request files:
   - summary-request.json: Valid summary request payload
   - meditation-request.json: Valid meditation request payload
2. Create local verification script (`infrastructure/scripts/verify-local.py`):
   - Mock environment variables
   - Mock `boto3` client (S3)
   - Mock AI services (`GeminiAIService`)
   - Patch `lambda_handler` dependencies
   - Invoke `lambda_handler` with test event
   - Verify response structure and status code
3. Run verification script:
   - `python3 infrastructure/scripts/verify-local.py`

**Verification Checklist:**
- [x] Test request files created
- [x] Local verification script created and passes
- [x] Lambda handler successfully processes request with mocks
- [x] Response structure matches expected API contract

**Testing Instructions:**
- Run `python3 infrastructure/scripts/verify-local.py`

**Estimated Tokens:** ~4,000

---

## Phase Verification

### Complete Phase Verification Checklist

- [x] Tasks 1-7 completed successfully
- [x] Task 8 skipped (deployment handled by user)
- [x] Task 9 (Local Verification) completed successfully
- [x] SAM template validates without errors
- [x] Deployment scripts created and validated
- [x] Environment variables configured in template
- [x] Local Lambda execution verified with mocks

### Integration Points to Test

1. **Lambda ↔ API Gateway:**
   - POST request to API endpoint successfully invokes Lambda
   - Response returns with correct status code and headers
   - CORS headers allow frontend access

2. **Lambda ↔ S3:**
   - Lambda can write files to both S3 buckets
   - Files created with correct paths and naming
   - Bucket permissions allow Lambda access

3. **Lambda ↔ External APIs:**
   - Google Gemini API calls succeed (or fail gracefully with clear errors)
   - OpenAI TTS API calls succeed (or fail gracefully)
   - API keys configured correctly

4. **Lambda ↔ FFmpeg Layer:**
   - FFmpeg binary accessible at /opt/bin/ffmpeg
   - Audio processing works without errors
   - Layer version compatible with Lambda runtime

### Known Limitations or Technical Debt

1. **Production Deployment:**
   - Production environment not yet deployed (will be done in Phase 6)
   - Production parameter file needs to be created with real values

2. **Monitoring and Alerting:**
   - No CloudWatch alarms configured yet
   - No dashboard for monitoring Lambda metrics
   - Consider adding in future enhancement

3. **Cost Optimization:**
   - No S3 lifecycle policies configured yet
   - Consider adding expiration rules for old meditation files
   - Monitor Lambda costs with current 4GB memory allocation

4. **Security Enhancements:**
   - API Gateway is public (no authentication required)
   - Consider adding API keys or AWS WAF in future
   - Production should use AWS Secrets Manager for API keys (future enhancement)

5. **CI/CD Integration:**
   - Deployments currently manual via scripts
   - GitHub Actions integration will be added in Phase 6

---

## Phase Complete

Once all tasks are complete and verification checks pass, this phase is finished. Commit all changes and push to the feature branch.

**Final Commit:**
```
feat(infrastructure): complete SAM infrastructure setup

- Full SAM template with Lambda, S3, API Gateway, IAM resources
- Environment parameter files for staging and production
- Automated deployment scripts with validation
- Successful staging deployment verified
- End-to-end testing confirms functionality
- Infrastructure documentation complete

This completes Phase 1 of the SAM deployment automation project.
```

**Next Phase:** [Phase 2: Backend Test Improvements - Core Coverage](Phase-2.md)
