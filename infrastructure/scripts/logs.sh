#!/bin/bash
# View logs for Float Meditation Lambda function

set -e

# Determine script location and navigate to infrastructure directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INFRASTRUCTURE_DIR="$(dirname "$SCRIPT_DIR")"

# Change to infrastructure directory
cd "$INFRASTRUCTURE_DIR"

# Read stack name from samconfig.toml
STACK_NAME=$(grep -A 20 "^\[default.deploy.parameters\]" samconfig.toml | grep "^stack_name" | head -n 1 | cut -d '=' -f 2 | tr -d ' "' 2>/dev/null)
if [ -z "$STACK_NAME" ]; then
  STACK_NAME=$(grep -A 20 "^\[default.global.parameters\]" samconfig.toml | grep "^stack_name" | head -n 1 | cut -d '=' -f 2 | tr -d ' "' 2>/dev/null)
fi

if [ -z "$STACK_NAME" ]; then
  STACK_NAME="float-meditation"
fi

# Get environment from parameter overrides
ENVIRONMENT=$(grep "parameter_overrides" samconfig.toml | grep -o 'Environment=\\"[^"]*\\"' | cut -d '"' -f 2 2>/dev/null)
if [ -z "$ENVIRONMENT" ]; then
  ENVIRONMENT="staging"
fi

FUNCTION_NAME="${STACK_NAME}-FloatMeditationFunction"
LOG_GROUP="/aws/lambda/float-meditation-${ENVIRONMENT}"

echo "Viewing logs for: $LOG_GROUP"
echo "Press Ctrl+C to exit"
echo ""

aws logs tail "$LOG_GROUP" --follow
