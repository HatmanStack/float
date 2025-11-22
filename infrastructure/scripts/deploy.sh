#!/bin/bash
# Simplified deployment script for Float Meditation backend

set -e

echo "======================================"
echo "Float Meditation Backend Deployment"
echo "======================================"
echo ""

# Determine script location and navigate to infrastructure directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INFRASTRUCTURE_DIR="$(dirname "$SCRIPT_DIR")"

# Change to infrastructure directory
cd "$INFRASTRUCTURE_DIR"

# Verify we're in the right place
if [ ! -f "template.yaml" ]; then
  echo "Error: template.yaml not found in infrastructure directory"
  exit 1
fi

# Check if SAM CLI is installed
if ! command -v uvx &> /dev/null; then
  echo "Error: uv not found"
  echo "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi
SAM_CMD="uvx --from aws-sam-cli sam"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null 2>&1; then
  echo "Error: AWS credentials not configured"
  echo "Run: aws configure"
  exit 1
fi

echo "AWS Account:"
aws sts get-caller-identity
echo ""

# Read existing configuration from samconfig.toml
EXISTING_STACK=""
EXISTING_REGION=""
EXISTING_ENV=""
EXISTING_FFMPEG=""
EXISTING_GKEY=""
EXISTING_OPENAI=""
EXISTING_XIKEY=""

if [ -f "samconfig.toml" ]; then
  EXISTING_STACK=$(grep -A 20 "^\[default.deploy.parameters\]" samconfig.toml | grep "^stack_name" | head -n 1 | cut -d '=' -f 2 | tr -d ' "')
  [ -z "$EXISTING_STACK" ] && EXISTING_STACK=$(grep -A 20 "^\[default.global.parameters\]" samconfig.toml | grep "^stack_name" | head -n 1 | cut -d '=' -f 2 | tr -d ' "')

  EXISTING_REGION=$(grep -A 20 "^\[default.deploy.parameters\]" samconfig.toml | grep "^region" | head -n 1 | cut -d '=' -f 2 | tr -d ' "')
  [ -z "$EXISTING_REGION" ] && EXISTING_REGION=$(grep -A 20 "^\[default.global.parameters\]" samconfig.toml | grep "^region" | head -n 1 | cut -d '=' -f 2 | tr -d ' "')

  EXISTING_ENV=$(grep "parameter_overrides" samconfig.toml | grep -o 'Environment=\\"[^"]*\\"' | cut -d '"' -f 2)
  EXISTING_FFMPEG=$(grep "parameter_overrides" samconfig.toml | grep -o 'FFmpegLayerArn=\\"[^"]*\\"' | cut -d '"' -f 2)
  EXISTING_GKEY=$(grep "parameter_overrides" samconfig.toml | grep -o 'GKey=\\"[^"]*\\"' | cut -d '"' -f 2)
  EXISTING_OPENAI=$(grep "parameter_overrides" samconfig.toml | grep -o 'OpenAIKey=\\"[^"]*\\"' | cut -d '"' -f 2)
  EXISTING_XIKEY=$(grep "parameter_overrides" samconfig.toml | grep -o 'XIKey=\\"[^"]*\\"' | cut -d '"' -f 2)
fi

# Set defaults
DEFAULT_STACK="${EXISTING_STACK:-float-meditation}"
DEFAULT_REGION="${EXISTING_REGION:-us-east-1}"
DEFAULT_ENV="${EXISTING_ENV:-staging}"

# Check if configuration is needed
NEED_CONFIG=false
if [ -z "$EXISTING_FFMPEG" ] || [ -z "$EXISTING_GKEY" ] || [ -z "$EXISTING_OPENAI" ]; then
  NEED_CONFIG=true
fi

