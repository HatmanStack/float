# Development Workflow

This guide covers daily development practices, common commands, and troubleshooting for Float.

## Daily Workflow

### Start Your Day

```bash
# Update dependencies
npm install
cd backend && pip install -e ".[dev]" && cd ..

# Create or switch to your feature branch
git checkout -b feat/your-feature
```

### During Development

```bash
# Frontend: Start the dev server
npm start -c
# Press 'i' for iOS, 'a' for Android, 'w' for Web

# Backend: Run tests as you work
cd backend && pytest tests/ -v --tb=short
```

### Before Committing

```bash
# Frontend checks
npm test              # Run Jest tests
npm run lint:fix      # Fix ESLint issues
npm run format        # Run Prettier

# Backend checks
cd backend
pytest tests/         # Run tests with coverage
make quality          # Run all quality checks
cd ..

# If all pass, commit
git add .
git commit -m "feat: your feature description"
```

## Common Commands

### Frontend

| Task | Command |
|------|---------|
| Start dev server | `npm start -c` |
| Run tests | `npm test` |
| Run tests once | `npm test -- --no-coverage` |
| Run specific test | `npm test -- auth` |
| Check types | `npm run type-check` |
| Lint code | `npm run lint` |
| Fix linting issues | `npm run lint:fix` |
| Format code | `npm run format` |
| Check formatting | `npm run format:check` |

### Backend

```bash
cd backend
source .venv/bin/activate  # Activate venv if not already
```

| Task | Command |
|------|---------|
| Run all tests | `pytest tests/` |
| Run specific test | `pytest tests/unit/test_models.py` |
| Run with coverage | `pytest tests/ --cov=src/` |
| Run type check | `mypy src/` |
| Run linting | `ruff check src/` |
| Fix linting issues | `ruff check src/ --fix` |
| Format code | `black src/` |
| Run all quality checks | `make quality` |

## Debugging

### Frontend

**React DevTools Browser Extension**
- Install for Chrome/Firefox
- Inspect component props and state
- Track re-renders with Profiler tab

**Console Debugging**
```javascript
console.log('value:', myVar)
console.warn('warning message')
console.error('error message')
```

**Common Issues**
- "Module not found" → Run `npm install`
- Port 8081 in use → Kill process or use `expo start -c --port 8082`
- TypeError in render → Check component prop types and optional chaining

### Backend

**Print Debugging**
```python
print(f"Debug value: {my_var}")
print(f"Type: {type(my_var)}")
```

**Pytest Debugging**
```bash
# See print statements
pytest tests/ -s

# Verbose output with tracebacks
pytest tests/ -vv

# Stop at first failure
pytest tests/ -x

# Run specific test
pytest tests/unit/test_handlers.py::test_handle_summary_request -vv
```

**Common Issues**
- Import errors → Check Python path and venv activation
- Type errors → Run `mypy src/` to find issues
- Test failures → Check test fixtures and mock data

## Configuration Files

### Frontend Configuration

- **`.eslintrc.json`**: ESLint rules and plugins
- **`.prettierrc.json`**: Code formatting rules
- **`tsconfig.json`**: TypeScript compiler settings
- **`package.json`**: Dependencies and npm scripts

### Backend Configuration

- **`backend/pyproject.toml`**: Project metadata and tool configuration
- **`backend/.env.example`**: Environment variables template
- **`backend/Makefile`**: Build and quality check commands

### Shared Configuration

- **`.env.example`**: Environment variable documentation
- **`.editorconfig`**: Cross-editor settings (indentation, line endings)
- **`.gitignore`**: Files to exclude from version control

## Environment Setup

### First Time Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env  # or use your editor

# Required variables:
# Frontend:
#   EXPO_PUBLIC_LAMBDA_FUNCTION_URL = <your-lambda-url>
#   EXPO_PUBLIC_WEB_CLIENT_ID = <google-oauth-client-id>
#   EXPO_PUBLIC_ANDROID_CLIENT_ID = <google-oauth-android-id>
#
# Backend:
#   G_KEY = <google-gemini-api-key>
#   OPENAI_API_KEY = <openai-api-key>
#   AWS_S3_BUCKET = <your-s3-bucket>
#   AWS_ACCESS_KEY_ID = <aws-access-key>
#   AWS_SECRET_ACCESS_KEY = <aws-secret-key>
```

### Frontend Only

For frontend development without backend:
- Set `EXPO_PUBLIC_LAMBDA_FUNCTION_URL` to a mock/test endpoint
- Tests can mock the Lambda calls

### Backend Only

For backend development:
- Set all API keys (Google, OpenAI, AWS)
- Run tests with `pytest tests/`
- Tests can use mocks for external services

## Performance Tips

### Frontend

**React Optimization**
- Use `React.memo()` for pure components
- Use `useCallback()` for event handlers
- Use `useMemo()` for expensive calculations
- Avoid creating objects in render: `const style = {} // BAD`

**Profiling**
```bash
npm run analyze  # Bundle size analysis (if available)
```

**Check DevTools Profiler**
1. Open React DevTools
2. Go to Profiler tab
3. Click Record and use app
4. Analyze render times

### Backend

**Profile Slow Tests**
```bash
pytest tests/ --durations=10  # Show 10 slowest tests
```

**Check Type Checking Speed**
```bash
mypy src/ --verbose  # See what mypy is checking
```

**Memory Usage**
```bash
# Run memory-intensive tests
pytest tests/ -v --tb=short
```

## Common Issues & Solutions

### "Module not found" (Frontend)
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### "Python module not found" (Backend)
```bash
# Activate venv and reinstall
source backend/.venv/bin/activate
pip install -e ".[dev]"
```

### "Port already in use"
```bash
# Find process using port 8081
lsof -i :8081

# Kill it
kill -9 <PID>

# Or use different port
expo start -c --port 8082
```

### "Type checking errors"
```bash
# Incremental type checking
mypy src/ --incremental

# Check specific file
mypy src/handlers/lambda_handler.py
```

### "Tests failing but code looks right"
1. Check `.env` is set correctly
2. Run `npm install` or `pip install -e ".[dev]"`
3. Clear cache: `pytest tests/ --cache-clear`
4. Check git branch: `git status`

### "ESLint/Prettier disagreement"
```bash
# Format with Prettier first
npm run format

# Then check/fix with ESLint
npm run lint:fix
```

## Code Review Checklist

Before pushing, verify:

- [ ] Tests pass locally: `npm test` and `pytest tests/`
- [ ] No lint errors: `npm run lint` and `ruff check src/`
- [ ] Code formatted: `npm run format` and `black src/`
- [ ] Types check: `npm run type-check` and `mypy src/`
- [ ] No console errors/warnings
- [ ] No hardcoded API keys or secrets
- [ ] Commit message follows convention
- [ ] Changes are focused on one feature

## IDE Setup (Recommended)

### VS Code Extensions

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-python.python",
    "charliermarsh.ruff",
    "ms-python.black-formatter"
  ]
}
```

**Settings (.vscode/settings.json)**
```json
{
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  },
  "eslint.validate": ["typescript", "typescriptreact"],
  "python.linting.enabled": true
}
```

## Getting Help

1. **Check existing issues**: Search GitHub issues for your problem
2. **Ask in PR comments**: Questions are welcome and encouraged
3. **Review tests**: Look at similar tests for patterns
4. **Read docs**: Check README, ARCHITECTURE, and API documentation
5. **Pair programming**: Talk to teammates if stuck

---

**Happy coding!** 🚀
