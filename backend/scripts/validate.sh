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

if [ ! -f "template.yaml" ]; then
    print_error "Error: template.yaml not found. Please run this script from the backend/ directory."
    exit 1
fi

print_status "Validating SAM template..."
if sam validate --template template.yaml --lint; then
    print_status "Template is valid!"
    exit 0
else
    print_error "Template validation failed!"
    exit 1
fi
