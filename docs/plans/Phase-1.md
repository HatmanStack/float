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
- FFmpeg Lambda layer ARN available for staging environment
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
- [ ] `infrastructure/` directory exists at project root
- [ ] Subdirectories created: `parameters/`, `scripts/`
- [ ] `.gitignore` file prevents committing `parameters/*.json` (except `*-example.json`)
- [ ] `README.md` documents the infrastructure setup and deployment process

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
- [ ] Template includes Transform: AWS::Serverless-2016-10-31
- [ ] All environment-specific values are parameters (no hardcoded values)
- [ ] Lambda function resource defined with correct runtime and handler
- [ ] Execution role grants CloudWatch Logs permissions
- [ ] FFmpeg layer referenced from parameter
- [ ] Template validates: `sam validate --template infrastructure/template.yaml`

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
2. Add two S3 bucket resources to Resources section:
   - Customer data bucket (stores user data, summaries, meditation records)
   - Audio bucket (stores generated meditation audio files)
3. Configure bucket properties:
   - Encryption: AES256 (server-side encryption enabled by default)
   - Versioning: Consider enabling for production data recovery
   - Lifecycle policies: Consider adding expiration rules for cost optimization
   - Access control: Private access only
4. Add bucket policies if needed for cross-service access
5. Update Lambda execution role to grant S3 permissions:
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
- [ ] Two S3 bucket resources defined (customer data and audio)
- [ ] Bucket names use parameters with environment suffix
- [ ] Server-side encryption enabled
- [ ] Lambda execution role has appropriate S3 permissions
- [ ] Bucket ARNs exported as outputs for reference
- [ ] Template still validates successfully

**Testing Instructions:**
- Run `sam validate` to ensure template is still valid
- Review IAM permissions to ensure they follow least-privilege principle
- Verify bucket naming will be unique (include account ID or random suffix if needed)

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
- [ ] HTTP API resource defined with CORS configuration
- [ ] Lambda integration configured correctly
- [ ] API Gateway has permission to invoke Lambda
- [ ] API endpoint URL exported as output
- [ ] CORS allows appropriate origins and methods
- [ ] Template validates successfully

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
- [ ] All required environment variables defined in Lambda
- [ ] Sensitive parameters use NoEcho: true
- [ ] S3 bucket names reference actual bucket resources (!Ref)
- [ ] FFmpeg paths point to /opt/bin/ffmpeg
- [ ] Voice configuration values have sensible defaults
- [ ] Template validates successfully

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
   - Use "your-api-key-here" for API keys
   - Use "arn:aws:lambda:region:account:layer:ffmpeg:1" for layer ARN
   - Use "float-cust-data-staging" for bucket names
   - Include all parameters defined in template
2. Create actual staging.json with real values:
   - Real API keys for staging environment
   - Real FFmpeg layer ARN
   - Real bucket names (with -staging suffix)
   - Appropriate environment name: "staging"
3. Document parameter file format in infrastructure/README.md
4. Verify staging.json is git-ignored

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
- [ ] Example parameter files exist and are tracked by git
- [ ] staging.json exists with real values
- [ ] staging.json is git-ignored
- [ ] All template parameters have corresponding entries in parameter files
- [ ] Example files have clear placeholder values
- [ ] README.md documents parameter file usage

**Testing Instructions:**
- Run `git status` and verify staging.json is not listed
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
- [ ] All three scripts created and executable
- [ ] Scripts include error handling
- [ ] validate-template.sh successfully validates template
- [ ] Scripts use correct parameter file paths
- [ ] Production script includes safety confirmation
- [ ] Scripts print helpful output messages

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

### Task 8: Deploy to Staging Environment

**Goal:** Execute first deployment to staging environment and validate all resources are created correctly.

**Files to Modify:**
- None (deployment only)

**Prerequisites:**
- All previous tasks complete
- staging.json parameter file populated with real values
- FFmpeg layer exists in AWS account
- AWS credentials configured for target account/region

**Implementation Steps:**

1. Pre-deployment verification:
   - Run validate-template.sh
   - Review staging.json parameter values
   - Verify AWS CLI credentials: `aws sts get-caller-identity`
   - Verify target region is correct
2. Initial deployment:
   - Run `./infrastructure/scripts/deploy-staging.sh`
   - Follow guided prompts (first deployment)
   - Review proposed changes
   - Confirm deployment
3. Save generated samconfig.toml to infrastructure/ directory
4. Post-deployment verification:
   - Check CloudFormation stack in AWS console
   - Verify all resources created: Lambda, S3 buckets, API Gateway, IAM role
   - Note API Gateway endpoint URL from outputs
5. Update infrastructure/README.md with actual deployment results

