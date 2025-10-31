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

Float is a cross-platform meditation app built with React Native and Expo. It uses Google Generative AI, Eleven Labs text-to-Speech (migrating to Google TTS), and a library of sound files to create personalized meditation experiences based on user-submitted incidents that have affected them emotionally, which we refer to as "floats". Floats are categorized by emotion and intensity, and include a timer and a color scheme to indicate the duration, summary, and reasoning behind each meditation. The app can generate meditations from up to three floats at a time.

## Features :zap:

- **Personalized Meditations**: Generates customized meditation sessions based on user-submitted floats.
- **Multi-Platform Support**: Built with React Native and Expo, supporting iOS, Android and Web platforms.
- **Create Floats with Audio and Text**: User can create floats with audio or text allowing Gemini to capture tonality and speech patterns to asses mood and intensity of emotion as well as text
- **Google Generative AI Integration**: Utilizes Google Generative AI for generating floats and meditation content.
- **ElevenLabs Text-to-Speech**: Converts generated text into spoken meditations using ElevenLabs' text-to-speech technology.
- **Color-Coded Timer**: Provides a visual timer with a color scheme to indicate the elapsed time of the meditation session.
- **Emotion and Intensity Categorization**: Categorizes floats by emotion and intensity to tailor meditation experiences.
- **Backend Powered by AWS Lambda**: Manages API calls to Google Generative AI and ElevenLabs through AWS Lambda functions.

## Code Quality Standards 🏆

The Float project maintains high code quality standards for both frontend and backend:

### Backend (Python)

We enforce consistent code quality using:

- **Type Hints** (`mypy`): Full type annotations on public APIs
- **Linting** (`ruff`): Catch bugs and enforce consistent style
- **Formatting** (`black`): Opinionated code formatter for consistency
- **Testing** (`pytest`): 60%+ coverage on critical paths

#### Quick Start for Backend Development

```bash
# Setup (one-time)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Before committing
make quality      # Run all checks
# Or individual checks:
make test         # Run pytest with coverage
make type-check   # Run mypy type checker
make lint         # Run ruff linter
make format       # Auto-format with black
```

#### Available Commands

| Command              | Purpose                                                |
| -------------------- | ------------------------------------------------------ |
| `make quality`       | Run all quality checks (tests → types → lint → format) |
| `make quality-fix`   | Auto-fix linting and formatting issues                 |
| `make test`          | Run pytest with coverage report                        |
| `make type-check`    | Check types with mypy                                  |
| `make lint`          | Run ruff linter                                        |
| `make format`        | Format code with black                                 |
| `./check_quality.sh` | Bash alternative to `make quality`                     |

For detailed quality standards, see [backend/QUALITY.md](backend/QUALITY.md).

### Frontend (TypeScript/React Native)

We enforce consistent code quality using:

- **Type Checking** (`tsc`): TypeScript strict mode for full type safety
- **Linting** (`eslint`): Catch bugs and enforce consistent patterns
- **Formatting** (`prettier`): Opinionated code formatter for consistency
- **Testing** (`jest`): Unit and component tests with React Native testing library

#### Quick Start for Frontend Development

```bash
# Setup (one-time)
npm install

# Before committing
./check_frontend_quality.sh   # Run all checks
# Or individual checks:
npm test                      # Run tests
npm run type-check            # Run TypeScript type checker
npm run lint                  # Run ESLint linter
npm run format                # Auto-format with Prettier
```

#### Available Commands

| Command                       | Purpose                          |
| ----------------------------- | -------------------------------- |
| `npm test`                    | Run Jest tests with watch mode   |
| `npm run type-check`          | Check types with TypeScript      |
| `npm run lint`                | Run ESLint linter                |
| `npm run lint:fix`            | Auto-fix ESLint issues           |
| `npm run format`              | Format code with Prettier        |
| `npm run format:check`        | Check formatting without changes |
| `./check_frontend_quality.sh` | Run all quality checks           |

For detailed quality standards, see [FRONTEND_QUALITY.md](FRONTEND_QUALITY.md).

# Installation :eyes:

To set up and run Float locally, follow these steps:

### Prerequisites

**Frontend (All platforms)**

- Node.js (version 22 or higher)
- npm (version 9 or higher)

**Backend (Python)**

- Python 3.12 or higher
- pip (Python package manager)
- Virtual environment support

