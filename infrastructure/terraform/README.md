# Terraform Configuration

This directory contains Terraform configuration for deploying the Public Shop application to Azure using **Azure Container Instances (ACI)**.

## Architecture

```
Azure Resources:
├── Resource Group
├── Container Registry (ACR)
│   ├── public-shop:latest
│   ├── redis:7
│   └── postgres:15-alpine
├── Container Instances (ACI)
│   ├── App Container (public-shop)
│   ├── PostgreSQL Container
│   └── Redis Container
├── Key Vault (secrets)
├── Storage Account (file storage)
└── Application Insights (monitoring)
```

## Files

### Core Configuration
- `main.tf` - Main configuration and local values
- `provider.tf` - Azure provider configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variables file

### Resources
- `resource-group.tf` - Azure Resource Group
- `container-registry.tf` - Azure Container Registry (ACR)
- `app-aci.tf` - Application Container Instance
- `database.tf` - PostgreSQL Container Instance
- `redis.tf` - Redis Container Instance
- `storage.tf` - Storage Account and containers
- `key-vault.tf` - Key Vault for secrets
- `app-insights.tf` - Application Insights

## Prerequisites

1. **Azure CLI**
   ```bash
   az --version
   ```

2. **Terraform**
   ```bash
   terraform --version
   ```

3. **Azure Login**
   ```bash
   az login
   ```

4. **Service Principal** (for Terraform)
   ```bash
   az ad sp create-for-rbac \
     --name "terraform-public-shop" \
     --role contributor \
     --scopes /subscriptions/{subscription-id}
   ```

## Quick Start

### 1. Configure Variables

Create `terraform.tfvars`:
```hcl
subscription_id = "your-subscription-id"
client_id       = "your-client-id"
client_secret   = "your-client-secret"
tenant_id       = "your-tenant-id"

project_name = "public-shop"
environment  = "poc"
location     = "eastus"
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan Deployment

```bash
terraform plan
```

### 4. Apply Configuration

```bash
terraform apply
```

**Note:** This will create the ACR but not push images yet.

### 5. Push Images to ACR

Run from project root:
```powershell
cd ../scripts
.\deploy.ps1
```

This script will:
- Pull Redis and PostgreSQL images from Docker Hub
- Push them to your ACR
- Build and push your application image

### 6. Apply Again (Create Containers)

```bash
terraform apply
```

Now that images are in ACR, Terraform will create the container instances.

### 7. Run Migrations

```bash
$RG = terraform output -raw resource_group_name
$APP_NAME = terraform output -raw app_container_name

az container exec \
  --resource-group $RG \
  --name $APP_NAME \
  --exec-command "flask db upgrade"
```

## Outputs

After deployment, you can view:

```bash
# All outputs
terraform output

# Specific output
terraform output app_service_url
```

### Available Outputs
- `app_service_url` - Application URL
- `app_container_ip` - Application IP address
- `app_container_fqdn` - Application FQDN
- `container_registry_name` - ACR name
- `container_registry_login_server` - ACR server
- `key_vault_name` - Key Vault name
- `postgresql_container_ip` - PostgreSQL IP
- `redis_container_ip` - Redis IP

## Common Commands

### View Resources
```bash
# List all resources in resource group
az resource list --resource-group rg-public-shop-poc --output table
```

### Check Container Status
```bash
az container list \
  --resource-group rg-public-shop-poc \
  --query "[].{Name:name, State:instanceView.state, IP:ipAddress.ip}" \
  --output table
```

### View Container Logs
```bash
az container logs \
  --resource-group rg-public-shop-poc \
  --name aci-app-public-shop-poc \
  --container-name app
```

### Restart Container
```bash
az container restart \
  --resource-group rg-public-shop-poc \
  --name aci-app-public-shop-poc
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning:** This will delete all resources and cannot be undone!

## Important Notes

### Sensitive Files
The following files are **NOT** committed to Git (in `.gitignore`):
- `terraform.tfstate` - Contains sensitive data
- `terraform.tfvars` - Contains credentials
- `tfplan` - May contain sensitive data
- `.terraform/` - Terraform plugins

### State Management
- State is stored locally (not recommended for production)
- For production, use remote state (Azure Storage, Terraform Cloud, etc.)

### Costs
- Container Instances: Pay per second
- Container Registry: Basic tier (~$5/month)
- Storage Account: Pay per usage (very minimal)
- Key Vault: Pay per operation (very minimal)
- Application Insights: Pay per GB (free tier available)

**Estimated monthly cost: $10-20 for POC environment**

## Troubleshooting

### Container won't start
1. Check if images are in ACR:
   ```bash
   az acr repository list --name acrpublicshoppoc
   ```

2. Check container logs:
   ```bash
   az container logs --resource-group rg-public-shop-poc --name aci-app-public-shop-poc --container-name app
   ```

3. Check container events:
   ```bash
   az container show --resource-group rg-public-shop-poc --name aci-app-public-shop-poc --query "instanceView.events"
   ```

### Can't connect to application
1. Verify container is running:
   ```bash
   az container show --resource-group rg-public-shop-poc --name aci-app-public-shop-poc --query "instanceView.state"
   ```

2. Check IP and port:
   ```bash
   terraform output app_service_url
   ```

3. Test connectivity:
   ```bash
   curl http://$(terraform output -raw app_container_ip):8000/health
   ```

## Next Steps

After deployment:
1. Configure GitHub Secrets for CI/CD
2. Push code to trigger automated deployments
3. Monitor application in Azure Portal
4. Review Application Insights for performance metrics

For more information, see the main project documentation.

