# Deployment Guide

This guide provides step-by-step instructions for deploying the Float Meditation app infrastructure to AWS.

## Prerequisites Checklist

Before deploying, ensure you have:

- [ ] **AWS SAM CLI installed** (v1.100.0 or newer)
  ```bash
  sam --version
  ```
  Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

- [ ] **AWS CLI installed and configured**
  ```bash
  aws --version
  aws sts get-caller-identity  # Verify credentials
  ```

- [ ] **Docker installed** (for SAM builds)
  ```bash
  docker --version
  ```

- [ ] **FFmpeg Lambda Layer created** (see docs/plans/Phase-0.md ADR-9)
  ```bash
  aws lambda list-layer-versions --layer-name ffmpeg --region us-east-1
  # Copy the LayerVersionArn for your parameter file
  ```

- [ ] **API Keys obtained:**
  - Google Gemini API key (from Google AI Studio)
  - OpenAI API key (from OpenAI platform)
  - ElevenLabs API key (optional)

- [ ] **Parameter file configured:**
  - Edit `infrastructure/parameters/staging.json`
  - Replace ALL placeholder values with real credentials
  - Verify file is git-ignored: `git status` should NOT show staging.json

## Deployment Steps

### Step 1: Prepare Environment

1. **Navigate to infrastructure directory:**
   ```bash
   cd infrastructure/
   ```

2. **Edit parameter file with real values:**
   ```bash
   # Open staging.json in your editor
   # Replace these placeholder values:
   #   - FFmpegLayerArn: Your actual FFmpeg layer ARN
   #   - GoogleGeminiApiKey: Your Google Gemini API key
   #   - OpenAIApiKey: Your OpenAI API key
   #   - ElevenLabsApiKey: Your ElevenLabs key (or leave empty)
   ```

3. **Verify .gitignore protection:**
   ```bash
   git status
   # staging.json should NOT appear in output
   ```

### Step 2: Validate Template

```bash
./scripts/validate-template.sh
```

Expected output:
```
✓ Template validation successful!
```

If validation fails, review the error messages and fix template issues.

### Step 3: Deploy to Staging

```bash
./scripts/deploy-staging.sh
```

**First deployment** will use SAM guided mode and prompt for:
- Stack name: `float-meditation-staging` (recommended)
- AWS Region: e.g., `us-east-1`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to configuration file: `Y`

This creates `samconfig.toml` for future deployments.

**Subsequent deployments** will use saved configuration from `samconfig.toml`.

### Step 4: Verify Deployment

After successful deployment, the script will display stack outputs:

```
Stack outputs:
┌────────────────────┬─────────────────────────────────────────────┐
│ OutputKey          │ OutputValue                                  │
├────────────────────┼─────────────────────────────────────────────┤
│ ApiEndpoint        │ https://xxxxx.execute-api.us-east-1.amazo... │
│ LambdaFunctionArn  │ arn:aws:lambda:us-east-1:123456789012:fun... │
│ CustomerDataBucket │ float-meditation-staging-cust-data-123...   │
│ AudioBucket        │ float-meditation-staging-audio-123...        │
└────────────────────┴─────────────────────────────────────────────┘
```

Copy the **ApiEndpoint** value for testing.

### Step 5: Test the Deployment

#### Test via curl:

```bash
# Replace API_ENDPOINT with your actual endpoint from stack outputs
API_ENDPOINT="https://xxxxx.execute-api.us-east-1.amazonaws.com/api/meditation"

# Test summary endpoint
curl -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d @test-requests/summary-request.json

# Expected response:
# {
#   "statusCode": 200,
#   "body": "{\"sentiment_label\": \"positive\", \"intensity\": 0.8, ...}"
# }
```

#### Test via AWS CLI:

```bash
# Direct Lambda invocation
aws lambda invoke \
  --function-name float-meditation-staging \
  --payload file://test-requests/summary-request.json \
  response.json

# View response
cat response.json
```

#### View CloudWatch Logs:

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/float-meditation-staging --follow

# View recent logs
aws logs tail /aws/lambda/float-meditation-staging --since 10m
```

## Troubleshooting

### Deployment Fails: "Layer not found"

**Problem:** FFmpeg layer ARN is invalid or in wrong region.

**Solution:**
```bash
# List available layers
aws lambda list-layer-versions --layer-name ffmpeg --region us-east-1