# Prompt for configuration if needed
if [ "$NEED_CONFIG" = true ]; then
  echo "Configuration required. Please provide the following:"
  echo ""

  read -p "Stack name [$DEFAULT_STACK]: " STACK_NAME
  STACK_NAME=${STACK_NAME:-$DEFAULT_STACK}

  read -p "AWS Region [$DEFAULT_REGION]: " REGION
  REGION=${REGION:-$DEFAULT_REGION}

  read -p "Environment (staging/production) [$DEFAULT_ENV]: " ENVIRONMENT
  ENVIRONMENT=${ENVIRONMENT:-$DEFAULT_ENV}

  if [ -n "$EXISTING_FFMPEG" ]; then
    echo "FFmpeg Layer ARN [current: ...${EXISTING_FFMPEG: -20}]:"
    read -p "  (press enter to keep existing): " FFMPEG_ARN
    FFMPEG_ARN=${FFMPEG_ARN:-$EXISTING_FFMPEG}
  else
    read -p "FFmpeg Layer ARN: " FFMPEG_ARN
  fi

  if [ -n "$EXISTING_GKEY" ]; then
    read -p "Google Gemini API key [****${EXISTING_GKEY: -4}]: " GKEY
    GKEY=${GKEY:-$EXISTING_GKEY}
  else
    read -p "Google Gemini API key: " GKEY
  fi

  if [ -n "$EXISTING_OPENAI" ]; then
    read -p "OpenAI API key [****${EXISTING_OPENAI: -4}]: " OPENAI_KEY
    OPENAI_KEY=${OPENAI_KEY:-$EXISTING_OPENAI}
  else
    read -p "OpenAI API key: " OPENAI_KEY
  fi

  if [ -n "$EXISTING_XIKEY" ]; then
    read -p "ElevenLabs API key [****${EXISTING_XIKEY: -4}] (optional): " XI_KEY
    XI_KEY=${XI_KEY:-$EXISTING_XIKEY}
  else
    read -p "ElevenLabs API key (optional, press enter to skip): " XI_KEY
    XI_KEY=${XI_KEY:-""}
  fi

  if [ -z "$FFMPEG_ARN" ] || [ -z "$GKEY" ] || [ -z "$OPENAI_KEY" ]; then
    echo "Error: Required parameters cannot be empty (FFmpeg ARN, Google Gemini key, OpenAI key)"
    exit 1
  fi

  echo ""
  echo "Saving configuration to samconfig.toml..."

  # Build parameter overrides string
  PARAM_OVERRIDES="Environment=\\\\\"$ENVIRONMENT\\\\\" FFmpegLayerArn=\\\\\"$FFMPEG_ARN\\\\\" GKey=\\\\\"$GKEY\\\\\" OpenAIKey=\\\\\"$OPENAI_KEY\\\\\""

  if [ -n "$XI_KEY" ]; then
    PARAM_OVERRIDES="$PARAM_OVERRIDES XIKey=\\\\\"$XI_KEY\\\\\""
  fi

  # Update samconfig.toml
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "/^\[default.global.parameters\]/,/^\[/ s|^stack_name = .*|stack_name = \"$STACK_NAME\"|" samconfig.toml
    sed -i '' "/^\[default.global.parameters\]/,/^\[/ s|^region = .*|region = \"$REGION\"|" samconfig.toml
    sed -i '' "/^\[default.deploy.parameters\]/,/^\[/ s|^stack_name = .*|stack_name = \"$STACK_NAME\"|" samconfig.toml
    sed -i '' "/^\[default.deploy.parameters\]/,/^\[/ s|^s3_prefix = .*|s3_prefix = \"$STACK_NAME\"|" samconfig.toml
    sed -i '' "/^\[default.deploy.parameters\]/,/^\[/ s|^# Parameter overrides.*|parameter_overrides = \"$PARAM_OVERRIDES\"|" samconfig.toml
    sed -i '' "/^\[default.deploy.parameters\]/,/^\[/ s|^# Format: parameter_overrides.*||" samconfig.toml
  else
    sed -i "/^\[default.global.parameters\]/,/^\[/ s|^stack_name = .*|stack_name = \"$STACK_NAME\"|" samconfig.toml
    sed -i "/^\[default.global.parameters\]/,/^\[/ s|^region = .*|region = \"$REGION\"|" samconfig.toml
    sed -i "/^\[default.deploy.parameters\]/,/^\[/ s|^stack_name = .*|stack_name = \"$STACK_NAME\"|" samconfig.toml
    sed -i "/^\[default.deploy.parameters\]/,/^\[/ s|^s3_prefix = .*|s3_prefix = \"$STACK_NAME\"|" samconfig.toml
    sed -i "/^\[default.deploy.parameters\]/,/^\[/ s|^# Parameter overrides.*|parameter_overrides = \"$PARAM_OVERRIDES\"|" samconfig.toml
    sed -i "/^\[default.deploy.parameters\]/,/^\[/ s|^# Format: parameter_overrides.*||" samconfig.toml
  fi

  echo "✓ Configuration saved"
  echo ""
fi

# Extract stack name for display
STACK_NAME=$(grep -A 20 "^\[default.deploy.parameters\]" samconfig.toml | grep "^stack_name" | head -n 1 | cut -d '=' -f 2 | tr -d ' "')
if [ -z "$STACK_NAME" ]; then
  STACK_NAME=$(grep -A 20 "^\[default.global.parameters\]" samconfig.toml | grep "^stack_name" | head -n 1 | cut -d '=' -f 2 | tr -d ' "')
fi

# Build and deploy
echo "[1/2] Building SAM application..."
$SAM_CMD build
echo "✓ Build complete"
echo ""

echo "[2/2] Deploying to AWS..."
echo "Stack: $STACK_NAME"
$SAM_CMD deploy
echo "✓ Deployment complete"
echo ""

echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""

# Get stack outputs
echo "Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs' \
  --output table

echo ""
echo "To view logs:"
echo "  npm run logs"
echo ""
