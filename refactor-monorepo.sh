#!/bin/bash
set -euo pipefail

# Monorepo Refactoring Script
# Restructures repository into frontend/, backend/, docs/, tests/ layout

echo "=== Monorepo Refactoring Script ==="
echo "Starting at $(date)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Track deleted files
CLEANUP_LIST="cleanup-list.txt"
> "$CLEANUP_LIST"

log_deleted() {
    echo "$1" >> "$CLEANUP_LIST"
    echo "  DELETED: $1"
}

# =============================================================================
# PHASE 1: Create target directory structure
# =============================================================================
echo ""
echo "=== PHASE 1: Creating directory structure ==="

mkdir -p frontend/app
mkdir -p frontend/components
mkdir -p frontend/constants
mkdir -p frontend/context
mkdir -p frontend/hooks
mkdir -p frontend/assets
mkdir -p frontend/scripts
mkdir -p tests/frontend/integration
mkdir -p tests/frontend/e2e
mkdir -p tests/frontend/unit

# =============================================================================
# PHASE 2: Move frontend code
# =============================================================================
echo ""
echo "=== PHASE 2: Moving frontend code ==="

# Move app directory
if [ -d "app" ]; then
    cp -r app/* frontend/app/
    rm -rf app
    echo "  MOVED: app/ -> frontend/app/"
fi

# Move components (excluding tests)
if [ -d "components" ]; then
    # Move non-test components
    find components -maxdepth 1 -name "*.tsx" -exec cp {} frontend/components/ \;
    [ -d "components/navigation" ] && cp -r components/navigation frontend/components/
    [ -d "components/ScreenComponents" ] && cp -r components/ScreenComponents frontend/components/

    # Move component tests to tests/frontend/unit
    if [ -d "components/__tests__" ]; then
        cp -r components/__tests__/* tests/frontend/unit/
        echo "  MOVED: components/__tests__/ -> tests/frontend/unit/"
    fi
    rm -rf components
    echo "  MOVED: components/ -> frontend/components/"
fi

# Move constants
if [ -d "constants" ]; then
    cp -r constants/* frontend/constants/
    rm -rf constants
    echo "  MOVED: constants/ -> frontend/constants/"
fi

# Move context
if [ -d "context" ]; then
    cp -r context/* frontend/context/
    rm -rf context
    echo "  MOVED: context/ -> frontend/context/"
fi

# Move hooks
if [ -d "hooks" ]; then
    cp -r hooks/* frontend/hooks/
    rm -rf hooks
    echo "  MOVED: hooks/ -> frontend/hooks/"
fi

# Move assets
if [ -d "assets" ]; then
    cp -r assets/* frontend/assets/
    rm -rf assets
    echo "  MOVED: assets/ -> frontend/assets/"
fi

# Move scripts
if [ -d "scripts" ]; then
    cp -r scripts/* frontend/scripts/
    rm -rf scripts
    echo "  MOVED: scripts/ -> frontend/scripts/"
fi

# =============================================================================
# PHASE 3: Move tests
# =============================================================================
echo ""
echo "=== PHASE 3: Moving tests ==="

# Move root __tests__ integration tests
if [ -d "__tests__/integration" ]; then
    cp -r __tests__/integration/* tests/frontend/integration/
    rm -rf __tests__
    echo "  MOVED: __tests__/integration/ -> tests/frontend/integration/"
fi

# Move e2e tests
if [ -d "e2e" ]; then
    cp -r e2e/* tests/frontend/e2e/
    rm -rf e2e
    echo "  MOVED: e2e/ -> tests/frontend/e2e/"
fi

# =============================================================================
# PHASE 4: Consolidate documentation
# =============================================================================
echo ""
echo "=== PHASE 4: Consolidating documentation ==="

# Move backend docs to docs/backend/
mkdir -p docs/backend
for doc in backend/*.md; do
    if [ -f "$doc" ]; then
        filename=$(basename "$doc")
        mv "$doc" "docs/backend/$filename"
        echo "  MOVED: $doc -> docs/backend/$filename"
    fi
done

# Move infrastructure docs
mkdir -p docs/infrastructure
for doc in infrastructure/*.md; do
    if [ -f "$doc" ]; then
        filename=$(basename "$doc")
        mv "$doc" "docs/infrastructure/$filename"
        echo "  MOVED: $doc -> docs/infrastructure/$filename"
    fi
done

# Delete redundant/outdated root docs
for doc in TESTING.md CONTRIBUTING.md; do
    if [ -f "$doc" ]; then
        rm "$doc"
        log_deleted "$doc"
    fi
done

# Delete phase summary files that are now obsolete
find . -maxdepth 2 -name "PHASE_*.md" -type f -exec rm {} \; -exec echo "  DELETED: {}" \;
find . -maxdepth 1 -name "PHASE_*.md" -type f | while read f; do log_deleted "$f"; done

# =============================================================================
# PHASE 5: Update imports in frontend code
# =============================================================================
echo ""
echo "=== PHASE 5: Updating import paths ==="

# Update @/ path aliases in frontend code (they still work since tsconfig will be updated)
# The @/ alias maps to the frontend/ directory now

find frontend -name "*.tsx" -o -name "*.ts" | while read file; do
    if [ -f "$file" ]; then
        # Update relative imports that might be broken
        sed -i 's|from '\''@/components/|from '\''@/components/|g' "$file"
        sed -i 's|from '\''@/constants/|from '\''@/constants/|g' "$file"
        sed -i 's|from '\''@/context/|from '\''@/context/|g' "$file"
        sed -i 's|from '\''@/hooks/|from '\''@/hooks/|g' "$file"
    fi
done

echo "  Updated import paths in frontend files"

# =============================================================================
# PHASE 6: Update test paths
# =============================================================================
echo ""
echo "=== PHASE 6: Updating test paths ==="

# Update test setup paths
find tests -name "*.ts" -o -name "*.tsx" | while read file; do
    if [ -f "$file" ]; then
        # Update imports to point to frontend/
        sed -i 's|from '\''../../components/|from '\''../../frontend/components/|g' "$file"
        sed -i 's|from '\''../../constants/|from '\''../../frontend/constants/|g' "$file"
        sed -i 's|from '\''../../context/|from '\''../../frontend/context/|g' "$file"
        sed -i 's|from '\''../../hooks/|from '\''../../frontend/hooks/|g' "$file"
        sed -i 's|from '\''@/|from '\''../../frontend/|g' "$file"
    fi
done

echo "  Updated test import paths"

# =============================================================================
# PHASE 7: Clean up development noise files
# =============================================================================
echo ""
echo "=== PHASE 7: Cleaning up development noise ==="

# Remove coverage directories and files
if [ -d "coverage" ]; then
    rm -rf coverage
    log_deleted "coverage/"
fi

# Remove error logs
for f in eslint_errors.log mypy_errors.log mypy_output.txt ruff_baseline.log; do
    [ -f "$f" ] && rm "$f" && log_deleted "$f"
    [ -f "backend/$f" ] && rm "backend/$f" && log_deleted "backend/$f"
done

# Remove coverage files from backend
for f in backend/.coverage backend/coverage_baseline.txt backend/coverage_report.txt; do
    [ -f "$f" ] && rm "$f" && log_deleted "$f"
done

# Remove .expo readme if exists
[ -f ".expo/README.md" ] && rm ".expo/README.md" && log_deleted ".expo/README.md"

# Remove banner.png (development asset)
[ -f "banner.png" ] && rm "banner.png" && log_deleted "banner.png"

# =============================================================================
# PHASE 8: Move frontend config files
# =============================================================================
echo ""
echo "=== PHASE 8: Organizing config files ==="

# Move frontend-specific configs
for config in app.config.js babel.config.js .detoxrc.js eas.json .eslintrc.json .prettierrc.json expo-env.d.ts tsconfig.test.json; do
    if [ -f "$config" ]; then
        mv "$config" "frontend/$config"
        echo "  MOVED: $config -> frontend/$config"
    fi
done

echo ""
echo "=== Refactoring complete ==="
echo "Deleted files logged to: $CLEANUP_LIST"
echo ""
echo "Next steps:"
echo "  1. Run ./strip-comments.sh to sanitize code"
echo "  2. Update package.json scripts"
echo "  3. Update tsconfig.json paths"
echo "  4. Run tests to verify"
