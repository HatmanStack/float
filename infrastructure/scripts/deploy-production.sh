#!/bin/bash
set -e  # Exit on error

echo "========================================="
echo "Float Meditation - PRODUCTION Deployment"
echo "========================================="
echo ""
echo "⚠️  WARNING: You are about to deploy to PRODUCTION!"
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INFRASTRUCTURE_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$INFRASTRUCTURE_DIR/template.yaml"
PARAMETER_FILE="$INFRASTRUCTURE_DIR/parameters/production.json"
STACK_NAME="float-meditation-production"

# Production deployment confirmation
read -p "Are you sure you want to deploy to PRODUCTION? (yes/NO): " -r
echo
if [[ ! $REPLY == "yes" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Check prerequisites
echo "Checking prerequisites..."

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "ERROR: SAM CLI not found"
    echo "Please install SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

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
echo "⚠️  Deploying to AWS Account:"
aws sts get-caller-identity
echo ""

# Second confirmation after seeing account
read -p "Confirm this is the correct PRODUCTION account? (yes/NO): " -r
echo
if [[ ! $REPLY == "yes" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Check if parameter file exists
if [ ! -f "$PARAMETER_FILE" ]; then
    echo "ERROR: Production parameter file not found: $PARAMETER_FILE"
    echo ""
    echo "Please create the production parameter file:"
    echo "  cd $INFRASTRUCTURE_DIR/parameters/"
    echo "  cp production-example.json production.json"
    echo "  # Edit production.json with your actual production API keys"
    exit 1
fi

# Check if parameter file contains placeholder values
if grep -q "YOUR_.*_API_KEY_HERE\|REPLACE_WITH_YOUR\|REPLACE_WITH_ACCOUNT_ID" "$PARAMETER_FILE"; then
    echo "ERROR: Production parameter file contains placeholder values!"
    echo "File: $PARAMETER_FILE"
    echo ""
    echo "Please edit the file and replace all placeholder values with actual production values."
    exit 1
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
if sam build --template "$TEMPLATE_FILE"; then
    echo "✓ Build successful"
    echo ""
else
    echo "ERROR: Build failed"
    exit 1
fi

# Step 3: Review change set
echo "Step 3: Creating change set for review..."
echo "Stack name: $STACK_NAME"
echo ""

# Create change set
CHANGE_SET_NAME="production-deploy-$(date +%Y%m%d-%H%M%S)"
sam deploy \
    --template-file .aws-sam/build/template.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides file://"$PARAMETER_FILE" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --no-execute-changeset \
    --changeset-name "$CHANGE_SET_NAME"

echo ""
echo "Change set created: $CHANGE_SET_NAME"
echo ""
echo "Review the change set in AWS Console:"
echo "https://console.aws.amazon.com/cloudformation"
echo ""

# Final confirmation
read -p "Review complete. Execute this change set? (yes/NO): " -r
echo
if [[ ! $REPLY == "yes" ]]; then
    echo "Deployment cancelled. Change set created but not executed."
    echo "You can execute it manually from the AWS Console."
    exit 0
fi

# Execute change set
echo "Executing change set..."
aws cloudformation execute-change-set \
    --change-set-name "$CHANGE_SET_NAME" \
    --stack-name "$STACK_NAME"

echo "Waiting for deployment to complete..."
aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME" || \
aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME"

# Step 4: Display outputs
echo ""
echo "========================================="
echo "PRODUCTION Deployment Complete!"
echo "========================================="
echo ""

echo "Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "To view production logs:"
echo "  aws logs tail /aws/lambda/float-meditation-production --follow"
echo ""
