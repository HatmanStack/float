#!/bin/bash
set -euo pipefail

# Code Sanitization Script
# Removes console.log, print(), debugger statements, and commented code

echo "=== Code Sanitization Script ==="
echo "Starting at $(date)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

CHANGES_LOG="sanitization-changes.log"
> "$CHANGES_LOG"

log_change() {
    echo "$1" >> "$CHANGES_LOG"
}

# =============================================================================
# TypeScript/JavaScript Sanitization
# =============================================================================
echo ""
echo "=== Sanitizing TypeScript/JavaScript files ==="

# Find all TS/TSX/JS files (excluding node_modules, test files, and setup files)
find frontend -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" \) \
    ! -path "*/node_modules/*" \
    ! -path "*/__tests__/*" \
    ! -name "*.test.*" \
    ! -name "*.spec.*" \
    ! -name "setup.ts" \
    ! -name "testUtils.*" | while read file; do

    if [ -f "$file" ]; then
        original_size=$(wc -c < "$file")

        # Remove console.log statements (single and multi-line)
        perl -i -0pe 's/\s*console\.log\([^;]*\);\n?//gs' "$file" 2>/dev/null || true

        # Remove console.warn statements (keep console.error for production error tracking)
        perl -i -0pe 's/\s*console\.warn\([^;]*\);\n?//gs' "$file" 2>/dev/null || true

        # Remove debugger statements
        sed -i '/^\s*debugger;*\s*$/d' "$file"

        # Remove single-line commented code (lines that are just // followed by code-like content)
        # Preserve legitimate comments that explain behavior
        sed -i '/^\s*\/\/\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[=\(\[\{]/d' "$file"

        # Remove empty console blocks
        sed -i '/^\s*console\.\s*$/d' "$file"

        # Clean up multiple consecutive blank lines (reduce to max 1)
        sed -i '/^$/N;/^\n$/d' "$file"

        new_size=$(wc -c < "$file")
        if [ "$original_size" -ne "$new_size" ]; then
            log_change "SANITIZED: $file (${original_size}b -> ${new_size}b)"
            echo "  SANITIZED: $file"
        fi
    fi
done

# =============================================================================
# Python Sanitization
# =============================================================================
echo ""
echo "=== Sanitizing Python files ==="

find backend/src -type f -name "*.py" ! -path "*/__pycache__/*" | while read file; do
    if [ -f "$file" ]; then
        original_size=$(wc -c < "$file")

        # Remove print() statements (keep logging.* calls)
        # This regex handles multi-line print statements
        perl -i -0pe 's/^\s*print\s*\([^)]*\)\s*\n?//gm' "$file" 2>/dev/null || true

        # Remove single print statements more aggressively
        sed -i '/^\s*print\s*(/d' "$file"

        # Remove pass-only blocks that might be left behind
        # (careful not to break valid pass statements)

        # Remove consecutive blank lines
        sed -i '/^$/N;/^\n$/d' "$file"

        new_size=$(wc -c < "$file")
        if [ "$original_size" -ne "$new_size" ]; then
            log_change "SANITIZED: $file (${original_size}b -> ${new_size}b)"
            echo "  SANITIZED: $file"
        fi
    fi
done

# =============================================================================
# Replace hardcoded values with environment variables
# =============================================================================
echo ""
echo "=== Checking for hardcoded secrets ==="

# Check for potential hardcoded secrets (log but don't auto-replace)
grep -rn "api[_-]?key\s*[:=]\s*['\"][^'\"]*['\"]" frontend backend/src 2>/dev/null | \
    grep -v "process\.env\|os\.environ\|\.env\|example\|test\|mock" | \
    head -20 | while read match; do
    echo "  WARNING: Potential hardcoded secret: $match"
    log_change "WARNING: $match"
done

echo ""
echo "=== Sanitization complete ==="
echo "Changes logged to: $CHANGES_LOG"
echo ""
echo "Note: console.error statements preserved for production error tracking"
echo "Note: Test files excluded from sanitization"
