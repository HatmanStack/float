<h1 align="center">
  <img width="800" src="banner.png" alt="float-app icon">
</h1>
<h4 align="center">
  <a href="https://www.apache.org/licenses/LICENSE-2.0.html">
    <img src="https://img.shields.io/badge/license-Apache2.0-blue" alt="float is under the Apache 2.0 liscense" />
  </a>
  <a href="https://github.com/circlemind-ai/fast-graphrag/blob/main/CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/Expo-51+-green" alt="Expo Version" />
  </a>
  <a href="https://cloud.google.com/text-to-speech/docs/basics">
    <img src="https://img.shields.io/badge/Google%20TTS->=2.6-yellow" alt="Google Text-To-Speech" />
  </a>
  <a href="https://platform.openai.com/docs/guides/text-to-speech">
    <img src="https://img.shields.io/badge/OpenAI-voilet" alt="OpenAI Text-To-Speech" />
  </a>
  <img src="https://img.shields.io/youtube/views/8hmrio2A5Og">
  <a href="https://www.python.org/">
  <img src="https://img.shields.io/badge/python->=3.12.1-blue">
  </a>
</h4>
<p align="center">
  <p align="center"><b>From feelings to Flow - Customized Meditations <br> <a href="https://float-app.fun/"> FLOAT » </a> </b> </p>
</p>

# Float

Float is a cross-platform meditation app that generates personalized meditation sessions from user-submitted emotional incidents ("floats"). Built with React Native/Expo and AWS Lambda, it uses Google Generative AI to analyze emotions and OpenAI TTS to synthesize meditation audio.

## Features

- **Personalized Meditations**: AI-generated meditations based on your emotions and incidents
- **Audio & Text Input**: Submit floats via audio or text for accurate mood detection
- **Multi-Platform**: iOS, Android, and Web via Expo
- **Emotion Analysis**: Automatic categorization by emotion and intensity
- **Background Music Integration**: Combined meditation voice with curated sound libraries
- **Serverless Backend**: AWS Lambda for scalability

## Code Quality Standards

Float maintains strict code quality across frontend and backend using automated tools and tests. Detailed standards are documented in configuration files (.eslintrc.json, pyproject.toml, etc.).

### Backend (Python)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run all checks
make quality
```

**Tools**: mypy (type checking), ruff (linting), black (formatting), pytest (testing)

See [backend/QUALITY.md](backend/QUALITY.md) for detailed standards.

### Frontend (TypeScript/React Native)

```bash
npm install

# Run all checks
./check_frontend_quality.sh
```

**Tools**: TypeScript (strict mode), ESLint, Prettier, Jest

See [FRONTEND_QUALITY.md](FRONTEND_QUALITY.md) for detailed standards.

## Quick Start

### Prerequisites

- **Node.js** 22+ ([via nvm](https://github.com/nvm-sh/nvm))
- **Python** 3.12+
- **Git**
- API keys: Google Gemini, OpenAI (TTS), AWS credentials

### Setup

```bash
# Clone and install frontend
git clone https://github.com/circlemind-ai/float.git
cd float
npm install

# Setup backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..

# Create .env from .env.example
cp .env.example .env
# Edit .env with your API keys
```

### Development

```bash
# Frontend: Start metro bundler
npm start -c

# Backend: Run quality checks
cd backend && make quality

# Run tests
npm test                    # Frontend
cd backend && pytest tests/ # Backend
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed workflow and commands.

## Usage

1. **Submit a Float**: Record or type an emotional incident
2. **Get Analysis**: AI analyzes sentiment and intensity
3. **Create Meditation**: Select floats to personalize your session
4. **Meditate**: Listen to AI-generated meditation with background music

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for daily workflow, common commands, and tips.

### Before Committing

```bash
# Backend
cd backend && make quality

# Frontend
npm run lint && npm run format
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, code standards, and pull request process.

### Continuous Integration

Tests run automatically on push/PR via GitHub Actions. See [docs/CI_CD.md](docs/CI_CD.md) for details.

## Architecture

Float uses a serverless architecture with separation between frontend and backend:

- **Frontend**: React Native/Expo app for iOS, Android, and Web
- **Backend**: AWS Lambda functions handling AI, TTS, and storage
- **AI**: Google Gemini for emotion analysis and meditation generation
- **TTS**: OpenAI for meditation audio synthesis
- **Storage**: AWS S3 for user data and generated meditations

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design and data flows.

## API Reference

See [docs/API.md](docs/API.md) for Lambda endpoint documentation.

## Troubleshooting

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for common issues and solutions.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Contact

- GitHub: [circlemind-ai/float](https://github.com/circlemind-ai/float)
- Email: gemenielabs@gmail.com

---

**From feelings to Flow** 🧘‍♀️ - Personalized meditations for emotional well-being
