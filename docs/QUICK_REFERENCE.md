# Quick Reference

Quick lookup guide for common tasks, commands, and file locations.

## Common Commands

### Frontend

```bash
npm start -c              # Start dev server (iOS/Android/Web)
npm test                  # Run tests (watch mode)
npm test -- --coverage    # Run tests with coverage
npm run lint              # Check for lint errors
npm run lint:fix          # Fix lint errors automatically
npm run format            # Format code with Prettier
npm run type-check        # Check TypeScript types
```

### Backend

```bash
cd backend
source .venv/bin/activate # Activate virtual environment

# Testing
pytest tests/             # Run all tests
pytest tests/ --cov=src/  # Run tests with coverage
pytest tests/ -v          # Verbose output

# Quality Checks
ruff check src/           # Check for lint errors
ruff check src/ --fix     # Fix lint errors
black src/                # Format code
mypy src/                 # Check types
make quality              # Run all checks

# Deployment
npm run deploy            # Interactive deployment
npm run validate          # Validate template
npm run logs              # View logs
```

## File Locations

| Item                    | Location                                 |
| ----------------------- | ---------------------------------------- |
| Frontend app code       | `app/`                                   |
| React Native components | `components/`                            |
| Backend source          | `backend/src/`                           |
| Lambda handler          | `backend/src/handlers/lambda_handler.py` |
| Services                | `backend/src/services/`                  |
| Deployment scripts      | `backend/scripts/`                       |
| SAM Template            | `backend/template.yaml`                  |
| Deployment Config       | `backend/.deploy-config.json`            |
| Secrets (Local)         | `backend/samconfig.toml`                 |
| Backend tests           | `backend/tests/`                         |
| Python requirements     | `backend/requirements.txt`               |

## Deployment Process

The backend uses a single-environment deployment model with AWS SAM.

1. **Deploy**: `cd backend && npm run deploy`
2. **Configure**: Enter API keys when prompted (first time only)
3. **Frontend Config**: `frontend/.env` is auto-generated
4. **Logs**: `npm run logs` to monitor

See [docs/DEPLOYMENT.md](./DEPLOYMENT.md) for full details.

## Code Quality Tools

### Frontend

| Tool       | Command              | Purpose                  |
| ---------- | -------------------- | ------------------------ |
| Jest       | `npm test`           | Unit and component tests |
| TypeScript | `npm run type-check` | Static type checking     |
| ESLint     | `npm run lint`       | Code style and bugs      |
| Prettier   | `npm run format`     | Code formatting          |

### Backend

| Tool   | Command           | Purpose                    |
| ------ | ----------------- | -------------------------- |
| pytest | `pytest tests/`   | Unit and integration tests |
| mypy   | `mypy src/`       | Static type checking       |
| ruff   | `ruff check src/` | Code style and bugs        |
| black  | `black src/`      | Code formatting            |

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  Frontend (React Native + Expo)         │
│  - iOS, Android, Web                    │
│  - TypeScript + ESLint + Jest           │
└────────────────────┬────────────────────┘
                     │
                     │ HTTP API
                     │
┌────────────────────▼────────────────────┐
│  Backend (AWS Lambda)                   │
│  - Python 3.13                          │
│  - Google Gemini AI                     │
│  - OpenAI TTS                           │
│  - AWS S3 Storage                       │
└─────────────────────────────────────────┘
```

## Development Setup Checklist

- [ ] Node.js 22+ installed
- [ ] Python 3.13+ installed
- [ ] AWS CLI & SAM CLI installed
- [ ] Repository cloned
- [ ] Frontend: `npm install`
- [ ] Backend: `python3 -m venv backend/.venv && source backend/.venv/bin/activate`
- [ ] Backend Deps: `pip install -r backend/requirements.txt -r backend/requirements-dev.txt`
- [ ] API keys configured (via deploy script)

## Before Committing

**Frontend**:

```bash
npm test && npm run lint && npm run format
```

**Backend**:

```bash
cd backend && make quality
```

**Git**:

```bash
git add .
git commit -m "type: description"  # Use conventional commits
```

## Common Issues

| Issue                       | Solution                                             |
| --------------------------- | ---------------------------------------------------- |
| "sam: command not found"    | `brew install aws-sam-cli`                           |
| "Module not found" (Python) | Activate venv: `source backend/.venv/bin/activate`   |
| Tests failing               | Check `.env`, run `npm install`, or check git branch |
| Deployment fails            | Run `npm run validate` to check template             |

## Important Files

### Configuration

- `.env.example` - Environment variable template
- `.editorconfig` - Editor settings (tabs, line endings)
- `backend/template.yaml` - AWS SAM configuration
- `backend/samconfig.toml` - SAM deployment config (gitignored)
- `.gitignore` - Git ignore rules

### Workflows & Docs

- `README.md` - Project overview
- `CONTRIBUTING.md` - Contributing guidelines
- `docs/DEVELOPMENT.md` - Daily development guide
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/ARCHITECTURE.md` - System architecture
- `docs/API.md` - API documentation
- `docs/CI_CD.md` - CI/CD information

## API Endpoints

**Base URL**: `https://<your-lambda-function-url>/api/meditation`

See [docs/API.md](./API.md) for full details.

## Testing

### Frontend

```bash
npm test                              # Watch mode
npm test -- --testNamePattern=foo    # Specific test
npm test -- --coverage               # With coverage
```

### Backend

```bash
cd backend
pytest tests/                         # All tests
pytest tests/ -k test_name           # Specific test
pytest tests/ -v -s                  # Verbose with output
pytest tests/ --cov=src/             # With coverage
```
