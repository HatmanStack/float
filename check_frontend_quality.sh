#!/bin/bash

# Frontend Quality Check Script
# This script runs all frontend quality checks in sequence:
# 1. Tests
# 2. Type checking
# 3. Linting
# 4. Formatting

set -e  # Exit on any error

echo "========================================"
echo "Float Frontend Quality Check"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Function to print status
print_status() {
  if [ $1 -eq 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC}: $2"
  else
    echo -e "${RED}✗ FAILED${NC}: $2"
    FAILED=$((FAILED + 1))
  fi
}

# 1. Run tests
echo "Running tests..."
echo "==============="
if npm test -- --passWithNoTests 2>&1 | head -50; then
  print_status 0 "Tests"
else
  print_status 1 "Tests"
fi
echo ""

# 2. Type checking
echo "Type checking with TypeScript..."
echo "================================"
if npm run type-check 2>&1 | head -20; then
  print_status 0 "Type checking"
else
  print_status 1 "Type checking"
fi
echo ""

# 3. Linting
echo "Linting with ESLint..."
echo "====================="
LINT_OUTPUT=$(npm run lint 2>&1 || true)
# Extract actual error count from ESLint summary line (e.g., "✖ 37 problems (0 errors, 37 warnings)")
LINT_ERRORS=$(echo "$LINT_OUTPUT" | grep -oP '\(\K[0-9]+(?= errors)' || echo "0")

echo "$LINT_OUTPUT" | head -30
echo ""

if [ "$LINT_ERRORS" = "0" ]; then
  print_status 0 "Linting (0 errors)"
else
  print_status 1 "Linting ($LINT_ERRORS errors found)"
fi
echo ""

# 4. Formatting
echo "Checking code formatting with Prettier..."
echo "========================================="
if npm run format:check 2>&1 | head -20; then
  print_status 0 "Formatting"
else
  print_status 1 "Formatting"
fi
echo ""

# Summary
echo "========================================"
echo "Quality Check Summary"
echo "========================================"

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}All checks passed!${NC}"
  echo ""
  echo "You're ready to commit. Run:"
  echo "  git add ."
  echo "  git commit -m 'your message'"
  exit 0
else
  echo -e "${RED}$FAILED check(s) failed${NC}"
  echo ""
  echo "Fix the issues above and try again."
  exit 1
fi
