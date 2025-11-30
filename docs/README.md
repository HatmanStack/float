<div align="center">
<h1 align="center">
  <img width="600" src="../banner.png" alt="float-app icon">
</h1>

<h4>
<a href="https://www.apache.org/licenses/LICENSE-2.0.html"><img src="https://img.shields.io/badge/license-Apache2.0-blue" alt="Apache 2.0 license" /></a>
<a href="https://expo.dev"><img src="https://img.shields.io/badge/Expo-52+-orange" alt="Expo Version" /></a>
<a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/Google-Gemini-violet" alt="Google Gemini" /></a>
<a href="https://platform.openai.com/docs/guides/text-to-speech"><img src="https://img.shields.io/badge/OpenAI-TTS-yellow" alt="OpenAI TTS" /></a>
<a href="https://docs.aws.amazon.com/lambda/"><img src="https://img.shields.io/badge/AWS-Lambda-green" alt="AWS Lambda" /></a>
</h4>

<p><br><a href="https://float-app.fun/">FLOAT »</a></b></p>
</div>

## Overview

Float is a cross-platform meditation app that generates personalized sessions from user-submitted emotional incidents ("floats"). Built with React Native/Expo and AWS Lambda.

## Documentation

- [API.md](API.md) - Lambda endpoint documentation, request/response formats
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and data flows

## Development

### Setup

```bash
# Frontend
npm install

# Backend (for local testing)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running

```bash
npm start           # Start Expo dev server
npm run check       # Run all lint and tests
```

### Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start Expo dev server |
| `npm test` | Run Jest tests |
| `npm run lint` | Run ESLint + TypeScript check |
| `npm run lint:backend` | Run ruff on backend |
| `npm run check` | Run all checks |
| `npm run deploy` | Deploy backend to AWS |

## Testing

### Frontend

```bash
npm test                    # Run Jest (watch mode)
npm run check               # Run lint + tests
```

### Backend

```bash
cd backend
PYTHONPATH=. pytest tests/unit -v
```

## Deployment

Uses AWS SAM for infrastructure-as-code deployment.

```bash
npm run deploy
# Equivalent to: cd backend && sam build && sam deploy
```

### Configuration

Edit `backend/samconfig.toml`:

```toml
version = 0.1
[default.deploy.parameters]
stack_name = "float-backend"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "Environment=production"
resolve_s3 = true
```

### Environment Variables

Set these via SAM parameter overrides during deployment:

| Variable | Description |
|----------|-------------|
| `GeminiApiKey` | Google Gemini API key |
| `OpenAIApiKey` | OpenAI API key for TTS |
| `S3DataBucket` | S3 bucket for user data |
| `S3AudioBucket` | S3 bucket for background music |
| `IncludeDevOrigins` | Set to `true` for local dev (CORS wildcard) |
| `ProductionOrigins` | Comma-separated production origins for CORS |

## Project Structure

```text
float/
├── frontend/           # Expo/React Native app
│   ├── app/           # Expo Router pages
│   ├── components/    # React components
│   ├── context/       # React Context providers
│   ├── constants/     # App constants
│   └── hooks/         # Custom React hooks
├── backend/           # AWS Lambda
│   ├── src/           # Python source
│   │   ├── handlers/  # Lambda handlers
│   │   ├── services/  # Business logic
│   │   └── providers/ # External API clients
│   ├── tests/         # Backend tests
│   ├── template.yaml  # SAM template
│   └── samconfig.toml # SAM deployment config
├── tests/             # Frontend tests
│   └── frontend/
│       ├── unit/
│       ├── integration/
│       └── e2e/
└── docs/              # Documentation
```

## Troubleshooting

### Module not found (npm)

```bash
rm -rf node_modules package-lock.json
npm install
```

### Python import errors

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

### SAM deployment fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Validate template
sam validate --template backend/template.yaml
```
