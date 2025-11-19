#!/bin/bash
set -e  # Exit on error

echo "========================================="
echo "Validating SAM Template"
echo "========================================="

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INFRASTRUCTURE_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$INFRASTRUCTURE_DIR/template.yaml"

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "ERROR: Template file not found: $TEMPLATE_FILE"
    exit 1
fi

echo "Template file: $TEMPLATE_FILE"
echo ""

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "ERROR: SAM CLI not found"
    echo "Please install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

echo "SAM CLI version:"
sam --version
echo ""

# Validate template
echo "Running: sam validate --template $TEMPLATE_FILE"
if sam validate --template "$TEMPLATE_FILE"; then
    echo ""
    echo "✓ Template validation successful!"
    echo ""
    exit 0
else
    echo ""
    echo "✗ Template validation failed!"
    echo ""
    exit 1
fi