**External Services**

- A Google Cloud account with API access for Generative AI
- An ElevenLabs account with API access for Text-to-Speech
- OpenAI Account and API key
- AWS account with Lambda functions set up

### Clone the Repository

```bash
git clone https://github.com/yourusername/float.git
cd float
```

### Install Frontend Dependencies

```bash
npm install
```

### Setup Backend (Python)

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (including dev tools)
pip install -e ".[dev]"

# Verify setup with quality checks
make quality
```

## Configure Environment Variables

Create a .env file in the root directory and add the following variables. Google is the gold standard for IDP. Find out [more](https://developers.google.com/identity/protocols/oauth2) :

Frontend

```bash
EXPO_PUBLIC_LAMBDA_FUNCTION_URL=<URL>
EXPO_PUBLIC_WEB_CLIENT_ID=<ID>
EXPO_PUBLIC_ANDROID_CLIENT_ID=<ID>
```

Backend

```bash
FFMPEG_BINARY=/opt/bin/ffmpeg
G_KEY=<google_api_key>
SIMILARITY_BOOST=0.7
STABILITY=0.3
STYLE=0.3
VOICE_ID=jKX50Q2OBT1CsDwwcTkZ
XI_KEY=<eleven_labs_key>
OPENAI_API_KEY=<openai_key>
```

# Run the App :smile:

### Frontend

Start the development server:

```bash
npm start -c
```

This will open the metro builder. You can run the app on iOS, Android, or web

### Backend

Create a Lambda Layer for the FFMPEG subprocess. Thanks to [SARVESH VIRKUD](https://virkud-sarvesh.medium.com/building-ffmpeg-layer-for-a-lambda-function-a206f36d3edc)

The Lambda packages need to be downloaded and built on a Linux machine with python 3.12 for google.protbuf and crypto binary packages to work correctly

## Usage

- **Add Floats:** Enter incidents with audio or text that have affected you.
- **Review:** Review the summary and reasoning behind the float-generation.
- **Timing:** Use the color-coded timer to monitor if enough temporal space has been created.
- **Generate Meditation:** Select up to three floats to create a personalized meditation.
- **Start Meditation:** Begin the meditation session.

## Development Workflow 🔧

### Before Committing Code

1. **Backend Changes:**

   ```bash
   cd backend
   make quality  # Run all quality checks
   ```

   This runs:
   - Tests with coverage report
   - Type checking (mypy)
   - Linting (ruff)
   - Code formatting (black)

2. **Frontend Changes:**

   ```bash
   npm run lint    # ESLint (Phase 3)
   npm run format  # Prettier (Phase 3)
   ```

3. **Commit with clear messages:**

   ```bash
   git add .
   git commit -m "feat: add awesome new feature

   Description of what was implemented and why."
   ```

### Code Quality Standards

- **Python Backend:** 100% type hints on public APIs, 60%+ test coverage
- **TypeScript Frontend:** Strict mode enabled, comprehensive tests
- **All Code:** Must pass linting and formatting before merge

See [backend/QUALITY.md](backend/QUALITY.md) for detailed quality guidelines.

### Continuous Integration

Tests run automatically on pull requests and commits via GitHub Actions:
- **Frontend Tests**: Jest, TypeScript, ESLint, Prettier (Node 22.x)
- **Backend Tests**: Pytest, MyPy, Ruff, Black (Python 3.11 and 3.12)

See [docs/CI_CD.md](docs/CI_CD.md) for details on viewing and debugging workflows.

## API Integration :fire:

- **Google Generative AI:** Used for generating the content of the meditations.
- **AWS Lambda:** Manages API calls and processes data from Google and ElevenLabs APIs.

**Choice of Voice API:** Converts generated text into audio for the meditation sessions.

- **ElevenLabs**
- **Google TTS**
- **OpenAI Text-to-Speech**

## License

This project is licensed under the Apache 2.0 License. See the LICENSE file for details.

## Acknowledgements

**Google Icons:** Material Icons provided by Google Material Icons

**Logo Font:** Font provided by notyourtypefoundry testType(1.1)

## Contact

For questions or feedback, please contact:

- Email: gemenielabs@gmail.com
- GitHub: https://github.com/hatmanstack
- Twitter: @hatmanstack

Enjoy your meditative journey with Float!
