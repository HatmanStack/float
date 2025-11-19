# Integration and End-to-End Testing Guide

This document describes the integration and E2E test suite for the Float meditation backend.

## Overview

The test suite is organized into three layers following the test pyramid:

1. **Unit Tests** (`tests/unit/`) - Fast, isolated tests (70%)
2. **Integration Tests** (`tests/integration/`) - Tests with real external services (20%)
3. **E2E Tests** (`tests/e2e/`) - Complete request-to-response flows (10%)

## Prerequisites

### Required for Integration Tests

Integration tests make real API calls to external services and require valid credentials:

- **Gemini AI API Key**: Set `G_KEY` environment variable
- **OpenAI API Key**: Set `OPENAI_API_KEY` environment variable
- **AWS Credentials**: Configure AWS credentials for S3 access

### Required for E2E Tests

E2E tests require all integration test prerequisites plus:

- **FFmpeg**: Must be available in the test environment
- **AWS S3 Buckets**: Access to S3 buckets for data storage

### Optional Configuration

```bash
# Skip integration tests (useful for CI without credentials)
export SKIP_INTEGRATION_TESTS=true

# Skip E2E tests
export SKIP_E2E_TESTS=true

# Use test-specific S3 buckets
export AWS_S3_TEST_BUCKET="your-test-bucket"
export AWS_AUDIO_TEST_BUCKET="your-test-audio-bucket"
```

## Test Organization

### Integration Tests (`tests/integration/`)

**47 integration tests** covering:

- **Gemini AI Service** (17 tests)
  - Sentiment analysis with real API
  - Meditation generation with real API
  - Various emotions and intensities
  - Error handling and performance

- **TTS Providers** (15 tests)
  - OpenAI TTS synthesis with real API
  - Audio format validation
  - Error handling and performance

- **S3 Storage** (15 tests)
  - Upload/download operations with real AWS S3
  - Path generation and listing
  - Cleanup verification

### E2E Tests (`tests/e2e/`)

**24 E2E tests** covering:

- **Summary Request Flow** (11 tests)
  - Complete flow: request → AI → response
  - Various emotions (sad, happy, anxious)
  - Edge cases and error handling
  - Performance verification

- **Meditation Request Flow** (13 tests)
  - Complete flow: request → AI → TTS → audio → response
  - Various emotions and intensities
  - Music integration
  - Audio validation and performance

### Lambda Initialization Tests (14 tests)

- Cold start simulation
- Service initialization
- Configuration validation
- Error recovery

## Running Tests

### Run All Unit Tests (Fast)

```bash
cd backend
pytest tests/unit/ -v
```

**Expected time:** <30 seconds

### Run Integration Tests Only

```bash
# Set required API keys first
export G_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"

# Run integration tests
pytest tests/integration/ -v -m integration
```

**Expected time:** <2 minutes
**Note:** Makes real API calls (costs may apply)

### Run E2E Tests Only

```bash
# Set all required credentials
export G_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"
# AWS credentials should be configured

# Run E2E tests
pytest tests/e2e/ -v -m e2e
```

**Expected time:** <5 minutes
**Note:** Makes real API calls and creates test files in S3

### Run All Tests (Unit + Integration + E2E)

```bash
pytest tests/ -v
```

**Expected time:** <8 minutes

### Run Tests Excluding Integration/E2E

```bash
# Run only unit tests (no external dependencies)
pytest tests/ -v -m "not integration and not e2e"
```

### Run with Coverage

```bash
# Full coverage report
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Integration tests coverage
pytest tests/integration/ --cov=src/services --cov-report=term-missing

# E2E tests coverage
pytest tests/e2e/ --cov=src/handlers --cov-report=term-missing
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (real API calls)
- `@pytest.mark.e2e` - End-to-end tests (complete flows)
- `@pytest.mark.slow` - Tests that take longer to execute

### Examples

```bash
# Run only fast unit tests
pytest -m unit -v

# Run slow tests only
pytest -m slow -v

