# Float Meditation App - Infrastructure

This directory contains AWS SAM (Serverless Application Model) infrastructure-as-code for deploying the Float meditation app's serverless backend.

## Overview

The infrastructure automates deployment of:
- AWS Lambda function (Python 3.12 runtime)
- S3 buckets for customer data and audio files
- API Gateway HTTP API for public access
- IAM roles and policies
- CloudWatch Logs for monitoring

## Directory Structure

```
infrastructure/
├── template.yaml              # SAM template (environment-agnostic)
├── parameters/
│   ├── staging-example.json  # Example staging parameters (safe to commit)
│   ├── production-example.json # Example production parameters (safe to commit)
│   ├── staging.json          # Actual staging parameters (git-ignored)
│   └── production.json       # Actual production parameters (git-ignored)
├── scripts/
│   ├── validate-template.sh  # Validate SAM template
│   ├── deploy-staging.sh     # Deploy to staging
│   └── deploy-production.sh  # Deploy to production
├── test-requests/            # Sample API requests for testing
└── README.md                 # This file
```

## Prerequisites

### Required Tools

- **AWS SAM CLI**: Install from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
  ```bash
  sam --version  # Should be 1.100.0 or newer
  ```

- **AWS CLI**: Configure with appropriate credentials
  ```bash
  aws configure
  aws sts get-caller-identity  # Verify credentials
  ```

- **Docker**: Required for SAM local testing
  ```bash
  docker --version
  ```

- **Python 3.12**: For local development and testing

### AWS Permissions

Your AWS credentials must have permissions to create/manage:
- CloudFormation stacks
- Lambda functions
- S3 buckets
- API Gateway (HTTP API)
- IAM roles and policies
- CloudWatch Logs

### FFmpeg Lambda Layer

The Lambda function requires a pre-built FFmpeg layer for audio processing. See `docs/plans/Phase-0.md` ADR-9 for setup instructions.

**Quick check:**
```bash
# Verify layer exists in your account
aws lambda list-layer-versions --layer-name ffmpeg --region us-east-1
```

If layer doesn't exist, follow ADR-9 setup before proceeding.

## Parameter Files

Parameter files store environment-specific configuration values using the AWS CloudFormation parameter override format.

**Files:**
- `staging-example.json` - Template with placeholders (safe to commit)
- `production-example.json` - Template with placeholders (safe to commit)
- `staging.json` - Actual staging values (git-ignored, DO NOT COMMIT)
- `production.json` - Actual production values (git-ignored, DO NOT COMMIT)

**Parameter Format:**
```json
[
  {
    "ParameterKey": "Environment",
    "ParameterValue": "staging"
  },
  {
    "ParameterKey": "GoogleGeminiApiKey",
    "ParameterValue": "your-actual-api-key-here"
  }
]
```

**Required Parameters:**
- `Environment`: "staging" or "production"
- `FFmpegLayerArn`: ARN of your FFmpeg Lambda layer (see Phase-0 ADR-9)
- `GoogleGeminiApiKey`: Your Google Gemini API key
- `OpenAIApiKey`: Your OpenAI API key
- `ElevenLabsApiKey`: Optional, can be empty string ""

**Optional Parameters with Defaults:**
- `SimilarityBoost`: "0.7" (voice similarity)
- `Stability`: "0.3" (voice stability)
- `VoiceStyle`: "0.3" (voice style)
- `VoiceId`: "jKX50Q2OBT1CsDwwcTkZ" (ElevenLabs voice)

## Deployment Process

### First-Time Setup

1. **Edit staging.json with real values:**

   The file `infrastructure/parameters/staging.json` already exists as a template. Edit it to add your actual values:

   ```bash
   cd infrastructure/parameters/
   # Edit staging.json - replace ALL placeholder values
   # - FFmpegLayerArn: Get from AWS Console or `aws lambda list-layer-versions --layer-name ffmpeg`
   # - GoogleGeminiApiKey: Your Google AI Studio API key
   # - OpenAIApiKey: Your OpenAI API key
   # - ElevenLabsApiKey: Optional, can leave as empty string
   ```

2. **Verify .gitignore protection:**
   ```bash
   cd /home/user/float
   git status  # staging.json should NOT appear in output
   git ls-files | grep staging.json  # Should return nothing
   ```

3. **Important Security Note:**
   - NEVER commit `staging.json` or `production.json`
   - These files contain sensitive API keys
   - The .gitignore is configured to exclude them
   - Only example files should be committed

### Deploy to Staging

```bash
cd infrastructure/
./scripts/deploy-staging.sh
```

First deployment will use SAM guided mode to configure:
- Stack name: `float-meditation-staging`
- AWS Region (e.g., us-east-1)
- Capabilities: CAPABILITY_IAM
- Parameter overrides from `parameters/staging.json`

Subsequent deployments use saved configuration in `samconfig.toml`.

### Deploy to Production

**⚠️ PRODUCTION DEPLOYMENT - REQUIRES EXTRA CAUTION**

