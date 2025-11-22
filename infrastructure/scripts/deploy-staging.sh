#!/bin/bash
set -e  # Exit on error

echo "========================================="
echo "Float Meditation - Staging Deployment"
echo "========================================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INFRASTRUCTURE_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$INFRASTRUCTURE_DIR/template.yaml"
PARAMETER_FILE="$INFRASTRUCTURE_DIR/parameters/staging.json"
STACK_NAME="float-meditation-staging"

# Check prerequisites
echo "Checking prerequisites..."

# Check if SAM CLI is installed
if ! command -v uvx &> /dev/null; then
    echo "ERROR: uv not found"
    echo "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
SAM_CMD="uvx --from aws-sam-cli sam"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo "Verifying AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured or invalid"
    echo "Run: aws configure"
    exit 1
fi

# Display AWS account info
echo "AWS Account:"
aws sts get-caller-identity
echo ""

# Check if parameter file exists
if [ ! -f "$PARAMETER_FILE" ]; then
    echo "ERROR: Parameter file not found: $PARAMETER_FILE"
    echo ""
    echo "Please create the parameter file:"
    echo "  cd $INFRASTRUCTURE_DIR/parameters/"
    echo "  cp staging-example.json staging.json"
    echo "  # Edit staging.json with your actual API keys and configuration"
    exit 1
fi

# Check if parameter file contains placeholder values
if grep -q "YOUR_.*_API_KEY_HERE\|REPLACE_WITH_YOUR\|REPLACE_WITH_ACCOUNT_ID" "$PARAMETER_FILE"; then
    echo "WARNING: Parameter file contains placeholder values!"
    echo "File: $PARAMETER_FILE"
    echo ""
    echo "Please edit the file and replace all placeholder values with actual values:"
    echo "  - GoogleGeminiApiKey"
    echo "  - OpenAIApiKey"
    echo "  - FFmpegLayerArn"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

echo "✓ Prerequisites check passed"
echo ""

# Step 1: Validate template
echo "Step 1: Validating SAM template..."
if ! "$SCRIPT_DIR/validate-template.sh"; then
    echo "ERROR: Template validation failed"
    exit 1
fi

# Step 2: Build Lambda package
echo "Step 2: Building Lambda package..."
cd "$INFRASTRUCTURE_DIR"
if $SAM_CMD build --template "$TEMPLATE_FILE"; then
    echo "✓ Build successful"
    echo ""
else
    echo "ERROR: Build failed"
    exit 1
fi

# Step 3: Deploy to AWS
echo "Step 3: Deploying to AWS..."
echo "Stack name: $STACK_NAME"
echo "Parameter file: $PARAMETER_FILE"
echo ""

# Check if this is first deployment (samconfig.toml doesn't exist)
if [ ! -f "$INFRASTRUCTURE_DIR/samconfig.toml" ]; then
    echo "First deployment detected - using guided mode"
    echo ""
    $SAM_CMD deploy \
        --template-file .aws-sam/build/template.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides file://"$PARAMETER_FILE" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --guided
else
    echo "Using existing configuration from samconfig.toml"
    echo ""
    $SAM_CMD deploy \
        --template-file .aws-sam/build/template.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides file://"$PARAMETER_FILE" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --no-confirm-changeset
fi

# Step 4: Display outputs
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""

echo "Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "To test the deployment:"
echo "  cd $INFRASTRUCTURE_DIR"
echo "  curl -X POST <ApiEndpoint> -H 'Content-Type: application/json' -d @test-requests/summary-request.json"
echo ""
echo "To view logs:"
echo "  aws logs tail /aws/lambda/float-meditation-staging --follow"
echo ""
