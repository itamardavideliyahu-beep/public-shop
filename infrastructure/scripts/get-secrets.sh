#!/bin/bash

# Script to retrieve secrets from Key Vault
# Usage: ./get-secrets.sh

set -e

# Check if running from correct directory
if [ ! -f "terraform.tfvars" ]; then
    echo "Error: terraform.tfvars not found. Please run from infrastructure/terraform directory"
    exit 1
fi

# Get Key Vault name from Terraform
KEY_VAULT_NAME=$(terraform output -raw key_vault_name 2>/dev/null || echo "")

if [ -z "$KEY_VAULT_NAME" ]; then
    echo "Error: Key Vault not found. Please run terraform apply first"
    exit 1
fi

echo "Retrieving secrets from Key Vault: $KEY_VAULT_NAME"
echo ""

# Get Flask Secret Key
echo "Flask SECRET_KEY:"
az keyvault secret show --vault-name $KEY_VAULT_NAME --name flask-secret-key --query value -o tsv
echo ""

# Get PostgreSQL Password
echo "PostgreSQL Password:"
az keyvault secret show --vault-name $KEY_VAULT_NAME --name postgres-password --query value -o tsv
echo ""

echo "Secrets retrieved successfully!"






