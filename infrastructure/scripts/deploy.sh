#!/bin/bash

# Deployment script for Public Shop
# This script automates deployment tasks EXCEPT Terraform commands
# Terraform commands (init, plan, apply) should be run manually

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_note() {
    echo -e "${CYAN}[NOTE]${NC} $1"
}

# Check if running from correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")/terraform"

if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
    print_error "terraform.tfvars not found in $TERRAFORM_DIR"
    print_error "Please ensure Terraform has been initialized and applied manually first"
    exit 1
fi

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed (needed to read outputs)"
    exit 1
fi

if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    print_warn "Not logged in to Azure. Please run: az login"
    exit 1
fi

print_info "Prerequisites check passed"
echo ""

# Check if Terraform has been applied
print_note "⚠️  IMPORTANT: This script does NOT run Terraform commands"
print_note "   Please ensure you have run the following manually:"
print_note "   1. cd $TERRAFORM_DIR"
print_note "   2. terraform init"
print_note "   3. terraform plan"
print_note "   4. terraform apply"
echo ""

# Verify Terraform state exists
if [ ! -f "$TERRAFORM_DIR/terraform.tfstate" ]; then
    print_error "Terraform state not found. Please run 'terraform apply' first"
    exit 1
fi

# Get outputs from Terraform (read-only, doesn't modify anything)
print_info "Reading Terraform outputs..."
cd "$TERRAFORM_DIR"

ACR_NAME=$(terraform output -raw container_registry_name 2>/dev/null || echo "")
APP_NAME=$(terraform output -raw app_service_name 2>/dev/null || echo "")
RESOURCE_GROUP=$(terraform output -raw resource_group_name 2>/dev/null || echo "")

if [ -z "$ACR_NAME" ] || [ -z "$APP_NAME" ] || [ -z "$RESOURCE_GROUP" ]; then
    print_error "Could not read Terraform outputs. Please ensure Terraform has been applied"
    exit 1
fi

print_info "ACR Name: $ACR_NAME"
print_info "App Service Name: $APP_NAME"
print_info "Resource Group: $RESOURCE_GROUP"
echo ""

# Step 1: Pull and push base images (Redis, PostgreSQL) to ACR
read -p "Do you want to pull and push base images (Redis, PostgreSQL) to ACR? (yes/no): " pull_images
if [ "$pull_images" == "yes" ]; then
    print_info "Pulling and pushing base images to ACR..."
    
    ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
    
    # Login to ACR
    print_info "Logging into ACR..."
    az acr login --name $ACR_NAME
    
    # Pull Redis
    print_info "Pulling Redis image..."
    docker pull redis:7-alpine
    
    # Pull PostgreSQL
    print_info "Pulling PostgreSQL image..."
    docker pull postgres:15-alpine
    
    # Tag Redis
    print_info "Tagging Redis image..."
    docker tag redis:7-alpine "${ACR_LOGIN_SERVER}/redis:7"
    
    # Tag PostgreSQL
    print_info "Tagging PostgreSQL image..."
    docker tag postgres:15-alpine "${ACR_LOGIN_SERVER}/postgres:15-alpine"
    
    # Push Redis
    print_info "Pushing Redis image to ACR..."
    docker push "${ACR_LOGIN_SERVER}/redis:7"
    
    # Push PostgreSQL
    print_info "Pushing PostgreSQL image to ACR..."
    docker push "${ACR_LOGIN_SERVER}/postgres:15-alpine"
    
    print_info "Base images pushed successfully"
    echo ""
fi

# Step 2: Build and push application Docker image
read -p "Do you want to build and push application Docker image? (yes/no): " build_image
if [ "$build_image" == "yes" ]; then
    print_info "Building and pushing application Docker image..."
    
    ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
    
    # Login to ACR
    print_info "Logging into ACR..."
    az acr login --name $ACR_NAME
    
    # Navigate to project root
    PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
    cd "$PROJECT_ROOT"
    
    # Build
    print_info "Building Docker image..."
    docker build -t ${ACR_LOGIN_SERVER}/public-shop:latest .
    
    # Push
    print_info "Pushing Docker image to ACR..."
    docker push ${ACR_LOGIN_SERVER}/public-shop:latest
    
    print_info "Application Docker image pushed successfully"
    echo ""
fi

# Step 3: Run database migrations
read -p "Do you want to run database migrations? (yes/no): " run_migrations
if [ "$run_migrations" == "yes" ]; then
    print_info "Running database migrations..."
    
    print_info "Connecting to App Service..."
    print_info "App Service: $APP_NAME"
    print_info "Resource Group: $RESOURCE_GROUP"
    echo ""
    print_warn "You will be connected to the container. Run the following commands:"
    print_info "  flask db upgrade"
    print_info "  exit"
    echo ""
    read -p "Press Enter to connect to App Service..."
    
    az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP
fi

# Display outputs
echo ""
print_info "Deployment tasks completed!"
echo ""
print_info "Terraform outputs:"
cd "$TERRAFORM_DIR"
terraform output

print_info "Deployment script completed"