**Architecture Guidance:**
- First deployment uses --guided mode to generate samconfig.toml
- Subsequent deployments can use saved configuration
- Review CloudFormation change sets carefully
- If deployment fails, review CloudFormation events for root cause

**Verification Checklist:**
- [ ] CloudFormation stack created successfully: float-meditation-staging
- [ ] Lambda function exists and shows correct configuration (4GB memory, 15min timeout)
- [ ] S3 buckets created with correct names
- [ ] API Gateway HTTP API created with endpoint URL
- [ ] IAM role created with appropriate permissions
- [ ] FFmpeg layer attached to Lambda function
- [ ] Environment variables configured in Lambda
- [ ] samconfig.toml generated and saved

**Testing Instructions:**
- Check CloudFormation stack status in AWS console
- Navigate to Lambda console and verify function configuration
- Check S3 console for created buckets
- Verify API Gateway endpoint in API Gateway console
- Review IAM role policies in IAM console

**Commit Message Template:**
```
feat(infrastructure): deploy SAM stack to staging environment

- Successfully deployed CloudFormation stack: float-meditation-staging
- Created Lambda function with 4GB memory and 15-minute timeout
- Created S3 buckets: float-cust-data-staging, audio-er-lambda-staging
- Created API Gateway HTTP API endpoint
- Attached FFmpeg layer and configured environment variables
- Save samconfig.toml for future deployments
```

**Estimated Tokens:** ~2,500

---

### Task 9: Test Lambda Function Invocation

**Goal:** Verify the deployed Lambda function works correctly by invoking it through API Gateway with test requests.

**Files to Create:**
- `infrastructure/test-requests/summary-request.json` - Test summary request
- `infrastructure/test-requests/meditation-request.json` - Test meditation request

**Prerequisites:**
- Task 8 complete
- API Gateway endpoint URL from stack outputs
- Understanding of Lambda request/response format

**Implementation Steps:**

1. Create test request files:
   - summary-request.json: Valid summary request payload
   - meditation-request.json: Valid meditation request payload
   - Use test user ID and simple inputs
2. Test Lambda invocation via AWS CLI:
   - Use `aws lambda invoke` command directly (bypass API Gateway first)
   - Verify Lambda executes without errors
   - Check CloudWatch Logs for execution logs
3. Test API Gateway endpoint:
   - Use curl or Postman to send POST request to API endpoint
   - Include proper headers (Content-Type: application/json)
   - Verify CORS headers in response
   - Check response status and body
4. Verify S3 integration:
   - Check if result files are created in S3 buckets
   - Verify file contents and format
5. Document test results

**Architecture Guidance:**
- Start with direct Lambda invocation to isolate issues
- Then test through API Gateway to verify end-to-end flow
- Use CloudWatch Logs for debugging
- Small test payloads first, then realistic payloads

**Test Request Example (Summary):**
```json
{
  "type": "summary",
  "user_id": "test-user-staging",
  "prompt": "I had a peaceful day today.",
  "audio": "NotAvailable"
}
```

**Verification Checklist:**
- [ ] Lambda invokes successfully via AWS CLI
- [ ] Lambda invokes successfully via API Gateway
- [ ] Response includes expected fields (sentiment_label, intensity, summary)
- [ ] S3 files created in correct bucket and path
- [ ] CloudWatch Logs show successful execution
- [ ] CORS headers present in API Gateway response
- [ ] No errors in CloudWatch Logs

**Testing Instructions:**

Direct Lambda invocation:
```bash
aws lambda invoke \
  --function-name float-meditation-staging \
  --payload file://infrastructure/test-requests/summary-request.json \
  --region us-east-1 \
  response.json
```

API Gateway invocation:
```bash
curl -X POST https://[api-id].execute-api.[region].amazonaws.com/meditation \
  -H "Content-Type: application/json" \
  -d @infrastructure/test-requests/summary-request.json
```

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/float-meditation-staging --follow
```

**Commit Message Template:**
```
test(infrastructure): verify Lambda function execution in staging

- Create test request payloads for summary and meditation
- Test direct Lambda invocation via AWS CLI
- Test API Gateway endpoint with curl
- Verify S3 file creation and CloudWatch Logs
- Confirm CORS headers and response format
- Document successful end-to-end flow
```

**Estimated Tokens:** ~4,000

---

## Phase Verification

### Complete Phase Verification Checklist

- [ ] All 9 tasks completed successfully
- [ ] SAM template validates without errors
- [ ] Staging environment deployed successfully
- [ ] Lambda function executes correctly via API Gateway
- [ ] S3 buckets created and accessible
- [ ] Environment variables configured properly
- [ ] FFmpeg layer attached and functional
- [ ] CORS working correctly
- [ ] CloudWatch Logs show successful executions
- [ ] Documentation updated with deployment results

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
