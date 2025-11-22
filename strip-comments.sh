#!/bin/bash
set -e

echo "=========================================="
echo "STRIPPING INLINE COMMENTS & DOCSTRINGS"
echo "=========================================="
echo ""

echo "Stripping TypeScript/JavaScript comments..."

find frontend -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) | while read file; do
    perl -i -pe 's|^\s*//.*$||g' "$file"
    perl -i -0pe 's|/\*\*[^*]*\*+(?:[^/*][^*]*\*+)*/||gs' "$file"
    perl -i -0pe 's|/\*[^*]*\*+(?:[^/*][^*]*\*+)*/||gs' "$file"
    perl -i -pe 's|\s+//.*$||g' "$file"

    perl -i -pe 's/^\s*\n//g' "$file"
    perl -i -0pe 's/\n\n\n+/\n\n/gs' "$file"
done

echo "Stripping Python docstrings and comments..."

find backend/src -type f -name "*.py" | while read file; do
    perl -i -pe 's|^\s*#.*$||g' "$file"
    perl -i -0pe 's|"""[^"]*"""|pass|gs' "$file"
    perl -i -0pe "s|'''[^']*'''|pass|gs" "$file"

    perl -i -pe 's/^\s*\n//g' "$file"
    perl -i -0pe 's/\n\n\n+/\n\n/gs' "$file"
done

echo ""
echo "Comment stripping complete."
echo "Note: Essential architectural notes should be moved to docs/"
echo ""
