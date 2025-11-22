# Contributing to Float

Thank you for your interest in contributing to Float! This guide will help you get started with the development workflow, code standards, and pull request process.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/circlemind-ai/float.git
cd float
```

### 2. Create a Feature Branch

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/bug-name
```

### 3. Set Up Your Development Environment

See [README.md](README.md) for prerequisites and setup instructions.

## Development Workflow

### Daily Workflow

```bash
# Update dependencies and activate environments
npm install
cd backend && pip install -e ".[dev]" && cd ..

# Make your changes
# ... edit files ...

# Run tests and quality checks before committing
npm test                    # Frontend tests
cd backend && pytest tests/ # Backend tests

# Run linting and formatting
npm run lint:fix && npm run format  # Frontend
cd backend && make quality          # Backend
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed workflow tips and common commands.

### Code Standards

#### Frontend (TypeScript/React Native)

- **TypeScript**: Strict mode enforced; add explicit types to functions and components
- **ESLint**: Must pass without warnings
- **Prettier**: Code must be formatted with Prettier
- **Testing**: Write Jest tests for new components and hooks

Key rules:

- Use functional components with hooks
- Keep components small and focused
- Avoid prop drilling (use Context API for shared state)
- Type function parameters and return types

#### Backend (Python)

- **Type Hints**: All public functions and methods must have type hints
- **mypy**: Must pass type checking in standard mode
- **ruff**: Must pass linting without warnings
- **black**: Code must be formatted with black
- **pytest**: Write tests for new features (target 60%+ coverage)

Key rules:

- Use Pydantic models for validation
- Add docstrings to classes and public methods
- Handle exceptions explicitly
- Add type hints to function signatures

See configuration files for details:

- Frontend: `.eslintrc.json`, `.prettierrc.json`, `tsconfig.json`
- Backend: `backend/pyproject.toml`, `.eslintrc.json`

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): short description

Optional longer description explaining the change and why.
Reference issues: Fix #123
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no feature change)
- `test`: Add or update tests
- `docs`: Documentation changes
- `style`: Code formatting (not logic changes)
- `chore`: Dependency or build changes

**Examples**:

```
feat(meditation): add support for custom meditation durations

Users can now request meditations between 5-60 minutes instead of fixed durations.

Fix #42
```

```
fix(frontend): resolve audio playback lag on Android devices

The audio service now pre-buffers before playing to avoid stuttering.
```

## Pull Request Process

### 1. Push Your Branch

```bash
git push origin feat/your-feature-name
```

### 2. Create Pull Request

- Use a descriptive title following conventional commits
- Write a clear description of what changed and why
- Link related issues: "Fix #123" or "Addresses #456"
- Add screenshots for UI changes

### 3. Code Review

- Address review feedback respectfully and promptly
- Commit fixes atomically with clear messages
- Push updates to the same branch
- Ask for clarification if feedback is unclear

### 4. Merge

Once approved:

- Ensure all checks pass (tests, linting, type checking)
- GitHub will handle the merge
- Celebrate! 🎉

## Testing

### Frontend Tests

```bash
npm test                           # Run in watch mode
npm test -- --coverage            # With coverage report
npm test -- --testNamePattern=foo # Run specific test
```

Write tests for:

- New components
- Custom hooks
- Context providers
- Complex UI logic

### Backend Tests

```bash
cd backend
pytest tests/                      # Run all tests
pytest tests/ --cov=src/          # With coverage
pytest tests/ -v                  # Verbose output
pytest tests/ -k test_name        # Specific test
```

Write tests for:

- Service methods
- Request validation
- Error handling
- Business logic

## Security & Performance

**Security**: Never commit API keys - use `.env`. Report security issues privately.

**Performance**: Use React DevTools Profiler and `pytest --durations=10` for profiling.

## Need Help?

- **Common issues**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API reference**: [docs/API.md](docs/API.md)
- **Quick lookup**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)

---

**Thanks for contributing to Float!** Your effort makes this project better for everyone.
