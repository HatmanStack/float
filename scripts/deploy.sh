#!/bin/bash
set -euo pipefail

# Float Backend Deployment Script
# Deploys the backend to AWS using SAM CLI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
ENV_FILE="$BACKEND_DIR/.env.deploy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Phase 1: Load Configuration
# =============================================================================
load_config() {
    log_info "Loading configuration..."

    # Source .env.deploy if it exists
    if [ -f "$ENV_FILE" ]; then
        log_info "Loading variables from $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    else
        log_warn ".env.deploy not found. Will prompt for required values."
    fi
}

# =============================================================================
# Phase 2: Interactive Prompts for Missing Variables
# =============================================================================
prompt_for_variables() {
    log_info "Checking required configuration..."

    # AWS Region
    if [ -z "${AWS_REGION:-}" ]; then
        read -p "Enter AWS Region [us-east-1]: " AWS_REGION
        AWS_REGION="${AWS_REGION:-us-east-1}"
    fi
    log_info "AWS Region: $AWS_REGION"

    # Environment
    if [ -z "${ENVIRONMENT:-}" ]; then
        read -p "Enter Environment (staging/production) [production]: " ENVIRONMENT
        ENVIRONMENT="${ENVIRONMENT:-production}"
    fi
    log_info "Environment: $ENVIRONMENT"

    # Stack Name
    STACK_NAME="${STACK_NAME:-float-backend-$ENVIRONMENT}"
    log_info "Stack Name: $STACK_NAME"

    # Gemini API Key
    if [ -z "${G_KEY:-}" ]; then
        read -sp "Enter Gemini API Key (G_KEY): " G_KEY
        echo
        if [ -z "$G_KEY" ]; then
            log_error "Gemini API Key is required"
            exit 1
        fi
    fi
    log_success "Gemini API Key: [SET]"

    # OpenAI API Key
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        read -sp "Enter OpenAI API Key: " OPENAI_API_KEY
        echo
        if [ -z "$OPENAI_API_KEY" ]; then
            log_error "OpenAI API Key is required"
            exit 1
        fi
    fi
    log_success "OpenAI API Key: [SET]"

    # S3 Data Bucket
    if [ -z "${S3_DATA_BUCKET:-}" ]; then
        read -p "Enter S3 Data Bucket name [float-cust-data]: " S3_DATA_BUCKET
        S3_DATA_BUCKET="${S3_DATA_BUCKET:-float-cust-data}"
    fi
    log_info "S3 Data Bucket: $S3_DATA_BUCKET"

    # S3 Audio Bucket
    if [ -z "${S3_AUDIO_BUCKET:-}" ]; then
        read -p "Enter S3 Audio Bucket name [audio-er-lambda]: " S3_AUDIO_BUCKET
        S3_AUDIO_BUCKET="${S3_AUDIO_BUCKET:-audio-er-lambda}"
    fi
    log_info "S3 Audio Bucket: $S3_AUDIO_BUCKET"
}

# =============================================================================
# Phase 3: Validate Prerequisites
# =============================================================================
validate_prerequisites() {
    log_info "Validating prerequisites..."

    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        log_error "SAM CLI not found. Install with: pip install aws-sam-cli"
        exit 1
    fi
    log_success "SAM CLI found: $(sam --version)"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install AWS CLI."
        exit 1
    fi
    log_success "AWS CLI found: $(aws --version | head -1)"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Docker is required for SAM build."
        exit 1
    fi
    log_success "Docker found: $(docker --version)"

    # Verify AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    log_success "AWS credentials valid"

    # Check template exists
    if [ ! -f "$BACKEND_DIR/template.yaml" ]; then
        log_error "template.yaml not found at $BACKEND_DIR/template.yaml"
        exit 1
    fi
    log_success "SAM template found"
}

# =============================================================================
# Phase 4: Create/Verify Deployment Bucket
# =============================================================================
setup_deployment_bucket() {
    DEPLOY_BUCKET="sam-deploy-float-${AWS_REGION}"
    log_info "Checking deployment bucket: $DEPLOY_BUCKET"

    if aws s3 ls "s3://$DEPLOY_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
        log_info "Creating deployment bucket..."
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3 mb "s3://$DEPLOY_BUCKET" --region "$AWS_REGION"
        else
            aws s3 mb "s3://$DEPLOY_BUCKET" --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi
        log_success "Deployment bucket created"
    else
        log_success "Deployment bucket exists"
    fi
}

# =============================================================================
# Phase 5: Build
# =============================================================================
build_application() {
    log_info "Building application with SAM..."
    cd "$BACKEND_DIR"

    sam build \
        --template-file template.yaml \
        --use-container \
        --parallel

    log_success "Build completed"
}

# =============================================================================
# Phase 6: Deploy
# =============================================================================
deploy_application() {
    log_info "Deploying to AWS..."
    cd "$BACKEND_DIR"

    sam deploy \
        --template-file .aws-sam/build/template.yaml \
        --stack-name "$STACK_NAME" \
        --s3-bucket "$DEPLOY_BUCKET" \
        --s3-prefix "$STACK_NAME" \
        --region "$AWS_REGION" \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
        --no-confirm-changeset \
        --no-fail-on-empty-changeset \
        --parameter-overrides \
            "Environment=$ENVIRONMENT" \
            "GeminiApiKey=$G_KEY" \
            "OpenAIApiKey=$OPENAI_API_KEY" \
            "S3DataBucket=$S3_DATA_BUCKET" \
            "S3AudioBucket=$S3_AUDIO_BUCKET"

    log_success "Deployment completed"
}

# =============================================================================
# Phase 7: Post-Deploy - Get Outputs
# =============================================================================
post_deploy() {
    log_info "Retrieving stack outputs..."

    # Get API URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
        --output text)

    FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
        --output text)

    echo ""
    echo "=============================================="
    log_success "Deployment Complete!"
    echo "=============================================="
    echo ""
    echo -e "${GREEN}API URL:${NC} $API_URL"
    echo -e "${GREEN}Lambda Function:${NC} $FUNCTION_NAME"
    echo -e "${GREEN}Region:${NC} $AWS_REGION"
    echo -e "${GREEN}Environment:${NC} $ENVIRONMENT"
    echo ""
    echo "=============================================="
    echo "Frontend Configuration"
    echo "=============================================="
    echo ""
    echo "Add to your frontend .env file:"
    echo ""
    echo -e "${YELLOW}EXPO_PUBLIC_LAMBDA_FUNCTION_URL=$API_URL${NC}"
    echo ""
    echo "Or for Expo app.config.js:"
    echo ""
    echo -e "${YELLOW}EXPO_PUBLIC_API_GATEWAY_URL=$API_URL${NC}"
    echo ""
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    echo ""
    echo "=============================================="
    echo "  Float Backend Deployment"
    echo "=============================================="
    echo ""

    load_config
    prompt_for_variables
    validate_prerequisites
    setup_deployment_bucket
    build_application
    deploy_application
    post_deploy
}

# Run main
main "$@"
