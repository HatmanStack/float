#!/bin/bash

# Quality assurance check script for Float backend
# Runs all quality checks in sequence: tests, type checking, linting, formatting

set -e  # Exit on first error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Float Backend Quality Assurance Checks        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"

# Ensure we're in the backend directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Run from backend directory.${NC}"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Warning: Virtual environment not activated. Attempting to activate...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found. Run: python3 -m venv .venv${NC}"
        exit 1
    fi
fi

# Step 1: Run tests
echo -e "\n${BLUE}[1/4]${NC} Running pytest..."
if pytest tests/ -v; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
    exit 1
fi

# Step 2: Type checking with mypy
echo -e "\n${BLUE}[2/4]${NC} Checking types with mypy..."
if mypy src/ --show-error-codes; then
    echo -e "${GREEN}✓ Type checks passed${NC}"
else
    echo -e "${RED}✗ Type checks failed${NC}"
    exit 1
fi

# Step 3: Linting with ruff
echo -e "\n${BLUE}[3/4]${NC} Linting with ruff..."
if ruff check src/ tests/; then
    echo -e "${GREEN}✓ Lint checks passed${NC}"
else
    echo -e "${RED}✗ Lint checks failed${NC}"
    exit 1
fi

# Step 4: Formatting with black
echo -e "\n${BLUE}[4/4]${NC} Checking format with black..."
if black --check src/ tests/; then
    echo -e "${GREEN}✓ Format checks passed${NC}"
else
    echo -e "${RED}✗ Format checks failed${NC}"
    exit 1
fi

# All checks passed
echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✓ All quality checks passed!                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo -e "\n${GREEN}Code quality verified. Ready to commit!${NC}"

exit 0
