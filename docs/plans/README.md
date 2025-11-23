# Deployment Simplification - Implementation Plan

## Overview

This feature simplifies the Float meditation app's deployment infrastructure by consolidating the overly complex multi-script, multi-environment setup into a streamlined, single-environment deployment system modeled after the successful react-stocks project pattern.

The current deployment system has evolved into an unnecessarily complicated structure with separate infrastructure directories, multiple deployment scripts (staging, production, validation), complex Makefile-based builds, and scattered configuration. This refactoring eliminates this complexity by: (1) colocating infrastructure code with the backend, (2) implementing an interactive deployment script that manages secrets locally, (3) removing unnecessary build complexity, and (4) adopting standard SAM CLI conventions.

The result is a simpler, more maintainable deployment process that reduces cognitive overhead for developers while maintaining all necessary functionality for the Float app's serverless backend architecture.

## Prerequisites

### Required Tools

- **AWS SAM CLI** (installed globally): `brew install aws-sam-cli` or equivalent
- **AWS CLI** (configured): `aws configure` with valid credentials
- **Node.js** (v20+): For frontend and npm scripts
- **Python 3.13**: For backend Lambda functions
- **uv** (Python package manager): For development tooling
- **Git**: For version control

### Environment Setup

- AWS account with appropriate permissions (Lambda, API Gateway, S3, CloudFormation, IAM)
- Public FFmpeg Lambda layer available (or custom layer ARN ready)
- API keys ready: Google Gemini, OpenAI, ElevenLabs (optional)

### Existing Codebase

- Monorepo structure in place: `frontend/`, `backend/`, `tests/`, `docs/`
- Backend Python code in `backend/src/`
- Current infrastructure in `infrastructure/` directory (will be migrated)

## Phase Summary

| Phase   | Goal                                                                                     | Token Estimate | Status  |
| ------- | ---------------------------------------------------------------------------------------- | -------------- | ------- |
| Phase-0 | Foundation: Architecture decisions, deployment script design, testing strategy           | ~15,000        | Pending |
| Phase-1 | Implementation: Migrate infrastructure, create deployment scripts, update configurations | ~85,000        | Pending |

**Total Estimated Tokens**: ~100,000

## Navigation

- [Phase 0: Foundation & Architecture](./Phase-0.md)
- [Phase 1: Implementation & Migration](./Phase-1.md)

## Quick Start (After Implementation)

```bash
# First-time deployment (interactive)
cd backend
npm run deploy

# Subsequent deployments (uses saved config)
cd backend
npm run deploy

# Validate template before deploying
npm run validate

# View Lambda logs
npm run logs
```

## Key Changes

1. **Directory Structure**: Infrastructure files move from `infrastructure/` to `backend/`
2. **Configuration**: Single environment (default), secrets in gitignored `samconfig.toml`
3. **Deployment**: Interactive script with local state persistence (`.deploy-config.json`)
4. **Build Process**: Remove Makefile and pyproject.toml, use standard SAM Python builder
5. **Scripts**: Consolidate to three core scripts: deploy, validate, logs

## Success Criteria

- ✅ Single `npm run deploy` command handles entire deployment
- ✅ Secrets never committed to git (samconfig.toml gitignored)
- ✅ Interactive prompts for missing configuration
- ✅ Automatic `.env` file generation from stack outputs
- ✅ No manual SAM guided mode (`--guided`) required
- ✅ Standard SAM CLI usage (no custom wrappers)
- ✅ All tests pass in CI without live AWS resources
