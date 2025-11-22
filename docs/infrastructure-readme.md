# Infrastructure

This directory contains the AWS SAM (Serverless Application Model) infrastructure-as-code definitions for the Float meditation app.

## Directory Structure

- `template.yaml`: The main SAM template defining AWS resources (Lambda, S3, API Gateway, IAM).
- `parameters/`: Environment-specific parameter files.
    - `staging.json`: Parameters for the staging environment (git-ignored).
    - `production.json`: Parameters for the production environment (git-ignored).
    - `*-example.json`: Example parameter files with placeholder values.
- `scripts/`: Deployment automation scripts.
    - `deploy-staging.sh`: Deploys to the staging environment.
    - `deploy-production.sh`: Deploys to the production environment.
    - `validate-template.sh`: Validates the SAM template.

## Prerequisites

To deploy this infrastructure, you need:

1.  **AWS CLI** configured with appropriate credentials (`aws configure`).
2.  **AWS SAM CLI** installed (`sam --version`).
3.  **FFmpeg Lambda Layer** ARN available in your AWS account (see Phase-0 ADR-9).
4.  **API Keys** for Google Gemini, OpenAI, and ElevenLabs (optional).

## Deployment Process

### 1. Setup Parameters

Create the environment-specific parameter file from the example:

```bash
cp infrastructure/parameters/staging-example.json infrastructure/parameters/staging.json
```

Edit `infrastructure/parameters/staging.json` and fill in the actual values for your environment.

### 2. Deploy

Run the deployment script for the target environment:

```bash
./infrastructure/scripts/deploy-staging.sh
```

The script will:
1.  Validate the SAM template.
2.  Build the Lambda function.
3.  Deploy the CloudFormation stack using the parameters provided.

## AWS Permissions

The user deploying the stack needs permissions to manage the following AWS resources:
- CloudFormation
- Lambda
- S3
- API Gateway
- IAM (to create execution roles)
- CloudWatch Logs

