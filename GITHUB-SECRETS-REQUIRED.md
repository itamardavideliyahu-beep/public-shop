# GitHub Secrets Configuration

## Required Secrets for CI/CD Pipeline

### 1. Azure Credentials (for Terraform & ACI)

```bash
AZURE_CLIENT_ID       = "<your-service-principal-client-id>"
AZURE_CLIENT_SECRET   = "<your-service-principal-client-secret>"
AZURE_SUBSCRIPTION_ID = "<your-subscription-id>"
AZURE_TENANT_ID       = "<your-tenant-id>"
```

**Get these from:**
```bash
az ad sp show --id <your-service-principal-client-id>
```

### 2. Azure Credentials JSON (for Azure Login Action)

```bash
AZURE_CREDENTIALS = '{
  "clientId": "<your-client-id>",
  "clientSecret": "<your-client-secret>",
  "subscriptionId": "<your-subscription-id>",
  "tenantId": "<your-tenant-id>"
}'
```

### 3. Azure Container Registry

```bash
AZURE_CONTAINER_REGISTRY          = "acrpublicshoppoc.azurecr.io"
AZURE_CONTAINER_REGISTRY_USERNAME = "<acr-username>"
AZURE_CONTAINER_REGISTRY_PASSWORD = "<acr-password>"
```

**Get ACR credentials:**
```bash
az acr credential show --name acrpublicshoppoc --resource-group rg-public-shop-poc
```

### 4. Email Configuration (Gmail App Password)

```bash
MAIL_USERNAME = "publicshop456@gmail.com"
MAIL_PASSWORD = "gxit brfo rfgi wvmu"
```

---

## How to Add Secrets to GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name shown above
5. Click **Add secret**

---

## Verification

After adding all secrets, you can verify by:
1. Go to **Actions** tab
2. Run **CD Pipeline** manually (workflow_dispatch)
3. Check that all steps pass

---

## Current Secrets Status

Check which secrets are configured:
- Go to: https://github.com/itamardavideliyahu-beep/public-shop/settings/secrets/actions

You should see:
- ✅ AZURE_CLIENT_ID
- ✅ AZURE_CLIENT_SECRET
- ✅ AZURE_SUBSCRIPTION_ID
- ✅ AZURE_TENANT_ID
- ✅ AZURE_CREDENTIALS
- ✅ AZURE_CONTAINER_REGISTRY
- ✅ AZURE_CONTAINER_REGISTRY_USERNAME
- ✅ AZURE_CONTAINER_REGISTRY_PASSWORD
- ✅ MAIL_USERNAME
- ✅ MAIL_PASSWORD

