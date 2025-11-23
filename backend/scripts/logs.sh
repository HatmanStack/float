#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[*] $1${NC}"
}

print_error() {
    echo -e "${RED}[x] $1${NC}"
}

CONFIG_FILE=".deploy-config.json"
SAM_CONFIG_FILE="samconfig.toml"
STACK_NAME=""

# Try to get stack name from config
if [ -f "$CONFIG_FILE" ]; then
    if command -v jq &> /dev/null; then
        STACK_NAME=$(jq -r .stackName "$CONFIG_FILE")
    else
        STACK_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['stackName'])")
    fi
elif [ -f "$SAM_CONFIG_FILE" ]; then
    # Simple grep to find stack_name in toml
    STACK_NAME=$(grep "stack_name" "$SAM_CONFIG_FILE" | head -n 1 | cut -d '"' -f 2)
fi

# Fallback to prompt
if [ -z "$STACK_NAME" ] || [ "$STACK_NAME" == "null" ]; then
    read -p "Enter Stack Name (default: float-meditation-dev): " INPUT_STACK_NAME
    STACK_NAME=${INPUT_STACK_NAME:-float-meditation-dev}
fi

FUNCTION_NAME="float-meditation"
LOG_GROUP="/aws/lambda/$FUNCTION_NAME"

print_status "Fetching logs for function: $FUNCTION_NAME (Stack: $STACK_NAME)"
print_status "Log Group: $LOG_GROUP"
print_status "Press Ctrl+C to stop streaming logs."

# Check if log group exists (optional, or just let aws logs tail handle it)
# We pass all arguments to the script to aws logs tail (e.g. --since 1h)
aws logs tail "$LOG_GROUP" --follow "$@"
