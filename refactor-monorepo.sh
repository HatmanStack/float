#!/bin/bash
set -e

echo "=========================================="
echo "MONOREPO RESTRUCTURING SCRIPT"
echo "=========================================="
echo ""

CLEANUP_LOG="cleanup-list.txt"
echo "# Cleanup List - Deleted Files and Directories" > $CLEANUP_LOG
echo "Generated: $(date)" >> $CLEANUP_LOG
echo "" >> $CLEANUP_LOG

echo "Phase 1: Delete dead code and temporary artifacts..."
echo "## Dead Code & Temporary Files" >> $CLEANUP_LOG

if [ -d "coverage" ]; then
    echo "  - coverage/ (generated test artifacts)" >> $CLEANUP_LOG
    rm -rf coverage
fi

if [ -f "backend/mypy_errors.log" ]; then
    echo "  - backend/mypy_errors.log" >> $CLEANUP_LOG
    rm backend/mypy_errors.log
fi

if [ -f "backend/ruff_baseline.log" ]; then
    echo "  - backend/ruff_baseline.log" >> $CLEANUP_LOG
    rm backend/ruff_baseline.log
fi

if [ -f "scripts/reset-project.js" ]; then
    echo "  - scripts/reset-project.js (one-time setup script)" >> $CLEANUP_LOG
    rm scripts/reset-project.js
    rmdir scripts 2>/dev/null || true
fi

find . -type d -name "__pycache__" -not -path "./.git/*" -not -path "./node_modules/*" | while read dir; do
    echo "  - $dir" >> $CLEANUP_LOG
    rm -rf "$dir"
done

find . -type f -name "*.pyc" -not -path "./.git/*" -not -path "./node_modules/*" | while read file; do
    echo "  - $file" >> $CLEANUP_LOG
    rm "$file"
done

echo "" >> $CLEANUP_LOG
echo "Phase 1: Complete"
echo ""

echo "Phase 2: Create new directory structure..."
mkdir -p frontend
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e

echo "Phase 2: Complete"
echo ""

echo "Phase 3: Move frontend files..."
mv app frontend/
mv assets frontend/
mv components frontend/
mv constants frontend/
mv context frontend/
mv hooks frontend/

echo "Phase 3: Complete"
echo ""

echo "Phase 4: Consolidate tests..."
mv frontend/components/__tests__ tests/unit/components
mv __tests__/integration/* tests/integration/
rmdir __tests__/integration
rmdir __tests__
mv e2e/* tests/e2e/
rmdir e2e

echo "Phase 4: Complete"
echo ""

echo "Phase 5: Consolidate documentation..."
mv TESTING.md docs/
mv CONTRIBUTING.md docs/
mv infrastructure/DEPLOY.md docs/infrastructure-deploy.md
mv infrastructure/DEPLOYMENT.md docs/infrastructure-deployment.md
mv infrastructure/DEPLOYMENT_STATUS.md docs/infrastructure-deployment-status.md
mv infrastructure/README.md docs/infrastructure-readme.md
mv backend/README.md docs/backend-readme.md
mv backend/INTEGRATION_TESTING.md docs/backend-integration-testing.md
mv tests/e2e/README.md docs/e2e-testing.md
mv tests/integration/README.md docs/integration-testing.md

echo "## Consolidated Documentation" >> $CLEANUP_LOG
echo "Moved to docs/ and renamed for clarity" >> $CLEANUP_LOG
echo "" >> $CLEANUP_LOG

echo "Phase 5: Complete"
echo ""

echo "Phase 6: Update configuration file paths..."

sed -i 's|"@/\*": \["\./\*"\]|"@/*": ["./frontend/*"]|g' tsconfig.json

sed -i 's|\./assets/|./frontend/assets/|g' app.config.js

sed -i 's|"\./jest\.setup\.js"|"./jest.setup.js"|g' package.json
sed -i 's|"\./components/__tests__/utils/setup\.ts"|"./tests/unit/components/__tests__/utils/setup.ts"|g' package.json
sed -i 's|"/components/__tests__/utils/"|"/tests/unit/components/__tests__/utils/"|g' package.json
sed -i 's|"/__tests__/integration/setup\.ts"|"/tests/integration/setup.ts"|g' package.json
sed -i 's|"/__tests__/integration/test-utils\.tsx"|"/tests/integration/test-utils.tsx"|g' package.json
sed -i 's|"reset-project": "node \./scripts/reset-project\.js",||g' package.json

sed -i "s|testMatch: \['\<rootDir\>/e2e/|testMatch: ['\<rootDir\>/tests/e2e/|g" tests/e2e/jest.config.js

sed -i 's|"\*\*/\__tests__/\*\*"|"tests/**"|g' tsconfig.json
sed -i 's|"components/__tests__/\*\*"||g' tsconfig.json

echo "Phase 6: Complete"
echo ""

echo "Phase 7: Update import paths in all TypeScript/JavaScript files..."

find frontend -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/components/|from "@/frontend/components/|g' {} \;
find frontend -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/constants/|from "@/frontend/constants/|g' {} \;
find frontend -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/context/|from "@/frontend/context/|g' {} \;
find frontend -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/hooks/|from "@/frontend/hooks/|g' {} \;

find tests -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/components/|from "@/frontend/components/|g' {} \;
find tests -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/constants/|from "@/frontend/constants/|g' {} \;
find tests -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/context/|from "@/frontend/context/|g' {} \;
find tests -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -exec sed -i 's|from ["'\'']\@/hooks/|from "@/frontend/hooks/|g' {} \;

echo "Phase 7: Complete"
echo ""

echo "Phase 8: Update relative documentation links..."
find docs -type f -name "*.md" -exec sed -i 's|\.\./infrastructure/|../infrastructure/|g' {} \;
find docs -type f -name "*.md" -exec sed -i 's|\.\./backend/|../backend/|g' {} \;
find docs -type f -name "*.md" -exec sed -i 's|\.\./tests/|../tests/|g' {} \;

echo "Phase 8: Complete"
echo ""

echo "=========================================="
echo "RESTRUCTURING COMPLETE"
echo "=========================================="
echo ""
echo "Cleanup log written to: $CLEANUP_LOG"
echo ""
