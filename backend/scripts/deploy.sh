#!/bin/bash
set -e

# Source helper functions
source "$(dirname "$0")/deploy-helpers.sh"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration file paths
CONFIG_FILE=".deploy-config.json"
SAM_CONFIG_FILE="samconfig.toml"
TEMPLATE_FILE="template.yaml"

# Function to print status
print_status() {
    echo -e "${GREEN}[*] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[x] $1${NC}"
}

# Pre-flight checks
print_status "Running pre-flight checks..."

if [ ! -f "$TEMPLATE_FILE" ]; then
    print_error "Error: template.yaml not found. Please run this script from the backend/ directory."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    print_error "Error: AWS CLI is not installed or not in PATH."
    exit 1
fi

if ! command -v sam &> /dev/null; then
    print_error "Error: SAM CLI is not installed or not in PATH."
    exit 1
fi

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ $? -ne 0 ]; then
    print_error "Error: Failed to get AWS account ID. Please check your AWS credentials."
    exit 1
fi
print_status "Using AWS Account: $AWS_ACCOUNT_ID"

# Configuration Discovery
print_status "Checking configuration..."

STACK_NAME="float-meditation-dev"
REGION="us-east-1"
FFMPEG_LAYER_ARN="arn:aws:lambda:us-east-1:145266761615:layer:ffmpeg:4"
GEMINI_API_KEY=""
OPENAI_API_KEY=""
ELEVENLABS_API_KEY=""
VOICE_ID="jKX50Q2OBT1CsDwwcTkZ"
SIMILARITY_BOOST="0.7"
STABILITY="0.3"
VOICE_STYLE="0.3"

if [ -f "$CONFIG_FILE" ]; then
    print_status "Loading configuration from $CONFIG_FILE"
    if command -v jq &> /dev/null; then
        STACK_NAME=$(jq -r .stackName "$CONFIG_FILE")
        REGION=$(jq -r .region "$CONFIG_FILE")
        FFMPEG_LAYER_ARN=$(jq -r .ffmpegLayerArn "$CONFIG_FILE")
        GEMINI_API_KEY=$(jq -r .geminiApiKey "$CONFIG_FILE")
        OPENAI_API_KEY=$(jq -r .openaiApiKey "$CONFIG_FILE")
        ELEVENLABS_API_KEY=$(jq -r .elevenLabsApiKey "$CONFIG_FILE")
        VOICE_ID=$(jq -r .voiceId "$CONFIG_FILE")
        SIMILARITY_BOOST=$(jq -r .similarityBoost "$CONFIG_FILE")
        STABILITY=$(jq -r .stability "$CONFIG_FILE")
        VOICE_STYLE=$(jq -r .voiceStyle "$CONFIG_FILE")
    else
        # Fallback to Python
        STACK_NAME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['stackName'])")
        REGION=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['region'])")
        FFMPEG_LAYER_ARN=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['ffmpegLayerArn'])")
        GEMINI_API_KEY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['geminiApiKey'])")
        OPENAI_API_KEY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['openaiApiKey'])")
        ELEVENLABS_API_KEY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['elevenLabsApiKey'])")
        VOICE_ID=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['voiceId'])")
        SIMILARITY_BOOST=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['similarityBoost'])")
        STABILITY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['stability'])")
        VOICE_STYLE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['voiceStyle'])")
    fi
fi

# Interactive Prompts
if [ -z "$GEMINI_API_KEY" ] || [ -z "$OPENAI_API_KEY" ]; then
    print_warning "Missing required configuration. Starting interactive setup..."

    if [ -z "$GEMINI_API_KEY" ]; then
        read -p "Enter Google Gemini API Key: " GEMINI_API_KEY
    fi

    if [ -z "$OPENAI_API_KEY" ]; then
        read -p "Enter OpenAI API Key: " OPENAI_API_KEY
    fi

    if [ -z "$ELEVENLABS_API_KEY" ] && [ ! -f "$CONFIG_FILE" ]; then
         read -p "Enter ElevenLabs API Key (optional, press Enter to skip): " ELEVENLABS_API_KEY
    fi

    # Save configuration
    print_status "Saving configuration to $CONFIG_FILE"
    cat > "$CONFIG_FILE" <<EOF
{
  "stackName": "$STACK_NAME",
  "region": "$REGION",
  "ffmpegLayerArn": "$FFMPEG_LAYER_ARN",
  "geminiApiKey": "$GEMINI_API_KEY",
  "openaiApiKey": "$OPENAI_API_KEY",
  "elevenLabsApiKey": "$ELEVENLABS_API_KEY",
  "voiceId": "$VOICE_ID",
  "similarityBoost": "$SIMILARITY_BOOST",
  "stability": "$STABILITY",
  "voiceStyle": "$VOICE_STYLE"
}
EOF
fi

# Generate samconfig.toml
print_status "Generating $SAM_CONFIG_FILE..."
generate_samconfig_toml "$STACK_NAME" "$REGION" "$FFMPEG_LAYER_ARN" "$GEMINI_API_KEY" "$OPENAI_API_KEY" "$ELEVENLABS_API_KEY" "$SIMILARITY_BOOST" "$STABILITY" "$VOICE_STYLE" "$VOICE_ID" "$SAM_CONFIG_FILE"

# Build Phase
print_status "Building SAM application..."
sam build

# Deployment Phase
print_status "Deploying to AWS..."
sam deploy

# Post-Deployment
print_status "Deployment complete. Generating frontend configuration..."

# Get Stack Outputs
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)
AUDIO_BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query "Stacks[0].Outputs[?OutputKey=='AudioBucketName'].OutputValue" --output text)

if [ -z "$API_ENDPOINT" ] || [ "$API_ENDPOINT" == "None" ]; then
    print_warning "Could not retrieve API Endpoint from stack outputs."
else
    print_status "API Endpoint: $API_ENDPOINT"
fi

if [ -z "$AUDIO_BUCKET" ] || [ "$AUDIO_BUCKET" == "None" ]; then
    print_warning "Could not retrieve Audio Bucket from stack outputs."
else
    print_status "Audio Bucket: $AUDIO_BUCKET"
fi

# Update Frontend .env
FRONTEND_ENV_FILE="../frontend/.env"
print_status "Updating $FRONTEND_ENV_FILE..."
generate_frontend_env "$API_ENDPOINT" "$AUDIO_BUCKET" "$FRONTEND_ENV_FILE"

print_status "Success! Backend deployed and frontend configured."
