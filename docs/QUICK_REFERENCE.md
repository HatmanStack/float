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

pytest tests/             # Run all tests
pytest tests/ --cov=src/  # Run tests with coverage
pytest tests/ -v          # Verbose output
ruff check src/           # Check for lint errors
ruff check src/ --fix     # Fix lint errors
black src/                # Format code
mypy src/                 # Check types
make quality              # Run all checks
```

## File Locations

| Item | Location |
|------|----------|
| Frontend app code | `app/` |
| React Native components | `components/` |
| Component tests | `components/__tests__/` |
| State management | `context/` |
| Frontend constants | `constants/` |
| Backend source | `backend/src/` |
| Lambda handler | `backend/src/handlers/lambda_handler.py` |
| Services | `backend/src/services/` |
| Data models | `backend/src/models/` |
| Backend tests | `backend/tests/` |
| ESLint config | `.eslintrc.json` |
| Prettier config | `.prettierrc.json` |
| TypeScript config | `tsconfig.json` |
| Python config | `backend/pyproject.toml` |
| Environment template | `.env.example` |

## Code Quality Tools

### Frontend

| Tool | Command | Purpose |
|------|---------|---------|
| Jest | `npm test` | Unit and component tests |
| TypeScript | `npm run type-check` | Static type checking |
| ESLint | `npm run lint` | Code style and bugs |
| Prettier | `npm run format` | Code formatting |

### Backend

| Tool | Command | Purpose |
|------|---------|---------|
| pytest | `pytest tests/` | Unit and integration tests |
| mypy | `mypy src/` | Static type checking |
| ruff | `ruff check src/` | Code style and bugs |
| black | `black src/` | Code formatting |

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
│  - Python 3.12                          │
│  - Google Gemini AI                     │
│  - OpenAI TTS                           │
│  - AWS S3 Storage                       │
└─────────────────────────────────────────┘
```

## Development Setup Checklist

- [ ] Node.js 22+ installed
- [ ] Python 3.12+ installed
- [ ] Git configured
- [ ] Repository cloned
- [ ] Frontend: `npm install`
- [ ] Backend: `python3 -m venv backend/.venv && source backend/.venv/bin/activate && pip install -e ".[dev]"`
- [ ] `.env` file created from `.env.example`
- [ ] API keys configured

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

| Issue | Solution |
|-------|----------|
| "Module not found" (npm) | Run `npm install` |
| "Module not found" (Python) | Activate venv: `source backend/.venv/bin/activate` |
| Port 8081 in use | Kill process or use `expo start -c --port 8082` |
| Type errors | Run `npm run type-check` or `mypy src/` |
| Lint errors | Run `npm run lint:fix` or `ruff check src/ --fix` |
| Format conflicts | Run `npm run format` first, then `npm run lint:fix` |
| Tests failing | Check `.env`, run `npm install`, or check git branch |

## Important Files

### Configuration

- `.env.example` - Environment variable template
- `.editorconfig` - Editor settings (tabs, line endings)
- `.eslintrc.json` - ESLint rules
- `.prettierrc.json` - Prettier formatting rules
- `tsconfig.json` - TypeScript configuration
- `backend/pyproject.toml` - Python project config
- `.gitignore` - Git ignore rules

### Workflows & Docs

- `README.md` - Project overview
- `CONTRIBUTING.md` - Contributing guidelines
- `docs/DEVELOPMENT.md` - Daily development guide
- `docs/ARCHITECTURE.md` - System architecture
- `docs/API.md` - API documentation
- `docs/CI_CD.md` - CI/CD information

## API Endpoints

**Base URL**: `https://<your-lambda-function-url>/`

### Summary Request
```bash
POST /
{
  "user_id": "user123",
  "inference_type": "summary",
  "audio": "base64_or_NotAvailable",
  "prompt": "text_or_NotAvailable"
}
```
Returns: sentiment analysis

### Meditation Request
```bash
POST /
{
  "user_id": "user123",
  "inference_type": "meditation",
  "input_data": {...},
  "music_list": [...]
}
```
Returns: base64 encoded meditation audio

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
pytest tests/                         # All tests
pytest tests/ -k test_name           # Specific test
pytest tests/ -v -s                  # Verbose with output
pytest tests/ --cov=src/             # With coverage
```

## Debugging

**Frontend**: Use React DevTools Profiler
**Backend**: Use `pytest -s` to see print statements

See [docs/DEVELOPMENT.md](./DEVELOPMENT.md) for detailed debugging guide.

## Learning Resources

- [React Native Docs](https://reactnative.dev/)
- [Expo Docs](https://docs.expo.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Python Docs](https://docs.python.org/3.12/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [AWS Lambda Docs](https://docs.aws.amazon.com/lambda/)

## Useful Links

- [GitHub Repository](https://github.com/circlemind-ai/float)
- [Project Documentation](../README.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [API Reference](./API.md)
- [Development Workflow](./DEVELOPMENT.md)

## Keyboard Shortcuts (Expo)

When running `npm start -c`:

| Key | Action |
|-----|--------|
| `i` | Launch iOS simulator |
| `a` | Launch Android emulator |
| `w` | Open web client |
| `r` | Reload app |
| `m` | Toggle menu |
| `q` | Quit |

## Git Workflow

```bash
# Create feature branch
git checkout -b feat/your-feature

# Make changes and commit
git add .
git commit -m "feat: your feature"

# Push to remote
git push origin feat/your-feature

# Create pull request on GitHub
# Address review feedback
# Merge when approved
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

**For more information**, see:
- [README.md](../README.md) - Project overview
- [docs/DEVELOPMENT.md](./DEVELOPMENT.md) - Full development guide
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
