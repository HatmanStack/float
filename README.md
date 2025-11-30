<div align="center">
<h1 align="center">
  <img width="600" src="banner.png" alt="float-app icon">
</h1>

<h4>
<a href="https://www.apache.org/licenses/LICENSE-2.0.html"><img src="https://img.shields.io/badge/license-Apache2.0-blue" alt="Apache 2.0 license" /></a>
<a href="https://expo.dev"><img src="https://img.shields.io/badge/Expo-52+-orange" alt="Expo Version" /></a>
<a href="https://ai.google.dev/"><img src="https://img.shields.io/badge/Google-Gemini-violet" alt="Google Gemini" /></a>
<a href="https://platform.openai.com/docs/guides/text-to-speech"><img src="https://img.shields.io/badge/OpenAI-TTS-yellow" alt="OpenAI TTS" /></a>
<a href="https://docs.aws.amazon.com/lambda/"><img src="https://img.shields.io/badge/AWS-Lambda-green" alt="AWS Lambda" /></a>
</h4>

<p><b>From Feelings to Flow - Personalized Meditations<br><a href="https://float-app.fun/">FLOAT »</a></b></p>

<p>AI turns your most stressful moments into personalized guided meditations</p>
</div>

## Structure

```text
├── frontend/   # Expo/React Native client
├── backend/    # AWS Lambda serverless API
├── docs/       # Documentation
└── tests/      # Frontend test suites
```

## Prerequisites

- **Node.js** v24 LTS
- **Python** 3.13+
- **AWS CLI** configured (`aws configure`)
- **AWS SAM CLI** for deployment

## Quick Start

```bash
npm install     # Install dependencies
npm run deploy  # Deploy backend
npm start       # Start Expo dev server
npm run check   # Run all lint and tests
```

## Deployment

```bash
npm run deploy
```

Deploys the backend Lambda using AWS SAM. Configuration in `backend/samconfig.toml`.

| Parameter | Description |
|-----------|-------------|
| `GeminiApiKey` | Google Gemini API key |
| `OpenAIApiKey` | OpenAI API key |
| `ProductionOrigins` | Comma-separated allowed origins for CORS (e.g., `https://float-app.fun`) |

See [docs/README.md](docs/README.md) for full documentation.

## License

Apache 2.0