# Run everything except slow tests
pytest -m "not slow" -v
```

## Performance Targets

### Integration Tests

| Service | Target Time | Actual |
|---------|------------|--------|
| Gemini Sentiment Analysis | <15s | ~5-10s |
| Gemini Meditation Generation | <60s | ~20-40s |
| OpenAI TTS Synthesis | <10s | ~3-8s |
| S3 Upload/Download | <5s | ~1-3s |

### E2E Tests

| Flow | Target Time | Actual |
|------|------------|--------|
| Summary Request | <15s | ~8-12s |
| Meditation Request | <90s | ~40-70s |

## Test Data Cleanup

### Automatic Cleanup

All integration and E2E tests automatically clean up test data:

- **S3 files**: Deleted after each test using `test_s3_keys_to_cleanup` fixture
- **Local files**: Temporary files deleted in finally blocks
- **Test prefixes**: All S3 test data uses `test-data/` prefix

### Manual Cleanup

If tests fail and leave orphaned data:

```bash
# List test data in S3
aws s3 ls s3://your-bucket/test-data/ --recursive

# Remove all test data
aws s3 rm s3://your-bucket/test-data/ --recursive
```

## Troubleshooting

### Integration Tests Skipping

If integration tests are skipped with "API keys not available":

```bash
# Check environment variables
echo $G_KEY
echo $OPENAI_API_KEY

# Set them if missing
export G_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

### E2E Tests Skipping

If E2E tests are skipped with "credentials not available":

```bash
# Check AWS credentials
aws configure list

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

### Rate Limiting

If you encounter rate limit errors:

- Integration tests include retry logic with exponential backoff
- Consider running tests less frequently
- Use smaller test batches

### Long Test Times

If tests are taking too long:

- Run only unit tests for development: `pytest tests/unit/`
- Skip integration tests: `pytest -m "not integration and not e2e"`
- Reduce number of E2E iterations in performance tests

## Cost Considerations

### API Costs

Integration and E2E tests make real API calls:

- **Gemini API**: ~$0.01-0.05 per test run
- **OpenAI TTS**: ~$0.05-0.15 per test run
- **AWS S3**: Negligible (<$0.01)

**Total estimated cost per full test run:** ~$0.10-0.25

### Recommendations

- Run unit tests frequently (free)
- Run integration tests before commits (~$0.05)
- Run E2E tests before merges/deploys (~$0.25)
- Use `SKIP_INTEGRATION_TESTS=true` in CI for cost savings

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run unit tests
  run: |
    cd backend
    pytest tests/unit/ -v --cov=src

- name: Run integration tests (if secrets available)
  if: ${{ secrets.G_KEY != '' }}
  env:
    G_KEY: ${{ secrets.G_KEY }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    cd backend
    pytest tests/integration/ -v -m integration

- name: Run E2E tests (manual trigger only)
  if: github.event_name == 'workflow_dispatch'
  env:
    G_KEY: ${{ secrets.G_KEY }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    cd backend
    pytest tests/e2e/ -v -m e2e
```

## Test Coverage Metrics

### Current Coverage (Phase 3 Complete)

- **Overall Backend**: 65%+ (up from 39%)
- **Services**: 90%+ (with integration tests)
- **Handlers**: 70%+ (with E2E tests)
- **Models**: 95%+
- **Utils**: 90%+

### Coverage by Test Type

- **Unit Tests**: Cover 55% of codebase
- **Integration Tests**: Add 5% coverage (external service paths)
- **E2E Tests**: Add 5% coverage (integration paths)

## Best Practices

### For Integration Tests

1. Always use test API keys (not production)
2. Use unique test identifiers to avoid conflicts
3. Clean up all test data in fixtures
4. Include retry logic for rate limits
5. Skip tests gracefully if credentials missing

### For E2E Tests

1. Test complete user flows, not implementation details
2. Verify response format and data integrity
3. Include performance assertions
4. Clean up S3 test data
5. Use minimal test data to reduce costs

### Writing New Tests

1. Add appropriate markers (`@pytest.mark.integration`, `@pytest.mark.slow`)
2. Use existing fixtures from `conftest.py`
3. Include cleanup in finally blocks or fixtures
4. Document any new prerequisites
5. Add performance assertions where appropriate

## Support

For issues or questions about the test suite:

1. Check this documentation first
2. Review test output for specific error messages
3. Check AWS CloudWatch logs for Lambda errors
4. Verify all prerequisites are met
5. Review Phase 3 implementation plan for details
