# Code Quality Standards

This document outlines the code quality standards and practices for the Float backend.

## Overview

We maintain consistent code quality through:

- **Type hints** with mypy type checking
- **Linting** with ruff to catch bugs and style issues
- **Formatting** with black for consistent style
- **Testing** with pytest for critical paths

## Type Hints

All public functions and methods must have complete type annotations.

### Requirements

- All function parameters must have type hints
- All function return types must be specified
- Class instance variables should be typed (especially in `__init__`)
- Use `Optional[T]` for nullable values
- Use generic types: `List[T]`, `Dict[K, V]`, `Union[T, U]`
- Complex types can use `Any` for truly ambiguous values

### Examples

**Good:**

```python
def process_request(data: Dict[str, Any]) -> str:
    """Process request data and return result."""
    result: str = str(data)
    return result

class Service:
    def __init__(self, name: str) -> None:
        self.name: str = name
```

**Bad:**

```python
def process_request(data):  # Missing type hints
    result = str(data)
    return result
```

### Running mypy

```bash
# Check for type errors
mypy src/

# Show error codes for reference
mypy src/ --show-error-codes

# Check specific file
mypy src/handlers/lambda_handler.py
```

## Linting with ruff

Ruff finds bugs, style violations, and code quality issues using configurable rules.

### Configuration

Rules are configured in `pyproject.toml` under `[tool.ruff]`. We use balanced rules that catch real issues without being overly strict.

### Common Issues

- **F401**: Unused imports - remove them
- **E501**: Line too long - break lines or let black handle it
- **F841**: Unused variables - remove or prefix with `_`
- **I**: Import sorting - keep imports organized
- **B**: Flake8-bugbear - actual bugs, fix these first

### Running ruff

```bash
# Check for violations
ruff check src/

# Show available fixes
ruff check src/ --show-fixes

# Auto-fix common issues
ruff check src/ --fix

# Auto-fix including unsafe fixes
ruff check src/ --fix --unsafe-fixes
```

## Formatting with black

Black is an opinionated code formatter that ensures consistent style across the codebase.

### Configuration

- Line length: 100 characters
- Quote style: Single quotes (configurable)
- Trailing commas: Always (cleaner diffs)
- No configuration needed beyond pyproject.toml

### Running black

```bash
# Format all files
black src/ tests/

# Check without formatting
black --check src/ tests/

# Format specific directory
black src/handlers/
```

## Testing

Critical paths must have tests. Tests use pytest and are located in `backend/tests/`.

### Structure

- `tests/unit/` - Unit tests for individual functions/classes
- `tests/fixtures/` - Shared test data and fixtures
- `tests/mocks/` - Mock objects for external services

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_handlers.py -v

# Run with coverage report
pytest tests/ --cov=src

# Run specific test function
pytest tests/unit/test_handlers.py::test_function_name -v
```

### Test Coverage

Current targets:

- **Minimum**: 30% overall coverage
- **Target**: 60%+ on critical paths (handlers, services, models)
- **Excluded**: External integrations (Gemini, S3, etc.)

## Quality Checks Script

Run all quality checks with the provided script:

```bash
# Run all checks in order
./check_quality.sh

# The script runs:
# 1. Tests (pytest)
# 2. Type checking (mypy)
# 3. Linting (ruff)
# 4. Formatting (black)
```

## Development Workflow

### Before Committing

```bash
# 1. Run tests
pytest tests/ -v

# 2. Check types
mypy src/ --show-error-codes

# 3. Lint code
ruff check src/ --fix

# 4. Format code
black src/

# Or use the convenience script
./check_quality.sh
```

### Making Code Changes

1. Write or update code
2. Add type hints
3. Run tests to ensure behavior
4. Run linting to catch issues
5. Run formatting to ensure consistency
6. Commit with clear message

### Resolving Issues

**Type Errors:**

- Add explicit type hints
- Use `Any` for truly ambiguous types
- Check imports and dependencies

**Linting Violations:**

- Follow the suggestion in the error message
- Run `--fix` to auto-fix common issues
- Manual fixes for semantic issues

**Formatting Issues:**

- Run `black` to format automatically
- No style debates - black decides

## Code Style Guidelines

### Naming Conventions

- Classes: `PascalCase` (e.g., `AudioService`)
- Functions: `snake_case` (e.g., `process_audio`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_SIZE`)
- Private methods/variables: prefix with `_` (e.g., `_internal_method`)

### Docstrings

All public functions should have docstrings:

```python
def process_data(input_data: Dict[str, Any]) -> str:
    """Process input data and return result.

    Args:
        input_data: Dictionary containing data to process

    Returns:
        Processed result as string

    Raises:
        ValueError: If input data is invalid
    """
```

### Comments

Use comments for "why", not "what":

```python
# Good - explains intent
if user_id not in cache:  # Cache miss, need to query database
    user = query_database(user_id)

# Bad - just describes code
user_id_in_cache = user_id in cache  # Check if user_id is in cache
if not user_id_in_cache:
    user = query_database(user_id)
```

## Handling Exceptions

- Catch specific exceptions, not broad `Exception`
- Provide meaningful error messages
- Log errors appropriately
- Re-raise when appropriate

```python
try:
    result = service.call()
except ServiceError as e:
    print(f"Service failed: {e}")
    raise ValueError(f"Processing failed: {str(e)}") from e
```

## Integration with CI/CD

GitHub Actions runs these checks automatically on:

- Pull requests
- Pushes to main branch
- Scheduled runs

Results are visible in the Actions tab. Developers are responsible for fixing issues.

## Useful Resources

- **Type hints**: https://docs.python.org/3/library/typing.html
- **mypy**: https://www.mypy-lang.org/
- **ruff**: https://github.com/astral-sh/ruff
- **black**: https://github.com/psf/black
- **pytest**: https://docs.pytest.org/

## Questions?

Refer to:

1. Code examples in this file
2. Existing code that passes all checks
3. Tool documentation links above
4. Phase documentation in `docs/plans/`
