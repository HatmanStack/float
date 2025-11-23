# Deployment Guide

The Float backend uses a simplified, single-environment deployment process built on AWS SAM (Serverless Application Model).

## Prerequisites

- **AWS CLI** configured with credentials (`aws configure`)
- **SAM CLI** installed (`brew install aws-sam-cli`)
- **Node.js** (for npm scripts)
- **Python 3.13** (for backend code)

## Quick Start

Deploy the entire backend stack with a single command:

```bash
cd backend
npm run deploy
```

This interactive script will:
1. Check for required tools
2. Prompt for missing configuration (first run only)
3. Build the SAM application
4. Deploy to AWS CloudFormation
5. Generate `../frontend/.env` automatically

## Configuration

Configuration is stored locally in `backend/.deploy-config.json`. This file is gitignored to prevent leaking secrets.

### Required Secrets
- `GEMINI_API_KEY`: Google Gemini API key
- `OPENAI_API_KEY`: OpenAI API key
- `ELEVENLABS_API_KEY`: ElevenLabs API key (optional)

### Default Settings
- **Region**: `us-east-1`
- **Stack Name**: `float-meditation-dev`
- **FFmpeg Layer**: Public layer in us-east-1

## Commands

All commands should be run from the `backend/` directory:

| Command | Description |
|---------|-------------|
| `npm run deploy` | Interactive build and deployment |
| `npm run validate` | Validate SAM template |
| `npm run logs` | Stream CloudWatch logs for the Lambda function |
| `npm run build` | Build the application (SAM build) |

## Troubleshooting

### "sam: command not found"
Install the SAM CLI:
```bash
brew install aws-sam-cli
```

### "AWS credentials not found"
Configure your AWS CLI:
```bash
aws configure
```

### Frontend .env not updating
Ensure the deployment script completes successfully. It writes to `../frontend/.env` only after a successful CloudFormation deployment.
