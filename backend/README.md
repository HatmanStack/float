# Float Backend

Serverless Python backend for the Float meditation app.

## Directory Structure

```
backend/
├── src/                    # Application source code
├── tests/                  # Test suite
├── scripts/                # Deployment and utility scripts
├── template.yaml          # AWS SAM template
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
└── package.json           # npm scripts for deployment
```

## Development Setup

1. **Install Python 3.13**
2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

## Testing

Run the full test suite:
```bash
make test
```

Run specific test categories:
```bash
pytest tests/unit
pytest tests/integration
```

## Deployment

Deploy to AWS:
```bash
npm run deploy
```

See [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for full details.
