# Float Meditation Backend - Simple Deployment

## Quick Start

Deploy the backend with a single command from root:

```bash
npm run backend:deploy
```

Or from the infrastructure directory:

```bash
cd infrastructure
npm run deploy
```

The first time you run this, you'll be prompted for:
- Stack name (default: `float-meditation`)
- AWS Region (default: `us-east-1`)
- Environment (`staging` or `production`)
- FFmpeg Layer ARN
- Google Gemini API key
- OpenAI API key
- ElevenLabs API key (optional)

Your configuration is saved to `samconfig.toml` (ignored by git). Subsequent deployments will reuse your saved configuration.

## Prerequisites

1. **AWS SAM CLI**
   ```bash
   pip install aws-sam-cli
   ```

2. **AWS CLI with credentials configured**
   ```bash
   aws configure
   ```

3. **FFmpeg Lambda Layer**
   - Deploy a layer with FFmpeg or use an existing one
   - Example ARN: `arn:aws:lambda:us-east-1:123456789:layer:ffmpeg:1`

## Commands

### From Root Directory

| Command | Description |
|---------|-------------|
| `npm run backend:deploy` | Build and deploy backend |
| `npm run backend:validate` | Validate CloudFormation template |
| `npm run backend:logs` | View Lambda function logs (live tail) |

### From Infrastructure Directory

| Command | Description |
|---------|-------------|
| `npm run deploy` | Build and deploy backend |
| `npm run validate` | Validate CloudFormation template |
| `npm run logs` | View Lambda function logs (live tail) |

## What Gets Deployed

- **Lambda Function**: Python 3.12, 15min timeout, 4GB memory
  - Handles meditation generation using Google Gemini and OpenAI
  - FFmpeg for audio processing

- **API Gateway**: HTTP API with `/meditation` POST endpoint

- **S3 Buckets**:
  - Customer data bucket (encrypted, versioned)
  - Audio files bucket (encrypted, 90-day expiration)

## Configuration Details

Configuration is stored in `samconfig.toml`:

```toml
[default.global.parameters]
stack_name = "float-meditation"
region = "us-east-1"

[default.deploy.parameters]
capabilities = "CAPABILITY_IAM CAPABILITY_NAMED_IAM"
confirm_changeset = true
parameter_overrides = "Environment=\"staging\" FFmpegLayerArn=\"...\" GKey=\"...\" OpenAIKey=\"...\" XIKey=\"...\""
```

**Note**: `samconfig.toml` contains sensitive API keys and is excluded from git.

## Updating Configuration

To update API keys or other parameters:

1. Edit `samconfig.toml` directly, or
2. Delete `samconfig.toml` and run `npm run deploy` to be prompted again

## Getting FFmpeg Layer ARN

If you need to create an FFmpeg layer:

1. Use the Serverless Application Repository layer:
   ```
   arn:aws:serverlessrepo:us-east-1:145266761615:applications/ffmpeg-lambda-layer
   ```

2. Or deploy your own layer following AWS Lambda layer guidelines

## Viewing Deployment Info

After deployment, get the API endpoint:

```bash
aws cloudformation describe-stacks \
  --stack-name float-meditation \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Troubleshooting

**"AWS credentials not configured"**
- Run `aws configure` and enter your credentials

**"SAM CLI not found"**
- Install SAM CLI: `pip install aws-sam-cli`

**"Parameter validation failed"**
- Check that FFmpegLayerArn matches the pattern `arn:aws:lambda:REGION:ACCOUNT:layer:NAME:VERSION`

**"Stack does not exist"**
- First deployment will create the stack
- Use `confirm_changeset: true` in samconfig.toml to review changes

## Differences from GitHub Actions Deployment

Previously, deployments required:
- GitHub Actions workflows
- Manual approval gates
- Multiple jobs and steps
- GitHub secrets management

Now:
- Single local command: `npm run deploy`
- Configuration stored locally in `samconfig.toml`
- Immediate deployment with optional changeset confirmation
- No external dependencies on CI/CD platform

## Migration from Old Deployment

If migrating from the GitHub Actions workflow:

1. Get your API keys from GitHub Secrets
2. Run `npm run deploy` and enter the keys when prompted
3. Configuration is saved for future deployments
4. Old GitHub workflows can be archived or removed

## Stack Outputs

After deployment, the following outputs are available:

- **ApiEndpoint**: The API Gateway URL for the `/meditation` endpoint
- **LambdaFunctionArn**: ARN of the deployed Lambda function
- **CustomerDataBucketName**: Name of the S3 bucket for customer data
- **AudioBucketName**: Name of the S3 bucket for audio files