1. Create production parameter file:
   ```bash
   cd infrastructure/parameters/
   cp production-example.json production.json
   # Edit with production API keys and configuration
   ```

2. Deploy with extra confirmation:
   ```bash
   cd infrastructure/
   ./scripts/deploy-production.sh
   ```

The production script includes additional safety prompts.

## Validation

### Validate Template

```bash
cd infrastructure/
./scripts/validate-template.sh
```

### Local Testing (Optional)

Test Lambda locally using SAM:

```bash
# Build Lambda package
sam build

# Invoke locally with test event
sam local invoke FloatMeditationFunction -e test-requests/summary-request.json

# Start local API Gateway
sam local start-api
```

**Note:** Local testing requires Docker and may not have access to AWS resources (S3, etc.).

## Testing Deployed Function

### Test via AWS CLI

```bash
# Direct Lambda invocation
aws lambda invoke \
  --function-name float-meditation-staging-FloatMeditationFunction \
  --payload file://test-requests/summary-request.json \
  response.json

cat response.json
```

### Test via API Gateway

```bash
# Get API endpoint from CloudFormation outputs
ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name float-meditation-staging \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Send test request
curl -X POST $ENDPOINT/meditation \
  -H "Content-Type: application/json" \
  -d @test-requests/summary-request.json
```

### View Logs

```bash
# Tail CloudWatch Logs
aws logs tail /aws/lambda/float-meditation-staging-FloatMeditationFunction --follow
```

## Architecture Decisions

Key architectural decisions documented in `docs/plans/Phase-0.md`:

- **ADR-1:** Single environment-agnostic SAM template with parameter files
- **ADR-2:** HTTP API v2 (not REST API) for cost efficiency
- **ADR-3:** Environment variables for secrets (not AWS Secrets Manager)
- **ADR-4:** FFmpeg layer managed separately
- **ADR-7:** Manual review required for production deployments

## Troubleshooting

### Deployment Fails: "Layer not found"

FFmpeg layer ARN is invalid or in wrong region.

**Fix:**
```bash
# List available layers
aws lambda list-layer-versions --layer-name ffmpeg --region us-east-1

# Update parameters/*.json with correct ARN
```

### Deployment Fails: "Bucket name already exists"

S3 bucket names are globally unique across ALL AWS accounts.

**Fix:**
Update bucket names in `parameters/*.json` to include AWS account ID:
```json
{
  "ParameterKey": "CustomerDataBucketName",
  "ParameterValue": "float-cust-data-staging-123456789012"
}
```

Or let CloudFormation generate unique names (remove BucketName property from template).

### Deployment Fails: "User is not authorized"

AWS credentials lack necessary permissions.

**Fix:**
```bash
# Check current identity
aws sts get-caller-identity

# Ensure IAM user/role has CloudFormation, Lambda, S3, IAM permissions
```

### Lambda Execution Fails: "FFmpeg not found"

FFmpeg binary not accessible in Lambda environment.

**Fix:**
- Verify layer is attached to Lambda function
- Verify FFMPEG_PATH environment variable = `/opt/bin/ffmpeg`
- Test: Add debug logging in Lambda to check if file exists

### API Gateway Returns CORS Error

CORS configuration mismatch between API Gateway and frontend.

**Fix:**
- Verify AllowOrigins in template.yaml includes your frontend domain
- Check CORS headers in Lambda response (should include Access-Control-Allow-Origin)

## Cost Estimation

**Staging Environment (estimated monthly):**
- Lambda: $0-5 (depends on usage)
- S3: $0-2 (depends on storage)
- API Gateway HTTP API: $0-1 (very low cost)
- CloudWatch Logs: $0-1
- **Total: ~$0-10/month** (with light usage)

**Production Environment:**
- Varies based on user traffic
- Monitor costs via AWS Cost Explorer

## Security Notes

- **Parameter files** (`parameters/*.json`) contain sensitive API keys
- These files are git-ignored - never commit them
- Example files are safe to commit (contain placeholders only)
- Production API keys should be rotated regularly
- Consider migrating to AWS Secrets Manager for production (future enhancement)

## Stack Outputs

After deployment, CloudFormation exports these outputs:

- **ApiEndpoint**: API Gateway endpoint URL
- **LambdaFunctionArn**: Lambda function ARN
- **CustomerDataBucket**: S3 bucket name for customer data
- **AudioBucket**: S3 bucket name for audio files

View outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name float-meditation-staging \
  --query 'Stacks[0].Outputs'
```

## Rollback

If deployment fails, CloudFormation automatically rolls back to previous state.

To manually rollback:
```bash
# Delete failed stack
aws cloudformation delete-stack --stack-name float-meditation-staging

# Re-deploy after fixing issue
./scripts/deploy-staging.sh
```

## CI/CD Integration

GitHub Actions integration will be added in Phase 6 of the implementation plan.

## Support

For issues or questions:
- Review `docs/plans/Phase-1.md` for detailed task breakdown
- Check `docs/plans/Phase-0.md` for architecture decisions
- Review CloudFormation events for deployment errors
- Check CloudWatch Logs for runtime errors
