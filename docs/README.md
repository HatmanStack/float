<div align="center">
<h1 align="center">
  <img width="600" src="../banner.png" alt="float-app icon">
</h1>

<h4>
<a href="https://www.apache.org/licenses/LICENSE-2.0.html"><img src="https://img.shields.io/badge/license-Apache2.0-blue" alt="Apache 2.0 license" /></a>
<a href="https://expo.dev"><img src="https://img.shields.io/badge/Expo-55+-orange" alt="Expo Version" /></a>
<a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/Google-Gemini-violet" alt="Google Gemini" /></a>
<a href="https://platform.openai.com/docs/guides/text-to-speech"><img src="https://img.shields.io/badge/OpenAI-TTS-yellow" alt="OpenAI TTS" /></a>
<a href="https://docs.aws.amazon.com/lambda/"><img src="https://img.shields.io/badge/AWS-Lambda-green" alt="AWS Lambda" /></a>
</h4>

<p><br><a href="https://float.hatstack.fun/">FLOAT »</a></b></p>
</div>

## Overview

Float is a cross-platform meditation app that generates personalized sessions from user-submitted emotional incidents ("floats"). Built with React Native/Expo and AWS Lambda.

## Documentation

- [API.md](API.md) - Lambda endpoint documentation, request/response formats
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and data flows
- [plans/](plans/) - Remediation plans and audit history

## Development

### Setup

```bash
# Frontend
npm install --legacy-peer-deps

# Backend (for local testing)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend Environment

Create `frontend/.env` with:

```
EXPO_PUBLIC_LAMBDA_FUNCTION_URL=<your-api-url>
EXPO_PUBLIC_WEB_CLIENT_ID=<your-google-oauth-client-id>
```

| Variable | Description |
|----------|-------------|
| `EXPO_PUBLIC_LAMBDA_FUNCTION_URL` | API Gateway URL (set automatically by `npm run deploy`) |
| `EXPO_PUBLIC_WEB_CLIENT_ID` | Google OAuth Web Client ID for Google Sign-in on web |
| `EXPO_PUBLIC_ANDROID_CLIENT_ID` | Google OAuth Android Client ID (optional, required for Android builds that use native Google Sign-in) |

See `frontend/.env.example` for the canonical template.

To get `EXPO_PUBLIC_WEB_CLIENT_ID`:
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID → Web application
3. Add authorized JavaScript origins (e.g., `http://localhost:8081` for dev)
4. Copy the Client ID

### Running

```bash
npm start           # Start Expo dev server
npm run check       # Run all lint and tests
```

### Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start Expo dev server |
| `npm test` | Run Jest (`cd frontend && npx jest --forceExit`, no watch) |
| `npm run lint` | Run ESLint + TypeScript check |
| `npm run lint:backend` | Run ruff on backend |
| `npm run check` | Run all checks |
| `npm run deploy` | Deploy backend to AWS |

## Testing

### Frontend

```bash
npm test                    # Run Jest once (cd frontend && npx jest --forceExit)
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

Create `backend/samconfig.toml` (this file is gitignored — each developer creates their own):

```toml
version = 0.1
[default.deploy.parameters]
stack_name = "float-backend"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "Environment=production GeminiApiKey=your-key OpenAIApiKey=your-key FfmpegLayerArn=arn:aws:lambda:..."
resolve_s3 = true
```

### Environment Variables

Set these via SAM parameter overrides during deployment:

| Variable | Description |
|----------|-------------|
| `GeminiApiKey` | Google Gemini API key (read by `settings.py` from env var `GEMINI_API_KEY`; the legacy alias `G_KEY` is still accepted via `AliasChoices`) |
| `OpenAIApiKey` | OpenAI API key for TTS |
| `S3DataBucket` | S3 bucket for user data (default: `float-cust-data`) |
| `S3AudioBucket` | S3 bucket for background music |
| `IncludeDevOrigins` | Set to `true` for local dev (CORS wildcard) |
| `ProductionOrigins` | Comma-separated production origins for CORS (e.g., `https://float-app.fun`) |
| `FfmpegLayerArn` | ARN of the FFmpeg Lambda layer (auto-created by deploy script) |

The following environment variables are set automatically in Lambda via the SAM template but are useful for local development:

| Variable | Description |
|----------|-------------|
| `ENABLE_HLS_STREAMING` | Enable HLS streaming for meditation audio (default: `true`) |
| `LOG_LEVEL` | Log level (default: `INFO`) |
| `ENVIRONMENT` | Deployment environment (default: `production`) |

## Project Structure

```text
float/
├── frontend/           # Expo/React Native app
│   ├── app/           # Expo Router pages
│   ├── components/    # React components
│   │   ├── HLSPlayer/       # HLS audio player
│   │   ├── DownloadButton/  # Download meditation button
│   │   ├── ScreenComponents/ # UI controls (record, meditation, incidents)
│   │   └── navigation/      # Navigation components
│   ├── context/       # React Context providers
│   ├── constants/     # App constants
│   ├── hooks/         # Custom React hooks
│   └── tests/         # Jest suites (unit/, integration/, e2e/)
├── backend/           # AWS Lambda
│   ├── src/           # Python source
│   │   ├── handlers/  # Lambda handlers
│   │   ├── services/  # Business logic
│   │   ├── providers/ # External API clients
│   │   ├── config/    # Settings and constants
│   │   ├── models/    # Pydantic request/response models
│   │   ├── utils/     # Circuit breaker, caching, logging, audio utilities
│   │   └── exceptions.py  # Custom exception hierarchy
│   ├── tests/         # pytest suites (unit/, integration/, e2e/)
│   ├── template.yaml  # SAM template
│   └── samconfig.toml # SAM deployment config (gitignored, create from template)
└── docs/              # Documentation (API.md, ARCHITECTURE.md, plans/)
```

## Troubleshooting

### Module not found (npm)

```bash
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
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
