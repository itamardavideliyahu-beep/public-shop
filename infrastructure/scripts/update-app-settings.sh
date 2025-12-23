#!/bin/bash

# Script to update App Service settings
# Usage: ./update-app-settings.sh KEY=VALUE [KEY2=VALUE2 ...]

set -e

# Check if running from correct directory
if [ ! -f "terraform.tfvars" ]; then
    echo "Error: terraform.tfvars not found. Please run from infrastructure/terraform directory"
    exit 1
fi

# Get App Service details
APP_NAME=$(terraform output -raw app_service_name 2>/dev/null || echo "")
RESOURCE_GROUP=$(terraform output -raw resource_group_name 2>/dev/null || echo "")

if [ -z "$APP_NAME" ] || [ -z "$RESOURCE_GROUP" ]; then
    echo "Error: App Service not found. Please run terraform apply first"
    exit 1
fi

# Check if settings provided
if [ $# -eq 0 ]; then
    echo "Usage: ./update-app-settings.sh KEY=VALUE [KEY2=VALUE2 ...]"
    echo "Example: ./update-app-settings.sh POSTS_PER_PAGE=30 MAX_IMAGE_SIZE=10485760"
    exit 1
fi

# Build settings string
SETTINGS=""
for arg in "$@"; do
    if [[ $arg == *"="* ]]; then
        SETTINGS="$SETTINGS $arg"
    else
        echo "Warning: Invalid format: $arg (should be KEY=VALUE)"
    fi
done

# Update settings
echo "Updating App Service settings..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings $SETTINGS

echo "Settings updated successfully!"
echo ""
echo "Restarting App Service..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
echo "App Service restarted!"