# Update parameters/staging.json with correct ARN
```

### Deployment Fails: "Bucket name already exists"

**Problem:** S3 bucket names are globally unique.

**Solution:** The template uses CloudFormation-generated names with account ID. If this still fails, another AWS account may have a conflicting name. The template will automatically handle this.

### Deployment Fails: "User is not authorized"

**Problem:** AWS credentials lack necessary permissions.

**Solution:**
```bash
# Check current identity
aws sts get-caller-identity

# Required permissions:
# - CloudFormation full access
# - Lambda full access
# - S3 full access
# - IAM role creation
# - API Gateway full access
```

Contact your AWS administrator to grant necessary permissions.

### Lambda Execution Fails: "FFmpeg not found"

**Problem:** FFmpeg binary not accessible in Lambda.

**Solution:**
1. Verify layer is attached to Lambda function in AWS Console
2. Check FFMPEG_PATH environment variable = `/opt/bin/ffmpeg`
3. Verify layer architecture matches Lambda (x86_64)

### API Gateway Returns CORS Error

**Problem:** CORS configuration mismatch.

**Solution:**
- Verify your frontend domain is in AllowOrigins list in template.yaml
- For local testing, `http://localhost:*` is already included
- Check Lambda response includes CORS headers

### Test Request Returns Error

**Problem:** API keys invalid or services unavailable.

**Solution:**
1. Check CloudWatch Logs for detailed error messages
2. Verify API keys are valid and have appropriate quotas
3. Test API keys directly with service providers
4. Check Lambda environment variables in AWS Console

## Production Deployment

⚠️ **WARNING:** Production deployment requires extra care.

### Prerequisites for Production:

- [ ] Staging environment deployed and tested successfully
- [ ] Production parameter file created: `parameters/production.json`
- [ ] Production API keys obtained (separate from staging)
- [ ] Production FFmpeg layer ARN obtained
- [ ] AWS account verified (ensure correct production account)

### Deploy to Production:

```bash
./scripts/deploy-production.sh
```

The production script will:
1. Prompt for confirmation (type "yes" exactly)
2. Display AWS account for verification
3. Prompt for second confirmation
4. Create a CloudFormation change set for review
5. Prompt for final confirmation before executing

**Best Practices:**
- Deploy to staging first and test thoroughly
- Review the CloudFormation change set carefully
- Deploy during low-traffic periods
- Have a rollback plan ready
- Monitor CloudWatch Logs after deployment

## Rollback

If deployment fails or causes issues:

### Automatic Rollback:

CloudFormation automatically rolls back failed deployments.

### Manual Rollback:

```bash
# Delete stack (will remove all resources)
aws cloudformation delete-stack --stack-name float-meditation-staging

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name float-meditation-staging

# Re-deploy after fixing issues
./scripts/deploy-staging.sh
```

### Rollback to Previous Version:

```bash
# List stack events to find previous successful deployment
aws cloudformation describe-stack-events --stack-name float-meditation-staging

# Update with previous template version (if saved)
sam deploy --template-file previous-template.yaml
```

## Monitoring

### View Stack Status:

```bash
aws cloudformation describe-stacks --stack-name float-meditation-staging
```

### View Stack Events:

```bash
aws cloudformation describe-stack-events \
  --stack-name float-meditation-staging \
  --max-items 20
```

### View Lambda Metrics:

```bash
# Invocations, errors, duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=float-meditation-staging \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### View S3 Bucket Contents:

```bash
# List customer data
aws s3 ls s3://float-meditation-staging-cust-data-ACCOUNT_ID/

# List audio files
aws s3 ls s3://float-meditation-staging-audio-ACCOUNT_ID/
```

## Cost Monitoring

Monitor AWS costs to avoid surprises:

```bash
# View current month cost
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

**Expected monthly costs for staging (light usage):**
- Lambda: $0-5
- S3: $0-2
- API Gateway: $0-1
- CloudWatch Logs: $0-1
- **Total: ~$0-10/month**

## Next Steps

After successful deployment:

1. **Update frontend configuration** with API endpoint
2. **Set up CloudWatch alarms** for errors and high costs
3. **Configure S3 lifecycle policies** for cost optimization
4. **Implement CI/CD** (Phase 6 of implementation plan)
5. **Add monitoring dashboard** for visibility

## Support

For issues or questions:
- Review Phase 1 plan: `docs/plans/Phase-1.md`
- Check architecture decisions: `docs/plans/Phase-0.md`
- View CloudFormation events for deployment errors
- Check CloudWatch Logs for runtime errors
- Create an issue in the project repository
